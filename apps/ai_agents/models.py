from django.db import models
from django.conf import settings


class AgentPromptTemplate(models.Model):
    AGENT_TYPES = [
        ("STRATEGIST", "Content Strategist"),
        ("IDEATOR", "Idea Generator"),
        ("WRITER", "Writer"),
        ("SCRIPTWRITER", "Script Writer"),
        ("REPURPOSER", "Content Repurposer"),
        ("REVIEWER", "Brand Reviewer"),
    ]

    name = models.CharField(max_length=100, unique=True)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_agent_type_display()} - {self.name}"


class AgentExecutionLog(models.Model):
    MODEL_TIERS = [
        ("FLAGSHIP", "Flagship Tier (250k/day quota)"),
        ("MINI_NANO", "Mini/Nano Tier (2.5M/day quota)"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_logs")
    agent_name = models.CharField(max_length=100)
    input_text = models.TextField()
    output_text = models.TextField()
    model_used = models.CharField(max_length=50, default="gpt-4o-mini")
    model_tier = models.CharField(max_length=20, choices=MODEL_TIERS, default="MINI_NANO")
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent_name} ({self.model_used}) - {self.total_tokens} tokens"


class TopicResearchCampaign(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("QUEUED", "Queued"),
        ("RESEARCHING", "Researching & Fact Checking"),
        ("GENERATING_MEDIUM", "Drafting Medium Article"),
        ("GENERATING_REEL", "Writing Instagram Reel Script"),
        ("GENERATING_LINKEDIN", "Creating LinkedIn Post"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="research_campaigns")
    topic = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")
    research_depth = models.CharField(max_length=20, default="DEEP", choices=[("QUICK", "Quick"), ("STANDARD", "Standard"), ("DEEP", "Deep")])

    # Outputs
    research_notes = models.TextField(blank=True, default="")
    fact_check_summary = models.TextField(blank=True, default="")
    medium_blog = models.TextField(blank=True, default="")
    insta_reel_script = models.TextField(blank=True, default="")
    insta_reel_caption = models.TextField(blank=True, default="")
    linkedin_post = models.TextField(blank=True, default="")

    medium_link = models.URLField(blank=True, default="", help_text="Link to published Medium blog post")
    insta_reel_link = models.URLField(blank=True, default="", help_text="Link to published Instagram Reel")

    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Campaign: {self.topic} ({self.status})"
