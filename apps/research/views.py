from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import KnowledgeDocument
from .services import RetrievalService


class KnowledgeBaseListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        query = request.GET.get("q", "")
        documents = RetrievalService.search_knowledge_base(user, query, limit=20)

        context = {
            "documents": documents,
            "query": query,
        }
        return render(request, "research/list.html", context)

    def post(self, request):
        user = request.user
        title = request.POST.get("title", "").strip()
        source_url = request.POST.get("source_url", "").strip()
        content_text = request.POST.get("content_text", "").strip()
        tags = request.POST.get("tags", "").strip()

        if title and content_text:
            KnowledgeDocument.objects.create(
                user=user,
                title=title,
                source_url=source_url,
                content_text=content_text,
                tags=tags,
            )

        return redirect("research:list")
