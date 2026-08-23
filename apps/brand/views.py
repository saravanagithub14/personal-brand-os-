from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from .models import BrandProfile, BrandVoice
from .serializers import BrandProfileSerializer, BrandVoiceSerializer
from apps.projects.models import Project
from apps.content.models import ContentItem

User = get_user_model()


class PublicPortfolioView(View):
    def get(self, request, username=None):
        if username:
            target_user = get_object_or_404(User, username=username)
        elif request.user.is_authenticated:
            target_user = request.user
        else:
            target_user = User.objects.first()
            if not target_user:
                return render(request, "brand/public_portfolio.html", {"profile": None})

        profile, _ = BrandProfile.objects.get_or_create(user=target_user)
        projects = Project.objects.filter(user=target_user).order_by("-updated_at")
        published_content = ContentItem.objects.filter(user=target_user, status="PUBLISHED").order_by("-published_at", "-updated_at")
        from apps.social.models import SocialAccount
        social_accounts = SocialAccount.objects.filter(user=target_user, active=True)

        context = {
            "portfolio_user": target_user,
            "profile": profile,
            "projects": projects,
            "published_content": published_content,
            "social_accounts": social_accounts,
        }
        return render(request, "brand/public_portfolio.html", context)


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

