from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовая группа для теста",
        )
        cls.user_leo = User.objects.create(id=1, username="leo")
        cls.post = Post.objects.create(
            text="ж" * 100,
            id=1,
            author=PostsURLTests.user_leo,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="Chuvak")
        self.non_author_authorized = Client()
        self.author_authorized = Client()
        self.non_author_authorized.force_login(self.user)
        self.author_authorized.force_login(self.user_leo)
        cache.clear()

    def test_home_url_exists_at_desired_location(self):
        """Главная страница доступна любому пользователю."""
        urls = (
            "/",
            "/group/test_group/",
            reverse("profile", kwargs={"username": "leo"}),
            reverse("post", kwargs={"username": "leo", "post_id": 1}),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_exists_at_desired_location_authorized(self):
        """Страница создания поста доступна авторизованному
        пользователю."""
        response = self.non_author_authorized.get("/new/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_redirect_anonymous_on_auth_login(self):
        """Страница создания поста перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get("/new/", follow=True)

        self.assertRedirects(response, ("/auth/login/?next=/new/"))

    def test_urls_uses_correct_template(self):
        templates_url_names = (
            (reverse("index"), "posts/index.html"),
            (reverse("new_post"), "posts/new_post.html"),
            (reverse("group_posts", kwargs={"slug": "test_group"}),
             "posts/group.html"),
            (
                reverse("post_edit", kwargs={"username": "leo", "post_id": 1}),
                "posts/new_post.html",
            ),
        )

        for reverse_name, template in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_authorized.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_post_url_redirect_anonymous_on_auth_login(self):
        """Страница редактирования поста перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            reverse(
                "post_edit", kwargs={"username": "leo", "post_id": 1}
            ), follow=True
        )

        self.assertRedirects(
            response,
            ("/auth/login/?next=" + str(reverse(
                "post_edit", kwargs={"username": "leo", "post_id": 1}
            ))
            ),
        )

    def test_edit_post_url_redirect_not_author_user_post_view_page(self):
        """Страница редактирования поста перенаправит не автора поста
        на страницу поста.
        """
        response = self.non_author_authorized.get(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 1}),
            follow=True
        )

        self.assertRedirects(
            response, reverse("post", kwargs={"username": "leo", "post_id": 1})
        )

    def test_edit_post_url_exist_at_desire_location(self):
        """Страница редактирования поста доступна автору"""
        response = self.author_authorized.get(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 1}),
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_not_available_to_anonymous_user(self):
        """Страница редактирования поста недоступна анонимному пользователю"""
        response = self.guest_client.get(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 1})
        )

        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_not_available_to_not_author_user(self):
        """Страница редактирования поста недоступна не автору"""
        response = self.non_author_authorized.get(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 1})
        )

        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_404_page_not_found(self):
        """Сервер возвращает код 404, если страница не найдена"""
        response = self.guest_client.get("/non-existent_page/")

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
