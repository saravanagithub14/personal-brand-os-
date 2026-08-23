import os
import json
import secrets
import hmac
import urllib.request
import urllib.parse
import urllib.error
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from apps.social.models import SocialAccount

LINKEDIN_AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"


class LinkedInOAuthError(Exception):
    """Raised when LinkedIn OAuth authorization or token exchange fails."""
    pass


class LinkedInAPIError(Exception):
    """Raised when LinkedIn REST API request fails."""
    pass


class LinkedInTokenExpiredError(LinkedInAPIError):
    """Raised when LinkedIn access token is expired or revoked."""
    pass


class LinkedInOAuthService:
    @classmethod
    def get_client_id(cls):
        return getattr(settings, "LINKEDIN_CLIENT_ID", "") or os.getenv("LINKEDIN_CLIENT_ID", "")

    @classmethod
    def get_client_secret(cls):
        return getattr(settings, "LINKEDIN_CLIENT_SECRET", "") or os.getenv("LINKEDIN_CLIENT_SECRET", "")

    @classmethod
    def get_redirect_uri(cls, request=None):
        if request:
            try:
                from django.urls import reverse
                return request.build_absolute_uri(reverse("auth_linkedin_callback"))
            except Exception:
                pass
        return getattr(settings, "LINKEDIN_REDIRECT_URI", "") or os.getenv(
            "LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/linkedin/callback/"
        )

    @classmethod
    def get_scopes(cls):
        return getattr(settings, "LINKEDIN_OAUTH_SCOPES", ["openid", "profile", "email", "w_member_social"])

    @classmethod
    def generate_authorization_url(cls, request):
        client_id = cls.get_client_id()
        if not client_id or client_id.startswith("your_"):
            raise LinkedInOAuthError("LINKEDIN_CLIENT_ID is not configured in environment or Django settings.")

        state = secrets.token_urlsafe(32)
        request.session["linkedin_oauth_state"] = state

        scopes_str = " ".join(cls.get_scopes())
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": cls.get_redirect_uri(request),
            "state": state,
            "scope": scopes_str,
        }
        return f"{LINKEDIN_AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def validate_oauth_state(cls, request, state):
        stored_state = request.session.get("linkedin_oauth_state")
        if not stored_state or not state:
            return False

        is_valid = hmac.compare_digest(stored_state, state)
        if "linkedin_oauth_state" in request.session:
            del request.session["linkedin_oauth_state"]
        return is_valid

    @classmethod
    def exchange_code_for_token(cls, code, request=None):
        client_id = cls.get_client_id()
        client_secret = cls.get_client_secret()
        redirect_uri = cls.get_redirect_uri(request)

        if not client_id or not client_secret:
            raise LinkedInOAuthError("LinkedIn OAuth credentials missing in configuration.")

        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode("utf-8")

        req = urllib.request.Request(
            LINKEDIN_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "PersonalBrandOS/1.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload
                else:
                    raise LinkedInOAuthError(f"Token exchange failed with HTTP status {response.status}")
        except Exception as e:
            if isinstance(e, LinkedInOAuthError):
                raise
            raise LinkedInOAuthError(f"Failed to communicate with LinkedIn token endpoint: {str(e)}")

    @classmethod
    def fetch_user_profile(cls, access_token):
        req = urllib.request.Request(
            LINKEDIN_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "PersonalBrandOS/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception:
            pass
        return {}

    @classmethod
    def save_or_update_account(cls, user, token_data, profile_data=None):
        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 5184000)
        scopes_raw = token_data.get("scope", "")
        scopes_list = scopes_raw.split(",") if isinstance(scopes_raw, str) else cls.get_scopes()

        token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))

        profile_data = profile_data or {}
        sub = profile_data.get("sub") or profile_data.get("id") or f"linkedin_{user.id}"
        name = profile_data.get("name") or profile_data.get("given_name") or f"{user.first_name} {user.last_name}".strip() or user.username
        email = profile_data.get("email", "")

        account, created = SocialAccount.objects.update_or_create(
            user=user,
            platform="LINKEDIN",
            defaults={
                "handle": name,
                "provider_user_id": sub,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expires_at": token_expires_at,
                "scopes": scopes_list,
                "metadata": {
                    "name": name,
                    "email": email,
                    "picture": profile_data.get("picture", ""),
                    "connected_at": timezone.now().isoformat(),
                },
                "profile_url": f"https://www.linkedin.com/in/{sub}" if not email else f"https://www.linkedin.com/in/{user.username}",
                "active": True,
            },
        )
        return account


class LinkedInPublisher:
    @classmethod
    def publish(cls, social_account, content_item):
        if not social_account or social_account.platform != "LINKEDIN":
            raise LinkedInAPIError("Invalid social account provided for LinkedIn publishing.")

        if not social_account.access_token:
            raise LinkedInAPIError("No LinkedIn OAuth access token found. Please connect your LinkedIn account.")

        if social_account.is_token_expired:
            raise LinkedInTokenExpiredError("LinkedIn access token has expired. Please reconnect your LinkedIn account.")

        author_urn = f"urn:li:person:{social_account.provider_user_id or 'me'}"
        text_content = f"{content_item.title}\n\n{content_item.body}" if content_item.title else content_item.body

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text_content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {social_account.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "User-Agent": "PersonalBrandOS/1.0",
        }

        req = urllib.request.Request(LINKEDIN_UGC_POSTS_URL, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    res_body = json.loads(response.read().decode("utf-8"))
                    post_id = res_body.get("id", "urn:li:share:published")

                    content_item.status = "PUBLISHED"
                    content_item.published_at = timezone.now()
                    content_item.save()

                    social_account.last_post_at = timezone.now()
                    social_account.posts_count = (social_account.posts_count or 0) + 1
                    social_account.save()

                    return {
                        "success": True,
                        "post_id": post_id,
                        "published_at": timezone.now().isoformat(),
                        "message": "Post published to LinkedIn successfully.",
                    }
                else:
                    raise LinkedInAPIError(f"LinkedIn API returned status {response.status}")
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                raise LinkedInTokenExpiredError("LinkedIn access token is invalid or lacks 'w_member_social' permission.")
            raise LinkedInAPIError(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            if isinstance(e, (LinkedInAPIError, LinkedInTokenExpiredError)):
                raise
            raise LinkedInAPIError(f"Failed to publish post to LinkedIn: {str(e)}")
