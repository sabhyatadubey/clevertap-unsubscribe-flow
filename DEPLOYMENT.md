# CleverTap Unsubscribe Flow - Deployment Guide

## Overview

This guide explains how to deploy the CleverTap Unsubscribe Flow to **Railway.app** with Gmail OAuth authentication for team members.

## Prerequisites

Before deployment, ensure you have:

1. ✅ **GitHub Account** - For connecting your repository
2. ✅ **Railway Account** - [Sign up at railway.app](https://railway.app)
3. ✅ **Google Cloud Account** - For OAuth credentials and Sheets API
4. ✅ **CleverTap Account** - With API credentials
5. ✅ **Google Sheet** - Shared with your service account

---

## Step 1: Set Up Google OAuth Credentials

### 1.1 Enable OAuth in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create a new one)
3. Enable the following APIs:
   - Google Sheets API
   - Google+ API (for OAuth)

### 1.2 Create OAuth 2.0 Credentials

1. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
2. Choose **Web application**
3. Under **Authorized redirect URIs**, add:
   ```
   https://your-railway-app-domain.up.railway.app/authorize
   ```
   (You'll get the exact domain after deploying to Railway first)
4. Save your **Client ID** and **Client Secret**

### 1.3 Create OAuth Consent Screen

1. Go to **OAuth Consent Screen**
2. Choose **External** user type
3. Fill in app information:
   - App name: "CleverTap Unsubscribe Flow"
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
5. Add test users (your team members' emails)

---

## Step 2: Push Code to GitHub

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow
git init
git add .
git commit -m "Initial commit: CleverTap Unsubscribe Flow with Gmail OAuth"
git remote add origin https://github.com/YOUR_USERNAME/clevertap-unsubscribe-flow.git
git push -u origin main
```

---

## Step 3: Deploy to Railway

### 3.1 Connect Railway to GitHub

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your `clevertap-unsubscribe-flow` repository
5. Railway will automatically detect the Python app and create a project

### 3.2 Configure Environment Variables

In Railway project settings, add the following environment variables:

```
CLEVERTAP_PROJECT_ID=[your-clevertap-project-id]
CLEVERTAP_PASSCODE=[your-clevertap-passcode]
SHEET_ID=[your-sheet-id]
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
ALLOWED_EMAILS=user1@company.com,user2@company.com,@company.com
SECRET_KEY=generate-a-strong-random-string-here
SERVICE_ACCOUNT_FILE=service_account.json
```

### 3.3 Upload Service Account JSON

1. In Railway, click on **Variables**
2. Create a new file variable called `SERVICE_ACCOUNT_FILE`
3. Upload your `service_account.json` file

Alternatively, convert it to base64 and store as a string:
```bash
cat service_account.json | base64
```
Then in your code, decode it on startup.

### 3.4 Deploy

Railway automatically deploys when you push to GitHub. Monitor the deployment in the **Deployments** tab.

---

## Step 4: Update OAuth Redirect URI

1. Once Railway assigns a domain (e.g., `your-app-12345.up.railway.app`), update your Google OAuth credentials:
   - Go to **Google Cloud Console** → **Credentials**
   - Edit the OAuth 2.0 Client ID
   - Add the redirect URI: `https://your-app-12345.up.railway.app/authorize`

---

## Step 5: Access Your Deployed App

1. Get your Railway app URL from the **Railway Dashboard**
2. Visit: `https://your-app-12345.up.railway.app`
3. You'll see the login page
4. Click **Sign in with Google**
5. Authenticate with your Gmail account
6. Dashboard loads if your email is in `ALLOWED_EMAILS`

---

## Monitoring & Logs

### View Logs in Railway

```
Railway Dashboard → Your Project → Logs
```

### Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

---

## Troubleshooting

### "Authorization failed" Error

- Check that your OAuth consent screen has the correct scopes
- Verify your Client ID and Secret match your Google Cloud credentials
- Ensure the redirect URI in Google Console matches your Railway domain

### "Not authorized" Error

- Check that your email is in the `ALLOWED_EMAILS` list
- Email check is case-insensitive but domain must match exactly

### Google Sheets API Error

- Ensure `service_account.json` is uploaded correctly to Railway
- Verify the service account email has access to your Google Sheet

### Scheduled Job Not Running

- Railway keeps apps running 24/7
- The Friday 5 PM job (APScheduler) will run automatically
- Check **Logs** in Railway dashboard to verify the scheduler started

---

## Custom Domain (Optional)

To use a custom domain instead of Railway's default:

1. In Railway, go to **Settings** → **Domains**
2. Add your custom domain
3. Update your DNS records as instructed by Railway
4. Update Google OAuth redirect URI with your custom domain

---

## Updating the App

Every time you push to GitHub:

```bash
git add .
git commit -m "Update: [description]"
git push origin main
```

Railway automatically rebuilds and deploys the new version.

---

## Important Notes

⚠️ **Security Best Practices:**

- ✅ Never commit `.env` to GitHub
- ✅ Never commit `service_account.json` to GitHub
- ✅ Use environment variables for all secrets
- ✅ Railway environment variables are encrypted at rest
- ✅ Always use HTTPS (Railway handles this automatically)
- ✅ Regularly rotate your OAuth credentials

---

## Support

For Railway issues: [Railway Docs](https://docs.railway.app)  
For Google OAuth issues: [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
