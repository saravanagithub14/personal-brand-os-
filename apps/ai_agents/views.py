from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from apps.content.models import ContentItem
from .services import ContentRepurposer, BrandVoiceReviewer, IdeaGeneratorAgent


class RepurposeContentView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        user = request.user
        item = get_object_or_404(ContentItem, id=item_id, user=user)
        target_platforms = request.POST.getlist("target_platforms") or ["X_TWITTER", "INSTAGRAM", "LINKEDIN"]

        repurposed_dict = ContentRepurposer.repurpose_content(item, target_platforms)

        # Create new ContentItem drafts for each platform
        created_count = 0
        for platform, text in repurposed_dict.items():
            ContentItem.objects.create(
                user=user,
                platform=platform,
                title=f"[Repurposed] {item.title[:60]} ({platform})",
                body=text,
                status="DRAFT",
                pillar=item.pillar,
            )
            created_count += 1

        return redirect("content:list")


class ReviewBrandVoiceView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        text_to_review = request.POST.get("text_to_review", "")
        item_id = request.POST.get("item_id")

        analysis = BrandVoiceReviewer.review_content(user, text_to_review)

        if item_id:
            try:
                item = ContentItem.objects.get(id=item_id, user=user)
                item.review_feedback = f"Score: {analysis['score']}/100 | Hook: {analysis['hook_strength']}"
                item.save()
            except ContentItem.DoesNotExist:
                pass

        return JsonResponse({"success": True, "analysis": analysis})


class GenerateScriptView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        topic = request.POST.get("topic", "")
        language = request.POST.get("language", "ENGLISH")
        platform = request.POST.get("platform", "INSTAGRAM_REEL")
        duration_seconds = request.POST.get("duration_seconds", 60)
        item_id = request.POST.get("item_id")

        from .services import ScriptGeneratorAgent
        res = ScriptGeneratorAgent.generate_script(
            topic=topic,
            language=language,
            platform=platform,
            duration_seconds=duration_seconds,
            user=user,
        )

        if item_id:
            try:
                item = ContentItem.objects.get(id=item_id, user=user)
                item.script = res["script"]
                item.visual_instructions = res["visual_instructions"]
                item.caption = res["caption"]
                item.save()
            except ContentItem.DoesNotExist:
                pass

        return JsonResponse({"success": True, "result": res})


class AIChatbotView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "ai_agents/chat.html")


class AIChatbotAPIView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user_msg = request.POST.get("message", "").strip()

        if not user_msg:
            return JsonResponse({"success": False, "error": "Message cannot be empty."})

        from .services import DatabaseContextRetriever, BrandCopilotAgent
        db_context = DatabaseContextRetriever.get_full_user_context(user, user_msg)

        # Check intent for Malayalam / Reel script request
        msg_lower = user_msg.lower()
        if "malayalam" in msg_lower or "manglish" in msg_lower or "reel" in msg_lower or "script" in msg_lower:
            from .services import ScriptGeneratorAgent
            lang = "MALAYALAM" if "malayalam" in msg_lower else ("MANGLISH" if "manglish" in msg_lower else "ENGLISH")
            res = ScriptGeneratorAgent.generate_script(topic=user_msg, language=lang, user=user)
            reply = f"{res['script']}\n\n{res['visual_instructions']}"
        elif "review" in msg_lower or "score" in msg_lower:
            from .services import BrandVoiceReviewer
            rev = BrandVoiceReviewer.review_content(user, user_msg)
            reply = f"Brand Alignment Score: {rev['score']}/100\nHook Strength: {rev['hook_strength']}\nTone: {rev['tone']}\n\nRecommendations:\n- " + "\n- ".join(rev['recommendations'])
        else:
            reply = BrandCopilotAgent.generate_reply(user_msg=user_msg, context=db_context, user=user)

        return JsonResponse({"success": True, "reply": reply})


class TopicCampaignListView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import TopicResearchCampaign
        campaigns = TopicResearchCampaign.objects.filter(user=request.user).order_by("-created_at")
        return render(request, "ai_agents/campaign_list.html", {"campaigns": campaigns})


class TopicCampaignCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "ai_agents/campaign_create.html")

    def post(self, request):
        from .models import TopicResearchCampaign
        from .services import TopicResearchCampaignOrchestrator

        topic = request.POST.get("topic", "").strip()

        if not topic:
            return render(request, "ai_agents/campaign_create.html", {"error": "Topic is required."})

        campaign = TopicResearchCampaign.objects.create(
            user=request.user,
            topic=topic,
            status="PENDING",
        )

        # Trigger campaign orchestrator
        TopicResearchCampaignOrchestrator.run_campaign(campaign.id)

        return redirect("ai_agents:campaign_detail", campaign_id=campaign.id)


class TopicCampaignDetailView(LoginRequiredMixin, View):
    def get(self, request, campaign_id):
        from .models import TopicResearchCampaign
        campaign = get_object_or_404(TopicResearchCampaign, id=campaign_id, user=request.user)
        return render(request, "ai_agents/campaign_detail.html", {"campaign": campaign})


class PublishMediumDraftView(LoginRequiredMixin, View):
    """API endpoint to publish campaign blog as a draft on Medium."""

    def post(self, request, campaign_id):
        import json
        from .models import TopicResearchCampaign
        from .services import MediumPublisherService

        campaign = get_object_or_404(TopicResearchCampaign, id=campaign_id, user=request.user)

        token = request.POST.get("token", "").strip()
        if not token and request.body:
            try:
                body = json.loads(request.body.decode("utf-8"))
                token = body.get("token", "").strip()
            except Exception:
                pass

        if token:
            MediumPublisherService.save_token_for_user(request.user, token)

        title = campaign.topic
        first_line = campaign.medium_blog.split("\n")[0].strip() if campaign.medium_blog else ""
        if first_line.startswith("#"):
            title = first_line.lstrip("#").strip()

        result = MediumPublisherService.publish_draft(
            title=title,
            content_markdown=campaign.medium_blog,
            token=token or None,
            user=request.user,
        )

        if result.get("success"):
            campaign.medium_link = result.get("url", "")
            campaign.save(update_fields=["medium_link"])
            return JsonResponse({
                "success": True,
                "url": result.get("url"),
                "post_id": result.get("post_id"),
                "message": "Draft created successfully on Medium!"
            })
        else:
            return JsonResponse({
                "success": False,
                "requires_token": result.get("requires_token", False),
                "error": result.get("error", "Failed to create Medium draft.")
            }, status=200 if result.get("requires_token") else 400)


class GenerateCampaignImagesView(LoginRequiredMixin, View):
    """API endpoint to generate AI illustrations for Medium blog prompts and embed them."""

    def post(self, request, campaign_id):
        from .models import TopicResearchCampaign
        from .services import MediumBlogImageGeneratorService

        campaign = get_object_or_404(TopicResearchCampaign, id=campaign_id, user=request.user)

        generated_count = MediumBlogImageGeneratorService.generate_and_embed_images(campaign, user=request.user)

        return JsonResponse({
            "success": True,
            "images_generated": generated_count,
            "medium_blog": campaign.medium_blog,
            "message": f"Successfully generated and embedded {generated_count} illustration(s) into your blog!"
        })



