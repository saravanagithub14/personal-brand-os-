from rest_framework import serializers
from .models import ContentPillar, ContentItem, ContentVersion, ContentApproval


class ContentPillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentPillar
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


class ContentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentVersion
        fields = "__all__"


class ContentApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentApproval
        fields = "__all__"


class ContentItemSerializer(serializers.ModelSerializer):
    versions = ContentVersionSerializer(many=True, read_only=True)
    approvals = ContentApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = ContentItem
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")
