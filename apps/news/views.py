from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.content.models import ContentItem
from .models import NewsArticle
from .services import NewsIngestionService


class CreateDraftFromNewsView(LoginRequiredMixin, View):
    def post(self, request, article_id):
        user = request.user
        article = get_object_or_404(NewsArticle, id=article_id)
        platform = request.POST.get("platform", "LINKEDIN")

        body_text = f"{article.ai_hook}\n\nSummary:\n{article.summary}\n\nRead full article: {article.url or ''}"

        item = ContentItem.objects.create(
            user=user,
            platform=platform,
            title=f"News Analysis: {article.title[:60]}",
            body=body_text,
            status="DRAFT",
        )

        return redirect("content:editor_edit", pk=item.id)
