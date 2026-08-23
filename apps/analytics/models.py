from django.db import models
from apps.social.models import SocialAccount


class SocialAnalyticsSnapshot(models.Model):
    social_account = models.ForeignKey(
        SocialAccount, on_delete=models.CASCADE, related_name="snapshots"
    )
    followers = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    likes_engagement = models.PositiveIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.social_account.handle} snapshot @ {self.recorded_at.strftime('%Y-%m-%d')}"
