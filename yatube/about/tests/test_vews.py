from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_and_tech_pages_accessible_by_name(self):
        """Страницы about и tech доступны по сгенерированному по name URL"""
        reverse_names = [reverse("about:author"), reverse("about:tech")]

        for name in reverse_names:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """При запросе к страницам about и tech применяются
        ожидаемые шаблоны"""
        templates_pages_names = (
            ("about/author.html", reverse("about:author")),
            ("about/tech.html", reverse("about:tech")),
        )

        for template, reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
