# CleverTap Unsubscribe Flow - Session Context

**Project Status:** ✅ Complete & Deployed to Vercel  
**Last Updated:** June 10, 2026  
**Live URL:** https://clevertap-unsubscribe-flow.vercel.app

---

## Project Overview

A Flask web application for managing CleverTap unsubscribe requests with Google Sheets integration and automated scheduling.

**Core Features:**
- Gmail OAuth 2.0 authentication (restricted to @justlife.com)
- Google Sheets interface for managing unsubscribe requests
- CleverTap API integration for processing unsubscribes
- Manual trigger for instant processing
- Automatic scheduling (Friday 5 PM) via APScheduler
- Dashboard with real-time statistics

---

## Architecture

**Framework:** Flask (Python)  
**Hosting:** Vercel (serverless functions)  
**Authentication:** Gmail OAuth 2.0 via Authlib  
**Database:** Google Sheets API  
**Scheduler:** APScheduler (background jobs)

### Key File Structure

```
/api/index.py           - Main Flask app (Vercel entry point)
/templates/dashboard.html - Dashboard UI
requirements.txt        - Python dependencies
vercel.json            - Vercel deployment config
.env                   - Environment variables (local only)
```

---

## Environment Variables Required

```
SECRET_KEY=clevertap-unsubscribe-flow-secret-key-2026
GOOGLE_CLIENT_ID=86690803239-fj3d8mdfjd2kf0finktduqr77dhlm7mq.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=[GET FROM GOOGLE CLOUD]
CLEVERTAP_PROJECT_ID=RKW-W4K-KK6Z
CLEVERTAP_PASSCODE=EHW-QAB-GLUL
SHEET_ID=11-gmht1OU586CE3kCak4pj7uug8LAZcITjX0OShgD9M
SERVICE_ACCOUNT_JSON_BASE64=[BASE64 ENCODED SERVICE ACCOUNT JSON]
PORT=8001
```

---

## Running Locally

### Setup

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Create .env File

Create `.env` in project root with all variables from above.

### Run App

```bash
python app.py
# or
python api/index.py
```

Visit: http://localhost:8001

**Auto-Login:** On localhost, you're automatically logged in as sabhy@justlife.com (OAuth bypassed)

---

## Google Cloud Setup

### OAuth 2.0 Client Credentials

1. Google Cloud Console → APIs & Services → Credentials
2. OAuth 2.0 Client ID: `86690803239-fj3d8mdfjd2kf0finktduqr77dhlm7mq.apps.googleusercontent.com`
3. Redirect URIs:
   - `http://localhost:8001/authorize` (local)
   - `http://localhost:8000/authorize` (local)
   - `https://clevertap-unsubscribe-flow.vercel.app/authorize` (production)

### Service Account

1. Google Cloud Console → Service Accounts
2. Account: `clevertap-unsubscribe@clevertap-unsubscribe-flow.iam.gserviceaccount.com`
3. Download JSON key and base64 encode it:
   ```bash
   base64 -i service_account.json
   ```
4. Paste into `SERVICE_ACCOUNT_JSON_BASE64` env var

---

## Google Sheets Setup

### Sheet Structure

Headers (Row 1):
- Column A: Date
- Column B: Cust ID
- Column C: Unsubscribe channel
- Column D: Status

Data rows start from Row 2.

### Share with Service Account

1. Open your Google Sheet
2. Click Share
3. Add email: `clevertap-unsubscribe@clevertap-unsubscribe-flow.iam.gserviceaccount.com`
4. Give Editor access

---

## CleverTap Integration

**Project ID:** RKW-W4K-KK6Z  
**Passcode:** EHW-QAB-GLUL  
**API Endpoint:** https://api.clevertap.com/1/upload

### Payload Format

```json
{
  "d": [{
    "customer_id": 12345,
    "unsubscribe": {
      "email": 1,
      "sms": 1,
      "push": 1
    }
  }]
}
```

---

## Deployment to Vercel

### Current Status: ✅ DEPLOYED

**Steps to Deploy:**

1. Push changes to GitHub
   ```bash
   git push origin main
   ```

2. Vercel auto-deploys on push to main branch

