from django.db import migrations, models


PLATFORMS = [
    ("LINKEDIN", "LinkedIn"), ("X", "X (Twitter)"), ("X_TWITTER", "X / Twitter"),
    ("X_THREAD", "X Thread"), ("YOUTUBE", "YouTube Video"),
    ("YOUTUBE_SHORT", "YouTube Short"), ("INSTAGRAM_REEL", "Instagram Reel"),
    ("INSTAGRAM", "Instagram"), ("CAROUSEL", "Carousel"), ("BLOG", "Blog Article"),
    ("MEDIUM", "Medium"), ("NEWSLETTER", "Newsletter"), ("REDDIT", "Reddit"),
    ("FACEBOOK", "Facebook"), ("THREADS", "Threads"), ("STORY", "Story"),
]


class Migration(migrations.Migration):
    dependencies = [("content", "0001_initial")]

    operations = [
        migrations.AddField(model_name="contentitem", name="review_feedback", field=models.TextField(blank=True, default="")),
        migrations.AlterField(model_name="contentitem", name="content_type", field=models.CharField(choices=PLATFORMS, default="LINKEDIN", max_length=50)),
        migrations.AlterField(model_name="contentitem", name="platform", field=models.CharField(choices=PLATFORMS, default="LINKEDIN", max_length=50)),
    ]
