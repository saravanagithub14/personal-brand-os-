from django.db.models import Q
from .models import KnowledgeDocument


class RetrievalService:
    """RAG & Context Retrieval Service for personal research documents & notes."""

    @classmethod
    def search_knowledge_base(cls, user, query_text, limit=5):
        if not user or not user.is_authenticated:
            return KnowledgeDocument.objects.none()

        if not query_text:
            return KnowledgeDocument.objects.filter(user=user)[:limit]

        keywords = [k.strip() for k in query_text.split() if len(k.strip()) > 2]
        query_filter = Q()

        for kw in keywords:
            query_filter |= Q(title__icontains=kw) | Q(content_text__icontains=kw) | Q(tags__icontains=kw)

        results = KnowledgeDocument.objects.filter(user=user).filter(query_filter).distinct()[:limit]

        if not results.exists():
            return KnowledgeDocument.objects.filter(user=user)[:limit]

        return results

    @classmethod
    def format_context_snippet(cls, documents):
        if not documents:
            return ""
        snippets = []
        for i, doc in enumerate(documents, 1):
            snippets.append(f"[{i}] {doc.title}:\n{doc.content_text[:300]}...")
        return "\n\n".join(snippets)
