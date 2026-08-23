from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.social.models import SocialAccount
from apps.content.models import ContentItem
from apps.social.linkedin_services import (
    LinkedInOAuthService,
    LinkedInPublisher,
    LinkedInOAuthError,
    LinkedInAPIError,
    LinkedInTokenExpiredError,
)

User = get_user_model()


class LinkedInOAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="linkedin_user", password="Password123!")
        self.client.login(username="linkedin_user", password="Password123!")

        self.account = SocialAccount.objects.create(
            user=self.user,
            platform="LINKEDIN",
            handle="Saravana Perumal R.",
            provider_user_id="urn_person_123",
            access_token="test_access_token_abc123",
            token_expires_at=timezone.now() + timedelta(days=60),
            scopes=["openid", "profile", "email", "w_member_social"],
        )

    def test_linkedin_connect_requires_login(self):
        self.client.logout()
        url = reverse("auth_linkedin_connect")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("apps.social.linkedin_services.LinkedInOAuthService.get_client_id")
    def test_oauth_state_is_generated(self, mock_client_id):
        mock_client_id.return_value = "test_client_id_123"
        url = reverse("auth_linkedin_connect")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://www.linkedin.com/oauth/v2/authorization", response.url)
        self.assertIn("state=", response.url)
        self.assertIn("linkedin_oauth_state", self.client.session)

    def test_invalid_state_is_rejected(self):
        session = self.client.session
        session["linkedin_oauth_state"] = "valid_state_123"
        session.save()

        url = reverse("auth_linkedin_callback") + "?code=test_code&state=invalid_state_999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_user_denial_is_handled(self):
        url = reverse("auth_linkedin_callback") + "?error=user_cancelled_login&error_description=User+cancelled"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_missing_code_is_handled(self):
        session = self.client.session
        session["linkedin_oauth_state"] = "state_123"
        session.save()

        url = reverse("auth_linkedin_callback") + "?state=state_123"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    @patch("apps.social.linkedin_services.LinkedInOAuthService.exchange_code_for_token")
    @patch("apps.social.linkedin_services.LinkedInOAuthService.fetch_user_profile")
    def test_successful_token_exchange(self, mock_fetch_profile, mock_exchange_token):
        mock_exchange_token.return_value = {
            "access_token": "new_oauth_token_xyz789",
            "expires_in": 5184000,
            "scope": "openid,profile,email,w_member_social",
        }
        mock_fetch_profile.return_value = {
            "sub": "linkedin_sub_999",
            "name": "Saravana Perumal R.",
            "email": "saravanamedia@example.com",
        }

        session = self.client.session
        session["linkedin_oauth_state"] = "valid_state_123"
        session.save()

        url = reverse("auth_linkedin_callback") + "?code=valid_code_123&state=valid_state_123"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.account.refresh_from_db()
        self.assertEqual(self.account.access_token, "new_oauth_token_xyz789")
        self.assertEqual(self.account.provider_user_id, "linkedin_sub_999")
        self.assertTrue(self.account.is_connected)

    def test_disconnect_requires_authentication(self):
        self.client.logout()
        url = reverse("social:linkedin_disconnect")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_disconnect_clears_stored_credentials(self):
        url = reverse("social:linkedin_disconnect")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.account.refresh_from_db()
        self.assertEqual(self.account.access_token, "")
        self.assertFalse(self.account.is_connected)

    def test_expired_token_is_detected(self):
        self.account.token_expires_at = timezone.now() - timedelta(days=1)
        self.account.save()
        self.assertTrue(self.account.is_token_expired)
        self.assertTrue(self.account.requires_reauthorization)

    @patch("apps.social.linkedin_services.LinkedInPublisher.publish")
    def test_publish_linkedin_post(self, mock_publish):
        mock_publish.return_value = {
            "success": True,
            "post_id": "urn:li:share:123456",
            "message": "Post published to LinkedIn.",
        }

        item = ContentItem.objects.create(
            user=self.user,
            platform="LINKEDIN",
            title="Genomics AI Benchmarks",
            body="Breakthrough performance on protein folding tasks.",
            status="APPROVED",
        )

        url = reverse("social:linkedin_publish", kwargs={"account_id": self.account.id})
        response = self.client.post(url, {"content_id": item.id})
        self.assertEqual(response.status_code, 302)
        mock_publish.assert_called_once()
