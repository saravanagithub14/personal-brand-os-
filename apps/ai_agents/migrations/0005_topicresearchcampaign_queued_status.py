from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_agents", "0004_add_research_depth_to_campaign")]

    operations = [
        migrations.AlterField(
            model_name="topicresearchcampaign",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"), ("QUEUED", "Queued"),
                    ("RESEARCHING", "Researching & Fact Checking"),
                    ("GENERATING_MEDIUM", "Drafting Medium Article"),
                    ("GENERATING_REEL", "Writing Instagram Reel Script"),
                    ("GENERATING_LINKEDIN", "Creating LinkedIn Post"),
                    ("COMPLETED", "Completed"), ("FAILED", "Failed"),
                ],
                default="PENDING", max_length=30,
            ),
        ),
    ]
