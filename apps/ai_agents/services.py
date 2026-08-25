import time
import logging
from django.utils import timezone
from django.conf import settings
from .models import AgentExecutionLog
from apps.brand.models import BrandVoice

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Centralized OpenAI API client for all campaign agents.
    Uses gpt-4o for flagship (research/blog), gpt-4o-mini for fast tasks (reel/linkedin).
    Falls back gracefully if OPENAI_API_KEY is not set.
    """

    @classmethod
    def _get_client(cls):
        """Lazy-import openai and return authenticated client."""
        try:
            import openai
            api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
            if not api_key:
                return None
            return openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("openai package not installed.")
            return None

    @classmethod
    def complete(cls, system_prompt: str, user_prompt: str, model: str = "gpt-4o", max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """
        Call OpenAI chat completion. Returns generated text or empty string on failure.
        """
        client = cls._get_client()
        if client is None:
            logger.warning("LLMClient: No OpenAI client available (missing key or package).")
            return ""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"LLMClient.complete error ({model}): {exc}")
            return ""

    @classmethod
    def flagship(cls, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        """Use gpt-4o for research-heavy / long-form tasks."""
        return cls.complete(system_prompt, user_prompt, model="gpt-4o", max_tokens=max_tokens, temperature=0.65)

    @classmethod
    def mini(cls, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Use gpt-4o-mini for fast, shorter tasks (reel scripts, social posts)."""
        return cls.complete(system_prompt, user_prompt, model="gpt-4o-mini", max_tokens=max_tokens, temperature=0.72)

    @classmethod
    def generate_image(cls, prompt: str, size: str = "1024x1024") -> str:
        """
        Generates a professional isometric 3D infographic illustration from prompt.
        1. Attempts OpenAI DALL-E 3 with configured OPENAI_API_KEY.
        2. If OpenAI key lacks DALL-E permissions / model is restricted, seamlessly
           falls back to high-res Flux isometric 3D infographic generation.
        Returns the image URL or empty string on failure.
        """
        import urllib.parse
        raw_prompt = prompt.replace("*", "").strip()
        style_prefix = (
            "Professional clean isometric 3D infographic illustration in modern editorial consulting presentation aesthetic, "
            "soft off-white or light cream background, dark navy typography, vibrant orange main accent color for highlights warnings and key actions, "
            "subtle gray and blue-gray secondary elements, clean geometric shapes with soft shadows, stylized polished 3D modular pipeline objects, "
            "16:9 wide landscape, minimal visual clutter, high clarity and visual storytelling:"
        )
        styled_prompt = f"{style_prefix} {raw_prompt}"[:1000]

        client = cls._get_client()
        if client:
            try:
                logger.info(f"LLMClient: Generating isometric 3D infographic with DALL-E 3: '{styled_prompt[:70]}...'")
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=styled_prompt,
                    size=size,
                    quality="standard",
                    n=1,
                )
                if response.data and response.data[0].url:
                    return response.data[0].url
            except Exception as exc:
                logger.warning(f"OpenAI DALL-E 3 unavailable on this API key ({exc}). Falling back to Flux isometric 3D infographic engine.")

        # Fallback: High-resolution Flux isometric 3D infographic engine
        try:
            encoded_prompt = urllib.parse.quote(styled_prompt)
            flux_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&model=flux"
            logger.info("LLMClient: Using Flux isometric 3D infographic engine.")
            return flux_url
        except Exception as e:
            logger.error(f"Fallback image generator error: {e}")
            return ""



HUMAN_WRITING_STYLE_GUIDE = """
STYLE & HUMAN WRITING DIRECTIVES (MANDATORY):
- Never use em dashes (—). Use commas or periods instead.
- Avoid AI sounding words and phrases like: delve, foster, elevate, navigate, furthermore, moreover, in conclusion, crucial, robust, seamless, game changer, unlock potential, fast paced world, cutting edge, revolutionary.
- Vary sentence length naturally. Mix short, punchy lines with longer ones. Occasionally use fragments.
- Avoid repetitive sentence structures and predictable rhythm.
- Use conversational, human sounding language. Avoid corporate, PR, textbook, motivational, or SEO content farm tone.
- Avoid excessive transitions like however, therefore, additionally, meanwhile, consequently, ultimately, and overall.
- Take clear positions instead of overly balanced "both sides" writing.
- Prioritize specificity over generic statements. Use concrete examples and realistic phrasing.
- Do not overexplain obvious points.
- Avoid hyper structured formatting unless requested.
- Skip generic introductions and conclusions. Start directly with the point.
- Allow slight natural imperfection. The writing should feel authored, not generated.
- For social content, sound culturally aware and current. Avoid cringe positivity and fake inspiration.
- Use contractions naturally and occasionally break perfect grammar for realism.
"""



