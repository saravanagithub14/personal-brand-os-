from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.http import url_has_allowed_host_and_scheme
from .models import SocialAccount
from .services import SocialStatsFetcher


class AutoSyncSocialAccountView(LoginRequiredMixin, View):
    def post(self, request, account_id=None):
        user = request.user
        if account_id:
            account = get_object_or_404(SocialAccount, id=account_id, user=user)
            SocialStatsFetcher.sync_social_account(account)
        else:
            # Sync all accounts for the user
            accounts = SocialAccount.objects.filter(user=user, active=True)
            for acc in accounts:
                SocialStatsFetcher.sync_social_account(acc)

        return redirect("dashboard:index")


class SocialAccountDetailView(LoginRequiredMixin, View):
    def get(self, request, account_id):
        user = request.user
        account = get_object_or_404(SocialAccount, id=account_id, user=user)
        snapshots = account.snapshots.all().order_by("-recorded_at")[:10]
        from apps.content.models import ContentItem
        from django.utils import timezone
        from datetime import timedelta

        platform_posts = ContentItem.objects.filter(user=user, platform=account.platform).order_by("-updated_at")[:10]

        # Calculate 52-week GitHub-style heatmap & streak stats
        today = timezone.now().date()
        days_offset = (today.weekday() + 1) % 7
        start_date = today - timedelta(days=363 + days_offset)

        daily_counts = {}
        post_details = {}

        # 1. Aggregate from ContentItem objects
        for item in ContentItem.objects.filter(user=user, platform=account.platform):
            c_date = item.created_at.date()
            daily_counts[c_date] = daily_counts.get(c_date, 0) + 1
            if c_date not in post_details:
                post_details[c_date] = []
            post_details[c_date].append(f"Post: {item.title[:45]}")

            if item.status == "PUBLISHED" and item.updated_at:
                u_date = item.updated_at.date()
                if u_date != c_date:
                    daily_counts[u_date] = daily_counts.get(u_date, 0) + 1
                    if u_date not in post_details:
                        post_details[u_date] = []
                    post_details[u_date].append(f"Published: {item.title[:45]}")

        # 2. Aggregate from SocialAccount last_post_at
        if account.last_post_at:
            lp_date = account.last_post_at.date()
            daily_counts[lp_date] = max(daily_counts.get(lp_date, 0), 1)
            if lp_date not in post_details:
                post_details[lp_date] = ["Logged Brand Plan Post"]

        # 3. Aggregate from Historical Snapshots
        for snap in account.snapshots.all():
            s_date = snap.recorded_at.date()
            daily_counts[s_date] = max(daily_counts.get(s_date, 0), 1)
            if s_date not in post_details:
                post_details[s_date] = ["Metric Snapshot Recorded"]

        # Build sorted list of logged post dates for UI timeline
        logged_post_dates = []
        for p_date in sorted(daily_counts.keys(), reverse=True):
            logged_post_dates.append({
                "date_str": p_date.strftime("%Y-%m-%d"),
                "formatted_date": p_date.strftime("%b %d, %Y"),
                "count": daily_counts[p_date],
                "activities": post_details.get(p_date, []),
            })

        heatmap_weeks = []
        current_week = []
        longest_streak = 0
        temp_streak = 0
        active_days_count = 0

        for i in range(364):
            day_date = start_date + timedelta(days=i)
            count = daily_counts.get(day_date, 0)

            if count > 0:
                active_days_count += 1
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

            level = 0 if count == 0 else (1 if count == 1 else (2 if count == 2 else 3))

            current_week.append({
                "date_str": day_date.strftime("%Y-%m-%d"),
                "formatted_date": day_date.strftime("%b %d, %Y"),
                "count": count,
                "level": level,
            })

            if len(current_week) == 7:
                heatmap_weeks.append(current_week)
                current_week = []

        # Current active streak up to today
        current_streak = 0
        check_d = today
        while daily_counts.get(check_d, 0) > 0 or (check_d == today and (today - (account.last_post_at.date() if account.last_post_at else today)).days <= account.target_cadence_days):
            current_streak += 1
            check_d -= timedelta(days=1)

        total_year_posts = sum(daily_counts.values())
        consistency_rate = round((active_days_count / 364) * 100, 1)

        context = {
            "account": account,
            "snapshots": snapshots,
            "platform_posts": platform_posts,
            "heatmap_weeks": heatmap_weeks,
            "current_streak": current_streak,
            "longest_streak": max(longest_streak, current_streak),
            "total_year_posts": total_year_posts,
            "consistency_rate": consistency_rate,
            "logged_post_dates": logged_post_dates,
        }
        return render(request, "social/detail.html", context)


