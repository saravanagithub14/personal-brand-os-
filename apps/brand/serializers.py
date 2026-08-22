from rest_framework import serializers
from .models import BrandProfile, BrandVoice


class BrandProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandProfile
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


class BrandVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandVoice
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")
