from django.urls import path
from . import views

app_name = "brand"

urlpatterns = [
    path("", views.BrandDetailView.as_view(), name="profile"),
    path("api/profile/", views.BrandProfileAPIView.as_view(), name="api_profile"),
    path("api/voice/", views.BrandVoiceAPIView.as_view(), name="api_voice"),
]
