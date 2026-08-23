from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from apps.social.models import SocialAccount
from apps.analytics.models import SocialAnalyticsSnapshot
from apps.social.services import SocialStatsFetcher

User = get_user_model()


class AutoSyncSocialStatsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="Password123!"
        )
        self.client.login(username="testuser", password="Password123!")

    def test_clean_handle_helper(self):
        self.assertEqual(SocialStatsFetcher.clean_handle("@cellstocode"), "cellstocode")
        self.assertEqual(SocialStatsFetcher.clean_handle("https://github.com/saravanagithub14"), "saravanagithub14")
        self.assertEqual(SocialStatsFetcher.clean_handle("  @saravana_codes  "), "saravana_codes")

    @patch("apps.social.services.SocialStatsFetcher.fetch_stats")
    def test_sync_social_account_service(self, mock_fetch):
        mock_fetch.return_value = {
            "followers": 1850,
            "posts": 24,
            "impressions": 32000,
            "engagement": 5.4,
        }
        account = SocialAccount.objects.create(
            user=self.user,
            platform="GITHUB",
            handle="saravanagithub14",
        )
        updated_acc = SocialStatsFetcher.sync_social_account(account)
        self.assertEqual(updated_acc.followers_count, 1850)
        self.assertEqual(updated_acc.posts_count, 24)
        self.assertEqual(updated_acc.total_impressions, 32000)
        self.assertEqual(updated_acc.engagement_rate, 5.4)

        # Check snapshot creation
        snapshot = SocialAnalyticsSnapshot.objects.filter(social_account=account).first()
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.followers, 1850)

    @patch("apps.social.services.SocialStatsFetcher.fetch_stats")
    def test_auto_sync_views(self, mock_fetch):
        mock_fetch.return_value = {
            "followers": 2100,
            "posts": 30,
            "impressions": 40000,
            "engagement": 4.8,
        }
        account = SocialAccount.objects.create(
            user=self.user,
            platform="INSTAGRAM",
            handle="@cellstocode",
        )
        
        # Test syncing single account endpoint
        url_single = reverse("social:sync_account", kwargs={"account_id": account.id})
        response = self.client.post(url_single, follow=True)
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEqual(account.followers_count, 2100)

        # Test syncing all accounts endpoint
        url_all = reverse("social:sync_all")
        response_all = self.client.post(url_all, follow=True)
        self.assertEqual(response_all.status_code, 200)

    @patch("apps.social.services.SocialStatsFetcher.fetch_github_last_post_date")
    def test_fetch_last_post_date(self, mock_dt):
        from django.utils import timezone
        now = timezone.now()
        mock_dt.return_value = now
        fetched = SocialStatsFetcher.fetch_last_post_date("GITHUB", "saravanagithub14")
        self.assertEqual(fetched, now)
