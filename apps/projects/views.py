from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer
from .services import ProjectContentService
from apps.content.serializers import ContentItemSerializer


class ProjectListView(LoginRequiredMixin, View):
    def get(self, request):
        projects = Project.objects.filter(user=request.user).order_by("-updated_at")
        return render(request, "projects/list.html", {"projects": projects})

    def post(self, request):
        action_type = request.POST.get("action")
        if action_type == "create_content":
            project_id = request.POST.get("project_id")
            project = get_object_or_404(Project, pk=project_id, user=request.user)
            platform = request.POST.get("platform", "LINKEDIN")
            item = ProjectContentService.create_content_from_project(request.user, project, platform=platform)
            return redirect("content:editor_edit", pk=item.pk)

        # Create Project
        title = request.POST.get("title")
        description = request.POST.get("description")
        problem = request.POST.get("problem")
        solution = request.POST.get("solution")
        technologies = request.POST.get("technologies")
        github_url = request.POST.get("github_url", "")
        demo_url = request.POST.get("demo_url", "")

        if title:
            Project.objects.create(
                user=request.user,
                title=title,
                description=description,
                problem=problem,
                solution=solution,
                technologies=technologies,
                github_url=github_url,
                demo_url=demo_url
            )
        return redirect("projects:list")


# DRF API ViewSet
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def create_content(self, request, pk=None):
        project = self.get_object()
        platform = request.data.get("platform", "LINKEDIN")
        content_item = ProjectContentService.create_content_from_project(request.user, project, platform)
        return Response(ContentItemSerializer(content_item).data, status=status.HTTP_201_CREATED)
