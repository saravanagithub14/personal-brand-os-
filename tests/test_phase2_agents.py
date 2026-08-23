from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.ai_agents.services import ContentRepurposer, BrandVoiceReviewer, AgentManager
from apps.content.models import ContentItem
from apps.news.services import NewsIngestionService
from apps.news.models import NewsArticle
from apps.research.services import RetrievalService
from apps.research.models import KnowledgeDocument

User = get_user_model()


class Phase2AgentsAndResearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="phase2_user", password="Password123!")
        self.client.login(username="phase2_user", password="Password123!")

    def test_content_repurposer(self):
        item = ContentItem.objects.create(
            user=self.user,
            title="Building High-Performance BioTech AI Pipelines",
            body="Here is a deep dive into GPU-accelerated computational genomics pipelines.",
            status="DRAFT",
        )
        repurposed = ContentRepurposer.repurpose_content(item)
        self.assertIn("X_TWITTER", repurposed)
        self.assertIn("INSTAGRAM", repurposed)
        self.assertIn("LINKEDIN", repurposed)

        # Test view endpoint
        url = reverse("ai_agents:repurpose_item", kwargs={"item_id": item.id})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContentItem.objects.filter(user=self.user).count(), 4)

    def test_brand_voice_reviewer(self):
        analysis = BrandVoiceReviewer.review_content(
            self.user,
            "Building robust protein structure prediction models using PyTorch."
        )
        self.assertGreaterEqual(analysis["score"], 0)
        self.assertLessEqual(analysis["score"], 100)
        self.assertIn("hook_strength", analysis)

    def test_news_ingestion_service(self):
        news = NewsIngestionService.get_daily_brief()
        self.assertGreater(len(news), 0)
        article = news[0]

        # Test draft creation from news
        url = reverse("news:create_draft", kwargs={"article_id": article.id})
        response = self.client.post(url, {"platform": "LINKEDIN"}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_retrieval_service_and_knowledge_base(self):
        doc = KnowledgeDocument.objects.create(
            user=self.user,
            title="Transformer Architecture in Computational Biology",
            content_text="Self-attention mechanisms enable long-range dependency modeling in protein sequences.",
            tags="ai, python, proteins",
        )
        results = RetrievalService.search_knowledge_base(self.user, "transformer")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, doc.id)

        # Test knowledge base list view
        url = reverse("research:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(doc, response.context["documents"])

    def test_script_generator_bilingual(self):
        from apps.ai_agents.services import ScriptGeneratorAgent
        res_malayalam = ScriptGeneratorAgent.generate_script("AI Workflows", language="MALAYALAM")
        self.assertIn("മലയാളം", res_malayalam["script"])
        self.assertIn("Visual Cues", res_malayalam["visual_instructions"])

        res_manglish = ScriptGeneratorAgent.generate_script("AI Workflows", language="MANGLISH")
        self.assertIn("Manglish Script", res_manglish["script"])

        res_english = ScriptGeneratorAgent.generate_script("AI Workflows", language="ENGLISH")
        self.assertNotIn("—", res_english["script"])
        self.assertNotIn("delve", res_english["script"].lower())
        self.assertNotIn("game changer", res_english["script"].lower())

        # Test view endpoint
        url = reverse("ai_agents:generate_script")
        response = self.client.post(
            url,
            {
                "topic": "Python Generators",
                "language": "MALAYALAM",
                "platform": "INSTAGRAM_REEL",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_token_budgeting_and_quota_routing(self):
        # Execute agent under normal mini/nano preference
        AgentManager.execute_agent(self.user, "Test Mini Agent", "Hello World input", preferred_tier="MINI_NANO")
        usage = AgentManager.get_daily_token_usage(self.user)
        self.assertGreater(usage["mini_nano_tokens"], 0)
        self.assertEqual(usage["flagship_cap"], 250000)
        self.assertEqual(usage["mini_nano_cap"], 2500000)

        # Test flagship model selection under normal conditions
        model, tier = AgentManager.select_optimal_model(self.user, preferred_tier="FLAGSHIP")
        self.assertEqual(tier, "FLAGSHIP")
        self.assertEqual(model, "gpt-4o")

    def test_ai_chatbot_views(self):
        url_page = reverse("ai_agents:chat")
        res_page = self.client.get(url_page)
        self.assertEqual(res_page.status_code, 200)

        url_api = reverse("ai_agents:api_chat")
        res_api = self.client.post(url_api, {"message": "hi"})
        self.assertEqual(res_api.status_code, 200)
        self.assertTrue(res_api.json()["success"])
        self.assertIn("Hey Saravana!", res_api.json()["reply"])

    def test_database_context_retriever(self):
        from apps.social.models import SocialAccount
        from apps.projects.models import Project

        # Create sample social account and project
        SocialAccount.objects.create(
            user=self.user,
            platform="GITHUB",
            handle="saravanagithub14",
            profile_url="https://github.com/saravanagithub14",
        )
        Project.objects.create(
            user=self.user,
            title="BioTech AI Pipeline",
            description="GPU computational genomics pipeline in Python.",
            technologies="Python, PyTorch",
        )

        SocialAccount.objects.create(
            user=self.user,
            platform="MEDIUM",
            handle="@mynamesaravanaperumal",
            profile_url="https://medium.com/@mynamesaravanaperumal",
        )

        url_api = reverse("ai_agents:api_chat")
        res_medium = self.client.post(url_api, {"message": "when did i last add medium post"})
        self.assertEqual(res_medium.status_code, 200)
        self.assertIn("Medium", res_medium.json()["reply"])
        self.assertIn("@mynamesaravanaperumal", res_medium.json()["reply"])

        res_handles = self.client.post(url_api, {"message": "What social handles do I have?"})
        self.assertEqual(res_handles.status_code, 200)
        self.assertIn("GitHub", res_handles.json()["reply"])
        self.assertIn("saravanagithub14", res_handles.json()["reply"])

        res_projects = self.client.post(url_api, {"message": "Show my active projects"})
        self.assertEqual(res_projects.status_code, 200)
        self.assertIn("BioTech AI Pipeline", res_projects.json()["reply"])
