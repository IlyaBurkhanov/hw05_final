from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

# Тестировать about не обязательно:)
# И изначально я включил тест урлов из about в posts/tests_urls
# По доп.заданию все тесты можно провести прямо в этом файле)
# Поэтому, если не возражаешь, так и сделаю

urls_test = {'about:author': 'about/author.html',
             'about:tech': 'about/tech.html'}


class TaskAllTests(TestCase):

    def setUp(self):
        # Урлы доступны всем, поэтому без авторизованной проверки
        self.guest = Client()

    def test_access_and_template(self):
        """Тест урлов и template About."""
        for url, template in urls_test.items():
            with self.subTest(url=url):
                response = self.guest.get(reverse(url))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_not_none_contex(self):
        """Проверка что скиллы указаны."""
        response = self.guest.get(reverse('about:tech'))
        with self.subTest(contex='skills'):
            self.assertIsNotNone(response.context.get('skills'))
