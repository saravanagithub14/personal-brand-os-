from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.DashboardSummaryAPIView.as_view(), name="api_dashboard_summary"),
]
