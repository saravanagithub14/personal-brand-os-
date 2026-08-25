from django.db import migrations

import apps.social.fields


class Migration(migrations.Migration):
    dependencies = [("social", "0004_socialaccount_access_token_socialaccount_metadata_and_more")]

    operations = [
        migrations.AlterField(
            model_name="socialaccount",
            name="access_token",
            field=apps.social.fields.EncryptedTextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="socialaccount",
            name="refresh_token",
            field=apps.social.fields.EncryptedTextField(blank=True, default=""),
        ),
    ]
