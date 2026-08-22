from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient

User = get_user_model()


class FoundationTestCase(TestCase):
    def test_custom_user_creation(self):
        user = User.objects.create_user(username="user1", email="user1@example.com", password="password123")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.email, "user1@example.com")
        self.assertTrue(user.check_password("password123"))

    def test_login_and_dashboard_access(self):
        user = User.objects.create_user(username="user2", password="password123")
        client = APIClient()

        # Unauthenticated access redirects to login
        response = client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

        # Authenticated access
        client.force_authenticate(user=user)
        client.login(username="user2", password="password123")
        response = client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_api_summary(self):
        user = User.objects.create_user(username="user3", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("api_dashboard_summary"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "online")
        self.assertEqual(response.data["user"], "user3")

    def test_installed_apps_contains_domain_apps(self):
        expected_apps = [
            "apps.accounts", "apps.dashboard", "apps.brand", "apps.content", "apps.calendar",
            "apps.ai_agents", "apps.research", "apps.news", "apps.social", "apps.analytics",
            "apps.projects", "apps.media", "apps.notifications"
        ]
        for app_name in expected_apps:
            self.assertIn(app_name, settings.INSTALLED_APPS)
