from django.urls import path
from .views import RepurposeContentView, ReviewBrandVoiceView, GenerateScriptView, AIChatbotView, AIChatbotAPIView

app_name = "ai_agents"

urlpatterns = [
    path("repurpose/<int:item_id>/", RepurposeContentView.as_view(), name="repurpose_item"),
    path("review/", ReviewBrandVoiceView.as_view(), name="review_content"),
    path("generate-script/", GenerateScriptView.as_view(), name="generate_script"),
    path("chat/", AIChatbotView.as_view(), name="chat"),
    path("api/chat/", AIChatbotAPIView.as_view(), name="api_chat"),
]
