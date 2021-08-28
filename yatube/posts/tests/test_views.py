import random

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Follow
from . import func_for_tests as test_func

User = get_user_model()
page_count = settings.GLOBALS['page_count']
view_test = {
    'about:author': {'template': 'about/author.html'},

    'about:tech': {'template': 'about/tech.html'},

    'posts:main': {'template': 'posts/index.html'},

    'posts:group-posts': {
        'template': 'posts/group_list.html',
        'slugs': ['slug']
    },

    'posts:profile': {
        'template': 'posts/profile.html',
        'slugs': ['username']
    },

    'posts:post_detail': {
        'template': 'posts/post_detail.html',
        'slugs': ['post_id']
    },

    'posts:post_edit': {
        'template': 'posts/create_post.html',
        'slugs': ['post_id'],
    },

    'posts:post_create': {'template': 'posts/create_post.html'},

    'login': {'template': 'users/login.html'}
}

has_paginator = {'posts:main': 'post_cnt',
                 'posts:group-posts': 'post_group_cnt',
                 'posts:profile': 'post_user_cnt'}

context_dict = {
    'posts:main': {
        'title': 'Последние обновления на сайте',
        'headline': 'Последние обновления на сайте',
        'page_obj': ['text']
    },
    'posts:group-posts': {
        'title': 'Записи сообщества ',
        'add_title': 'group',
        'group': 'group',
        'page_obj': ['text']
    },
    'posts:profile': {
        'author': 'user',
        'author_name': 'username_full',
        'page_obj': ['text']
    },
    'posts:post_detail': {
        'post': ['id']
    },
    'posts:post_edit': {
        'form': True
    }
}
test_forms = ['posts:post_create', 'posts:post_edit']

cache_url = 'posts:main'

follow_post = 'posts:follow_index'
profile_follow = 'posts:profile_follow'
profile_unfollow = 'posts:profile_unfollow'


