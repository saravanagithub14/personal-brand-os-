from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ContentPillar, ContentItem, ContentVersion, ContentApproval
from .serializers import ContentPillarSerializer, ContentItemSerializer, ContentVersionSerializer
from .services import ContentService


# UI Views
class ContentListView(LoginRequiredMixin, View):
    def get(self, request):
        items = ContentItem.objects.filter(user=request.user).order_by("-updated_at")
        status_filter = request.GET.get("status")
        if status_filter:
            items = items.filter(status=status_filter)
        return render(request, "content/list.html", {"items": items, "current_status": status_filter})


class ContentEditorView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        item = get_object_or_404(ContentItem, pk=pk, user=request.user) if pk else None
        pillars = ContentPillar.objects.filter(user=request.user, active=True)
        return render(request, "content/editor.html", {"item": item, "pillars": pillars})

    def post(self, request, pk=None):
        data = {
            "title": request.POST.get("title", "Untitled Content"),
            "idea": request.POST.get("idea", ""),
            "platform": request.POST.get("platform", "LINKEDIN"),
            "content_type": request.POST.get("content_type") or request.POST.get("platform", "LINKEDIN"),
            "status": request.POST.get("status", "DRAFT"),
            "priority": request.POST.get("priority", "MEDIUM"),
            "hook": request.POST.get("hook", ""),
            "body": request.POST.get("body", ""),
            "cta": request.POST.get("cta", ""),
            "script": request.POST.get("script", ""),
            "caption": request.POST.get("caption", ""),
            "hashtags": request.POST.get("hashtags", ""),
            "visual_instructions": request.POST.get("visual_instructions", ""),
            "change_reason": request.POST.get("change_reason", "Manual Edit"),
        }
        pillar_id = request.POST.get("pillar")
        if pillar_id:
            data["pillar"] = ContentPillar.objects.filter(id=pillar_id, user=request.user).first()

        item = ContentService.save_content_item(request.user, item_id=pk, **data)
        return redirect("content:editor_edit", pk=item.pk)


class IdeasListView(LoginRequiredMixin, View):
    def get(self, request):
        ideas = ContentItem.objects.filter(user=request.user, status="IDEA").order_by("-created_at")
        return render(request, "content/ideas.html", {"ideas": ideas})

    def post(self, request):
        title = request.POST.get("title")
        idea_text = request.POST.get("idea")
        if title:
            ContentService.save_content_item(
                user=request.user,
                title=title,
                idea=idea_text,
                status="IDEA"
            )
        return redirect("content:ideas")


class PillarsListView(LoginRequiredMixin, View):
    def get(self, request):
        pillars = ContentPillar.objects.filter(user=request.user)
        return render(request, "content/pillars.html", {"pillars": pillars})

    def post(self, request):
        name = request.POST.get("name")
        description = request.POST.get("description")
        allocation = request.POST.get("allocation_percentage", 25)
        if name:
            try:
                allocation = int(allocation)
            except (TypeError, ValueError):
                allocation = 25
            allocation = max(0, min(100, allocation))
            ContentPillar.objects.create(
                user=request.user,
                name=name,
                description=description,
                allocation_percentage=allocation
            )
        return redirect("content:pillars")


# DRF API ViewSets
class ContentItemViewSet(viewsets.ModelViewSet):
    serializer_class = ContentItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        notes = request.data.get("notes", "Approved via API")
        approval = ContentService.approve_content_item(request.user, pk, notes=notes)
        return Response({"status": "approved", "approval_id": approval.id})


class ContentPillarViewSet(viewsets.ModelViewSet):
    serializer_class = ContentPillarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentPillar.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
