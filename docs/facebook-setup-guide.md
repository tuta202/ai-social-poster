# Facebook Page Token Setup Guide
## PostPilot AI — One-time Setup

This guide helps you connect your Facebook Page to PostPilot AI for automated posting.

---

## Prerequisites

Before you begin, make sure you have:
- A Facebook Developer account (free): https://developers.facebook.com
- A Facebook App created (type: Business)
- Admin access to the Facebook Page you want to post to

---

## Step 1: Create a Facebook App (if not done)

1. Go to https://developers.facebook.com/apps
2. Click **Create App** -> Select **Business** type
3. Fill in app name (e.g. "PostPilot") and contact email
4. Under **Add Products**, find **Facebook Login** -> click **Set Up**

---

## Step 2: Configure App Permissions

1. In your app dashboard, go to **App Review -> Permissions and Features**
2. Request the following permissions:
   - `pages_manage_posts` -- to create posts
   - `pages_read_engagement` -- to read page info
3. For development/testing: these work immediately without review
4. For production (posting to real page): submit for App Review

---

## Step 3: Get Short-lived User Access Token

1. Go to **Graph API Explorer**: https://developers.facebook.com/tools/explorer
2. Select your App in the top-right dropdown
3. Click **Generate Access Token**
4. In the permissions dialog, check:
   - `pages_manage_posts`
   - `pages_read_engagement`
5. Click **Generate Access Token** -> Authorize in popup
6. Copy the token shown (starts with `EAA...`)

> WARNING: This token expires in **2 hours** -- PostPilot will automatically exchange it for a permanent token.

---

## Step 4: Find Your Page ID

**Option A -- From Facebook:**
1. Go to your Facebook Page
2. Click **About** -> scroll to bottom
3. Find **Page ID** (numeric, e.g. `123456789012345`)

**Option B -- From Graph API Explorer:**
1. In Graph API Explorer, change endpoint to `me/accounts`
2. Click **Submit**
3. Find your page in the response, copy the `id` field

---

## Step 5: Connect in PostPilot

1. Log in to PostPilot AI
2. Go to **FB Setup** in the top navigation
3. Paste your **Short-lived User Access Token**
4. Paste your **Page ID**
5. Click **Connect Page**

PostPilot will automatically:
- Exchange your short-lived token for a long-lived token (60 days)
- Get a **permanent Page Access Token** from that
- Save it securely -- you won't need to repeat this process

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Token exchange failed" | Token expired (>2h) -- generate a new one from Graph Explorer |
| "Page not found" | Double-check Page ID; ensure the page is linked to the app |
| "Permission denied" | Make sure `pages_manage_posts` was checked when generating token |
| "App not approved" | For production, submit App Review for `pages_manage_posts` |

---

## Security Notes

- PostPilot stores your **Page Access Token** (not your personal token)
- Page tokens are scoped to a single page -- they cannot access other pages or personal data
- To revoke access: go to Facebook Settings -> Security -> Apps and Websites