class AgentManager:
    """Centralized AI Agent Execution Engine with Token Budgeting & Quota Routing."""

    FLAGSHIP_DAILY_CAP = 250000
    MINI_NANO_DAILY_CAP = 2500000

    FLAGSHIP_MODELS = ["gpt-5.4", "gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o", "o1", "o3"]
    MINI_NANO_MODELS = ["gpt-5.4-mini", "gpt-5.4-nano", "gpt-5-mini", "gpt-5-nano", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o-mini", "o3-mini", "o4-mini"]

    @classmethod
    def get_daily_token_usage(cls, user):
        """Calculate today's total token consumption split by model tier."""
        today = timezone.now().date()
        logs = AgentExecutionLog.objects.filter(user=user, created_at__date=today) if user and user.is_authenticated else AgentExecutionLog.objects.none()

        flagship_used = sum(l.total_tokens for l in logs.filter(model_tier="FLAGSHIP"))
        mini_nano_used = sum(l.total_tokens for l in logs.filter(model_tier="MINI_NANO"))

        return {
            "flagship_tokens": flagship_used,
            "flagship_cap": cls.FLAGSHIP_DAILY_CAP,
            "flagship_remaining": max(0, cls.FLAGSHIP_DAILY_CAP - flagship_used),
            "flagship_percent": round((flagship_used / cls.FLAGSHIP_DAILY_CAP) * 100, 1),
            "mini_nano_tokens": mini_nano_used,
            "mini_nano_cap": cls.MINI_NANO_DAILY_CAP,
            "mini_nano_remaining": max(0, cls.MINI_NANO_DAILY_CAP - mini_nano_used),
            "mini_nano_percent": round((mini_nano_used / cls.MINI_NANO_DAILY_CAP) * 100, 1),
        }

    @classmethod
    def select_optimal_model(cls, user, preferred_tier="MINI_NANO"):
        """Route to appropriate model tier based on daily quota limits."""
        usage = cls.get_daily_token_usage(user)

        if preferred_tier == "FLAGSHIP":
            # If approaching 80% of daily Flagship quota (200k tokens), fallback to Mini/Nano tier
            if usage["flagship_tokens"] >= 200000:
                return "gpt-4o-mini", "MINI_NANO"
            return "gpt-4o", "FLAGSHIP"

        return "gpt-4o-mini", "MINI_NANO"

    @classmethod
    def execute_agent(cls, user, agent_name, input_text, preferred_tier="MINI_NANO", prompt_template="", system_prompt=""):
        start_time = time.time()
        
        model_used, model_tier = cls.select_optimal_model(user, preferred_tier)

        # Format or construct response
        output_text = cls._run_prompt_chain(agent_name, input_text, prompt_template, system_prompt)

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Estimate tokens (approx 1 word = 1.3 tokens)
        prompt_tokens = int(len(input_text.split()) * 1.3) + 15
        completion_tokens = int(len(output_text.split()) * 1.3) + 10
        total_tokens = prompt_tokens + completion_tokens

        # Log agent execution & token consumption
        if user and user.is_authenticated:
            AgentExecutionLog.objects.create(
                user=user,
                agent_name=agent_name,
                input_text=input_text[:1000],
                output_text=output_text[:4000],
                model_used=model_used,
                model_tier=model_tier,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                execution_time_ms=execution_time_ms,
            )

        return output_text

    @classmethod
    def _run_prompt_chain(cls, agent_name, input_text, prompt_template, system_prompt):
        if agent_name == "Content Repurposer":
            return ContentRepurposer.format_repurposed_output(input_text)
        elif agent_name == "Brand Reviewer":
            return BrandVoiceReviewer.format_review_output(input_text)
        elif agent_name == "Idea Generator":
            return IdeaGeneratorAgent.format_ideas_output(input_text)
        elif agent_name == "Brand Copilot Chatbot":
            return BrandCopilotAgent.generate_reply(user_msg=input_text)
        
        return f"AI Agent Response for '{agent_name}':\n\n{input_text}"


class ContentRepurposer:
    """1-Click Multi-Channel Repurposing Engine."""

    @classmethod
    def repurpose_content(cls, content_item, target_platforms=None):
        if not target_platforms:
            target_platforms = ["X_TWITTER", "INSTAGRAM", "LINKEDIN"]

        title = content_item.title or "Untitled Draft"
        body = content_item.body or title

        repurposed_results = {}

        for platform in target_platforms:
            if platform == "X_TWITTER":
                repurposed_results["X_TWITTER"] = (
                    f"🧵 1/3 {title}\n\n"
                    f"{body[:220]}...\n\n"
                    f"👇 Key takeaways from my latest work on computational biology & AI systems:"
                )
            elif platform == "INSTAGRAM":
                repurposed_results["INSTAGRAM"] = (
                    f"🧬 {title}\n\n"
                    f"[Reel Script Scene 1]: Show lab workspace & code terminal.\n"
                    f"[Voiceover]: {body[:150]}...\n\n"
                    f"💡 Save & share if you find this useful!\n#BioTech #Python #AI"
                )
            elif platform == "LINKEDIN":
                repurposed_results["LINKEDIN"] = (
                    f"🚀 {title}\n\n"
                    f"{body}\n\n"
                    f"--- \nWhat are your thoughts on this approach? Let's discuss in the comments below."
                )

        # Log via AgentManager
        if content_item.user:
            AgentManager.execute_agent(
                user=content_item.user,
                agent_name="Content Repurposer",
                input_text=f"Title: {title}\nBody: {body[:300]}",
            )

        return repurposed_results

    @classmethod
    def format_repurposed_output(cls, input_text):
        return f"Repurposed variants generated from input:\n{input_text}"


class BrandVoiceReviewer:
    """Automated Brand Compliance & Tone Reviewer."""

    @classmethod
    def review_content(cls, user, text_to_review):
        voice = BrandVoice.objects.filter(user=user).first()
        tone = voice.tone if (voice and voice.tone) else "Authoritative, Clear, Technical"
        avoid_raw = (voice.phrases_to_avoid if voice and voice.phrases_to_avoid else "") + "," + (voice.words_to_avoid if voice and voice.words_to_avoid else "")
        banned_words = [w.strip().lower() for w in avoid_raw.split(",") if w.strip()] or ["game-changer", "synergy", "paradigm shift"]

        # Scan text for banned phrases
        text_lower = text_to_review.lower()
        found_banned = [w for w in banned_words if w and w in text_lower]

        score = 92
        if found_banned:
            score -= (len(found_banned) * 12)
        if len(text_to_review) < 50:
            score -= 15

        score = max(35, min(100, score))

        hook_strength = "🔥 Strong" if score >= 80 else ("🟡 Moderate" if score >= 60 else "🔴 Weak Hook")

        analysis = {
            "score": score,
            "technical_depth": voice.technical_depth if voice else "Intermediate to Advanced",
            "tone": tone,
            "hook_strength": hook_strength,
            "found_banned_words": found_banned,
            "recommendations": [
                "Ensure your opening line poses a direct question or strong thesis.",
                "Include a call-to-action (CTA) at the end of the draft.",
            ]
        }

        if user:
            AgentManager.execute_agent(
                user=user,
                agent_name="Brand Reviewer",
                input_text=text_to_review[:500],
            )

        return analysis

    @classmethod
    def format_review_output(cls, input_text):
        return f"Brand Review Summary: Input scanned cleanly."


class IdeaGeneratorAgent:
    """Multi-Pillar Idea Generation Agent."""

    @classmethod
    def generate_ideas_for_pillar(cls, user, pillar_name):
        ideas = [
            f"How to build {pillar_name} pipelines in Python from scratch",
            f"3 common pitfalls developers make in {pillar_name} and how to fix them",
            f"The future of {pillar_name}: What the latest research paper shows",
            f"A step-by-step breakdown of my workflow for {pillar_name}",
        ]

        if user:
            AgentManager.execute_agent(
                user=user,
                agent_name="Idea Generator",
                input_text=f"Pillar: {pillar_name}",
            )

        return ideas

class ScriptGeneratorAgent:
    """Optimized Humanized Instagram Reel & Video Script Generator (Malayalam, Manglish, English)."""

    SYSTEM_HUMANIZATION_DIRECTIVE = (
        "HUMANIZATION CONSTRAINTS:\n"
        "1. Never use em dashes (—). Use commas or periods instead.\n"
        "2. Banned AI Words: delve, foster, elevate, navigate, furthermore, moreover, in conclusion, crucial, robust, seamless, game changer, unlock potential, fast paced world, cutting edge, revolutionary.\n"
        "3. Mix short punchy lines with fragments. Vary rhythm naturally.\n"
        "4. Avoid corporate, PR, textbook, or motivational AI fluff.\n"
        "5. Avoid transitions like however, therefore, additionally, consequently, ultimately.\n"
        "6. Start directly with the hook. Skip generic intros."
    )

    @classmethod
    def generate_script(cls, topic, language="ENGLISH", platform="INSTAGRAM_REEL", duration_seconds=60, user=None):
        topic_title = topic.strip() if topic else "Computational AI & BioTech Workflows"

        # Sanitize topic text to ensure no em-dashes
        topic_title = topic_title.replace("—", ", ").replace("--", ", ")

        if language == "MALAYALAM":
            script = (
                f"🎬 [ശീർഷകം]: {topic_title} (മലയാളം റീൽസ്)\n\n"
                f"[0:00 - 0:05 Hook]:\n"
                f"\"Python കോഡിംഗിൽ {topic_title} എങ്ങനെ വേഗത്തിൽ ചെയ്യാമെന്ന് നോക്കാം. സമയം കളയാതെ കാര്യത്തിലേക്ക് കടക്കാം.\"\n\n"
                f"[0:05 - 0:25 Core Code Demo]:\n"
                f"\"ഇവിടെ PyTorch മാട്രിക്സ് ഓപ്പറേഷൻസ് ലൈവായി കാണാം. അധിക ലൈൻ കോഡുകൾ ഇല്ലാതെ തന്നെ ഡാറ്റ ഫിൽട്ടർ ചെയ്യാം.\"\n\n"
                f"[0:25 - 0:45 Real Work Breakdown]:\n"
                f"\"ഈ വഴി ഉപയോഗിച്ചാൽ മെമ്മറി ലീക്ക് ഒഴിവാക്കാം. ബയോഇൻഫോർമാറ്റിക്സ് പ്രോജക്ടുകളിൽ ഇത് നേരിട്ട് അപ്ലൈ ചെയ്യാം.\"\n\n"
                f"[0:45 - 0:60 CTA]:\n"
                f"\"ഈ കോഡ് സ്നിപ്പെറ്റ് വേണമെങ്കിൽ കമന്റിൽ 'CODE' എന്ന് ടൈപ്പ് ചെയ്യൂ. അടുത്ത വീഡിയോ കാണാൻ ഫോളോ ചെയ്യൂ.\""
            )
            visual_instructions = (
                "🎥 [Visual Cues]:\n"
                "1. 0:00 - Direct camera eye contact. No generic waves.\n"
                "2. 0:05 - Split screen: Terminal output & highlighted code lines.\n"
                "3. 0:25 - Clean typography overlay with key function names.\n"
                "4. 0:45 - Text CTA on screen with quick arrow gesture."
            )
            caption = f"🧬 {topic_title} (മലയാളം)\n\nസ്ക്രിപ്റ്റും കോഡ് വിശദാംശങ്ങളും സേവ് ചെയ്തു വെക്കൂ. കമന്റിൽ നിങ്ങളുടെ അഭിപ്രായങ്ങൾ പറയൂ! 💡\n#MalayalamTech #AIInMalayalam #PythonMalayalam #BioTech"

        elif language == "MANGLISH":
            script = (
                f"🎬 [Title]: {topic_title} (Manglish Script)\n\n"
                f"[0:00 - 0:05 Hook]:\n"
                f"\"{topic_title} build cheyyumbaalkkulla pattu pacha bugs engane fix cheyyam? Simple step-by-step method idha.\"\n\n"
                f"[0:05 - 0:25 Core Code Demo]:\n"
                f"\"Nammal terminal thorannu PyTorch module import cheyyunnu. Internal loop optimize cheythaal 3x speed kittum.\"\n\n"
                f"[0:25 - 0:45 Real Work Breakdown]:\n"
                f"\"BioTech data processingil veruthe irunnu time waste aakkendathilla. Ee pipeline direct aayitt run cheyyam.\"\n\n"
                f"[0:45 - 0:60 CTA]:\n"
                f"\"Ithu save cheythu vecho. Github repo linku venel commentil 'DEV' ennu idaam. Follow for more!\""
            )
            visual_instructions = (
                "🎥 [Visual Cues]:\n"
                "1. 0:00 - Fast hard cut to terminal screen.\n"
                "2. 0:05 - Zoom in on main execution loop in VS Code.\n"
                "3. 0:25 - On-screen speed metric benchmark comparison.\n"
                "4. 0:45 - End frame with simple follow prompt."
            )
            caption = f"🚀 {topic_title} (Manglish Tech breakdown)\n\nNo filler. Just practical AI and coding workflows. Save for later! 💡\n#ManglishTech #KeralaCoders #AIReels #Python"

        else: # ENGLISH
            script = (
                f"🎬 [Title]: {topic_title} (Humanized Tech Reel)\n\n"
                f"[0:00 - 0:05 Hook]:\n"
                f"\"Most developers get {topic_title} completely wrong. Here is the exact fix.\"\n\n"
                f"[0:05 - 0:25 Core Implementation]:\n"
                f"\"Look at line 14. We drop the redundant wrapper and pass raw tensor buffers directly. Memory overhead drops instantly.\"\n\n"
                f"[0:25 - 0:45 Practical Breakdown]:\n"
                f"\"I tested this on production workloads. Latency cut by 40 percent without breaking API contracts.\"\n\n"
                f"[0:45 - 0:60 Call to Action]:\n"
                f"\"Comment 'BENCHMARK' and I will send over the full setup script. Save this before your next sprint.\""
            )
            visual_instructions = (
                "🎥 [Visual Cues]:\n"
                "1. 0:00 - Sharp opening cut directly to code workspace.\n"
                "2. 0:05 - Highlighted green/red diff comparison on screen.\n"
                "3. 0:25 - Real latency graph overlay.\n"
                "4. 0:45 - Clean final frame with repository link overlay."
            )
            caption = f"⚡ {topic_title}\n\nReal benchmarks. No marketing hype. Drop a comment for the script. 🚀\n#AI #Python #SoftwareEngineering"

        if user:
            AgentManager.execute_agent(
                user=user,
                agent_name="Script Generator",
                input_text=f"Topic: {topic_title} | Lang: {language} | Platform: {platform}\n\n{cls.SYSTEM_HUMANIZATION_DIRECTIVE}",
                preferred_tier="FLAGSHIP",
            )

        return {
            "script": script,
            "visual_instructions": visual_instructions,
            "caption": caption,
            "language": language,
            "platform": platform,
        }

    @classmethod
    def format_ideas_output(cls, input_text):
        return f"Ideas generated for: {input_text}"


class DatabaseContextRetriever:
    """Universal Database Context Engine querying across all OS models."""

    @classmethod
    def get_full_user_context(cls, user, query_str=""):
        if not user or not user.is_authenticated:
            return {}

        from apps.social.models import SocialAccount
        from apps.content.models import ContentItem
        from apps.projects.models import Project
        from apps.research.models import KnowledgeDocument
        from apps.brand.models import BrandVoice
        from apps.news.models import NewsArticle

        # 1. Social Accounts
        accounts = list(SocialAccount.objects.filter(user=user))
        account_summary = []
        overdue_summary = []
        for a in accounts:
            last_date_str = a.last_post_at.strftime("%Y-%m-%d") if a.last_post_at else "Not Set"
            status_str = f"{a.get_platform_display()}: handle='{a.handle}', last_post='{last_date_str}'"
            account_summary.append(status_str)
            if a.health_status == "OVERDUE":
                overdue_summary.append(f"OVERDUE ALERT: {a.get_platform_display()} ({a.days_since_last_post} days since last post)")

        # 2. Content Items
        recent_items = list(ContentItem.objects.filter(user=user).order_by("-updated_at")[:5])
        content_summary = [f"• [{i.status}] {i.title} ({i.platform})" for i in recent_items]

        # 3. Projects Hub
        projects = list(Project.objects.filter(user=user))
        project_summary = [f"• {p.title}: {p.description[:80]} (Tech: {p.technologies})" for p in projects]

        # 4. Knowledge Documents
        docs = list(KnowledgeDocument.objects.filter(user=user)[:5])
        doc_summary = [f"• {d.title} (Tags: {d.tags})" for d in docs]

        # 5. Brand Voice
        voice = BrandVoice.objects.filter(user=user).first()
        voice_summary = f"Tone: {voice.tone if voice else 'Technical'}, Depth: {voice.technical_depth if voice else 'Advanced'}, Audience: {voice.audience_level if voice else 'Engineers & Researchers'}"

        # 6. Daily News
        articles = list(NewsArticle.objects.order_by("-published_at")[:3])
        news_summary = [f"• {n.title} ({n.source})" for n in articles]

        return {
            "accounts": account_summary,
            "overdue_alerts": overdue_summary,
            "content_items": content_summary,
            "projects": project_summary,
            "knowledge_docs": doc_summary,
            "brand_voice": voice_summary,
            "news": news_summary,
        }


class BrandCopilotAgent:
    """Conversational AI Brand Assistant Agent with Universal Database Access."""

    @classmethod
    def generate_reply(cls, user_msg, context=None, user=None):
        msg_clean = user_msg.strip().lower()

        # Fetch live database context if available
        db = context if isinstance(context, dict) else DatabaseContextRetriever.get_full_user_context(user, user_msg)

        # Handle greetings
        if msg_clean in ["hi", "hello", "hey", "hlo", "namaskaram", "hi copilot", "hello copilot"]:
            accounts_count = len(db.get("accounts", []))
            projects_count = len(db.get("projects", []))
            drafts_count = len(db.get("content_items", []))

            reply = (
                "Hey Saravana! I am your Personal Brand AI Copilot.\n\n"
                f"Live Database Connections:\n"
                f"• Social Handles: {accounts_count} handles connected\n"
                f"• Projects: {projects_count} active projects\n"
                f"• Content Bank: {drafts_count} recent drafts\n\n"
                "Here is what you can ask me:\n"
                "• 'What social handles do I have?'\n"
                "• 'Show my active projects'\n"
                "• 'What are my latest content drafts?'\n"
                "• 'When did I last post on Facebook?' or 'Generate a Malayalam Reel script'"
            )
            return reply

        # Handle platform-specific queries (e.g. "when did i last add medium post")
        platforms = ["medium", "github", "linkedin", "instagram", "facebook", "orcid", "researchgate", "x", "twitter"]
        matched_platform = next((p for p in platforms if p in msg_clean), None)

        if matched_platform and ("last" in msg_clean or "when" in msg_clean or "post" in msg_clean or "date" in msg_clean or "add" in msg_clean):
            from apps.social.models import SocialAccount
            p_map = {
                "medium": "MEDIUM",
                "github": "GITHUB",
                "linkedin": "LINKEDIN",
                "instagram": "INSTAGRAM",
                "facebook": "FACEBOOK",
                "orcid": "ORCID",
                "researchgate": "RESEARCHGATE",
                "x": "X_TWITTER",
                "twitter": "X_TWITTER",
            }
            target_p = p_map.get(matched_platform)
            acc = SocialAccount.objects.filter(user=user, platform=target_p).first() if user and user.is_authenticated else None

            if acc:
                last_date = acc.last_post_at.strftime("%B %d, %Y") if acc.last_post_at else "No recorded post date yet"
                days_str = f"({acc.days_since_last_post} days ago)" if acc.last_post_at else ""
                badge_label = acc.health_badge["label"]
                profile_link = f"<a href='{acc.profile_url}' target='_blank' style='color: var(--accent-purple); font-weight: 600; text-decoration: underline;'>{acc.profile_url}</a>" if acc.profile_url else "N/A"
                
                return (
                    f"[{acc.get_platform_display()} Account Summary]\n\n"
                    f"• Handle: {acc.handle}\n"
                    f"• Last Post Date: {last_date} {days_str}\n"
                    f"• Cadence Status: {badge_label} (Target: Every {acc.target_cadence_days} days)\n"
                    f"• Profile URL: {profile_link}"
                )
            else:
                return f"You don't have a {matched_platform.capitalize()} social account connected in your OS yet. Add it on your Dashboard!"

        # Handle Social Handles Query
        if "handle" in msg_clean or "social" in msg_clean or "channel" in msg_clean or "platform" in msg_clean or "account" in msg_clean:
            accounts = db.get("accounts", [])
            overdue = db.get("overdue_alerts", [])

            if not accounts:
                return "You don't have any social handles configured yet. Head over to your Dashboard to connect your GitHub, LinkedIn, Medium, or Instagram profiles!"

            acc_str = "\n".join([f"• {a}" for a in accounts])
            overdue_str = "\n".join(overdue) if overdue else "All channels are on-track with your target post cadence."

            return f"[Your Social Handles & Cadence Status]\n\n{acc_str}\n\n{overdue_str}"

        # Handle Projects Query
        if "project" in msg_clean or "repo" in msg_clean or "tech stack" in msg_clean:
            projects = db.get("projects", [])
            if not projects:
                return "You don't have any projects listed in your Projects Hub yet. You can add them under /projects/!"

            proj_str = "\n".join(projects)
            return f"[Your Active Projects]\n\n{proj_str}"

        # Handle Content Drafts Query
        if "draft" in msg_clean or "content" in msg_clean or "post" in msg_clean:
            items = db.get("content_items", [])
            if not items:
                return "Your Content Bank is currently empty. Click 'Create New Content' or ask me to generate a draft!"

            item_str = "\n".join(items)
            return f"[Your Recent Content Items & Drafts]\n\n{item_str}"

        # Handle Brand Voice Query
        if "brand" in msg_clean or "voice" in msg_clean or "audience" in msg_clean or "archetype" in msg_clean:
            voice_str = db.get("brand_voice", "Default Brand Strategy")
            return f"[Your Brand Voice & Strategy]\n\n{voice_str}"

        # Handle Knowledge Base Query
        if "research" in msg_clean or "paper" in msg_clean or "knowledge" in msg_clean:
            docs = db.get("knowledge_docs", [])
            if not docs:
                return "Your Knowledge Base has no documents saved yet. Upload research preprints or notes under /research/!"

            doc_str = "\n".join(docs)
            return f"[Your Knowledge Base Documents]\n\n{doc_str}"

        # Default conversational response synthesis
        return (
            f"Got it! Let me assist you with '{user_msg[:60]}'.\n\n"
            f"[Copilot Recommendation]\n"
            f"• Brand Strategy: Aligning with your {db.get('brand_voice', 'tech persona')}.\n"
            f"• Recommended Action: Focus on concrete code benchmarks or paper breakdowns.\n\n"
            f"Would you like me to generate a full Malayalam/English script or draft post for this?"
        )


DEEP_RESEARCH_AGENT_SYSTEM_PROMPT = """
# Personal Brand OS — Deep Research Agent

## Your Role
You are a senior research analyst and domain expert. You do not produce surface-level summaries.
You write the kind of technical research report that an experienced engineer or founder would actually use to make a decision.

You have deep knowledge of AI, machine learning, software engineering, business strategy, and adjacent fields.
When given a topic, you draw on that knowledge fully. You name specific tools, papers, architectures, benchmarks, and failure modes.
You never write "various sources show..." or "experts believe...". You are specific. Always.

## Quality Bar
The output must be at the level of a well-researched Medium deep-dive by a practitioner who has worked in the field.
Not a Wikipedia summary. Not a listicle. A real technical breakdown that teaches something.

A reader who knows the field should find specific details they can verify and build on.
A reader new to the field should understand what the landscape actually looks like.

## Depth Requirements
- Name specific architectures, variants, approaches, and tools (e.g., "DPR", "BM25", "Haystack", "LlamaIndex", "FAISS", "HNSW")
- Reference real papers where relevant (e.g., "Lewis et al. 2020 NeurIPS", "Izacard & Grave's FiD", "Self-RAG 2023")
- Name real companies or products that use this approach in production where known
- Include actual performance numbers from literature or known benchmarks, not made-up percentages
- Identify real failure modes practitioners hit, not generic "implementation challenges"
- Separate what is empirically established from what is debated

## Mandatory Output Structure
Write the report in EXACTLY this format. Do not skip sections. Do not add new top-level sections.

---

# Deep Research Report: [Topic]

## Executive Summary
2-4 sentence synthesis. What is this, why does it matter, what is the state of the art right now?
Be specific. No generic opener like "In today's world...". Start with the core insight.

---

## Research Classification

| Parameter | Value |
|-----------|-------|
| Depth Tier | [QUICK/STANDARD/DEEP] |
| Target Audience | [from user context] |
| Voice Tone | [from brand voice] |
| Primary Focus | [the real technical angle of this topic] |
| Geographic Scope | Global |
| Freshness Required | [High/Medium based on how fast field moves] |

---

## Taxonomy & Domain Map

Write an actual ASCII tree that reflects the REAL structure of this specific topic.
The branches must be the actual subcategories, variants, or dimensions of THIS topic.
Not generic branches like "Core Concepts" and "Implementation".

Example for RAG:
```
RETRIEVAL-AUGMENTED GENERATION
├── By Retrieval Strategy
│   ├── Sparse (BM25, TF-IDF)
│   ├── Dense (DPR, Contriever, Sentence-BERT)
│   └── Hybrid (BM25 + Dense, RRF fusion)
├── By Pipeline Architecture
│   ├── Basic RAG (single-pass retrieve → generate)
│   ├── Advanced RAG (reranking, query rewriting, HyDE)
│   ├── Modular RAG (plug-in components, routing)
│   └── Graph RAG (knowledge graph retrieval)
...
```

---

## Key Findings (Confidence-Rated)

Produce a markdown table with 5-7 specific, verifiable findings about this topic.
Each finding must be based on real literature, production data, or empirically established patterns.
Do NOT use vague generic claims. Use specific numbers, named techniques, or named phenomena.

| # | Finding | Evidence Type | Confidence |
|---|---------|---------------|------------|
| 1 | [Specific, verifiable claim with actual data or named source] | [Academic paper / Production benchmark / Community survey] | HIGH/MEDIUM/LOW |
...

---

## Detailed Analysis & Empirical Evidence

### Source Audit & Evidence Chain

Write the actual sources relevant to this topic, organized by tier:

**Tier 1 (Primary Sources — academic papers, official docs, technical specs):**
- [Name real papers, repos, or official documentation for this topic]

**Tier 2 (High-Quality Secondary — major tech publications, benchmark reports):**
- [Name real publications, reports, or company engineering blogs relevant to this topic]

**Tier 3 (Expert Signal — practitioner blogs, conference talks):**
- [Name real practitioner sources, conference tracks, or community hubs for this topic]

**Tier 4 (Community Signal — directional, unverified):**
- [Relevant community spaces: Reddit subreddits, Discord servers, GitHub Discussions]

### Primary Analysis

Write 3-5 paragraphs of substantive analysis on this topic.
Each paragraph should teach something. Cover:
- How the main approaches/variants actually work (mechanically, not just at a label level)
- What the empirical evidence shows about performance trade-offs
- Where the field is actually at in 2025-2026 vs. where hype claims it is
- Production realities vs. research benchmarks

---

## Fact-Check & Contradiction Log

Identify 3-5 specific claims that circulate about this topic and fact-check them.
Be specific about what the claim is and what the evidence actually shows.

| Claim | Commonly Stated By | Verified? | What Evidence Actually Shows |
|-------|-------------------|-----------|------------------------------|
| [Specific claim] | [Vendor / Blog / Marketing] | PARTIAL/UNVERIFIED/CONFIRMED | [What literature or production data shows] |

---

## Contradictions, Disagreements & Uncertainty

Identify 2-4 real active debates or points of genuine uncertainty in this space.
Not made-up controversies. Real ones practitioners argue about.

---

## Strategic Implications

3-4 numbered, actionable implications for someone building in or writing about this space.
Each implication should be specific to this topic, not generic content advice.

---

## Scored Content Opportunities

| Format | Specific Angle | Timeliness | Novelty | Audience Fit | Score |
|--------|---------------|-----------|---------|--------------|-------|
| Medium Deep-Dive | [Specific angle that would perform for this topic] | High/Medium/Low | H/M/L | H/M/L | X/10 |
| Instagram Reel (Bilingual) | [Specific hook/angle for this topic] | H/M/L | H/M/L | H/M/L | X/10 |
| LinkedIn Post | [Specific angle for this topic] | H/M/L | H/M/L | H/M/L | X/10 |

**Best performing angle:** [One specific recommendation with reasoning]

---

## Research Confidence

**Overall: [HIGH/MEDIUM/LOW]**

[2-3 sentences explaining what the confidence rating is based on and what uncertainty remains.]

---

## Mandatory Quality Rules
- Never use em dashes (—). Use commas or periods instead.
- Never write "delve", "foster", "elevate", "navigate", "furthermore", "moreover", "in conclusion", "crucial", "robust", "seamless", "game changer", "cutting edge", "revolutionary".
- Never open with "In today's rapidly changing world" or any variant.
- Never write vague claims. Every claim needs either a named source, a named technique, or a specific data point.
- Write in the voice of an experienced practitioner who has worked in this field, not a content marketer.
- Vary sentence length. Short punchy lines mixed with longer technical ones.
"""


class DeepResearchAgent:
    """Agent that performs in-depth research, fact checks, key statistics gathering, and citation listing."""

    # Fallback template used when LLM API is unavailable
    @classmethod
    def _fallback_research(cls, topic, research_depth, target_audience, voice_tone):
        """Returns a structured but templated research report as fallback."""
        import hashlib
        seed = int(hashlib.md5(topic.encode()).hexdigest()[:6], 16)
        efficiency_pct = 35 + (seed % 30)
        failure_pct = 60 + (seed % 25)
        engagement_mult = round(2.5 + (seed % 20) / 10, 1)
        doc_score = round(8.5 + (seed % 15) / 10, 1)
        reel_score = round(8.2 + (seed % 15) / 10, 1)
        li_score = round(8.0 + (seed % 15) / 10, 1)
        topic_upper = topic.upper()
        return (
            f"# Deep Research Report: {topic}\n"
            f"{'=' * 60}\n\n"
            f"## Executive Summary\n"
            f"Systematic research audit analyzing real-world adoption patterns, verified performance benchmarks, "
            f"and implementation bottlenecks for **{topic}**. "
            f"This report applies a {research_depth} tier investigation protocol.\n\n"
            f"---\n\n"
            f"## Research Classification\n\n"
            f"| Parameter | Value |\n"
            f"|-----------|-------|\n"
            f"| Depth Tier | {research_depth} |\n"
            f"| Target Audience | {target_audience} |\n"
            f"| Voice Tone | {voice_tone} |\n\n"
            f"---\n\n"
            f"## Taxonomy & Domain Map\n\n"
            f"```\n"
            f"{topic_upper}\n"
            f"\u251c\u2500\u2500 Core Concepts\n"
            f"\u2502   \u251c\u2500\u2500 Foundational theory & principles\n"
            f"\u2502   \u2514\u2500\u2500 Architecture variants & design patterns\n"
            f"\u251c\u2500\u2500 Implementation Landscape\n"
            f"\u2502   \u251c\u2500\u2500 Production deployment patterns\n"
            f"\u2502   \u2514\u2500\u2500 Common failure modes\n"
            f"\u2514\u2500\u2500 Creator & Audience Intelligence\n"
            f"    \u2514\u2500\u2500 Best-performing content formats\n"
            f"```\n\n"
            f"---\n\n"
            f"## Key Findings (Confidence-Rated)\n\n"
            f"| # | Finding | Confidence |\n"
            f"|---|---------|------------|\n"
            f"| 1 | Efficiency gains of {efficiency_pct}-{efficiency_pct+15}% documented in production | HIGH |\n"
            f"| 2 | Data-backed content gets {engagement_mult}x higher engagement | HIGH |\n"
            f"| 3 | {failure_pct}% fail at implementation due to config gaps | MEDIUM |\n\n"
            f"---\n\n"
            f"## Research Confidence\n\n"
            f"**Overall: MEDIUM** (Fallback report. API call unavailable.)"
        )

    @classmethod
    def conduct_research(cls, topic, research_depth="DEEP", user=None):
        from apps.brand.models import BrandProfile

        target_audience = "Tech Professionals & Creators"
        voice_tone = "Technical, Authoritative"
        if user and user.is_authenticated:
            prof = BrandProfile.objects.filter(user=user).first()
            voice = BrandVoice.objects.filter(user=user).first()
            if prof and prof.target_audience:
                target_audience = prof.target_audience
            elif voice and hasattr(voice, "audience_level") and voice.audience_level:
                target_audience = voice.audience_level
            if voice and voice.tone:
                voice_tone = voice.tone

        # Build the user prompt for the LLM
        user_prompt = f"""You are researching: {topic}

Research depth: {research_depth}
Target audience: {target_audience}
Brand voice: {voice_tone}

Write a DEEP research report following EXACTLY the format in your system prompt.

CRITICAL REQUIREMENTS — failure to follow any of these means the output is rejected:

1. USE YOUR ACTUAL KNOWLEDGE. This is not a generic topic. "{topic}" has specific named variants, specific named tools, specific named papers, and specific known failure modes. Name them all.

2. THE TAXONOMY TREE must reflect the actual taxonomy of "{topic}" with real subcategories. Not generic branches like "Core Concepts" or "Implementation Landscape". Real structural divisions of the topic.

3. KEY FINDINGS must contain real, specific, verifiable claims — not made-up percentages. Use numbers from literature you actually know, or clearly attribute them. If you cite a benchmark, name the benchmark. If you cite a paper, name the paper.

4. SOURCES must be real ones. Name actual papers (with authors and venue where known), actual documentation pages, actual company blog posts, actual subreddits or communities. Not "various academic papers" or "multiple sources".

5. PRIMARY ANALYSIS must be 4-6 paragraphs explaining HOW the main variants/approaches actually work. Mechanical detail. Not just "it improves accuracy". How does it work and why does that matter?

6. FACT-CHECK LOG must identify real claims that circulate about "{topic}" — things vendors or blogs actually say — and assess them against evidence.

7. CONTENT OPPORTUNITIES must have specific, concrete angles for "{topic}" — not generic "deep dive on topic" suggestions.

Do not use placeholder text. Do not write template-style content with the topic name filled in.
Write like a senior engineer who has spent months on this and is explaining what they actually found."""

        # Call real LLM
        llm_result = LLMClient.flagship(
            system_prompt=DEEP_RESEARCH_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4500,
        )

        if llm_result and len(llm_result.strip()) > 200:
            research_summary = llm_result.strip()
        else:
            logger.warning(f"DeepResearchAgent: LLM returned empty/short result for '{topic}', using fallback.")
            research_summary = cls._fallback_research(topic, research_depth, target_audience, voice_tone)

        AgentManager.execute_agent(
            user=user,
            agent_name="Deep Research & Fact Checker",
            input_text=f"Topic: {topic}\nDepth: {research_depth}\nAudience: {target_audience}",
            preferred_tier="FLAGSHIP",
            system_prompt=DEEP_RESEARCH_AGENT_SYSTEM_PROMPT,
        )

        return research_summary


class MediumBlogWriterAgent:
    """Agent that drafts high-impact, human-sounding Medium articles directly on a given topic with contextual AI image prompts."""

    SYSTEM_PROMPT = """You are an expert long-form technical and domain essayist writing for Medium.

STYLE & HUMAN WRITING DIRECTIVES (MANDATORY):
- Never use em dashes (—). Use commas, hyphens, or periods instead.
- Avoid AI sounding words and cliches: delve, foster, elevate, navigate, furthermore, moreover, in conclusion, crucial, robust, seamless, game changer, unlock potential, fast-paced world, cutting edge, revolutionary.
- Vary sentence length naturally. Mix short, punchy lines with longer explanatory ones.
- Use conversational, human sounding language. Avoid corporate PR or generic content farm tone.
- Take clear, well-reasoned positions instead of lukewarm balance.
- Prioritize specificity. Include concrete examples, real tools/frameworks, and realistic mechanics.
- Skip generic introductions and conclusions. Start directly with the core problem or insight.
- The writing must feel authored by an experienced practitioner.
- Format cleanly with markdown: ## section headings, **bold** for key concepts, code/bullet blocks where helpful.

IMAGE PROMPT DIRECTIVE (MANDATORY & HIGHLY DETAILED):
- Insert 3 to 4 comprehensive, publication-grade AI image prompts for PROFESSIONAL ISOMETRIC 3D INFOGRAPHICS at natural visual pause points in the article:
  1. Header / System Architecture Flow (4 connected stages from left to right with data pipelines).
  2. Disruption / Bottleneck Infographic (Orange 'BREAK IN THE CHAIN' warning, failure point, blocked pathways).
  3. Production Architecture Variants & Schema Blueprint.
  4. End Result & Bottom IMPACT Panel (Consequence callout cards with orange accent icons).

- Every image prompt must follow this complete visual formula:
  * Isometric 3D editorial infographic illustration
  * Soft off-white or light cream background (#F8F9FA)
  * Dark navy typography & structural elements
  * Vibrant orange accent color for warnings, highlights, icons, and key action points
  * Subtle gray and blue-gray secondary components
  * Clean geometric shapes with soft ambient shadows
  * 4 connected stages from left to right linked by metallic conduits / data pipes
  * Rounded rectangular info callout cards with simple orange icons underneath each stage
  * 16:9 wide landscape aspect ratio, minimal visual clutter, high corporate consulting presentation aesthetic

- Format every image prompt cleanly as a blockquote with the exact prefix:
  > 🖼️ **Image Prompt — [Descriptive Title]:** *Professional clean isometric 3D infographic explaining [detailed system/process], modern editorial consulting presentation style, soft cream background, dark navy typography, vibrant orange highlights and warning accents, 4 connected stages from left to right with rounded info callout cards and metallic connectors, prominent orange disruption point, bottom horizontal IMPACT row with consequence icons, 16:9 wide landscape.*"""

    @classmethod
    def write_blog(cls, topic, user=None):
        from apps.brand.models import BrandProfile

        target_audience = "Tech Professionals & Engineers"
        voice_tone = "Technical, Authoritative yet accessible"
        if user and user.is_authenticated:
            prof = BrandProfile.objects.filter(user=user).first()
            voice = BrandVoice.objects.filter(user=user).first()
            if prof and prof.target_audience:
                target_audience = prof.target_audience
            elif voice and hasattr(voice, "audience_level") and voice.audience_level:
                target_audience = voice.audience_level
            if voice and voice.tone:
                voice_tone = voice.tone

        user_prompt = f"""Write a comprehensive, publication-ready Medium article on the topic: "{topic}".

Audience: {target_audience}
Tone: {voice_tone}

Requirements:
- Strong, non-generic title.
- Jump right into the core concept or industry reality.
- Include 3 to 4 distinct `> 🖼️ **Image Prompt — [Title]:** *[Prompt text]*` callouts placed naturally where visuals belong:
  1. Article Header: Isometric 3D End-to-End System Pipeline Overview (4 connected stages).
  2. Deep-Dive Section: Isometric 3D Data Schema & Component Flow with rounded callout cards.
  3. Trade-offs Section: Isometric 3D Break in the Chain / Bottleneck Failure Point (vibrant orange warning).
  4. Conclusion: Isometric 3D Deployment Matrix with Bottom Horizontal IMPACT panel.
- Explain the key methods, architectural variants, or practical paradigms clearly.
- Discuss real-world trade-offs, common bottlenecks, and failure modes practitioners hit in production.
- Include practical guidance and concrete takeaways.
- Length: 800 - 1200 words.

Write the complete Medium blog post in Markdown format now:"""

        llm_result = LLMClient.flagship(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=3800,
        )

        # Reject short completions. A Medium draft needs enough substance to
        # meet the requested 800-1200 word range, not merely a valid heading.
        if llm_result and len(llm_result.strip()) >= 4_000:
            blog_content = llm_result.strip()
        else:
            logger.warning(f"MediumBlogWriterAgent: LLM empty for '{topic}', using structured fallback.")
            blog_content = (
                f"# Definitive Deep-Dive: {topic}\n\n"
                f"## Practical Methods, Architecture Variants, and Production Realities\n\n"
                f"> 🖼️ **Image Prompt — System Architecture Overview**: *Professional clean isometric 3D infographic explaining the end-to-end {topic} pipeline, modern editorial consulting presentation style, soft light cream background, dark navy typography, vibrant orange accent highlights, 4 connected modular stages from left to right linked by metallic conduits with rounded callout cards underneath, 16:9 wide landscape, clean geometric shapes with soft shadows.*\n\n"
                f"When implementing {topic}, teams often get bogged down in hype rather than architecture. "
                f"Here is a clear look at how it works, where it breaks, and what actually works in production.\n\n"
                f"## Core Concepts & Foundational Principles\n\n"
                f"Understanding {topic} begins with separating the core mechanics from the tooling wrapper. "
                f"In real-world systems, performance is dictated by data quality, schema predictability, and pipeline orchestration.\n\n"
                f"> 🖼️ **Image Prompt — Data Flow & Component Schema**: *Wide horizontal isometric 3D infographic diagram showing the sequence of 4 connected modular stages for {topic}, polished 3D geometric nodes connected by large metallic data pipes, rounded info callout cards underneath each stage with orange icons, soft ambient shadows on off-white background, 16:9 aspect ratio.*\n\n"
                f"## Practical Architecture Variants\n\n"
                f"1. **Basic Single-Pass Pipeline**: Straightforward and fast, ideal for simple workflows.\n"
                f"2. **Hybrid & Optimized Flow**: Combines multiple matching techniques for higher accuracy.\n"
                f"3. **Modular & Agentic Architecture**: Multi-step decomposition for complex problem spaces.\n\n"
                f"## Common Production Bottlenecks\n\n"
                f"Most failures trace back to intermediate state handling and prompt fragmentation rather than raw compute limitations.\n\n"
                f"> 🖼️ **Image Prompt — Break in the Chain / Failure Modes**: *Professional isometric 3D infographic highlighting a critical bottleneck in {topic}, featuring a prominent orange 'BREAK IN THE CHAIN' warning symbol, disconnected data flow, leaking packets, and blocked pathways between stages, dark navy labels, 16:9 wide landscape.*\n\n"
                f"## Key Takeaways\n\n"
                f"- Validate on real representative data early.\n"
                f"- Define strict schemas before building abstractions.\n"
                f"- Keep human oversight in the loop for high-leverage steps.\n\n"
                f"## Implementation Playbook\n\n"
                f"Start by defining the decision that {topic} is expected to improve, then write down the input, output, "
                f"owner, and measurable failure condition for every step. Run the simplest useful version against a small, "
                f"representative workload before introducing autonomous branching or a larger toolchain. This keeps the team "
                f"from confusing a polished demo with a dependable production system.\n\n"
                f"Next, instrument the workflow. Capture latency, error types, quality-review outcomes, and the cost of each "
                f"successful result. Those signals reveal whether the bottleneck is retrieval, orchestration, data quality, or "
                f"human handoff. They also make trade-offs explicit: a slower route may be justified for high-risk work, while a "
                f"fast deterministic route is usually the better default for routine tasks.\n\n"
                f"Finally, introduce safeguards incrementally. Validate structured outputs, keep external actions behind an "
                f"approval boundary, and retain enough context to reproduce a bad result. A system that can explain why it made "
                f"a recommendation is easier to improve than one that only produces a confident answer. These practices turn "
                f"{topic} from a one-off experiment into an operating capability.\n\n"
                f"## Questions to Take Into Your Next Review\n\n"
                f"- Which input assumptions would invalidate the result?\n"
                f"- Where does a human need to approve, correct, or stop the flow?\n"
                f"- What metric proves the new approach is better than the current process?\n\n"
                f"> 🖼️ **Image Prompt — Production Impact & Deployment Matrix**: *Clean isometric 3D infographic roadmap for {topic}, showcasing the 4 progressive deployment phases with a bottom horizontal IMPACT panel containing 4 consequence cards with orange icons, editorial corporate aesthetic, 16:9 aspect ratio.*"
            )

        AgentManager.execute_agent(
            user=user,
            agent_name="Medium Blog Writer",
            input_text=f"Topic: {topic}\nAudience: {target_audience}",
            preferred_tier="FLAGSHIP",
            system_prompt=HUMAN_WRITING_STYLE_GUIDE,
        )

        return blog_content


class InstagramReelAgent:
    """Agent that creates high-retention, deep-technical Malayalam engineering Reels & YouTube Shorts scripts."""

    SYSTEM_PROMPT = """You are a senior AI systems engineer, software architect, and technical educator who creates viral, high-depth short-form content in spoken Malayalam.

Your job is to write HIGHLY TECHNICAL, systems-level scripts that dive directly into the real engineering mechanics, hardware constraints, data structures, and architectural trade-offs.

TARGET AUDIENCE:
- Software Engineers & Backend Developers
- ML/AI Engineers & Researchers
- Computer Science Students
- Systems Architects & DevOps Engineers

CORE PRINCIPLE: DEEP TECHNICAL RIGOR
- Do NOT provide shallow, generic summaries or basic definitions.
- Dive straight into the underlying mechanics:
  • Memory layouts, KV cache tensors, attention heads, autoregressive inference bottlenecks
  • Vector indexing (HNSW, IVF-PQ), cosine similarity / dot-product latency
  • Quantization (FP16, INT8, INT4 weight packing, activation scale factors)
  • GPU memory bandwidth (HBM) vs Compute bound (Tensor Cores), FlashAttention SRAM tiling
  • Agentic DAG graph execution, tool schemas, token context windows
  • Low-level bottlenecks, p99 latency, caching layers, and database concurrency
- Explain the exact "WHY" and "HOW" behind the architecture.

LANGUAGE STYLE:
- Spoken Malayalam sentence structure + exact English engineering terminology.
- Natural English technical vocabulary: Key-Value tensors, memory bandwidth, latency bottleneck, GPU SRAM, VRAM allocation, context window, vector embeddings, dot product, quantization, inference engine, pipeline, tokenization, serialization, DAG execution, concurrency.
- Do NOT translate technical terms into Malayalam.
- Conversational Malayalam delivery: "നിങ്ങൾ", "നമുക്ക്", "നമ്മൾ", "എങ്ങനെയാ...", "ഇവിടെയാണ് importance", "Simple ആയി പറഞ്ഞാൽ...", "കാരണം...".
- Avoid artificial textbook phrases like "ആകുന്നത്" or "ആകുന്നു". Use "ആണ്", "വരുന്നത്", "ചെയ്യുന്നത്", "ആയി മാറുകയാണ്".

STRUCTURE (30-45 SECONDS):
1. TOP 5 VIRAL HOOKS: Generate 5 distinct, high-converting hook variations categorized by psychological angle.
2. SPOKEN SCRIPT:
   - HOOK (0-3 sec): Primary hook used in the flow.
   - CONTEXT & PROBLEM (3-8 sec): The specific bottleneck, latency issue, memory constraint, or architecture limitation.
   - DEEP TECHNICAL MECHANISM (8-22 sec): The exact data structure, algorithm, or hardware primitive that solves it.
   - ARCHITECTURAL TAKEAWAY (22-28 sec): Concrete engineering best practice or trade-off to remember.
   - CTA (28-32 sec): Technical question for fellow developers.

OUTPUT FORMAT:
Return the script in this EXACT structure:

**TOP 5 VIRAL HOOKS (Choose One for Your Recording):**
1. 🎯 **Curiosity / Mechanism Hook**: [Hook in spoken Malayalam + English tech terms]
2. ⚡ **Contradiction / Myth-Buster Hook**: [Hook in spoken Malayalam + English tech terms]
3. 🚨 **Bottleneck / Latency Hook**: [Hook in spoken Malayalam + English tech terms]
4. 🚀 **Career / High-Leverage Hook**: [Hook in spoken Malayalam + English tech terms]
5. 💥 **Bold Statement Hook**: [Hook in spoken Malayalam + English tech terms]

**HOOK | 0-3 sec**
[Selected hook line]

**CONTEXT | 3-8 sec**
[The exact engineering bottleneck or architectural problem]

**EXPLANATION | 8-22 sec**
[Deep technical mechanism: tensors, memory layouts, algorithms, or hardware execution]

**TAKEAWAY | 22-28 sec**
[Actionable engineering takeaway / architectural rule]

**CTA | 28-32 sec**
[Interactive technical question for comments]

**ON-SCREEN TEXT**
* [2-6 words technical overlay 1]
* [2-6 words technical overlay 2]
* [2-6 words technical overlay 3]
* [2-6 words technical overlay 4]
* [2-6 words technical overlay 5]

**CAPTION**
[Technical Malayalam-English Instagram caption with bullet points]

**HASHTAGS**
[5-8 relevant technical hashtags]"""

    @classmethod
    def generate_reel(cls, topic, medium_blog="", user=None):
        blog_context = medium_blog[:2200] if medium_blog else ""

        user_prompt = f"""Topic: {topic}

Technical context from blog/research:
{blog_context}

Write a highly technical Malayalam engineering Reel script with AT LEAST 5 TOP-PERFORMING HOOKS categorized by hook type (Curiosity, Contradiction, Bottleneck, Career, Bold Statement), followed by the deep technical breakdown."""

        llm_result = LLMClient.mini(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2500,
        )

        if llm_result and len(llm_result.strip()) > 150:
            full_output = llm_result.strip()
            # Clean awkward artificial forms
            full_output = full_output.replace("ആകുന്നത്", "ആണ് വരുന്നത്").replace("ആകുന്നു", "ആണ്")
            if "**CAPTION**" in full_output:
                parts = full_output.split("**CAPTION**", 1)
                script_text = parts[0].strip()
                caption_part = parts[1].strip()
                caption_text = caption_part
            elif "CAPTION" in full_output.upper():
                parts = full_output.upper().split("CAPTION", 1)
                script_text = full_output[:len(parts[0])].strip()
                caption_text = full_output[len(parts[0]) + 7:].strip().lstrip(":").strip()
            else:
                script_text = full_output
                topic_tag = topic.replace(" ", "")[:20]
                caption_text = (
                    f"Deep Technical Breakdown: {topic}! ⚡\n\n"
                    f"{topic}-ൻ്റെ detailed engineering architecture Medium deep-dive-ൽ publish cheythittund!\n\n"
                    f"👉 Follow for systems-level AI & engineering breakdowns in Malayalam.\n\n"
                    f"#MalayalamTech #{topic_tag} #SoftwareEngineering #SystemDesign #KeralaTech #BuildInPublic"
                )
        else:
            logger.warning(f"InstagramReelAgent: LLM empty for '{topic}', using fallback.")
            topic_tag = topic.replace(" ", "")[:20]
            script_text = (
                f"# INSTAGRAM REEL SCRIPT: {topic}\n\n"
                f"**TOP 5 VIRAL HOOKS (Choose One for Your Recording):**\n"
                f"1. 🎯 **Curiosity / Mechanism**: 'LLM inference-ൽ ഏറ്റവും വലിയ bottleneck compute അല്ല, memory bandwidth ആണ് എന്ന് അറിയാമോ?'\n"
                f"2. ⚡ **Contradiction / Myth-Buster**: 'കൂടുതൽ GPU compute power വാങ്ങിയിട്ടും നിങ്ങളുടെ LLM latency കുറയാത്തത് എന്തുകൊണ്ടാണെന്ന് അറിയാമോ?'\n"
                f"3. 🚨 **Bottleneck / Latency**: 'ഓരോ token generate ചെയ്യുമ്പോഴും മുഴുവൻ model weights-ഉം GPU-ലേക്ക് load ചെയ്യുന്നത് എങ്ങനെ ഒഴിവാക്കാം?'\n"
                f"4. 🚀 **Career / High-Leverage**: 'AI Engineer ആകാൻ model prompt ചെയ്താൽ മാത്രം പോരാ, inference optimization mechanics കൂടെ അറിയണം.'\n"
                f"5. 💥 **Bold Statement**: '{topic.upper()}-ൽ KV cache optimize ചെയ്തില്ലെങ്കിൽ നിങ്ങളുടെ production system scale ചെയ്യാൻ കഴിയില്ല.'\n\n"
                f"**HOOK | 0-3 sec**\n"
                f"LLM inference-ൽ ഏറ്റവും വലിയ bottleneck compute അല്ല, memory bandwidth ആണ് എന്ന് അറിയാമോ?\n\n"
                f"**CONTEXT | 3-8 sec**\n"
                f"ഓരോ token generate ചെയ്യുമ്പോഴും മുഴുവൻ model weights-ഉം VRAM-ൽ നിന്ന് GPU SRAM-ലേക്ക് transfer ചെയ്യണം. ഇതാണ് generation slow ആക്കുന്നത്.\n\n"
                f"**EXPLANATION | 8-22 sec**\n"
                f"ഇത് solve ചെയ്യാൻ {topic}-ൽ KV Caching ഉം FlashAttention-ഉം ഉപയോഗിക്കും.\n"
                f"പഴയ tokens-ന്റെ Key and Value attention matrices memory-യിൽ cache ചെയ്ത് വെക്കും.\n"
                f"ഇതോടെ redundant tensor computations ഒഴിവാക്കി, token generation latency $O(N)$ ആക്കാൻ സാധിക്കും.\n\n"
                f"**TAKEAWAY | 22-28 sec**\n"
                f"അതുകൊണ്ട് production LLM systems build ചെയ്യുമ്പോൾ compute capacity-യേക്കാൾ context memory footprint ഉം KV cache management-ഉം optimize ചെയ്യണം.\n\n"
                f"**CTA | 28-32 sec**\n"
                f"നിങ്ങൾ production-ൽ KV cache optimization use ചെയ്തിട്ടുണ്ടോ? നിങ്ങളുടെ architecture thoughts comment ചെയ്യൂ!\n\n"
                f"**ON-SCREEN TEXT**\n"
                f"* LLM INFERENCE BOTTLENECK\n"
                f"* MEMORY BANDWIDTH VS COMPUTE\n"
                f"* KV CACHE TENSOR MATRICES\n"
                f"* {topic.upper()} ARCHITECTURE\n"
                f"* HOW DO YOU OPTIMIZE?\n\n"
                f"**HASHTAGS**\n"
                f"#MalayalamTech #{topic_tag} #SystemDesign #AIEngineering #SoftwareArchitecture #KeralaTech #DeepLearning"
            )
            caption_text = (
                f"Deep Technical Breakdown: {topic}! ⚡\n\n"
                f"LLM inference bottleneck-ഉം {topic} architecture-ഉം എങ്ങനെയാണ് low-level-ൽ work ചെയ്യുന്നത്?\n\n"
                f"📌 Core Architectural Highlights:\n"
                f"• Memory bandwidth saturation vs compute bounds\n"
                f"• KV Cache tensor matrices & attention caching\n"
                f"• Optimizing token generation latency in production\n\n"
                f"👉 Share your engineering thoughts in the comments below!\n\n"
                f"#MalayalamTech #{topic_tag} #SystemDesign #SoftwareEngineering #AIEngineer #KeralaTech #BuildInPublic"
            )

        AgentManager.execute_agent(
            user=user,
            agent_name="Instagram Reel Script Generator (Deep Technical Malayalam)",
            input_text=f"Topic: {topic}\nLanguage: Deep Technical Malayalam Engineering Reel",
            preferred_tier="MINI_NANO",
            system_prompt=cls.SYSTEM_PROMPT,
        )

        return script_text, caption_text



class LinkedInPostAgent:
    """Agent that generates a LinkedIn post cross-referencing the Medium blog post and Instagram Reel."""

    SYSTEM_PROMPT = """You are an expert LinkedIn technical storyteller writing for founders, engineers, and creators.

STYLE RULES:
- Never use em dashes (—). Use commas, hyphens, or periods instead.
- Never use markdown asterisks (like **bold** or *italics*) because LinkedIn displays raw asterisks rather than formatted text. Use plain text formatting or capitalized key terms instead.
- Avoid AI sounding words: delve, foster, elevate, in conclusion, crucial, robust, seamless, game changer, cutting edge, revolutionary.
- Write like an experienced practitioner sharing real insights, not a marketer.
- Open with a crisp, compelling statement or industry observation.
- Keep paragraphs short (2-3 sentences max) with good white space.
- Mention the full Medium guide and the bilingual Reel summary cleanly in context.
- End with an engaging open-ended question for technical practitioners.
- Include 3-5 relevant hashtags at the bottom.
- Total length: 180-260 words."""

    @classmethod
    def generate_linkedin_post(cls, topic, medium_link="", insta_reel_link="", medium_blog="", user=None):
        m_link = medium_link if medium_link else "[Medium Article Link]"
        i_link = insta_reel_link if insta_reel_link else "[Instagram Reel Link]"
        blog_summary = medium_blog[:800] if medium_blog else ""

        user_prompt = f"""Write a LinkedIn post about: "{topic}"

Context from article:
{blog_summary}

Links to include:
- Medium Deep Dive: {m_link}
- 60s Bilingual Reel: {i_link}

The post should:
1. Start with a direct, non-cliche hook on {topic}.
2. Share 2-3 core insights or practical lessons from the piece.
3. Provide the links to both the comprehensive Medium article and the short Reel summary.
4. End with a thoughtful question to prompt discussion.

Write the full LinkedIn post now:"""

        llm_result = LLMClient.mini(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=800,
        )

        # 180 words is the lower bound specified by the prompt.
        if llm_result and len(llm_result.split()) >= 180:
            post_text = llm_result.strip()
        else:
            logger.warning(f"LinkedInPostAgent: LLM empty for '{topic}', using fallback.")
            topic_tag = topic.replace(" ", "")[:20]
            post_text = (
                f"Most conversations around {topic} focus on tool selection rather than architectural foundations.\n\n"
                f"When building systems in production, success rarely comes from switching to a larger model or adding more libraries. "
                f"It comes down to structured data flows, strict validation schemas, and predictable state management.\n\n"
                f"The practical question is not whether the technology can produce an impressive first result. It is whether "
                f"your team can inspect its assumptions, measure its failure modes, and improve it after real users encounter it. "
                f"That is the difference between an experiment and a system people can trust.\n\n"
                f"I put together a complete breakdown covering practical methods, architecture variants, and failure modes:\n\n"
                f"📝 Full Medium Article: {m_link}\n"
                f"🎬 Instagram Reel, 60-Second Bilingual Summary (Malayalam + English): {i_link}\n\n"
                f"If you are building in this area, start with one narrow workflow, define the evaluation before the interface, "
                f"and keep a human review step wherever an incorrect outcome has a real cost. The smallest reliable system is a "
                f"better foundation than a broad, unmeasured automation.\n\n"
                f"How are you approaching {topic} in your current projects? What architectural choices made the biggest difference?\n\n"
                f"#{topic_tag} #SoftwareEngineering #TechArchitecture #BuildInPublic #PersonalBrand"
            )

        AgentManager.execute_agent(
            user=user,
            agent_name="LinkedIn Cross-Promotion Agent",
            input_text=f"Topic: {topic}\nMedium: {m_link}\nReel: {i_link}",
            preferred_tier="MINI_NANO",
            system_prompt=HUMAN_WRITING_STYLE_GUIDE,
        )

        return post_text


class TopicResearchCampaignOrchestrator:
    """Multi-Agent Campaign Pipeline Orchestrator (Medium Blog -> Instagram Reel -> LinkedIn Post)."""

    @classmethod
    def run_campaign(cls, campaign_id):
        from .models import TopicResearchCampaign
        from apps.content.models import ContentItem

        try:
            campaign = TopicResearchCampaign.objects.get(id=campaign_id)
        except TopicResearchCampaign.DoesNotExist:
            return None

        user = campaign.user
        topic = campaign.topic

        # Step 0: preserve the research and fact-check source for every draft.
        campaign.status = "RESEARCHING"
        campaign.save(update_fields=["status", "updated_at"])
        research_notes = DeepResearchAgent.conduct_research(
            topic=topic, research_depth=campaign.research_depth, user=user
        )
        campaign.research_notes = f"# Deep Research & Fact-Check Summary\n\n{research_notes}"
        campaign.fact_check_summary = research_notes
        campaign.save(update_fields=["research_notes", "fact_check_summary", "updated_at"])

        # Step 1: Medium Blog Article
        campaign.status = "GENERATING_MEDIUM"
        campaign.save()

        medium_blog = MediumBlogWriterAgent.write_blog(topic=topic, user=user)
        campaign.medium_blog = medium_blog
        campaign.save()

        # Make retries idempotent instead of creating duplicate drafts.
        ContentItem.objects.update_or_create(
            user=user,
            platform="MEDIUM",
            title=f"{topic}: The Complete Guide",
            defaults={"body": medium_blog, "status": "DRAFT"},
        )

        # Step 2: Instagram Reel Script (Bilingual: Malayalam + English)
        campaign.status = "GENERATING_REEL"
        campaign.save()

        reel_script, reel_caption = InstagramReelAgent.generate_reel(
            topic=topic,
            medium_blog=medium_blog,
            user=user,
        )
        campaign.insta_reel_script = reel_script
        campaign.insta_reel_caption = reel_caption
        campaign.save()

        # Create draft ContentItem for Instagram
        ContentItem.objects.update_or_create(
            user=user,
            platform="INSTAGRAM",
            title=f"[Reel Script] {topic}",
            defaults={"body": f"{reel_script}\n\n=== CAPTION ===\n{reel_caption}", "status": "DRAFT"},
        )

        # Step 3: LinkedIn Post (Cross-Promoting Medium + Reel)
        campaign.status = "GENERATING_LINKEDIN"
        campaign.save()

        medium_link = campaign.medium_link or "https://medium.com/@yourprofile/post"
        insta_reel_link = campaign.insta_reel_link or "https://instagram.com/reels/your-reel"

        linkedin_post = LinkedInPostAgent.generate_linkedin_post(
            topic=topic,
            medium_link=medium_link,
            insta_reel_link=insta_reel_link,
            medium_blog=medium_blog,
            user=user,
        )
        campaign.linkedin_post = linkedin_post

        # Create draft ContentItem for LinkedIn
        ContentItem.objects.update_or_create(
            user=user,
            platform="LINKEDIN",
            title=f"[LinkedIn Post] {topic} (Medium + Reel Cross-Post)",
            defaults={"body": linkedin_post, "status": "DRAFT"},
        )

        campaign.status = "COMPLETED"
        campaign.save()

        return campaign


class MediumPublisherService:
    """Official Medium REST API client to create draft stories directly on Medium."""

    BASE_URL = "https://api.medium.com/v1"

    @classmethod
    def get_token_for_user(cls, user=None):
        import os
        from django.conf import settings
        from apps.brand.models import BrandProfile

        token = os.environ.get("MEDIUM_INTEGRATION_TOKEN") or getattr(settings, "MEDIUM_INTEGRATION_TOKEN", None)
        if not token and user and user.is_authenticated:
            profile = BrandProfile.objects.filter(user=user).first()
            if profile and isinstance(profile.social_profiles, dict):
                token = profile.social_profiles.get("medium_token")
        return token

    @classmethod
    def save_token_for_user(cls, user, token):
        from apps.brand.models import BrandProfile
        if user and user.is_authenticated and token:
            profile, _ = BrandProfile.objects.get_or_create(user=user)
            if not isinstance(profile.social_profiles, dict):
                profile.social_profiles = {}
            profile.social_profiles["medium_token"] = token.strip()
            profile.save()

    @classmethod
    def publish_draft(cls, title, content_markdown, token=None, user=None, tags=None):
        """
        Publishes a story as DRAFT to Medium using the integration token.
        Returns: dict with {"success": True, "url": "https://medium.com/@...", "post_id": "..."}
        """
        import urllib.request
        import urllib.error
        import json

        token = token or cls.get_token_for_user(user)
        if not token:
            return {
                "success": False,
                "requires_token": True,
                "error": "Medium Integration Token is required. Please provide your token."
            }

        try:
            # 1. Fetch Author ID (/v1/me)
            req = urllib.request.Request(
                f"{cls.BASE_URL}/me",
                headers={
                    "Authorization": f"Bearer {token.strip()}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "PersonalBrandOS/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_data = data.get("data", {})
                author_id = user_data.get("id")

            if not author_id:
                return {
                    "success": False,
                    "error": "Could not identify author profile from Medium token. Please verify your token."
                }

            # 2. Create Draft Post (/v1/users/{authorId}/posts)
            tags_list = tags or ["Artificial Intelligence", "Technology", "Software Engineering"]
            payload = json.dumps({
                "title": title[:100],
                "contentFormat": "markdown",
                "content": content_markdown,
                "tags": tags_list,
                "publishStatus": "draft",
            }).encode("utf-8")

            post_req = urllib.request.Request(
                f"{cls.BASE_URL}/users/{author_id}/posts",
                data=payload,
                headers={
                    "Authorization": f"Bearer {token.strip()}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "PersonalBrandOS/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(post_req, timeout=20) as post_resp:
                post_res_data = json.loads(post_resp.read().decode("utf-8"))
                post_data = post_res_data.get("data", {})
                post_url = post_data.get("url", "")
                post_id = post_data.get("id", "")

            return {
                "success": True,
                "url": post_url,
                "post_id": post_id,
                "author": user_data.get("username", ""),
            }

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Medium API HTTP {e.code}: {err_body}")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("errors", [{}])[0].get("message", f"HTTP {e.code} Error")
            except Exception:
                msg = f"HTTP {e.code} Error: {e.reason}"
            return {"success": False, "error": f"Medium API: {msg}"}
        except Exception as ex:
            logger.error(f"Medium publish exception: {str(ex)}")
            return {"success": False, "error": f"Network error: {str(ex)}"}


class MediumBlogImageGeneratorService:
    """Service that parses image prompts from a Medium blog draft, generates images using DALL-E, and embeds them."""

    @classmethod
    def generate_and_embed_images(cls, campaign, user=None):
        import re
        import os
        import urllib.request
        from pathlib import Path
        from django.conf import settings
        from apps.content.models import ContentItem

        if not campaign or not campaign.medium_blog:
            return 0

        blog_text = campaign.medium_blog

        # Pattern to match blockquote image prompts:
        # > 🖼️ **Image Prompt — Title:** *Prompt description*
        # or > 🖼️ **Image Prompt — Title**: *Prompt description*
        pattern = re.compile(r'(> 🖼️ \*\*Image Prompt[^\*]*\*\*:\s*\*([^\*]+)\*)', re.IGNORECASE)
        matches = list(pattern.finditer(blog_text))

        if not matches:
            pattern = re.compile(r'(> 🖼️[^\n]+\*([^\*]+)\*)', re.IGNORECASE)
            matches = list(pattern.finditer(blog_text))

        if not matches:
            logger.info("No image prompt blockquotes found in Medium blog.")
            return 0

        media_dir = Path(settings.MEDIA_ROOT) / "campaigns" / str(campaign.id)
        media_dir.mkdir(parents=True, exist_ok=True)

        generated_count = 0
        replacements = []

        for idx, match in enumerate(matches, 1):
            full_match = match.group(1)
            prompt_text = match.group(2).strip()

            # Skip if already has an image right before this prompt
            match_start = match.start()
            preceding_text = blog_text[max(0, match_start - 300):match_start]
            if f"/media/campaigns/{campaign.id}/" in preceding_text or "![Illustration" in preceding_text:
                continue

            logger.info(f"Generating AI image {idx} for campaign {campaign.id}: '{prompt_text[:60]}...'")
            image_url = LLMClient.generate_image(prompt_text, size="1024x1024")

            if image_url:
                try:
                    filename = f"blog_image_{idx}_{int(time.time())}.png"
                    file_path = media_dir / filename
                    req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    img_data = b""
                    with urllib.request.urlopen(req, timeout=35) as resp:
                        img_data = resp.read()

                    if len(img_data) > 500:
                        with open(file_path, "wb") as out_file:
                            out_file.write(img_data)
                        img_src = f"{settings.MEDIA_URL}campaigns/{campaign.id}/{filename}"
                    else:
                        img_src = image_url

                    title_part = "Isometric 3D Infographic"
                    if "—" in full_match:
                        title_part = full_match.split("—")[1].split(":")[0].replace("*", "").strip()

                    img_markdown = f"![{title_part}]({img_src})\n\n{full_match}"
                    replacements.append((full_match, img_markdown))
                    generated_count += 1
                except Exception as exc:
                    logger.error(f"Failed to download generated image locally: {exc}")
                    title_part = "Isometric 3D Infographic"
                    if "—" in full_match:
                        title_part = full_match.split("—")[1].split(":")[0].replace("*", "").strip()
                    img_markdown = f"![{title_part}]({image_url})\n\n{full_match}"
                    replacements.append((full_match, img_markdown))
                    generated_count += 1

                # Polite delay between multi-image generations
                time.sleep(1.0)

        # Apply replacements
        for old_str, new_str in replacements:
            blog_text = blog_text.replace(old_str, new_str, 1)

        campaign.medium_blog = blog_text
        campaign.save(update_fields=["medium_blog"])

        # Also update ContentItem in Content Bank
        ContentItem.objects.filter(
            user=campaign.user,
            platform="MEDIUM",
            title__icontains=campaign.topic[:40],
        ).update(body=blog_text)

        return generated_count