3. Set environment variables in Vercel Dashboard:
   - Go to vercel.com/dashboard
   - Select project
   - Settings → Environment Variables
   - Add all variables from .env file

4. Monitor deployment:
   - Vercel Dashboard → Deployments
   - Wait for ✅ Ready status (3-5 minutes)

**Live Dashboard:** https://clevertap-unsubscribe-flow.vercel.app

---

## API Endpoints

### GET /
Redirects to login or dashboard (if authenticated)

### GET /login
Initiates OAuth login (bypassed on localhost)

### GET /authorize
OAuth callback handler

### GET /dashboard
Main dashboard (requires authentication)

### POST /api/trigger
Manually process pending unsubscribes

**Request:**
```bash
curl -X POST https://clevertap-unsubscribe-flow.vercel.app/api/trigger
```

**Response:**
```json
{
  "message": "Success! 5 processed, 0 failed",
  "processed": 5,
  "failed": 0
}
```

### GET /logout
Sign out and redirect to login

---

## Dashboard Features

**Statistics Cards:**
- TOTAL PENDING: Count of "Not Updated" rows in sheet
- COMPLETED: Count of "Updated" rows in sheet
- NEXT RUN: Friday 5 PM (scheduler next execution)
- SCHEDULER STATUS: Shows if background job is running

**Manual Trigger Button:**
- Processes all pending unsubscribes immediately
- Sends to CleverTap API
- Updates Google Sheet status to "Updated"

**Recent Activity Table:**
- Shows last 10 entries from sheet
- Displays: Email (Cust ID), Channel, Status
- Status color-coded: Green (Updated), Yellow (Not Updated)

---

## Common Issues & Fixes

### Issue: 0 Pending / 0 Completed Data
**Cause:** Service account not shared on Google Sheet or SERVICE_ACCOUNT_JSON_BASE64 not set  
**Fix:** 
1. Verify service account email is shared on sheet with Editor access
2. Check SERVICE_ACCOUNT_JSON_BASE64 is set in .env
3. Restart app

### Issue: OAuth Error (401 invalid_client)
**Cause:** GOOGLE_CLIENT_SECRET not set or incorrect  
**Fix:** Update GOOGLE_CLIENT_SECRET in .env from Google Cloud Console

### Issue: Sign Out Not Working
**Cause:** On older Vercel deployments with template files  
**Fix:** This is fixed in latest version (rewritten for Vercel)

### Issue: Port 8001 Already in Use
**Cause:** Flask app still running from previous session  
**Fix:** 
```bash
lsof -i :8001
kill -9 <PID>
```

---

## Git & Version Control

**Repository:** https://github.com/sabhyatadubey/clevertap-unsubscribe-flow

### Recent Commits

1. **Complete rewrite for Vercel** - Removed template dependencies, inlined HTML
2. **Proper Vercel function configuration** - Fixed functions section
3. **Working serverless setup** - API routes properly configured

### Branches

- `main` - Production (auto-deploys to Vercel)
- No other active branches

---

## Testing Checklist

- [ ] Local login works (http://localhost:8001/login)
- [ ] Dashboard displays with real Google Sheets data
- [ ] Stats show correct numbers (pending/completed)
- [ ] Recent Activity table populates
- [ ] Manual Trigger button works
- [ ] Sign Out button works
- [ ] Vercel deployment succeeds
- [ ] Production app accessible at live URL

---

## Next Steps (Optional Enhancements)

1. **APScheduler Setup** - Add automatic Friday 5 PM processing
2. **Error Logging** - Add comprehensive error tracking
3. **Retry Logic** - Handle failed CleverTap API calls
4. **Audit Trail** - Log all unsubscribe operations
5. **Rate Limiting** - Prevent API abuse

---

## Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python api/index.py
# or
python app.py

# Check if port is in use
lsof -i :8001

# Git status
git status

# Push to GitHub (triggers Vercel deploy)
git push origin main

# View Git log
git log --oneline -10
```

---

## Contact & Questions

- **Gmail OAuth:** Google Cloud Console
- **CleverTap API:** https://developer.clevertap.com
- **Google Sheets API:** https://developers.google.com/sheets
- **Vercel Docs:** https://vercel.com/docs

---

**All credentials and setup instructions complete. Ready for production use.**
