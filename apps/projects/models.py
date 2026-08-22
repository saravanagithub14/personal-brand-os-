from django.db import models
from django.conf import settings


class Project(models.Model):
    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("ARCHIVED", "Archived"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    problem = models.TextField(blank=True, default="")
    solution = models.TextField(blank=True, default="")
    technologies = models.CharField(max_length=500, blank=True, default="")
    github_url = models.URLField(blank=True, default="")
    demo_url = models.URLField(blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="Software Engineering")
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="IN_PROGRESS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
