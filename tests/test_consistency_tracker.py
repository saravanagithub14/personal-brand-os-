from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.social.models import SocialAccount

User = get_user_model()


class ConsistencyTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test_consistency", password="Password123!")
        self.client.login(username="test_consistency", password="Password123!")

    def test_social_account_health_properties(self):
        now = timezone.now()
        acc = SocialAccount.objects.create(
            user=self.user,
            platform="INSTAGRAM",
            handle="@cellstocode",
            last_post_at=now - timedelta(days=1),
            target_cadence_days=2,
        )
        self.assertEqual(acc.days_since_last_post, 1)
        self.assertEqual(acc.health_status, "ON_TRACK")
        self.assertEqual(acc.health_badge["label"], "On Track")

        # Test due soon status
        acc.last_post_at = now - timedelta(days=3)
        acc.save()
        self.assertEqual(acc.health_status, "DUE_SOON")
        self.assertEqual(acc.health_badge["label"], "Due Soon")

        # Test overdue status
        acc.last_post_at = now - timedelta(days=6)
        acc.save()
        self.assertEqual(acc.health_status, "OVERDUE")
        self.assertEqual(acc.health_badge["label"], "Overdue Alert")

    def test_dashboard_consistency_radar_context(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("consistency_radar", response.context)
        radar = response.context["consistency_radar"]
        self.assertGreaterEqual(radar["score"], 0)
        self.assertLessEqual(radar["score"], 100)
        self.assertIn("on_track_count", radar)
        self.assertIn("overdue_count", radar)

    def test_update_last_post_date_view(self):
        acc = SocialAccount.objects.create(
            user=self.user,
            platform="LINKEDIN",
            handle="Saravana Perumal R.",
            target_cadence_days=3,
        )
        url = reverse("social:update_last_post", kwargs={"account_id": acc.id})
        response = self.client.post(
            url,
            {
                "last_post_date": "2026-08-20",
                "target_cadence_days": 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        acc.refresh_from_db()
        self.assertEqual(acc.target_cadence_days, 2)
        self.assertIsNotNone(acc.last_post_at)
