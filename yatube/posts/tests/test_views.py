import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class YatubePagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.test_group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовая группа для теста",
        )
        cls.second_test_group = Group.objects.create(
            title="Тестовая группа 2",
            slug="second_test_group",
            description="Тестовая группа 2 для теста",
        )
        cls.leo = User.objects.create_user(id=1, username="leo")
        cls.mihailov = User.objects.create_user(id=2, username="StasMihailov")
        cls.test_post = Post.objects.create(
            text="Тестовый пост в группе", id=1,
            author=cls.leo, group=cls.test_group
        )
        cls.test_post_for_edit = Post.objects.create(
            text="Тестовый пост",
            id=2,
            author=cls.leo,
        )
        cls.test_post_with_image = Post.objects.create(
            text="Тестовый пост с картинкой",
            id=3,
            author=cls.leo,
            image=cls.uploaded,
            group=cls.test_group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.mihailov_client = Client()
        self.leo_client = Client()
        self.mihailov_client.force_login(YatubePagesTest.mihailov)
        self.leo_client.force_login(YatubePagesTest.leo)
        cache.clear()

    def test_pages_use_correct_template(self):
        """Странице использует ожидаемый шалон."""
        templates_pages_names = {
            "posts/index.html": reverse("index"),
            "posts/group.html": reverse("group_posts",
                                        kwargs={"slug": "test_group"}),
            "posts/new_post.html": reverse("new_post"),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.mihailov_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Главная страница получает ожидаемый контекст"""
        response = self.mihailov_client.get(reverse("index"))

        self.assertIn("page", response.context)

    def test_group_page_shows_correct_context(self):
        """Страница группы получает ожидаемый контекст"""
        response = self.mihailov_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )
        context = ["page", "group"]

        for expected_context in context:
            self.assertIn(expected_context, response.context)

    def test_new_post_page_shows_correct_content(self):
        """Страница создания поста получает ожидаемый контекст"""
        response = self.mihailov_client.get(reverse("new_post"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_group_on_homepage(self):
        """Пост, опубликованный в группе, появляется на главной странице"""
        response = self.mihailov_client.get(reverse("index"))
        post = response.context["page"].object_list[2]

        self.assertEqual(post, YatubePagesTest.test_post)

    def test_post_in_page_of_group(self):
        """Пост, опубликованный в группе, появляется на странице группы"""
        response = self.mihailov_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )
        post = response.context["page"].object_list[1]

        self.assertEqual(post, YatubePagesTest.test_post)

    def test_post_not_in_other_group_page(self):
        """Пост не публигуется на странице другой группы"""
        response = self.mihailov_client.get(
            reverse("group_posts", kwargs={"slug": "second_test_group"})
        )

        self.assertEqual(len(response.context["page"].object_list), 0)

    def test_edit_post_page_shows_correct_content(self):
        """Страница редактирования поста получает ожидаемый контекст"""
        response = self.leo_client.get(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 1})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_content(self):
        """Страница профиля пользователя получает ожидаемый контекст"""
        response = self.mihailov_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )
        context = ["page", "group"]

        for expected_context in context:
            self.assertIn(expected_context, response.context)

    def test_post_page_shows_correct_context(self):
        """Страница просмотра поста получает ожидаемый контекст"""
        response = self.leo_client.get(
            reverse("post", kwargs={"username": "leo", "post_id": 1})
        )
        context = ["author", "post", "count"]

        for expected_context in context:
            self.assertIn(expected_context, response.context)

    def test_create_post_with_correct_author(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": "Автор поста - Стас Михайлов",
        }

        response = self.mihailov_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Автор поста - Стас Михайлов",
                author=YatubePagesTest.mihailov
            ).exists()
        )

    def test_edit_post_not_author(self):
        form_data = {
            "text": "Измененный текст",
        }

        response = self.mihailov_client.post(
            reverse("post_edit", kwargs={"username": "leo", "post_id": 2}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse("post", kwargs={"username": "leo", "post_id": 2})
        )
        self.assertTrue(
            Post.objects.filter(text="Тестовый пост", id=2).exists()
        )

    def test_image_in_post_page(self):
        response = self.mihailov_client.get(
            reverse("post", kwargs={"username": "leo", "post_id": 3})
        )

        self.assertEqual(
            response.context.get("post").image, self.test_post_with_image.image
        )

    def test_image_in_index_page(self):
        response = self.mihailov_client.get(reverse("index"))

        self.assertEqual(
            response.context.get("page")[0].image,
            self.test_post_with_image.image
        )

    def test_image_in_profile_page(self):
        response = self.mihailov_client.get(
            reverse("profile", kwargs={"username": "leo"})
        )

        self.assertEqual(
            response.context.get("page")[0].image,
            self.test_post_with_image.image
        )

    def test_image_in_group_page(self):
        response = self.mihailov_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )

        self.assertEqual(
            response.context.get("page")[0].image,
            self.test_post_with_image.image
        )


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.mihailov = User.objects.create_user(id=2,
                                                username="StasMihailov")
        # cls.post = Post.objects.create(
        #     text="Пост для теста кэша",
        #     author=CacheTest.mihailov
        # )

    def setUp(self):
        self.mihailov_client = Client()
        self.mihailov_client.force_login(CacheTest.mihailov)
        cache.clear()

    def test_cache(self):
        response = self.mihailov_client.get(reverse("index"))

        Post.objects.create(
            text="Второй пост для теста кэша",
            author=CacheTest.mihailov,
            id=1
        )
        post_count = len(response.context["page"].object_list)
        print(f"Количество постов {post_count}")
        self.assertEqual(len(response.context["page"].object_list), post_count)

        cache.clear()

        second_response = self.mihailov_client.get(reverse("index"))
        post_count_after_clear = len(
            second_response.context["page"].object_list
        )
        print(f"Количество постов {post_count_after_clear}")
        self.assertEqual(len(second_response.context["page"].object_list),
                         post_count_after_clear)
