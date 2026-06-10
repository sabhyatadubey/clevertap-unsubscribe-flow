# Deploying to Vercel

This guide explains how to deploy the CleverTap Unsubscribe Flow to Vercel.

## Prerequisites

1. GitHub account with this repository
2. Vercel account (https://vercel.com)
3. All credentials ready:
   - Google Client ID & Secret
   - Google Sheets ID
   - Service Account JSON (base64 encoded)
   - CleverTap Project ID & Passcode

## Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

## Step 2: Connect to Vercel

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository: `sabhyatadubey/clevertap-unsubscribe-flow`
4. Vercel will auto-detect Flask framework

## Step 3: Configure Environment Variables

In Vercel dashboard, add these environment variables:

```
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_CLIENT_REDIRECT_URI=https://your-vercel-url.vercel.app/authorize
SHEET_ID=your-google-sheet-id
SERVICE_ACCOUNT_JSON_BASE64=your-base64-encoded-service-account
CLEVERTAP_PROJECT_ID=your-clevertap-project-id
CLEVERTAP_PASSCODE=your-clevertap-passcode
```

### Getting SERVICE_ACCOUNT_JSON_BASE64:

On your local machine:
```bash
base64 -i service_account.json
```

Copy the entire output and paste it as the `SERVICE_ACCOUNT_JSON_BASE64` value.

## Step 4: Update Google OAuth

1. Go to Google Cloud Console
2. Navigate to OAuth 2.0 Client IDs
3. Add your Vercel URL to Authorized Redirect URIs:
   - `https://your-vercel-url.vercel.app/authorize`

## Step 5: Share Google Sheet with Service Account

1. Open your Google Sheet
2. Click Share
3. Add the service account email: `clevertap-unsubscribe@clevertap-unsubscribe-flow.iam.gserviceaccount.com`
4. Give it Editor access

## Step 6: Deploy

Click "Deploy" in Vercel dashboard. Your app will be live in 2-3 minutes!

## Accessing Your App

Once deployed, visit: `https://your-vercel-url.vercel.app`

## Troubleshooting

### 401 Unauthorized Error
- Check that Google OAuth redirect URI is correctly set in Google Cloud Console
- Verify GOOGLE_CLIENT_SECRET is correct

### Google Sheets showing 0 records
- Confirm service account email has access to your sheet
- Verify SHEET_ID is correct
- Check that SERVICE_ACCOUNT_JSON_BASE64 is properly base64 encoded

### CleverTap not processing
- Verify CLEVERTAP_PROJECT_ID and CLEVERTAP_PASSCODE are correct
- Check CleverTap API endpoint is accessible

## Logs

To view deployment logs:
1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments" tab
4. Click on the latest deployment
5. View logs in real-time

## Rollback

To revert to a previous version:
1. Go to Deployments tab
2. Click the three-dot menu on an older deployment
3. Select "Promote to Production"
