import pytest
from django.contrib.auth import get_user_model
from apps.ai_agents.models import TopicResearchCampaign
from apps.ai_agents.services import TopicResearchCampaignOrchestrator
from apps.content.models import ContentItem

User = get_user_model()


@pytest.mark.django_db
def test_topic_research_campaign_pipeline():
    user, _ = User.objects.get_or_create(username="campaign_user_unique", defaults={"email": "campaign@example.com"})
    user.set_password("password123")
    user.save()
    
    campaign = TopicResearchCampaign.objects.create(
        user=user,
        topic="The Future of Autonomous AI Agents in 2026",
        medium_link="https://medium.com/@test/future-ai-agents",
        insta_reel_link="https://instagram.com/reels/future-ai-agents",
    )

    assert campaign.status == "PENDING"

    # Execute orchestrator
    completed_campaign = TopicResearchCampaignOrchestrator.run_campaign(campaign.id)

    assert completed_campaign is not None
    assert completed_campaign.status == "COMPLETED"
    assert "Deep Research & Fact-Check Summary" in completed_campaign.research_notes
    assert "Definitive Deep-Dive" in completed_campaign.medium_blog
    assert "INSTAGRAM REEL SCRIPT" in completed_campaign.insta_reel_script
    assert "Medium" in completed_campaign.linkedin_post
    assert "Instagram Reel" in completed_campaign.linkedin_post

    # Verify auto-created drafts in ContentItem bank
    medium_draft = ContentItem.objects.filter(user=user, platform="MEDIUM").first()
    insta_draft = ContentItem.objects.filter(user=user, platform="INSTAGRAM").first()
    linkedin_draft = ContentItem.objects.filter(user=user, platform="LINKEDIN").first()

    assert medium_draft is not None
    assert insta_draft is not None
    assert linkedin_draft is not None
    assert medium_draft.status == "DRAFT"
