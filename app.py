import os
import logging
import base64
import json
import requests
from datetime import datetime
from flask import Flask, jsonify, url_for, redirect, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

logger.info("[STARTUP] App initialized")

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Google Sheets Helper
def get_sheets_service():
    """Get authorized Google Sheets service using service account"""
    service_account_json_b64 = os.getenv('SERVICE_ACCOUNT_JSON_BASE64')
    if not service_account_json_b64:
        return None

    try:
        service_account_json = base64.b64decode(service_account_json_b64).decode('utf-8')
        service_account_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        logger.error(f"Error getting Sheets service: {e}")
        return None

def get_pending_unsubscribes():
    """Read pending unsubscribe requests from Google Sheets"""
    sheets_service = get_sheets_service()
    if not sheets_service:
        return []

    try:
        sheet_id = os.getenv('SHEET_ID')
        if not sheet_id:
            return []

        # Read from Sheet1 (assuming format: Email | Channel | Status)
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='Sheet1!A2:D'
        ).execute()

        rows = result.get('values', [])
        unsubscribes = []

        for row in rows:
            if len(row) >= 3:
                unsubscribes.append({
                    'email': row[0],
                    'channel': row[1],
                    'status': row[2],
                    'user_id': row[3] if len(row) > 3 else ''
                })

        return unsubscribes
    except Exception as e:
        logger.error(f"Error reading Google Sheets: {e}")
        return []

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return {'message': 'App is running - OAuth ready!'}, 200

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        email = user_info.get('email', '') if user_info else 'Unknown'

        # Check if email is @justlife.com
        if not email.endswith('@justlife.com'):
            return {'error': 'Access denied: Only @justlife.com emails allowed'}, 403

        # Create user session
        user = User(email)
        login_user(user)

        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        return {'error': str(e)}, 400

@app.route('/dashboard')
@login_required
def dashboard():
    pending = get_pending_unsubscribes()
    return render_template('dashboard.html', email=current_user.email, pending=pending)

def send_to_clevertap(email, channel, user_id=''):
    """Send unsubscribe request to CleverTap"""
    try:
        project_id = os.getenv('CLEVERTAP_PROJECT_ID')
        passcode = os.getenv('CLEVERTAP_PASSCODE')

        if not project_id or not passcode:
            logger.error("CleverTap credentials not set")
            return False

        url = 'https://api.clevertap.com/1/upload'

        # CleverTap unsubscribe payload
        payload = {
            'd': [{
                'email': email,
                'unsubscribe': {
                    channel: 1  # 1 = unsubscribed
                }
            }]
        }

        headers = {
            'X-CleverTap-Account-ID': project_id,
            'X-CleverTap-Passcode': passcode,
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info(f"[CLEVERTAP] Successfully unsubscribed {email} from {channel}")
            return True
        else:
            logger.error(f"[CLEVERTAP] Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"[CLEVERTAP] Error: {e}")
        return False

def update_sheet_status(email, status):
    """Update status in Google Sheets for processed email"""
    try:
        sheets_service = get_sheets_service()
        if not sheets_service:
            return False

        sheet_id = os.getenv('SHEET_ID')
        if not sheet_id:
            return False

        # Read all rows to find matching email
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='Sheet1!A2:D'
        ).execute()

        rows = result.get('values', [])

        for idx, row in enumerate(rows):
            if len(row) > 0 and row[0] == email:
                # Update status in row (idx+2 because row 1 is header, idx is 0-based)
                row_num = idx + 2
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f'Sheet1!C{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()
                logger.info(f"[SHEETS] Updated {email} status to '{status}'")
                return True

        return False
    except Exception as e:
        logger.error(f"[SHEETS] Update error: {e}")
        return False

@app.route('/api/trigger', methods=['POST'])
@login_required
def trigger():
    """Manually trigger unsubscribe processing"""
    try:
        pending = get_pending_unsubscribes()
        processed = 0
        failed = 0

        for item in pending:
            if item['status'].lower() != 'updated':
                email = item['email']
                channel = item['channel']

                # Send to CleverTap
                if send_to_clevertap(email, channel, item.get('user_id', '')):
                    # Update sheet status
                    if update_sheet_status(email, 'Updated'):
                        processed += 1
                    else:
                        failed += 1
                else:
                    failed += 1

        return jsonify({
            'message': f'Processing complete. {processed} processed, {failed} failed.',
            'processed': processed,
            'failed': failed
        }), 200
    except Exception as e:
        logger.error(f"[TRIGGER] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    port = int(os.getenv('PORT', 8000))
    logger.info(f"[STARTUP] Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
