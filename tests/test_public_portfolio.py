from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.brand.models import BrandProfile
from apps.projects.models import Project
from apps.content.models import ContentItem

User = get_user_model()


class PublicPortfolioTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex_creator",
            email="alex@example.com",
            password="Password123!"
        )
        self.client = Client()

        # Brand Profile
        self.profile = BrandProfile.objects.create(
            user=self.user,
            name="Alex Creator",
            professional_title="AI Systems Architect",
            short_bio="Building next-gen AI platforms and open source tools.",
            niche="AI Engineering",
            skills="Python, Django, PyTorch, LLMs",
            portfolio_url="https://alexcreator.dev"
        )

        # Projects
        self.project = Project.objects.create(
            user=self.user,
            title="Personal Brand OS",
            description="All-in-one AI operating system for creators.",
            technologies="Django, Python, SQLite",
            github_url="https://github.com/alex/personal-brand-os",
            demo_url="https://brand-os.demo"
        )

        # Published Content
        self.published_item = ContentItem.objects.create(
            user=self.user,
            title="How to Build Agentic Systems",
            content_type="ARTICLE",
            platform="LINKEDIN",
            status="PUBLISHED",
            hook="Agents are changing how software is built."
        )

    def test_public_portfolio_view_unauthenticated(self):
        url = reverse("public_portfolio_user", kwargs={"username": self.user.username})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Alex Creator")
        self.assertContains(res, "AI Systems Architect")
        self.assertContains(res, "Personal Brand OS")
        self.assertContains(res, "How to Build Agentic Systems")

    def test_dashboard_contains_public_portfolio_section(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse("dashboard:index"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Public Portfolio Pages & Showcase")
        self.assertContains(res, f"/portfolio/{self.user.username}/")
        self.assertContains(res, "Showcase Projects")
