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
