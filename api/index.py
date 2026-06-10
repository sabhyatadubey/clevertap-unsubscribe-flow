import os
import json
import base64
import requests
from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Proper path handling for Vercel
import sys
from pathlib import Path
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'localhost' in request.host or '127.0.0.1' in request.host:
        login_user(User('sabhy@justlife.com'))
        return redirect(url_for('dashboard'))
    return google.authorize_redirect(url_for('authorize', _external=True, _scheme='https'))

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        email = token.get('userinfo', {}).get('email', '')
        if not email.endswith('@justlife.com'):
            return {'error': 'Access denied'}, 403
        login_user(User(email))
        return redirect(url_for('dashboard'))
    except Exception as e:
        return {'error': str(e)}, 400

def get_sheets_service():
    try:
        service_account_json_b64 = os.getenv('SERVICE_ACCOUNT_JSON_BASE64')
        if not service_account_json_b64:
            return None
        service_account_json = base64.b64decode(service_account_json_b64).decode('utf-8')
        service_account_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        return None

def get_unsubscribe_stats():
    try:
        sheets = get_sheets_service()
        sheet_id = os.getenv('SHEET_ID')
        if not sheets or not sheet_id:
            return {'total_pending': 0, 'completed': 0, 'activity': []}

        result = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='Sheet1!A2:D'
        ).execute()

        rows = result.get('values', [])
        pending = 0
        completed = 0
        activity = []

        for row in rows:
            if len(row) >= 4:
                status = row[3] if len(row) > 3 else 'Not Updated'
                if status.lower() == 'updated':
                    completed += 1
                else:
                    pending += 1
                activity.append({
                    'email': row[1] if len(row) > 1 else '',
                    'channel': row[2] if len(row) > 2 else '',
                    'status': status
                })

        return {
            'total_pending': pending,
            'completed': completed,
            'activity': activity[-10:]
        }
    except Exception as e:
        return {'total_pending': 0, 'completed': 0, 'activity': []}

@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_unsubscribe_stats()
    return render_template('dashboard.html', email=current_user.email, **stats)

def send_to_clevertap(cust_id, channel):
    try:
        project_id = os.getenv('CLEVERTAP_PROJECT_ID')
        passcode = os.getenv('CLEVERTAP_PASSCODE')

        if not project_id or not passcode:
            return False

        url = 'https://api.clevertap.com/1/upload'

        payload = {
            'd': [{
                'customer_id': int(cust_id),
                'unsubscribe': {
                    channel.lower(): 1
                }
            }]
        }

        headers = {
            'X-CleverTap-Account-ID': project_id,
            'X-CleverTap-Passcode': passcode,
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False

def update_sheet_status(cust_id, new_status='Updated'):
    try:
        sheets = get_sheets_service()
        sheet_id = os.getenv('SHEET_ID')
        if not sheets or not sheet_id:
            return False

        result = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='Sheet1!A2:D'
        ).execute()

        rows = result.get('values', [])

        for idx, row in enumerate(rows):
            if len(row) > 1 and str(row[1]) == str(cust_id):
                row_num = idx + 2
                sheets.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f'Sheet1!D{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[new_status]]}
                ).execute()
                return True

        return False
    except Exception as e:
        return False

@app.route('/api/trigger', methods=['POST'])
def trigger():
    if not current_user.is_authenticated:
        return {'error': 'Unauthorized'}, 401

    try:
        stats = get_unsubscribe_stats()
        pending_rows = [row for row in stats.get('activity', []) if row['status'].lower() != 'updated']

        processed = 0
        failed = 0

        for item in pending_rows:
            cust_id = item['email']
            channel = item['channel']

            if send_to_clevertap(cust_id, channel):
                if update_sheet_status(cust_id, 'Updated'):
                    processed += 1
                else:
                    failed += 1
            else:
                failed += 1

        return jsonify({
            'message': f'Success! {processed} processed, {failed} failed',
            'processed': processed,
            'failed': failed
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)), debug=False)
