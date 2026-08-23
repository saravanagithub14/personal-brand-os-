from django.urls import path
from .views import KnowledgeBaseListView

app_name = "research"

urlpatterns = [
    path("", KnowledgeBaseListView.as_view(), name="list"),
]
