from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from apps.brand.models import BrandProfile, BrandVoice
from apps.content.models import ContentPillar, ContentItem, ContentVersion, ContentApproval
from apps.content.services import ContentService
from apps.projects.models import Project
from apps.projects.services import ProjectContentService

User = get_user_model()


class Phase2MVPContentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase2_user", password="password123")
        self.client.login(username="phase2_user", password="password123")
        
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def test_brand_profile_and_voice_views(self):
        res = self.client.get(reverse("brand:profile"))
        self.assertEqual(res.status_code, 200)

        # Update profile and voice
        post_data = {
            "name": "Alex Rivera",
            "professional_title": "AI Architect",
            "niche": "Generative AI",
            "tone": "Authoritative & Crisp",
        }
        res = self.client.post(reverse("brand:profile"), post_data)
        self.assertRedirects(res, reverse("brand:profile"))

        profile = BrandProfile.objects.get(user=self.user)
        self.assertEqual(profile.name, "Alex Rivera")
        self.assertEqual(profile.niche, "Generative AI")

        voice = BrandVoice.objects.get(user=self.user)
        self.assertEqual(voice.tone, "Authoritative & Crisp")

    def test_content_item_creation_and_versioning(self):
        item = ContentService.save_content_item(
            user=self.user,
            title="Mastering Django Celery",
            hook="Stop blocking main thread!",
            body="Here is how to scale task queues...",
            status="DRAFT"
        )
        self.assertEqual(item.title, "Mastering Django Celery")
        self.assertEqual(item.versions.count(), 1)
        self.assertEqual(item.versions.first().version_number, 1)

        # Update item and verify version 2 snapshot
        updated_item = ContentService.save_content_item(
            user=self.user,
            item_id=item.id,
            hook="Updated Hook: 10x Celery Speed",
            change_reason="Polished Hook"
        )
        self.assertEqual(updated_item.versions.count(), 2)
        self.assertEqual(updated_item.versions.order_by("-version_number").first().version_number, 2)

    def test_content_approval_workflow(self):
        item = ContentService.save_content_item(
            user=self.user,
            title="Production Architecture",
            status="DRAFT"
        )
        approval = ContentService.approve_content_item(self.user, item.id, notes="Approved for schedule")
        
        item.refresh_from_db()
        self.assertEqual(item.status, "APPROVED")
        self.assertEqual(approval.status, "APPROVED")
        self.assertEqual(ContentApproval.objects.filter(content_item=item).count(), 1)

    def test_project_to_content_generation(self):
        project = Project.objects.create(
            user=self.user,
            title="Personal Brand OS",
            description="Production-quality Django operating system",
            problem="Managing personal brand workflows manually is fragmented",
            solution="Centralized dashboard connecting knowledge, strategy, and content",
            technologies="Python, Django, Celery, Redis"
        )
        content_item = ProjectContentService.create_content_from_project(self.user, project, platform="LINKEDIN")
        
        self.assertIn("Case Study: How we built Personal Brand OS", content_item.title)
        self.assertEqual(content_item.status, "DRAFT")
        self.assertIn("Python, Django, Celery, Redis", content_item.body)

    def test_calendar_reschedule_api(self):
        item = ContentService.save_content_item(
            user=self.user,
            title="Scheduled Post",
            status="DRAFT"
        )
        res = self.api_client.post(
            reverse("calendar:api_reschedule"),
            {"content_id": item.id, "scheduled_at": "2026-09-01T10:00:00Z"},
            format="json"
        )
        self.assertEqual(res.status_code, 200)
        
        item.refresh_from_db()
        self.assertEqual(item.status, "SCHEDULED")

    def test_dashboard_metrics_with_real_data(self):
        ContentService.save_content_item(user=self.user, title="Idea 1", status="IDEA")
        ContentService.save_content_item(user=self.user, title="Draft 1", status="DRAFT")
        ContentService.save_content_item(user=self.user, title="Scheduled 1", status="SCHEDULED")

        res = self.client.get(reverse("dashboard:index"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["metrics"]["total_content"], 3)
        self.assertEqual(res.context["metrics"]["ideas_count"], 1)
        self.assertEqual(res.context["metrics"]["drafts_count"], 1)
        self.assertEqual(res.context["metrics"]["scheduled_count"], 1)
