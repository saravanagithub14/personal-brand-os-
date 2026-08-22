from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import generics, permissions
from .models import BrandProfile, BrandVoice
from .serializers import BrandProfileSerializer, BrandVoiceSerializer


class BrandDetailView(LoginRequiredMixin, View):
    def get(self, request):
        profile, _ = BrandProfile.objects.get_or_create(user=request.user)
        voice, _ = BrandVoice.objects.get_or_create(user=request.user)
        return render(request, "brand/profile.html", {"profile": profile, "voice": voice})

    def post(self, request):
        profile, _ = BrandProfile.objects.get_or_create(user=request.user)
        voice, _ = BrandVoice.objects.get_or_create(user=request.user)

        # Update profile fields
        profile.name = request.POST.get("name", profile.name)
        profile.professional_title = request.POST.get("professional_title", profile.professional_title)
        profile.short_bio = request.POST.get("short_bio", profile.short_bio)
        profile.long_bio = request.POST.get("long_bio", profile.long_bio)
        profile.positioning_statement = request.POST.get("positioning_statement", profile.positioning_statement)
        profile.niche = request.POST.get("niche", profile.niche)
        profile.target_audience = request.POST.get("target_audience", profile.target_audience)
        profile.expertise = request.POST.get("expertise", profile.expertise)
        profile.skills = request.POST.get("skills", profile.skills)
        profile.portfolio_url = request.POST.get("portfolio_url", profile.portfolio_url)
        profile.save()

        # Update voice fields
        voice.tone = request.POST.get("tone", voice.tone)
        voice.sentence_length = request.POST.get("sentence_length", voice.sentence_length)
        voice.words_to_avoid = request.POST.get("words_to_avoid", voice.words_to_avoid)
        voice.cta_style = request.POST.get("cta_style", voice.cta_style)
        voice.save()

        return redirect("brand:profile")


# DRF APIs
class BrandProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = BrandProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = BrandProfile.objects.get_or_create(user=self.request.user)
        return profile


class BrandVoiceAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = BrandVoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        voice, _ = BrandVoice.objects.get_or_create(user=self.request.user)
        return voice
