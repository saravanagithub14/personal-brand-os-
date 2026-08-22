from django.db import models
from django.conf import settings


class ContentPillar(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_pillars"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    target_audience = models.TextField(blank=True, default="")
    preferred_platforms = models.JSONField(blank=True, default=list)
    content_formats = models.JSONField(blank=True, default=list)
    allocation_percentage = models.IntegerField(default=25)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    STATUS_CHOICES = [
        ("IDEA", "Idea"),
        ("RESEARCHING", "Researching"),
        ("DRAFT", "Draft"),
        ("AI_GENERATED", "AI Generated"),
        ("EDITING", "Editing"),
        ("APPROVED", "Approved"),
        ("SCHEDULED", "Scheduled"),
        ("PUBLISHED", "Published"),
        ("ARCHIVED", "Archived"),
    ]

    PLATFORM_CHOICES = [
        ("LINKEDIN", "LinkedIn"),
        ("X", "X (Twitter)"),
        ("X_THREAD", "X Thread"),
        ("YOUTUBE", "YouTube Video"),
        ("YOUTUBE_SHORT", "YouTube Short"),
        ("INSTAGRAM_REEL", "Instagram Reel"),
        ("CAROUSEL", "Carousel"),
        ("BLOG", "Blog Article"),
        ("NEWSLETTER", "Newsletter"),
        ("REDDIT", "Reddit"),
        ("FACEBOOK", "Facebook"),
        ("THREADS", "Threads"),
        ("STORY", "Story"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_items"
    )
    title = models.CharField(max_length=255)
    idea = models.TextField(blank=True, default="")
    content_type = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default="LINKEDIN")
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default="LINKEDIN")
    pillar = models.ForeignKey(
        ContentPillar, on_delete=models.SET_NULL, null=True, blank=True, related_name="content_items"
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="IDEA")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="MEDIUM")
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    hook = models.TextField(blank=True, default="")
    body = models.TextField(blank=True, default="")
    cta = models.TextField(blank=True, default="")
    hashtags = models.CharField(max_length=500, blank=True, default="")
    keywords = models.CharField(max_length=500, blank=True, default="")
    references = models.TextField(blank=True, default="")
    source_urls = models.TextField(blank=True, default="")
    script = models.TextField(blank=True, default="")
    caption = models.TextField(blank=True, default="")
    visual_instructions = models.TextField(blank=True, default="")
    thumbnail_idea = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ContentVersion(models.Model):
    content_item = models.ForeignKey(
        ContentItem, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.IntegerField()
    content_snapshot = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    change_reason = models.CharField(max_length=255, blank=True, default="Manual Edit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]

    def __str__(self):
        return f"v{self.version_number} - {self.content_item.title}"


class ContentApproval(models.Model):
    APPROVAL_STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    content_item = models.ForeignKey(
        ContentItem, on_delete=models.CASCADE, related_name="approvals"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=50, choices=APPROVAL_STATUS, default="PENDING")
    notes = models.TextField(blank=True, default="")
    version = models.ForeignKey(
        ContentVersion, on_delete=models.SET_NULL, null=True, blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Approval ({self.status}) for {self.content_item.title}"
