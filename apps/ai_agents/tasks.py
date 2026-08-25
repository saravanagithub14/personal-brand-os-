import logging

from celery import shared_task

from .services import TopicResearchCampaignOrchestrator

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def run_topic_research_campaign(self, campaign_id):
    """Run a campaign outside the request/response lifecycle."""
    return TopicResearchCampaignOrchestrator.run_campaign(campaign_id)
