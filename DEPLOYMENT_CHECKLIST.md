# Deployment Checklist ✅

## Phase 1: Setup Google OAuth (10 minutes)

- [ ] Go to https://console.cloud.google.com
- [ ] Enable Google Sheets API
- [ ] Create OAuth 2.0 Client ID (Web application type)
- [ ] Add redirect URI: `http://localhost:8000/authorize`
- [ ] Save Client ID and Secret
- [ ] Create OAuth Consent Screen
- [ ] Mark as "External"
- [ ] Add test user (your email)
- [ ] Verify scopes: `userinfo.email`, `userinfo.profile`

**Save these for later:**
- [ ] Google Client ID: `_________________________________`
- [ ] Google Client Secret: `_________________________________`

---

## Phase 2: Test Locally (5 minutes)

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow
```

- [ ] Edit `.env` and add Google credentials
- [ ] Run: `pip install flask-login authlib`
- [ ] Run: `python3 app.py`
- [ ] Visit: http://localhost:8000
- [ ] See login page ✅
- [ ] Click "Sign in with Google"
- [ ] Successfully login ✅
- [ ] See dashboard ✅
- [ ] Logout works ✅

---

## Phase 3: Push to GitHub (5 minutes)

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow
git init
git add .
git commit -m "Add Gmail OAuth and Railway deployment"
git remote add origin https://github.com/YOUR_USERNAME/clevertap-unsubscribe-flow.git
git push -u origin main
```

- [ ] Code pushed to GitHub
- [ ] `.env` NOT committed (check `.gitignore` if needed)
- [ ] `service_account.json` NOT committed
- [ ] Repository is public or private (your choice)

**Your GitHub repo URL:** `_________________________________`

---

## Phase 4: Deploy to Railway (10 minutes)

- [ ] Visit https://railway.app
- [ ] Sign up with GitHub
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose `clevertap-unsubscribe-flow`
- [ ] Wait for deployment to complete
- [ ] Get your Railway domain URL

**Your Railway domain:** `_________________________________`

Example format: `your-app-12345.up.railway.app`

---

## Phase 5: Update Google OAuth Redirect URI (5 minutes)

- [ ] Go back to Google Cloud Console
- [ ] Go to Credentials
- [ ] Edit OAuth 2.0 Client ID
- [ ] Add redirect URI: `https://YOUR_RAILWAY_DOMAIN/authorize`
- [ ] Replace `YOUR_RAILWAY_DOMAIN` with actual domain
- [ ] Save changes

---

## Phase 6: Set Environment Variables in Railway (5 minutes)

In Railway project, go to **Variables** tab:

- [ ] `CLEVERTAP_PROJECT_ID` = `[your-clevertap-project-id]`
- [ ] `CLEVERTAP_PASSCODE` = `[your-clevertap-passcode]`
- [ ] `SHEET_ID` = `[your-sheet-id]`
- [ ] `GOOGLE_CLIENT_ID` = (from Phase 1)
- [ ] `GOOGLE_CLIENT_SECRET` = (from Phase 1)
- [ ] `ALLOWED_EMAILS` = `your_email@gmail.com` (or `@company.com`)
- [ ] `SECRET_KEY` = `some-random-string-here`
- [ ] `SERVICE_ACCOUNT_FILE` = `service_account.json`

**For SERVICE_ACCOUNT_FILE:**
- [ ] Click "File" type
- [ ] Upload your `service_account.json`

---

## Phase 7: Test the Live Deployment (2 minutes)

- [ ] Visit: `https://YOUR_RAILWAY_DOMAIN`
- [ ] See login page ✅
- [ ] Click "Sign in with Google"
- [ ] Successfully authenticate ✅
- [ ] See dashboard ✅
- [ ] Dashboard stats load ✅
- [ ] "Manual Trigger" button works ✅
- [ ] Logout works ✅

---

## Phase 8: Add Team Members (Optional)

To give access to your team:

**In Google Cloud Console:**
- [ ] Go to OAuth Consent Screen
- [ ] Add their emails as "test users"

**In Railway Variables:**
- [ ] Update `ALLOWED_EMAILS` with comma-separated emails
- [ ] Example: `user1@gmail.com,user2@gmail.com`
- [ ] Or domain: `@company.com` (everyone with that domain)

**Communication:**
- [ ] Tell them: `https://YOUR_RAILWAY_DOMAIN`
- [ ] They sign in with their Gmail
- [ ] They see the dashboard

---

## ✅ You're Live!

Congratulations! Your app is now:

- ✅ Deployed to Railway
- ✅ Secured with Gmail OAuth
- ✅ Running 24/7
- ✅ Accessible to team members
- ✅ Automating unsubscribes every Friday at 5 PM

---

## 🔧 How to Update the App

Every time you make changes:

```bash
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow
git add .
git commit -m "Description of changes"
git push origin main
```

Railway **automatically deploys** the new version. Check the Deployments tab.

---

## 🆘 Need Help?

- **Local issues?** Check `RAILWAY_SETUP.md`
- **Deployment issues?** Check `DEPLOYMENT.md`
- **OAuth issues?** See Troubleshooting in `RAILWAY_SETUP.md`
- **Railway docs?** https://docs.railway.app

---

**Questions? Message us or check the docs!** 🚀