class UpdateLastPostDateView(LoginRequiredMixin, View):
    def post(self, request, account_id):
        user = request.user
        account = get_object_or_404(SocialAccount, id=account_id, user=user)
        last_post_date_str = request.POST.get("last_post_date")
        target_cadence_days = request.POST.get("target_cadence_days")

        if last_post_date_str:
            from django.utils import timezone
            from datetime import datetime
            try:
                parsed_dt = datetime.strptime(last_post_date_str, "%Y-%m-%d")
                account.last_post_at = timezone.make_aware(parsed_dt)
            except Exception:
                pass

        if target_cadence_days:
            try:
                cadence = int(target_cadence_days)
                if cadence > 0:
                    account.target_cadence_days = cadence
            except (TypeError, ValueError):
                pass

        account.save()

        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("dashboard:index")


class LinkedInOAuthLoginView(LoginRequiredMixin, View):
    def get(self, request):
        from .linkedin_services import LinkedInOAuthService, LinkedInOAuthError
        try:
            auth_url = LinkedInOAuthService.generate_authorization_url(request)
            return redirect(auth_url)
        except LinkedInOAuthError as e:
            from django.contrib import messages
            messages.error(request, f"Unable to connect LinkedIn: {str(e)}")
            acc = SocialAccount.objects.filter(user=request.user, platform="LINKEDIN").first()
            if acc:
                return redirect("social:account_detail", account_id=acc.id)
            return redirect("dashboard:index")


class LinkedInOAuthCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        from django.contrib import messages
        from .linkedin_services import LinkedInOAuthService, LinkedInOAuthError

        error = request.GET.get("error")
        error_desc = request.GET.get("error_description")
        code = request.GET.get("code")
        state = request.GET.get("state")

        acc = SocialAccount.objects.filter(user=request.user, platform="LINKEDIN").first()

        if error or error_desc:
            messages.warning(request, f"LinkedIn authorization declined: {error_desc or error}")
            if acc:
                return redirect("social:account_detail", account_id=acc.id)
            return redirect("dashboard:index")

        if not state or not LinkedInOAuthService.validate_oauth_state(request, state):
            messages.error(request, "Invalid OAuth state parameter. Security check failed.")
            if acc:
                return redirect("social:account_detail", account_id=acc.id)
            return redirect("dashboard:index")

        if not code:
            messages.error(request, "Authorization code missing from LinkedIn redirect.")
            if acc:
                return redirect("social:account_detail", account_id=acc.id)
            return redirect("dashboard:index")

        try:
            token_data = LinkedInOAuthService.exchange_code_for_token(code, request)
            access_token = token_data.get("access_token")
            profile_data = LinkedInOAuthService.fetch_user_profile(access_token)
            account = LinkedInOAuthService.save_or_update_account(request.user, token_data, profile_data)

            messages.success(request, "LinkedIn connected successfully.")
            return redirect("social:account_detail", account_id=account.id)
        except LinkedInOAuthError as e:
            messages.error(request, f"Unable to connect LinkedIn. {str(e)}")
            if acc:
                return redirect("social:account_detail", account_id=acc.id)
            return redirect("dashboard:index")


class LinkedInOAuthDisconnectView(LoginRequiredMixin, View):
    def post(self, request):
        from django.contrib import messages
        account = SocialAccount.objects.filter(user=request.user, platform="LINKEDIN").first()
        if account:
            account.access_token = ""
            account.refresh_token = ""
            account.token_expires_at = None
            account.scopes = []
            account.save()
            messages.info(request, "LinkedIn connection disconnected.")
            return redirect("social:account_detail", account_id=account.id)

        messages.warning(request, "No connected LinkedIn account found.")
        return redirect("dashboard:index")


class LinkedInPublishPostView(LoginRequiredMixin, View):
    def post(self, request, account_id):
        from django.contrib import messages
        from .linkedin_services import LinkedInPublisher, LinkedInAPIError
        account = get_object_or_404(SocialAccount, id=account_id, user=request.user)
        content_id = request.POST.get("content_id")

        from apps.content.models import ContentItem
        content_item = get_object_or_404(ContentItem, id=content_id, user=request.user)

        try:
            res = LinkedInPublisher.publish(account, content_item)
            messages.success(request, res.get("message", "Post published to LinkedIn."))
        except LinkedInAPIError as e:
            messages.error(request, f"The LinkedIn post could not be published: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error publishing to LinkedIn: {str(e)}")

        return redirect("social:account_detail", account_id=account.id)
