from django.urls import path
from . import views

app_name = "calendar"

urlpatterns = [
    path("", views.CalendarView.as_view(), name="index"),
    path("api/reschedule/", views.RescheduleAPIView.as_view(), name="api_reschedule"),
    path("api/duplicate/", views.DuplicateAPIView.as_view(), name="api_duplicate"),
]
