# LinkedIn OAuth 2.0 & Publishing Setup Guide

This document explains how to set up LinkedIn OAuth 2.0 authorization code flow and post publishing in **Personal Brand OS**.

---

## 1. LinkedIn Developer App Setup

1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps).
2. Click **Create app**:
   - **App Name**: `Personal Brand OS`
   - **LinkedIn Page**: Link your LinkedIn company page or personal profile.
   - **App Logo**: Upload your application logo.
3. Under the **Products** tab, request access to:
   - **Share on LinkedIn** (Provides `w_member_social` permission for post publishing).
   - **Sign In with LinkedIn using OpenID Connect** (Provides `openid`, `profile`, `email` scopes).
4. Under the **Auth** tab, copy your credentials:
   - **Client ID**
   - **Client Secret**
5. Under **Authorized redirect URLs for your app**, add:
   ```text
   http://localhost:8000/auth/linkedin/callback/
   ```

---

## 2. Environment Configuration (`.env`)

Add the following environment variables to your `.env` file:

```env
# LinkedIn OAuth 2.0 Credentials
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/linkedin/callback/
```

> [!CAUTION]
> Never commit `LINKEDIN_CLIENT_SECRET` to git or expose it in frontend JavaScript.

---

## 3. How the OAuth 2.0 Flow Works

```text
User
  ↓
Clicks "Connect LinkedIn" (/auth/linkedin/connect/)
  ↓
Django generates CSRF state token & redirects to LinkedIn Authorization URL
  ↓
User approves access on LinkedIn
  ↓
LinkedIn redirects back to Django Callback (/auth/linkedin/callback/?code=...&state=...)
  ↓
Django validates state token in constant time
  ↓
Django exchanges code for access_token (POST https://www.linkedin.com/oauth/v2/accessToken)
  ↓
Django fetches member identity (GET https://api.linkedin.com/v2/userinfo)
  ↓
Per-user SocialAccount record saved with access_token & token_expires_at
  ↓
Dashboard displays "LinkedIn Connected"
```

---

## 4. Local Testing & Verification

1. Start your local Django development server:
   ```bash
   python manage.py runserver
   ```
2. Navigate to your LinkedIn analytics page:
   ```text
   http://localhost:8000/social/account/3/
   ```
3. Click **Connect LinkedIn** (or **Reconnect LinkedIn**).
4. Approve the permissions on LinkedIn.
5. Upon redirect, verify the page displays:
   ```text
   ✅ LinkedIn Connected (OAuth 2.0 Active)
   ```
6. Test publishing a draft post directly to LinkedIn using the integrated publisher.

---

## 5. Troubleshooting & Error Codes

| Error | Cause | Solution |
| :--- | :--- | :--- |
| `Invalid OAuth state parameter` | Session state mismatch or direct callback request. | Restart authorization flow from `/auth/linkedin/connect/`. |
| `redirect_uri_mismatch` | Configured redirect URI doesn't match LinkedIn app settings. | Ensure `LINKEDIN_REDIRECT_URI` matches exact URL in Developer Portal. |
| `LinkedIn access token has expired` | OAuth access token lifetime (60 days) reached. | Click **Reconnect LinkedIn** to re-authorize. |
| `Insufficient permission (403)` | `w_member_social` product not added in Developer Portal. | Enable **Share on LinkedIn** product in Developer Portal. |
