from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post
from . import func_for_tests as test_func

# Тестируемые урлы и их параметры
# ключ - имя урла
# permission - кто имеет доступ / slugs - используемые слаги
# Редирект урла в зависимости от типа пользователя
urls_test = {
    'about:author': {'permission': 'all',
                     'template': 'about/author.html'},

    'about:tech': {'permission': 'all',
                   'template': 'about/tech.html'},

    'posts:main': {'permission': 'all',
                   'template': 'posts/index.html'},

    'posts:group-posts': {'permission': 'all',
                          'template': 'posts/group_list.html',
                          'slugs': ['slug']},

    'posts:profile': {'permission': 'all',
                      'template': 'posts/profile.html',
                      'slugs': ['username']},

    'posts:post_detail': {'permission': 'all',
                          'template': 'posts/post_detail.html',
                          'slugs': ['post_id']},

    'posts:post_edit': {'permission': 'author',
                        'template': 'posts/create_post.html',
                        'slugs': ['post_id'],
                        'redirect': {'all': 'login',
                                     'auth': 'posts:profile'}
                        },

    'posts:post_create': {'permission': 'auth',
                          'template': 'posts/create_post.html',
                          'redirect': {'all': 'login'}
                          },

    'login': {'permission': 'all',
              'template': 'users/login.html',
              }
}

template_404 = 'core/404.html'

# Словарь доступных url различным пользователям
urls_permission = {}
for permission in ['all', 'auth', 'author']:
    urls_permission[permission] = [key for key, value in urls_test.items()
                                   if value['permission'] == permission]

User = get_user_model()


class TaskURLTests(TestCase):

    def setUp(self):
        # Новая группа
        group = Group.objects.create(
            title='URL_TEST',
            description='Текст',
            slug='test-group',
        )
        self.slug = group.slug
        # Обычный НЕ авторизованый клиент
        self.guest_client = Client()

        # Создаем авторизованый клиент 1
        self.username = 'author1'
        self.user1 = User.objects.create_user(username=self.username)
        # Пост для теста от клинета 1
        post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user1,
            group=group,
        )
        self.post_id = post.id
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)

        # Создаем авторизованый клиент 2
        self.user2 = User.objects.create_user(username='author2')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

        # Cоздаем урлы со слагами:
        self.use_urls = test_func.get_use_urls(self, urls_test)

    def test_access(self):
        # Проверяем доступность всех урлов пользователям (в т.ч залогеным)
        access_users = {'all': self.guest_client}
        for type_user, urls in urls_permission.items():
            use_user = access_users.get(type_user, self.authorized_client1)
            for url in urls:
                with self.subTest(field=url):
                    response = use_user.get(self.use_urls[url])
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        # 404 при недоступной странице
        url = 'unexisting_page/'
        with self.subTest(field=url):
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
            self.assertTemplateUsed(
                response,
                template_404,
                msg_prefix='Используется не кастомный шаблон')

    def test_redirect(self):
        # Проверка редиректа при отсутствии доступа
        user_redirect = {'auth': self.guest_client,
                         'author': self.authorized_client2}
        for type_user in user_redirect.keys():
            use_user = user_redirect[type_user]
            for url in urls_permission[type_user]:
                with self.subTest(field=url):
                    response = use_user.get(self.use_urls[url])
                    self.assertEqual(response.status_code,
                                     HTTPStatus.FOUND)

    def test_correct_redirect(self):
        """Проверка правильного редиректа."""
        # Выбор юзера редиректа
        user_redirect = {'all': self.guest_client,
                         'auth': self.authorized_client2}
        # Отбор урлов при редиректе
        urls_with_redirect = [url for url, value in urls_test.items()
                              if value.get('redirect')]
        # Словарь урлов для теста (для всех/авториз.)
        redirect_dict = {'all': {}, 'auth': {}}
        for url in urls_with_redirect:
            get_redir_for_all = urls_test[url]['redirect'].get('all', None)
            get_redir_for_auth = urls_test[url]['redirect'].get('auth', None)
            # Добавляем урлы для теста в словарь
            if get_redir_for_all:
                redirect_dict['all'][url] = get_redir_for_all
            elif get_redir_for_auth:
                redirect_dict['auth'][url] = get_redir_for_auth
        for user, urls in redirect_dict.items():
            for url_get, url_redirect in urls.items():
                with self.subTest(field=url_get):
                    response = user_redirect[user].get(self.use_urls[url_get],
                                                       follow=True)
                    # Запрос может прейти с параметром. Его запоминаем
                    query = ('?' + response.request['QUERY_STRING'] if
                             response.request['QUERY_STRING'] else '')
                    self.assertRedirects(
                        response,
                        f'{self.use_urls[url_redirect]}' + query
                    )

    def test_templates(self):
        access_users = {'all': self.guest_client}
        for url, val in urls_test.items():
            with self.subTest(field=url):
                response = (
                    access_users.get(
                        val['permission'],
                        self.authorized_client1).get(self.use_urls[url])
                )
            self.assertTemplateUsed(response, val['template'])
