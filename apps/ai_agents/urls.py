from django.urls import path
from .views import (
    RepurposeContentView,
    ReviewBrandVoiceView,
    GenerateScriptView,
    AIChatbotView,
    AIChatbotAPIView,
    TopicCampaignListView,
    TopicCampaignCreateView,
    TopicCampaignDetailView,
    PublishMediumDraftView,
    GenerateCampaignImagesView,
)

app_name = "ai_agents"

urlpatterns = [
    path("repurpose/<int:item_id>/", RepurposeContentView.as_view(), name="repurpose_item"),
    path("review/", ReviewBrandVoiceView.as_view(), name="review_content"),
    path("generate-script/", GenerateScriptView.as_view(), name="generate_script"),
    path("chat/", AIChatbotView.as_view(), name="chat"),
    path("api/chat/", AIChatbotAPIView.as_view(), name="api_chat"),
    path("campaigns/", TopicCampaignListView.as_view(), name="campaign_list"),
    path("campaigns/create/", TopicCampaignCreateView.as_view(), name="campaign_create"),
    path("campaigns/<int:campaign_id>/", TopicCampaignDetailView.as_view(), name="campaign_detail"),
    path("campaigns/<int:campaign_id>/publish-medium/", PublishMediumDraftView.as_view(), name="publish_medium_draft"),
    path("campaigns/<int:campaign_id>/generate-images/", GenerateCampaignImagesView.as_view(), name="generate_campaign_images"),
]

