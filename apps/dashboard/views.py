from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.content.models import ContentItem, ContentPillar
from apps.projects.models import Project
from apps.brand.models import BrandProfile


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

        context = {
            "user": user,
            "profile": profile,
            "metrics": metrics,
            "recent_items": recent_items,
        }
        return render(request, "dashboard/index.html", context)


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
