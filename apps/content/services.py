from django.db import transaction
from django.utils import timezone
from .models import ContentItem, ContentVersion, ContentApproval


class ContentService:
    @staticmethod
    @transaction.atomic
    def save_content_item(user, item_id=None, **data):
        reason = data.pop("change_reason", "Manual Edit")

        if item_id:
            item = ContentItem.objects.get(id=item_id, user=user)
            for key, val in data.items():
                if hasattr(item, key):
                    setattr(item, key, val)
            item.save()
        else:
            item = ContentItem.objects.create(user=user, **data)

        # Create ContentVersion snapshot
        latest_version = item.versions.order_by("-version_number").first()
        new_version_num = (latest_version.version_number + 1) if latest_version else 1

        snapshot = {
            "title": item.title,
            "hook": item.hook,
            "body": item.body,
            "cta": item.cta,
            "script": item.script,
            "caption": item.caption,
            "hashtags": item.hashtags,
            "status": item.status,
        }

        ContentVersion.objects.create(
            content_item=item,
            version_number=new_version_num,
            content_snapshot=snapshot,
            created_by=user,
            change_reason=reason,
        )
        return item

    @staticmethod
    @transaction.atomic
    def approve_content_item(user, item_id, notes="Approved by user"):
        item = ContentItem.objects.get(id=item_id, user=user)
        item.status = "APPROVED"
        item.save()

        latest_version = item.versions.order_by("-version_number").first()

        approval = ContentApproval.objects.create(
            content_item=item,
            reviewer=user,
            status="APPROVED",
            notes=notes,
            version=latest_version,
            approved_at=timezone.now(),
        )
        return approval
