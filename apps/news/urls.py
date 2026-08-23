from django.urls import path
from .views import CreateDraftFromNewsView

app_name = "news"

urlpatterns = [
    path("create-draft/<int:article_id>/", CreateDraftFromNewsView.as_view(), name="create_draft"),
]
