import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from ..models import Group, Post
from . import func_for_tests as test_func

User = get_user_model()
# slug испльзуется для формирования адреса, redirect - url редиректа
# поэтому в словарь и добавлены урлы без форм
forms_test = {
    'posts:post_create': {'redirect': 'posts:profile'},
    'posts:post_edit': {'redirect': 'posts:post_detail', 'slugs': ['post_id']},
    'posts:profile': {'slugs': ['username']},
    'posts:post_detail': {'slugs': ['post_id']},
    'login': {},
    'posts:main': {},
    'posts:group-posts': {'slugs': ['slug']},
    'posts:add_comment': {'slugs': ['post_id']}
}

forms_not_auth = {'posts:post_create': 'login',
                  'posts:post_edit': 'login'}

img_test = ['posts:main', 'posts:profile',
            'posts:group-posts', 'posts:post_detail']

redirect_url_non_auth = 'login'
comment_url = 'posts:add_comment'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):

    def setUp(self):
        # Новые группы х2
        self.slug = 'form-group_one'
        self.group = Group.objects.create(
            title='FORM_TEST1',
            description='Текст1',
            slug=self.slug,
        )
        self.group2 = Group.objects.create(
            title='FORM_TEST2',
            description='Текст2',
            slug='form-group_two',
        )

        # Создаем авторизованый клиент 1
        self.username = 'author_form'
        self.user = User.objects.create_user(username=self.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        # Пост для теста от клинета 1
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        self.test_post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user,
            group=self.group,
            image=uploaded
        )
        self.post_id = self.test_post.id
        self.image = self.test_post.image
        # Получаем редиректы
        self.use_urls = test_func.get_use_urls(self, forms_test)
        # Для теста неавторизованного пользователя
        self.guest = Client()
        # Для теста комментариев
        self.form_data_comment = {
            'text': 'Тестовый комент',
            'post': self.post_id
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_img_by_url(self):
        """Тест наличия картинки в словаре."""
        for url in img_test:
            response = self.authorized_client.get(self.use_urls[url])
            response_context = response.context
            obj_context = response_context.get('page_obj')
            obj_context = (obj_context[0] if obj_context else
                           response_context.get('post'))
            with self.subTest(url=url):
                self.assertEqual(obj_context.image, self.image)

    def test_comment_redirect_non_auth(self):
        """Тест комментария неавторизованным пользователем."""
        response = self.response_func(self.guest,
                                      self.use_urls[comment_url],
                                      self.form_data_comment)
        with self.subTest(form_for_not_auth=comment_url):
            # Тест редиректа
            self.assertRedirects(
                response,
                (self.use_urls[redirect_url_non_auth] + '?next='
                 + self.use_urls[comment_url]))

    def test_comment_add(self):
        """Тест добавления комментария авторизованным."""
        response = self.response_func(self.authorized_client,
                                      self.use_urls[comment_url],
                                      self.form_data_comment)
        with self.subTest(test_comment=comment_url):
            self.assertEqual(response.context['comments'].last().text,
                             self.form_data_comment['text'])

    def test_create_post(self):
        """Тест добавления новой формы."""
        name_url = 'posts:post_create'
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись 123',
            'group': self.group.id,
            'image': SimpleUploadedFile(
                name='small2.gif',
                content=self.small_gif,
                content_type='image/gif'),
        }
        response = self.response_func(self.authorized_client,
                                      self.use_urls[name_url],
                                      form_data)
        with self.subTest(form=name_url):
            self.assertRedirects(
                response,
                self.use_urls[forms_test[name_url]['redirect']]
            )
            self.assertEqual(Post.objects.count(), post_count + 1)
            # Проверка записи в БД c картинкой
            self.assertTrue(
                Post.objects.filter(
                    text=form_data['text'],
                    group=form_data['group'],
                    author=self.user,
                    image='posts/small2.gif'
                ).exists(),
                msg='Добавленная запись не найдена в БД'
            )
        # Тест создания поста неавторизованным
        form_data['text'] = 'Тестовая запись Noname'
        post_count = Post.objects.count()
        response = self.response_func(self.guest,
                                      self.use_urls[name_url],
                                      form_data)
        with self.subTest(form_for_not_auth=name_url):
            # Тест редиректа
            self.assertRedirects(
                response,
                (self.use_urls[forms_not_auth[name_url]] + '?next='
                 + self.use_urls[name_url])
            )
            # Тест записей
            self.assertEqual(Post.objects.count(), post_count,
                             msg='В БД добавлены записи от неавториз. '
                                 'пользователя'
                             )

    def test_edit_post(self):
        name_url = 'posts:post_edit'
        form_data = {
            'text': 'Измененная запись',
            'group': self.group2.id,
        }
        response = self.response_func(self.authorized_client,
                                      self.use_urls[name_url],
                                      form_data)
        with self.subTest(form=name_url):
            self.assertRedirects(
                response,
                self.use_urls[forms_test[name_url]['redirect']]
            )
            self.assertTrue(
                Post.objects.filter(
                    text=form_data['text'],
                    group=form_data['group'],
                ).exists(),
                msg="Новый пост не добавлен в БД"
            )

    @staticmethod
    def response_func(client, url, data):
        return client.post(url, data=data, follow=True)
