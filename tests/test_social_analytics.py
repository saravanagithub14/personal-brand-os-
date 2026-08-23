from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from apps.social.models import SocialAccount
from apps.analytics.models import SocialAnalyticsSnapshot

User = get_user_model()


class SocialAnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="Password123!"
        )
        self.client.login(username="testuser", password="Password123!")

    def test_social_account_creation(self):
        account = SocialAccount.objects.create(
            user=self.user,
            platform="INSTAGRAM",
            handle="@cellstocode",
            profile_url="https://instagram.com/cellstocode",
            followers_count=1500,
            total_impressions=25000,
            engagement_rate=4.8,
        )
        self.assertEqual(account.handle, "@cellstocode")
        self.assertEqual(account.followers_count, 1500)
        self.assertEqual(str(account), "Instagram (@cellstocode) - testuser")

    def test_social_analytics_snapshot(self):
        account = SocialAccount.objects.create(
            user=self.user,
            platform="LINKEDIN",
            handle="Saravana Perumal R.",
            followers_count=3200,
        )
        snapshot = SocialAnalyticsSnapshot.objects.create(
            social_account=account,
            followers=3200,
            views=12000,
            likes_engagement=250,
        )
        self.assertEqual(snapshot.followers, 3200)
        self.assertIn("Saravana Perumal R.", str(snapshot))

    def test_dashboard_social_analytics_render(self):
        SocialAccount.objects.create(
            user=self.user,
            platform="INSTAGRAM",
            handle="@cellstocode",
            followers_count=1500,
            total_impressions=25000,
            engagement_rate=5.0,
        )
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@cellstocode")
        self.assertContains(response, "1500")
        self.assertContains(response, "25000")

    @patch("apps.social.services.SocialStatsFetcher.sync_social_account")
    def test_dashboard_add_social_account_post(self, mock_sync):
        mock_sync.side_effect = lambda acc: acc
        response = self.client.post(
            reverse("dashboard:index"),
            {
                "action": "save_social_account",
                "platform": "GITHUB",
                "handle": "@saravanagithub14",
                "profile_url": "https://github.com/saravanagithub14",
                "followers_count": 450,
                "total_impressions": 8500,
                "engagement_rate": 6.2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        account = SocialAccount.objects.get(user=self.user, platform="GITHUB")
        self.assertEqual(account.handle, "@saravanagithub14")
        self.assertEqual(account.followers_count, 450)
        self.assertContains(response, "@saravanagithub14")

    def test_social_account_detail_view(self):
        account = SocialAccount.objects.create(
            user=self.user,
            platform="GITHUB",
            handle="@saravanagithub14",
            followers_count=450,
        )
        url = reverse("social:account_detail", kwargs={"account_id": account.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@saravanagithub14")
        self.assertContains(response, "Live Performance Matrix")
