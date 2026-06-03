from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from authlib.integrations.flask_client import OAuth
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    user_data = session.get('user_data')
    if user_data and user_data.get('id') == user_id:
        return User(user_data['id'], user_data['email'], user_data['name'])
    return None

# Configuration
CLEVERTAP_PROJECT_ID = os.getenv('CLEVERTAP_PROJECT_ID', 'RKW-W4K-KK6Z')
CLEVERTAP_PASSCODE = os.getenv('CLEVERTAP_PASSCODE', 'EHW-QAB-GLUL')
SHEET_ID = os.getenv('SHEET_ID', '11-gmht1OU586CE3kCak4pj7uug8LAZcITjX0OShgD9M')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
ALLOWED_EMAILS = os.getenv('ALLOWED_EMAILS', '').split(',') if os.getenv('ALLOWED_EMAILS') else []

# Global state
unsubscribe_log = []
scheduler = BackgroundScheduler()

def load_service_account_credentials():
    """Load service account credentials from file or environment variable"""
    try:
        # First, try to load from file (for local development)
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"[INIT] Loading service account from file: {SERVICE_ACCOUNT_FILE}")
            return service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        # If file doesn't exist, try to load from environment variable
        service_account_json = os.getenv('SERVICE_ACCOUNT_JSON')
        if service_account_json:
            print("[INIT] Loading service account from SERVICE_ACCOUNT_JSON environment variable")
            print(f"[INIT] JSON length: {len(service_account_json)} characters")
            try:
                service_account_dict = json.loads(service_account_json)
                print("[INIT] ✓ Successfully parsed SERVICE_ACCOUNT_JSON")
                creds = service_account.Credentials.from_service_account_info(
                    service_account_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                print("[INIT] ✓ Successfully created credentials from service account")
                return creds
            except json.JSONDecodeError as e:
                print(f"[INIT] ✗ JSON parsing error: {e}")
                print(f"[INIT] First 200 chars of JSON: {service_account_json[:200]}")
                return None
            except Exception as e:
                print(f"[INIT] ✗ Error creating credentials: {e}")
                import traceback
                traceback.print_exc()
                return None

        print("[INIT] ✗ ERROR: SERVICE_ACCOUNT_JSON not set and file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    except Exception as e:
        print(f"[INIT] ✗ Unexpected error loading service account: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_sheets_service():
    """Initialize Google Sheets service"""
    try:
        creds = load_service_account_credentials()
        if not creds:
            return None
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"Error initializing Sheets service: {e}")
        return None

def read_sheet_data():
    """Read unsubscribe data from Google Sheet"""
    try:
        service = get_sheets_service()
        if not service:
            return []

        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Sheet1!A:D'
        ).execute()

        values = result.get('values', [])
        if not values:
            return []

        # Skip header row
        data = []
        for i, row in enumerate(values[1:], start=2):
            if len(row) >= 4:
                data.append({
                    'row': i,
                    'date': row[0],
                    'cust_id': row[1],
                    'channel': row[2],
                    'status': row[3]
                })

        return data
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []

def unsubscribe_from_clevertap(cust_id, channel):
    """Call CleverTap API to unsubscribe user"""
    try:
        url = 'https://api.clevertap.com/1/upload'

        headers = {
            'X-CleverTap-Account-Id': CLEVERTAP_PROJECT_ID,
            'X-CleverTap-Passcode': CLEVERTAP_PASSCODE,
            'Content-Type': 'application/json; charset=utf-8'
        }

        # Unsubscribe from the subscription groups
        payload = {
            'd': [
                {
                    'identity': str(cust_id),
                    'type': 'profile',
                    'profileData': {
                        'category-unsubscribe': {
                            'email': ['Product Updates']
                        }
                    }
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            return True, "Success"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        return False, str(e)

def update_sheet_status(row_num, status, message=""):
    """Update sheet with status and timestamp"""
    try:
        service = get_sheets_service()
        if not service:
            return False

        status_text = status

        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f'Sheet1!D{row_num}',
            valueInputOption='USER_ENTERED',
            body={'values': [[status_text]]}
        ).execute()

        return True
    except Exception as e:
        print(f"Error updating sheet: {e}")
        return False

def process_unsubscribes():
    """Process all pending unsubscribes"""
    global unsubscribe_log
    unsubscribe_log = []

    print(f"[{datetime.now()}] Starting unsubscribe process...")

    data = read_sheet_data()

    for item in data:
        # Only process rows with "Not Updated" status
        if 'Not Updated' in item['status']:
            cust_id = item['cust_id']
            channel = item['channel']

            print(f"Processing: Cust ID {cust_id}, Channel: {channel}")

            success, message = unsubscribe_from_clevertap(cust_id, channel)

            if success:
                update_sheet_status(item['row'], 'Updated')
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'cust_id': cust_id,
                    'channel': channel,
                    'status': 'Success',
                    'message': message
                }
            else:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'cust_id': cust_id,
                    'channel': channel,
                    'status': 'Failed',
                    'message': message
                }

            unsubscribe_log.append(log_entry)

    print(f"[{datetime.now()}] Unsubscribe process completed. Processed {len(unsubscribe_log)} rows.")

def schedule_friday_eod():
    """Schedule unsubscribe process for Friday at EOD (5 PM)"""
    scheduler.add_job(
        process_unsubscribes,
        'cron',
        day_of_week='fri',
        hour=17,
        minute=0,
        id='friday_eod_unsubscribe',
        name='Friday EOD Unsubscribe'
    )
    print("Scheduled: Friday EOD (5 PM) unsubscribe job")

@app.route('/login')
def login():
    """Redirect to Google OAuth"""
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            return redirect(url_for('login'))

        email = user_info.get('email', '')

        # Check if email is allowed
        if ALLOWED_EMAILS and not any(email.endswith(domain) for domain in ALLOWED_EMAILS):
            return render_template('unauthorized.html', email=email), 403

        user = User(
            id=user_info.get('sub'),
            email=email,
            name=user_info.get('name', '')
        )

        session['user_data'] = {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }

        login_user(user)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Authorization error: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html', user=current_user)

@app.route('/api/status')
@login_required
def get_status():
    """Get current status and logs"""
    data = read_sheet_data()
    not_updated = [d for d in data if 'Not Updated' in d['status']]
    updated = [d for d in data if 'Updated' in d['status']]

    return jsonify({
        'total_rows': len(data),
        'pending': len(not_updated),
        'completed': len(updated),
        'recent_logs': unsubscribe_log[-10:] if unsubscribe_log else [],
        'scheduler_running': scheduler.running,
        'next_run': str(scheduler.get_job('friday_eod_unsubscribe').next_run_time) if scheduler.get_job('friday_eod_unsubscribe') else 'Not scheduled'
    })

@app.route('/api/trigger', methods=['POST'])
@login_required
def trigger_unsubscribe():
    """Manually trigger unsubscribe process"""
    process_unsubscribes()
    return jsonify({
        'status': 'success',
        'message': f'Processed {len(unsubscribe_log)} rows',
        'logs': unsubscribe_log
    })

@app.route('/api/pending')
@login_required
def get_pending():
    """Get pending unsubscribes"""
    data = read_sheet_data()
    pending = [d for d in data if 'Not Updated' in d['status']]
    return jsonify(pending)

if __name__ == '__main__':
    print("[STARTUP] Starting CleverTap Unsubscribe Flow Flask app...")

    # Start scheduler
    try:
        schedule_friday_eod()
        scheduler.start()
        print("[STARTUP] ✓ Scheduler started successfully")
    except Exception as e:
        print(f"[STARTUP] ✗ Error starting scheduler: {e}")
        import traceback
        traceback.print_exc()

    # Determine environment
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    debug_mode = not is_production

    print(f"[STARTUP] Environment: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")

    if is_production:
        # Production: Railway will handle port via PORT env var
        port = int(os.getenv('PORT', 8000))
        print(f"[STARTUP] Starting Flask on 0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development: localhost
        print(f"[STARTUP] Starting Flask in debug mode on localhost:8000")
        app.run(debug=True, port=8000)
