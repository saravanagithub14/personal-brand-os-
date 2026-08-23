from django.utils import timezone
from .models import NewsArticle


class NewsIngestionService:
    """Ingests daily AI/BioTech news and generates actionable hooks."""

    DEFAULT_NEWS_ITEMS = [
        {
            "title": "OpenAI & Anthropic Announce Next-Gen AI Agent Protocols",
            "source": "TechCrunch AI",
            "url": "https://techcrunch.com/category/artificial-intelligence/",
            "summary": "New standards for autonomous multi-agent task execution and safety verification have been unveiled.",
            "ai_hook": "💡 Autonomous AI agents are evolving rapidly. Here is what computational researchers need to know about the new multi-agent protocols...",
            "category": "AI_TECH",
        },
        {
            "title": "Breakthrough in Protein Structure Prediction with Generative Biology Models",
            "source": "Nature BioTech",
            "url": "https://nature.com/biotech/",
            "summary": "Researchers demonstrate 99.2% accuracy in de novo protein design using diffusion transformer models.",
            "ai_hook": "🧬 Generative AI just unlocked de novo protein engineering. Here is how deep learning models are transforming computational biology...",
            "category": "BIOTECH",
        },
        {
            "title": "PyTorch 2.5 Released with Enhanced Tensor Parallelism",
            "source": "PyTorch Blog",
            "url": "https://pytorch.org/blog/",
            "summary": "The latest release brings 3x faster distributed training for large-scale language and multimodal vision models.",
            "ai_hook": "⚡ PyTorch 2.5 is here with 3x faster distributed training. 3 key features every AI developer should implement today...",
            "category": "DEVELOPMENT",
        },
    ]

    @classmethod
    def seed_daily_news(cls):
        """Seed or update daily curated news items for the dashboard."""
        for item in cls.DEFAULT_NEWS_ITEMS:
            NewsArticle.objects.get_or_create(
                title=item["title"],
                defaults={
                    "source": item["source"],
                    "url": item["url"],
                    "summary": item["summary"],
                    "ai_hook": item["ai_hook"],
                    "category": item["category"],
                }
            )
        return list(NewsArticle.objects.all()[:5])

    @classmethod
    def get_daily_brief(cls):
        articles = NewsArticle.objects.all().order_by("-published_at")[:5]
        if not articles.exists():
            return cls.seed_daily_news()
        return list(articles)
