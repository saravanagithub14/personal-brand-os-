from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "content"

router = DefaultRouter()
router.register(r"items", views.ContentItemViewSet, basename="content_item_api")
router.register(r"pillars", views.ContentPillarViewSet, basename="content_pillar_api")

urlpatterns = [
    path("", views.ContentListView.as_view(), name="list"),
    path("editor/", views.ContentEditorView.as_view(), name="editor_create"),
    path("editor/<int:pk>/", views.ContentEditorView.as_view(), name="editor_edit"),
    path("ideas/", views.IdeasListView.as_view(), name="ideas"),
    path("pillars/", views.PillarsListView.as_view(), name="pillars"),
    # API router endpoints
    path("api/", include(router.urls)),
]
