from django.urls import path
from .views import (
    AutoSyncSocialAccountView,
    SocialAccountDetailView,
    UpdateLastPostDateView,
    LinkedInOAuthLoginView,
    LinkedInOAuthCallbackView,
    LinkedInOAuthDisconnectView,
    LinkedInPublishPostView,
)

app_name = "social"

urlpatterns = [
    path("sync/", AutoSyncSocialAccountView.as_view(), name="sync_all"),
    path("sync/<int:account_id>/", AutoSyncSocialAccountView.as_view(), name="sync_account"),
    path("account/<int:account_id>/", SocialAccountDetailView.as_view(), name="account_detail"),
    path("update-last-post/<int:account_id>/", UpdateLastPostDateView.as_view(), name="update_last_post"),
    path("linkedin/login/", LinkedInOAuthLoginView.as_view(), name="linkedin_login"),
    path("linkedin/callback/", LinkedInOAuthCallbackView.as_view(), name="linkedin_callback"),
    path("linkedin/disconnect/", LinkedInOAuthDisconnectView.as_view(), name="linkedin_disconnect"),
    path("account/<int:account_id>/publish/", LinkedInPublishPostView.as_view(), name="linkedin_publish"),
]
