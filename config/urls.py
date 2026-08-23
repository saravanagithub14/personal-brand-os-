from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.brand.views import PublicPortfolioView
from apps.social.views import LinkedInOAuthLoginView, LinkedInOAuthCallbackView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("brand/", include("apps.brand.urls")),
    path("social/", include("apps.social.urls")),
    path("auth/linkedin/connect/", LinkedInOAuthLoginView.as_view(), name="auth_linkedin_connect"),
    path("auth/linkedin/callback/", LinkedInOAuthCallbackView.as_view(), name="auth_linkedin_callback"),
    path("portfolio/", PublicPortfolioView.as_view(), name="public_portfolio"),
    path("portfolio/<str:username>/", PublicPortfolioView.as_view(), name="public_portfolio_user"),
    path("", include("apps.dashboard.urls")),
    path("content/", include("apps.content.urls")),
    path("agents/", include("apps.ai_agents.urls")),
    path("research/", include("apps.research.urls")),
    path("news/", include("apps.news.urls")),
    # API endpoints
    path("api/accounts/", include("apps.accounts.api_urls")),
    path("api/dashboard/", include("apps.dashboard.api_urls")),
    path("api/calendar/", include("apps.calendar.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/media/", include("apps.media.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
