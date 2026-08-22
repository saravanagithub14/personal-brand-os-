from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    # API endpoints
    path("api/accounts/", include("apps.accounts.api_urls")),
    path("api/dashboard/", include("apps.dashboard.api_urls")),
    path("api/brand/", include("apps.brand.urls")),
    path("api/content/", include("apps.content.urls")),
    path("api/calendar/", include("apps.calendar.urls")),
    path("api/ai_agents/", include("apps.ai_agents.urls")),
    path("api/research/", include("apps.research.urls")),
    path("api/news/", include("apps.news.urls")),
    path("api/social/", include("apps.social.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/media/", include("apps.media.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
