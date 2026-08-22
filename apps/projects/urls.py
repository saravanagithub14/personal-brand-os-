from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "projects"

router = DefaultRouter()
router.register(r"", views.ProjectViewSet, basename="project_api")

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("api/", include(router.urls)),
]
