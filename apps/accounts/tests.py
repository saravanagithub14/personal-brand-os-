from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


class AccountsTestCase(TestCase):
    def test_user_model(self):
        user = User.objects.create_user(username="acc_user", email="acc@example.com", password="password123")
        self.assertEqual(user.username, "acc_user")
        self.assertEqual(str(user), "acc_user")

    def test_login_and_register_views(self):
        # Register View Get
        res = self.client.get(reverse("accounts:register"))
        self.assertEqual(res.status_code, 200)

        # Login View Get
        res = self.client.get(reverse("accounts:login"))
        self.assertEqual(res.status_code, 200)
