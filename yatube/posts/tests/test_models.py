from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа все для теста',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        test_dict = {
            'group': [PostModelTest.group, PostModelTest.group.title],
            'post': [PostModelTest.post, PostModelTest.post.text[:15]],
        }
        for model in test_dict.values():
            self.assertEqual(str(model[0]), model[1])

    def test_help_text_and_verbose_name(self):
        """Проверяем только наличие help_text и verbose_name."""
        test_dict_models = {
            'post': {
                'model': PostModelTest.post,
                'verbose_name': ['text', 'pub_date', 'author', 'group', ],
                'help_text': ['text', 'group', ]
            }
        }
        for key in test_dict_models.keys():
            model = test_dict_models[key]['model']
            for method in ['help_text', 'verbose_name']:
                for name in test_dict_models[key][method]:
                    with self.subTest(field=name):
                        self.assertNotIn(
                            getattr(model._meta.get_field(name), method),
                            [name, ''],
                            msg=f'У поля "{name}" модели '
                                f'"{key}" '
                                f'не определен "{method}"'
                        )
