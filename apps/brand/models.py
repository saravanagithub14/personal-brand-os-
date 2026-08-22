from django.db import models
from django.conf import settings


class BrandProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="brand_profile"
    )
    name = models.CharField(max_length=255, blank=True, default="")
    professional_title = models.CharField(max_length=255, blank=True, default="")
    short_bio = models.CharField(max_length=500, blank=True, default="")
    long_bio = models.TextField(blank=True, default="")
    positioning_statement = models.TextField(blank=True, default="")
    niche = models.CharField(max_length=255, blank=True, default="")
    target_audience = models.TextField(blank=True, default="")
    expertise = models.TextField(blank=True, default="")
    skills = models.TextField(blank=True, default="")
    languages = models.CharField(max_length=255, blank=True, default="English")
    content_goals = models.TextField(blank=True, default="")
    career_story = models.TextField(blank=True, default="")
    achievements = models.TextField(blank=True, default="")
    education = models.TextField(blank=True, default="")
    experience = models.TextField(blank=True, default="")
    workshops = models.TextField(blank=True, default="")
    publications = models.TextField(blank=True, default="")
    portfolio_url = models.URLField(blank=True, default="")
    social_profiles = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Brand Profile - {self.name or self.user.username}"


class BrandVoice(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="brand_voice"
    )
    tone = models.CharField(max_length=255, blank=True, default="Authoritative yet accessible")
    sentence_length = models.CharField(max_length=255, blank=True, default="Short to medium")
    vocabulary_preferences = models.TextField(blank=True, default="")
    words_to_avoid = models.TextField(blank=True, default="")
    phrases_to_avoid = models.TextField(blank=True, default="")
    preferred_hooks = models.TextField(blank=True, default="")
    cta_style = models.CharField(max_length=255, blank=True, default="Direct and value-driven")
    technical_depth = models.CharField(max_length=255, blank=True, default="Intermediate to Advanced")
    audience_level = models.CharField(max_length=255, blank=True, default="Professionals & Engineers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Brand Voice - {self.user.username}"
