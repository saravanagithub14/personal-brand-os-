from django.db import models
from django.conf import settings
from .fields import EncryptedTextField


class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ("INSTAGRAM", "Instagram"),
        ("LINKEDIN", "LinkedIn"),
        ("X_TWITTER", "X / Twitter"),
        ("YOUTUBE", "YouTube"),
        ("GITHUB", "GitHub"),
        ("THREADS", "Threads"),
        ("MEDIUM", "Medium"),
        ("ORCID", "ORCID Research"),
        ("RESEARCHGATE", "ResearchGate"),
        ("FACEBOOK", "Facebook"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_accounts"
    )
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    handle = models.CharField(max_length=100, help_text="e.g. @cellstocode")
    profile_url = models.URLField(blank=True, default="")
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0, help_text="Percentage engagement rate e.g. 4.5")
    total_impressions = models.PositiveIntegerField(default=0)
    stars_count = models.PositiveIntegerField(default=0)
    citations_count = models.PositiveIntegerField(default=0)
    last_post_at = models.DateTimeField(blank=True, null=True)
    target_cadence_days = models.PositiveIntegerField(default=3, help_text="Target frequency in days (e.g. 2 for IG, 3 for LinkedIn, 7 for GitHub)")
    active = models.BooleanField(default=True)
    # OAuth 2.0 Credentials & Storage
    provider_user_id = models.CharField(max_length=255, blank=True, null=True)
    access_token = EncryptedTextField(blank=True, default="")
    refresh_token = EncryptedTextField(blank=True, default="")
    token_expires_at = models.DateTimeField(blank=True, null=True)
    scopes = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "platform")
        ordering = ["-followers_count"]

    def __str__(self):
        return f"{self.get_platform_display()} ({self.handle}) - {self.user.username}"

    @property
    def days_since_last_post(self):
        if not self.last_post_at:
            return 999
        from django.utils import timezone
        delta = timezone.now() - self.last_post_at
        return max(0, delta.days)

    @property
    def health_status(self):
        days = self.days_since_last_post
        if days <= self.target_cadence_days:
            return "ON_TRACK"
        elif days <= self.target_cadence_days + 2:
            return "DUE_SOON"
        else:
            return "OVERDUE"

    @property
    def is_connected(self):
        return bool(self.access_token) and not self.is_token_expired

    @property
    def is_token_expired(self):
        if not self.token_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at

    @property
    def requires_reauthorization(self):
        return bool(self.access_token) and self.is_token_expired

    @property
    def health_badge(self):
        status = self.health_status
        if status == "ON_TRACK":
            return {"label": "On Track", "emoji": "🟢", "bg": "#e6f4ea", "color": "#137333", "border": "#ceedd5"}
        elif status == "DUE_SOON":
            return {"label": "Due Soon", "emoji": "🟡", "bg": "#fef7e0", "color": "#b06000", "border": "#feefc3"}
        else:
            return {"label": "Overdue Alert", "emoji": "🔴", "bg": "#fce8e6", "color": "#c5221f", "border": "#fad2cf"}
