import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.test_group = Group.objects.create(
            title="Тестовая группа 1",
            slug="test_group_1",
            description="Тестовая группа для теста",
        )
        cls.tolstoy = User.objects.create_user(id=25, username="tolstoy")
        cls.mihailov = User.objects.create_user(id=55, username="StasMihailov")
        cls.test_post = Post.objects.create(
            text="Тестовый пост для изменения",
            id=80,
            author=cls.tolstoy,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.mihailov_authorized_client = Client()
        self.tolstoy_authorized_client = Client()
        self.mihailov_authorized_client.force_login(
            PostCreateFormTests.mihailov)
        self.tolstoy_authorized_client.force_login(PostCreateFormTests.tolstoy)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
            "group": PostCreateFormTests.test_group.id,
        }

        response = self.mihailov_authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                group=PostCreateFormTests.test_group.id,
                author=PostCreateFormTests.mihailov,
            ).exists()
        )

    def test_create_post_without_group(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
        }

        response = self.mihailov_authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст", author=PostCreateFormTests.mihailov
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            "text": "Измененный текст",
        }

        response = self.tolstoy_authorized_client.post(
            reverse("post_edit",
                    kwargs={"username": "tolstoy", "post_id": 80}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse("post",
                              kwargs={"username": "tolstoy", "post_id": 80})
        )
        self.assertTrue(
            Post.objects.filter(
                text="Измененный текст",
            ).exists()
        )

    def test_edit_post_with_edit_group(self):
        form_data = {
            "text": "Измененный текст",
            "group": PostCreateFormTests.test_group.id,
        }

        response = self.tolstoy_authorized_client.post(
            reverse("post_edit",
                    kwargs={"username": "tolstoy", "post_id": 80}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse("post",
                              kwargs={"username": "tolstoy", "post_id": 80})
        )
        self.assertTrue(
            Post.objects.filter(
                text="Измененный текст",
                group=PostCreateFormTests.test_group.id
            ).exists()
        )

    def test_create_post_with_correct_image(self):
        posts_count = Post.objects.count()
        gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        picture = SimpleUploadedFile(
            name="pic.gif", content=gif, content_type="image/gif"
        )
        form_data = {
            "text": "Пост Стаса с картинкой",
            "image": picture,
        }

        response = self.mihailov_authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Пост Стаса с картинкой",
                author=PostCreateFormTests.mihailov,
                image="posts/pic.gif",
            ).exists()
        )
