from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils.dateparse import parse_datetime
from apps.content.models import ContentItem
from apps.content.serializers import ContentItemSerializer
from apps.content.services import ContentService


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        scheduled_items = ContentItem.objects.filter(
            user=request.user
        ).exclude(status="ARCHIVED").order_by("scheduled_at", "-created_at")

        return render(request, "calendar/index.html", {"items": scheduled_items})


# DRF APIs
class RescheduleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_id = request.data.get("content_id")
        scheduled_at_str = request.data.get("scheduled_at")

        if not content_id or not scheduled_at_str:
            return Response(
                {"detail": "content_id and scheduled_at are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(ContentItem, pk=content_id, user=request.user)
        scheduled_at = parse_datetime(scheduled_at_str)
        if not scheduled_at:
            return Response({"detail": "Invalid datetime format"}, status=status.HTTP_400_BAD_REQUEST)

        item.scheduled_at = scheduled_at
        if item.status in ["DRAFT", "EDITING", "APPROVED"]:
            item.status = "SCHEDULED"
        item.save()

        # Save version snapshot
        ContentService.save_content_item(
            user=request.user,
            item_id=item.id,
            change_reason=f"Rescheduled to {scheduled_at_str}"
        )

        return Response(ContentItemSerializer(item).data)


class DuplicateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_id = request.data.get("content_id")
        item = get_object_or_404(ContentItem, pk=content_id, user=request.user)

        new_item = ContentService.save_content_item(
            user=request.user,
            title=f"Copy of {item.title}",
            idea=item.idea,
            content_type=item.content_type,
            platform=item.platform,
            pillar=item.pillar,
            hook=item.hook,
            body=item.body,
            cta=item.cta,
            script=item.script,
            caption=item.caption,
            hashtags=item.hashtags,
            status="DRAFT",
            change_reason=f"Duplicated from Content #{item.id}"
        )
        return Response(ContentItemSerializer(new_item).data, status=status.HTTP_201_CREATED)
