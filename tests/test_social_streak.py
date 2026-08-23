from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.social.models import SocialAccount
from apps.content.models import ContentItem

User = get_user_model()


class SocialAccountStreakTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="streak_user", password="Password123!")
        self.client.login(username="streak_user", password="Password123!")

        self.account = SocialAccount.objects.create(
            user=self.user,
            platform="LINKEDIN",
            handle="Saravana Perumal R.",
            profile_url="https://linkedin.com/in/saravana-perumal-r-04b368288",
            last_post_at=timezone.now() - timedelta(days=1),
            target_cadence_days=3,
        )

    def test_handle_detail_view_heatmap_context(self):
        # Create a sample content item
        ContentItem.objects.create(
            user=self.user,
            platform="LINKEDIN",
            title="Building High-Performance BioTech AI Pipelines",
            body="Deep dive into computational genomics pipelines.",
            status="PUBLISHED",
        )

        url = reverse("social:account_detail", kwargs={"account_id": self.account.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify streak context variables
        self.assertIn("heatmap_weeks", response.context)
        self.assertIn("current_streak", response.context)
        self.assertIn("longest_streak", response.context)
        self.assertIn("total_year_posts", response.context)

        # Verify 52 weeks in heatmap grid
        self.assertEqual(len(response.context["heatmap_weeks"]), 52)
