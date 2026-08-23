from django.db import models
from django.conf import settings


class KnowledgeDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_docs")
    title = models.CharField(max_length=255)
    source_url = models.URLField(max_length=500, blank=True, null=True)
    content_text = models.TextField()
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags e.g. python, genomics, AI")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"
