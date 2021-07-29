from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(id=1, username="leo")
        cls.post = Post.objects.create(
            text="ж" * 100,
            id=1,
            author=PostsModelTest.user,
        )

    def test_post_str(self):
        post = PostsModelTest.post.__str__()
        self.assertEqual(post, "ж" * 15)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовая группа для теста",
        )

    def test_group_str(self):
        group = GroupModelTest.group.__str__()
        self.assertEqual(group, "Тестовая группа")
