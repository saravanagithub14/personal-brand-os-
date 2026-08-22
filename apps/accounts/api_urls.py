from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.UserProfileAPIView.as_view(), name="api_user_profile"),
    path("register/", views.RegisterAPIView.as_view(), name="api_register"),
    path("login/", views.LoginAPIView.as_view(), name="api_login"),
    path("logout/", views.LogoutAPIView.as_view(), name="api_logout"),
]
