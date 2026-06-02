# Railway Deployment Setup - Quick Start

## ✅ What's Been Done

Your Flask app has been updated with:

- ✅ **Gmail OAuth Authentication** - Team members can log in with their Google accounts
- ✅ **Team Access Control** - Restrict access to specific email addresses/domains
- ✅ **User Session Management** - Flask-Login handles user persistence
- ✅ **Secure Credential Storage** - All secrets use environment variables
- ✅ **Production Ready** - Configured for Railway deployment with Gunicorn
- ✅ **Beautiful Login UI** - Professional login and error pages
- ✅ **Scheduler Persistence** - APScheduler runs 24/7 for Friday 5 PM jobs

---

## 🚀 Next Steps to Deploy

### Step 1: Create Google OAuth Credentials (10 minutes)

**Go to:** https://console.cloud.google.com

1. **Create OAuth 2.0 Credentials**
   - Click **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Select **Web application**
   - Add Authorized redirect URI: `http://localhost:8000/authorize` (for local testing)
   - Save your **Client ID** and **Client Secret**

2. **Set up OAuth Consent Screen**
   - Go to **OAuth Consent Screen**
   - Choose **External**
   - Fill app name: "CleverTap Unsubscribe Flow"
   - Add your email as test user
   - Scopes: `userinfo.email`, `userinfo.profile`

### Step 2: Test Locally (5 minutes)

```bash
# Navigate to project
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow

# Install new dependencies
pip install flask-login authlib

# Update .env with your Google credentials
# GOOGLE_CLIENT_ID=your_client_id
# GOOGLE_CLIENT_SECRET=your_client_secret
# ALLOWED_EMAILS=your_email@gmail.com

# Run the app
python3 app.py

# Visit http://localhost:8000
# You should see the login page!
```

### Step 3: Push to GitHub (5 minutes)

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Add Gmail OAuth authentication and Railway deployment"

# Add your GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/clevertap-unsubscribe-flow.git

# Push
git push -u origin main
```

### Step 4: Deploy to Railway (10 minutes)

1. **Sign up:** https://railway.app (use GitHub account)
2. **Create new project** → **Deploy from GitHub repo**
3. **Select** your `clevertap-unsubscribe-flow` repository
4. **Wait** for deployment to complete
5. **Get your domain** from Railway dashboard (e.g., `your-app-12345.up.railway.app`)

### Step 5: Update Google OAuth Redirect URI (5 minutes)

Go back to Google Cloud Console:

1. **Credentials** → Edit your OAuth 2.0 Client ID
2. **Add Authorized Redirect URI:**
   ```
   https://your-app-12345.up.railway.app/authorize
   ```
   (Replace with your actual Railway domain)
3. **Save**

### Step 6: Set Environment Variables in Railway (5 minutes)

In Railway dashboard, go to **Variables** and add:

```
CLEVERTAP_PROJECT_ID=RKW-W4K-KK6Z
CLEVERTAP_PASSCODE=EHW-QAB-GLUL
SHEET_ID=11-gmht1OU586CE3kCak4pj7uug8LAZcITjX0OShgD9M
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
ALLOWED_EMAILS=user1@gmail.com,user2@gmail.com,user3@gmail.com
SECRET_KEY=generate-a-random-string-here
SERVICE_ACCOUNT_FILE=service_account.json
```

**For SERVICE_ACCOUNT_FILE**, you have two options:

**Option A: Upload as File (Recommended)**
- In Railway Variables, select type: **File**
- Upload your `service_account.json` directly

**Option B: Encode as Base64**
```bash
# Encode your service account
base64 -i service_account.json

# Paste the output into a variable called SERVICE_ACCOUNT_JSON_BASE64
# Then modify app.py to decode it on startup
```

### Step 7: Test the Deployment (2 minutes)

1. Visit your Railway domain: `https://your-app-12345.up.railway.app`
2. You should see the **Login** page
3. Click **Sign in with Google**
4. Sign in with your Gmail account
5. If your email is in `ALLOWED_EMAILS`, you'll see the dashboard ✅

---

## 📱 Adding Team Members

To give access to your team:

1. **In Google Cloud:** Add their emails to the OAuth consent screen as test users
2. **In Railway:** Update `ALLOWED_EMAILS` variable with their email addresses (comma-separated)
3. They can now log in with their Gmail accounts

Examples:
```
# Single domain (everyone @company.com)
ALLOWED_EMAILS=@company.com

# Specific emails
ALLOWED_EMAILS=user1@gmail.com,user2@gmail.com,user3@company.com

# Mix
ALLOWED_EMAILS=user1@gmail.com,@company.com
```

---

## 🔒 Security Notes

✅ **What's Secure:**
- OAuth tokens are encrypted
- Credentials stored as environment variables
- Service account JSON is private
- HTTPS enforced by Railway
- Session cookies are secure
- No passwords stored

✅ **Best Practices:**
- Never commit `.env` to GitHub
- Never commit `service_account.json` to GitHub
- Rotate OAuth secrets quarterly
- Use strong `SECRET_KEY` in production
- Keep team emails list updated

---

## 📊 Scheduled Jobs

Your Friday 5 PM unsubscribe automation will:

- ✅ Run automatically every Friday at 5 PM (timezone aware)
- ✅ Process all rows with "Not Updated" status
- ✅ Continue running even if you close the app
- ✅ Log results visible in the dashboard

Railway keeps the app running 24/7, so the scheduler works perfectly.

---

## 🆘 Troubleshooting

### Login Loop / Not Authenticating

- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Verify the redirect URI matches exactly in Google Console
- Make sure email is in `ALLOWED_EMAILS`

### "Unauthorized" Error

- Confirm your email is in `ALLOWED_EMAILS`
- Email check is case-insensitive: `USER@GMAIL.COM` = `user@gmail.com`

### Sheets Not Updating

- Check that service account has access to your Google Sheet
- Verify `SHEET_ID` is correct
- Look at Railway **Logs** for API errors

### Scheduled Job Not Running

- Check Railway **Logs** for scheduler startup message
- Friday 5 PM should show in the dashboard
- Railway auto-restarts app, keeping scheduler alive

---

## 📚 Links

- **Railway Docs:** https://docs.railway.app
- **Google OAuth:** https://developers.google.com/identity/protocols/oauth2
- **Python Authlib:** https://authlib.org
- **Flask-Login:** https://flask-login.readthedocs.io

---

## ✨ You're All Set!

Once deployed to Railway with OAuth enabled:

1. ✅ Your team can access the dashboard securely
2. ✅ Friday 5 PM automation runs 24/7
3. ✅ Manual triggers work anytime
4. ✅ All data encrypted and secure
5. ✅ Professional, production-grade app

**Questions?** Check DEPLOYMENT.md for detailed step-by-step instructions.
