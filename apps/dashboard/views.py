from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.content.models import ContentItem, ContentPillar
from apps.projects.models import Project
from apps.brand.models import BrandProfile


from django.db.models import Sum, Avg
from django.shortcuts import render, redirect
from apps.social.models import SocialAccount
from apps.analytics.models import SocialAnalyticsSnapshot


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        content_qs = ContentItem.objects.filter(user=user)

        metrics = {
            "total_content": content_qs.count(),
            "ideas_count": content_qs.filter(status="IDEA").count(),
            "drafts_count": content_qs.filter(status__in=["DRAFT", "EDITING", "AI_GENERATED"]).count(),
            "scheduled_count": content_qs.filter(status__in=["APPROVED", "SCHEDULED"]).count(),
            "published_count": content_qs.filter(status="PUBLISHED").count(),
            "pillars_count": ContentPillar.objects.filter(user=user, active=True).count(),
            "projects_count": Project.objects.filter(user=user).count(),
        }

        recent_items = content_qs.order_by("-updated_at")[:5]
        profile, _ = BrandProfile.objects.get_or_create(user=user)

        projects = Project.objects.filter(user=user).order_by("-updated_at")
        published_items = content_qs.filter(status="PUBLISHED").order_by("-published_at", "-updated_at")

        social_accounts = SocialAccount.objects.filter(user=user, active=True)

        total_followers = social_accounts.aggregate(Sum("followers_count"))["followers_count__sum"] or 0
        total_impressions = social_accounts.aggregate(Sum("total_impressions"))["total_impressions__sum"] or 0
        avg_engagement = social_accounts.aggregate(Avg("engagement_rate"))["engagement_rate__avg"] or 0.0

        # Compute Consistency Radar & Urgent Brand Plan Alerts
        on_track = sum(1 for a in social_accounts if a.health_status == "ON_TRACK")
        due_soon = sum(1 for a in social_accounts if a.health_status == "DUE_SOON")
        overdue = sum(1 for a in social_accounts if a.health_status == "OVERDUE")
        total_accs = social_accounts.count() or 1
        consistency_score = round(((on_track + (due_soon * 0.5)) / total_accs) * 100)

        urgent_brand_alerts = []
        for acc in social_accounts:
            if acc.health_status == "OVERDUE":
                urgent_brand_alerts.append({
                    "id": acc.id,
                    "platform": acc.platform,
                    "platform_display": acc.get_platform_display(),
                    "handle": acc.handle,
                    "days_since": acc.days_since_last_post,
                    "target_days": acc.target_cadence_days,
                    "last_post_at": acc.last_post_at,
                })

        consistency_radar = {
            "score": min(100, consistency_score),
            "on_track_count": on_track,
            "due_soon_count": due_soon,
            "overdue_count": overdue,
            "total_channels": social_accounts.count(),
        }

        social_analytics = {
            "total_followers": total_followers,
            "total_impressions": total_impressions,
            "avg_engagement": round(avg_engagement, 1),
            "channels_count": social_accounts.count(),
        }

        from apps.news.services import NewsIngestionService
        daily_news = list(NewsIngestionService.get_daily_brief())

        context = {
            "user": user,
            "profile": profile,
            "metrics": metrics,
            "recent_items": recent_items,
            "public_projects": projects,
            "published_items": published_items,
            "public_portfolio_path": f"/portfolio/{user.username}/",
            "social_accounts": social_accounts,
            "social_analytics": social_analytics,
            "consistency_radar": consistency_radar,
            "urgent_brand_alerts": urgent_brand_alerts,
            "daily_news": daily_news,
        }
        return render(request, "dashboard/index.html", context)

    def post(self, request):
        user = request.user
        action = request.POST.get("action")
        if action == "save_social_account":
            platform = request.POST.get("platform")
            handle = request.POST.get("handle")
            profile_url = request.POST.get("profile_url", "")
            followers_count = request.POST.get("followers_count", 0)
            total_impressions = request.POST.get("total_impressions", 0)
            engagement_rate = request.POST.get("engagement_rate", 0.0)

            if platform and handle:
                account, _ = SocialAccount.objects.get_or_create(user=user, platform=platform)
                account.handle = handle
                if profile_url:
                    account.profile_url = profile_url
                try:
                    if int(followers_count) >= 0:
                        account.followers_count = int(followers_count)
                    if int(total_impressions) >= 0:
                        account.total_impressions = int(total_impressions)
                    if float(engagement_rate) >= 0:
                        account.engagement_rate = float(engagement_rate)
                except (TypeError, ValueError):
                    # Leave existing values unchanged when optional inputs are invalid.
                    pass
                account.save()

        return redirect("dashboard:index")




class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        content_qs = ContentItem.objects.filter(user=user)

        return Response({
            "status": "online",
            "user": user.username,
            "metrics": {
                "total_content": content_qs.count(),
                "ideas": content_qs.filter(status="IDEA").count(),
                "drafts": content_qs.filter(status__in=["DRAFT", "EDITING", "AI_GENERATED"]).count(),
                "scheduled": content_qs.filter(status__in=["APPROVED", "SCHEDULED"]).count(),
                "published": content_qs.filter(status="PUBLISHED").count(),
                "pillars": ContentPillar.objects.filter(user=user, active=True).count(),
                "projects": Project.objects.filter(user=user).count(),
            }
        })
