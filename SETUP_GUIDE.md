# CleverTap Unsubscribe Flow - Setup Guide

This guide walks you through setting up the automated unsubscribe flow for your CleverTap customers.

## What This Does

- ✅ Automatically reads your Google Sheet every Friday at 5 PM (EOD)
- ✅ Unsubscribes customers from all subscription groups in CleverTap
- ✅ Updates the sheet with "Updated" status and timestamp
- ✅ Provides a dashboard to view logs and manually trigger unsubscribes
- ✅ No n8n needed - runs locally on your machine

---

## Step 1: Install Python Dependencies

```bash
cd clevertap-unsubscribe-flow
pip3 install -r requirements.txt
```

---

## Step 2: Create Google Sheets Service Account

This allows the app to read and update your Google Sheet securely.

### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click "New Project"
4. Name it "CleverTap Unsubscribe" and click Create
5. Wait for the project to be created

### 2.2 Enable Google Sheets API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click on it and click **Enable**

### 2.3 Create a Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in the details:
   - Service account name: `clevertap-unsubscribe`
   - Description: `Automated unsubscribe flow for CleverTap`
4. Click **Create and Continue**
5. Skip the optional steps and click **Done**

### 2.4 Create and Download the Key

1. In Credentials, find the service account you just created
2. Click on it
3. Go to the **Keys** tab
4. Click **Add Key** → **Create new key**
5. Choose **JSON** and click **Create**
6. A JSON file will download - **save it as `service_account.json` in the project folder**

### 2.5 Share Your Google Sheet with the Service Account

1. Open the downloaded `service_account.json` file in a text editor
2. Find and copy the `client_email` value (looks like `xxx@xxx.iam.gserviceaccount.com`)
3. Go to your Google Sheet: https://docs.google.com/spreadsheets/d/11-gmht1OU586CE3kCak4pj7uug8LAZcITjX0OShgD9M/edit
4. Click **Share** (top right)
5. Paste the email address
6. Give it **Editor** access
7. Uncheck "Notify people" and click **Share**

---

## Step 3: Set Up Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and verify the values:
   ```
   CLEVERTAP_PROJECT_ID=RKW-W4K-KK6Z
   CLEVERTAP_PASSCODE=EHW-QAB-GLUL
   SHEET_ID=11-gmht1OU586CE3kCak4pj7uug8LAZcITjX0OShgD9M
   SERVICE_ACCOUNT_FILE=service_account.json
   ```

---

## Step 4: Run the Application

```bash
python3 app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
Scheduled: Friday EOD (5 PM) unsubscribe job
```

---

## Step 5: Access the Dashboard

1. Open your browser and go to **http://localhost:5000**
2. You'll see the dashboard with:
   - **Pending count**: Number of "Not Updated" rows
   - **Completed count**: Number of "Updated" rows
   - **Next Run**: When the Friday job will execute
   - **Scheduler Status**: Whether the background job is running
   - **Manual Trigger**: Button to run unsubscribes immediately

---

## How It Works

### Automatic (Friday EOD)
The app runs automatically every Friday at 5 PM:
1. Reads all rows from your Google Sheet
2. Finds rows with "Not Updated" status
3. Calls CleverTap API to unsubscribe each customer
4. Updates the sheet with "Updated" status + timestamp

### Manual (Anytime)
Click the "Run Now" button in the dashboard to trigger immediately.

---

## API Endpoints

If you want to integrate with other tools:

- `GET /api/status` - Get current status and logs
- `POST /api/trigger` - Manually trigger unsubscribe process
- `GET /api/pending` - Get list of pending unsubscribes

Example:
```bash
curl -X POST http://localhost:5000/api/trigger
```

---

## Troubleshooting

### "service_account.json not found"
- Make sure the file is in the project folder with the exact name
- Check the path in `.env`

### "Google Sheets API error"
- Verify the service account has been shared with your Google Sheet
- Check that `SHEET_ID` in `.env` is correct

### "CleverTap API error"
- Verify `CLEVERTAP_PROJECT_ID` and `CLEVERTAP_PASSCODE` are correct
- Make sure users are actually in the "Product Updates" subscription group

### "Scheduler not running"
- If you stop the app with Ctrl+C, the scheduler stops too
- Restart with `python3 app.py`

---

## Keeping It Running 24/7

For the scheduled job to run every Friday, the app needs to be running continuously. Options:

### Option 1: Keep Terminal Open
Simple but requires keeping a terminal window open

### Option 2: Run as Background Service (macOS)
Create a LaunchAgent to run it automatically:

1. Create file: `~/Library/LaunchAgents/com.clevertap.unsubscribe.plist`
2. Add:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clevertap.unsubscribe</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/clevertap-unsubscribe.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/clevertap-unsubscribe.log</string>
</dict>
</plist>
```

3. Run: `launchctl load ~/Library/LaunchAgents/com.clevertap.unsubscribe.plist`
4. To stop: `launchctl unload ~/Library/LaunchAgents/com.clevertap.unsubscribe.plist`

---

## Need Help?

- Check the logs in the dashboard
- Look at terminal output for errors
- Verify all API credentials are correct

---

**You're all set! The flow is ready to unsubscribe your customers automatically. 🚀**
