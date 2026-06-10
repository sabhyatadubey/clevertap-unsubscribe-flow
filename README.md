# 🚀 CleverTap Unsubscribe Flow

Automated unsubscribe management for CleverTap customers via Google Sheets.

## Quick Start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set up Google Sheets service account (see SETUP_GUIDE.md)
# 3. Create .env file with your credentials
cp .env.example .env

# 4. Run the app
python3 app.py

# 5. Open http://localhost:5000 in your browser
```

## Features

✅ **Automated Friday EOD Unsubscribes** - Runs every Friday at 5 PM automatically  
✅ **Google Sheets Integration** - Read and update directly from your sheet  
✅ **CleverTap API** - Unsubscribes users from all subscription groups  
✅ **Dashboard** - Monitor status, view logs, trigger manually  
✅ **No n8n Required** - Runs on your local machine  

## Project Structure

```
clevertap-unsubscribe-flow/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── service_account.json  # Google credentials (you create this)
├── SETUP_GUIDE.md        # Step-by-step setup instructions
└── templates/
    └── dashboard.html    # Web dashboard
```

## Configuration

Create a `.env` file with:

```
CLEVERTAP_PROJECT_ID=[your-clevertap-project-id]
CLEVERTAP_PASSCODE=[your-clevertap-passcode]
SHEET_ID=[your-sheet-id]
SERVICE_ACCOUNT_FILE=service_account.json
```

## How It Works

1. **Scheduled Job** - Runs every Friday at 5 PM
2. **Reads Sheet** - Gets all rows with "Not Updated" status
3. **Calls CleverTap** - Unsubscribes user from "Product Updates" group
4. **Updates Sheet** - Changes status to "Updated" + timestamp
5. **Logs Activity** - View all transactions in the dashboard

## Dashboard

Access at `http://localhost:5000`

- 📊 View pending and completed unsubscribes
- 🔄 Manually trigger the process anytime
- 📋 See detailed logs of all activity
- ⏰ Check when the next Friday run is scheduled

## API Endpoints

```
GET  /api/status              # Get current status
POST /api/trigger             # Run unsubscribes now
GET  /api/pending             # Get pending rows
```

## See Also

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup instructions
- **CleverTap API** - https://docs.clevertap.com/

---

Built with ❤️ for automated unsubscribe management
