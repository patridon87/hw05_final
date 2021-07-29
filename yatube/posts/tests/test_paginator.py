from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        leo = User.objects.create_user(username="leo")

        objs = [Post(text="Тестовый пост",
                     id=i, author=leo) for i in range(1, 14)]
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.user = User.objects.create_user(username="StasMihailov")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context["page"].object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context["page"].object_list), 3)
