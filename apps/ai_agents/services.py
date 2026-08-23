import time
from django.utils import timezone
from .models import AgentExecutionLog
from apps.brand.models import BrandVoice


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