class TaskPagesTests(TestCase):

    def setUp(self):
        self.slug = 'test-group-1'
        self.description = 'Текст1'
        self.title = 'VIEW_TEST_1'
        self.group = Group.objects.create(
            title=self.title,
            description=self.description,
            slug=self.slug,
        )

        group2 = Group.objects.create(
            title='VIEW_TEST_2',
            description='Текст2',
            slug='test-group-2',
        )

        # Создаем авторизованный клиент
        self.username = 'StasBasov'
        self.user = User.objects.create_user(username=self.username,
                                             first_name='Q',
                                             last_name='Q')
        self.username_full = self.user.get_full_name()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        # Второй и третий пользователь для теста подписки
        self.user2, self.user3 = [
            User.objects.create_user(username=f'author{x}')
            for x in range(2, 4)
        ]

        # User неавтор. для теста
        user_1 = User.objects.create_user(username='TestUser')

        # Один пост для теста
        self.text = '---'
        self.post = Post.objects.create(text=self.text,
                                        author=self.user,
                                        group=self.group)
        self.post_id = self.post.id

        # Для теста пагинатора
        [Post.objects.create(group=random.choice([self.group, group2]),
                             author=random.choice([self.user, user_1]),
                             text=self.text) for _ in range(99)]

        self.use_urls = test_func.get_use_urls(self, view_test)

        # Для теста кэша
        self.cache_text = 'QWERTYUIOPASDFGH'
        self.cache_post = Post.objects.create(
            group=self.group,
            author=self.user,
            text=self.cache_text)

        # Вспомогательные переменные
        self.post_cnt = Post.objects.count()
        self.post_group_cnt = Post.objects.filter(group=self.group).count()
        self.post_user_cnt = Post.objects.filter(author=self.user).count()

    def test_template(self):
        """Тест темплейтов."""
        for name, reverse_name in self.use_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, view_test[name]['template'])

    def test_paginator(self):
        """Тест пагинатора."""
        for name, cnt_arg in has_paginator.items():
            cnt = getattr(self, cnt_arg)
            first_page_cnt = min(page_count, cnt)
            last_page = ((cnt - 1) // page_count) + 1
            last_page_cnt = cnt % page_count
            last_page_cnt = last_page_cnt if last_page_cnt else page_count
            response = self.authorized_client.get(self.use_urls[name])
            self.assertEqual(len(response.context['page_obj']),
                             min(10, first_page_cnt),
                             msg='Ошибка в количестве записей для'
                                 f'первой страницы {name}. ')
            if last_page > 1:
                response = (
                    self.authorized_client.get(self.use_urls[name]
                                               + f'?page={last_page}'))
                self.assertEqual(len(response.context['page_obj']),
                                 last_page_cnt,
                                 msg='Ошибка в количестве записей для '
                                     f'последней страницы {name}. '
                                 )

    def assert_page_obj(self, page_obj, response_context):
        first_object = response_context['page_obj'][0]
        for category in page_obj:
            with self.subTest(category=category):
                self.assertIn(getattr(first_object, category),
                              [getattr(self, category), self.cache_text])

    def assert_title(self, title, context, response_context):
        add_title = context.get('add_title', '')
        if add_title:
            title += str(getattr(self, add_title))
        with self.subTest(title=title):
            self.assertEqual(response_context['title'], title)

    def assert_headline(self, headline, response_context):
        with self.subTest(headline=headline):
            self.assertEqual(response_context['headline'], headline)

    def assert_objects_key(self, context, response_context):
        objects_key = ['group', 'author']
        for obj in objects_key:
            entity = context.get(obj)
            if not entity:
                continue
            response_group = response_context[obj]
            with self.subTest(entity=obj):
                self.assertEqual(response_group,
                                 getattr(self, entity))

    def assert_post(self, post, response_context):
        response_post = response_context['post']
        for atr in post:
            with self.subTest(post_atribute=atr):
                self.assertEqual(getattr(response_post, atr),
                                 getattr(self.post, atr))

    def assert_form_text(self, response_context, name):
        response_text = response_context['form']['text'].value()
        with self.subTest(form_atr=name):
            self.assertIn(response_text, [self.text, self.cache_text])

    def test_context(self):
        """
        Шаблон контекста.
        Тестим: group/author/author_name/post/page_obj/title/headline.
        """
        for name, context in context_dict.items():
            response = self.authorized_client.get(self.use_urls[name])
            response_context = response.context

            # Тест возврата правильного поста списка
            page_obj = context.get('page_obj')  # Не понял, он и так в цикле:(
            if page_obj:
                self.assert_page_obj(page_obj, response_context)

            # Тест возврата правильного title
            title = context.get('title')
            if title:
                self.assert_title(title, context, response_context)

            # Тест возврата правильного headline
            headline = context.get('headline')
            if headline:
                self.assert_headline(headline, response_context)

            # Тест возврата правильных объектов
            self.assert_objects_key(context, response_context)

            # Тест возврата правильного поста
            post = context.get('post')
            if post:
                self.assert_post(post, response_context)

            # Тест возврата сохраненного текста в посте
            form_text = context.get('form')
            if form_text:
                self.assert_form_text(response_context, name)

    def test_form(self):
        """Шаблон сформирован с правильной формой."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for name in test_forms:
            response = self.authorized_client.get(self.use_urls[name])

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_cash(self):
        def response_page():
            response = self.authorized_client.get(
                reverse('posts:main')).content.decode('UTF-8')
            return response

        cache.clear()
        self.assertIn(self.cache_text, response_page())
        self.cache_post.delete()
        self.assertIn(self.cache_text, response_page())
        cache.clear()
        self.assertNotIn(self.cache_text, response_page())

    def test_following(self):
        """Тест проверки механизма подписки."""
        user_list = [self.user2, self.user3]
        posts = [Post.objects.create(
            text=f'Пост пользователя {num + 1}',
            author=usr,
            group=self.group)
            for num, usr in enumerate(user_list)]
        # Подписка
        self.authorized_client.get(
            reverse(profile_follow, kwargs={'username': user_list[1]}))
        following = self.authorized_client.get(reverse(follow_post))
        self.assertEqual(posts[1].text,
                         following.context['page_obj'][0].text,
                         msg='Подписка не работает')
        self.authorized_client.get(
            reverse(profile_unfollow, kwargs={'username': self.user3}))

    def test_unfollowing(self):
        """Тест проверки механизма отписки."""
        test_text = 'Пост пользователя 1'
        Post.objects.create(
            text=test_text,
            author=self.user2,
            group=self.group)
        Follow.objects.create(user=self.user, author=self.user2)
        following = self.authorized_client.get(reverse(follow_post))
        self.assertEqual(test_text,
                         following.context['page_obj'][0].text,
                         msg='Подписка не найдена')
        self.authorized_client.get(
            reverse(profile_unfollow, kwargs={'username': self.user2}))
        following = self.authorized_client.get(reverse(follow_post))
        self.assertFalse(len(following.context['page_obj']),
                         msg='Отписка не работает')
