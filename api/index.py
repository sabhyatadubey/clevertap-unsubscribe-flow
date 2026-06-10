import os
import json
import time
import base64
import logging
import requests
from flask import Flask, render_template_string, redirect, url_for, jsonify, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('unsubscribe-flow')

app = Flask(__name__)
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
    except Exception:
        logger.exception('Failed to build Google Sheets service - check SERVICE_ACCOUNT_JSON_BASE64')
        return None

def get_unsubscribe_stats():
    try:
        sheets = get_sheets_service()
        sheet_id = os.getenv('SHEET_ID')
        if not sheets or not sheet_id:
            logger.warning('Sheets service or SHEET_ID unavailable - returning empty stats')
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
            if len(row) >= 2:
                status = row[3] if len(row) > 3 else 'Not Updated'
                if status.lower() == 'updated':
                    completed += 1
                else:
                    pending += 1
                activity.append({
                    'email': row[1],
                    'channel': row[2] if len(row) > 2 else '',
                    'status': status
                })

        return {
            'total_pending': pending,
            'completed': completed,
            'activity': activity,
            'recent': activity[-10:]
        }
    except Exception:
        logger.exception('Failed to read stats from Google Sheet')
        return {'total_pending': 0, 'completed': 0, 'activity': [], 'recent': []}

def send_to_clevertap(cust_id, channel, max_attempts=3):
    project_id = os.getenv('CLEVERTAP_PROJECT_ID')
    passcode = os.getenv('CLEVERTAP_PASSCODE')
    if not project_id or not passcode:
        logger.error('CLEVERTAP_PROJECT_ID or CLEVERTAP_PASSCODE not set')
        return False
    url = 'https://api.clevertap.com/1/upload'
    try:
        payload = {
            'd': [{
                'customer_id': int(cust_id),
                'unsubscribe': {channel.lower(): 1}
            }]
        }
    except (ValueError, TypeError):
        logger.error('Invalid cust_id %r - must be numeric', cust_id)
        return False
    headers = {
        'X-CleverTap-Account-ID': project_id,
        'X-CleverTap-Passcode': passcode,
        'Content-Type': 'application/json'
    }
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info('CleverTap unsubscribe OK for cust_id=%s channel=%s', cust_id, channel)
                return True
            logger.warning('CleverTap returned %s for cust_id=%s (attempt %d/%d): %s',
                           response.status_code, cust_id, attempt, max_attempts, response.text[:200])
            if 400 <= response.status_code < 500:
                return False
        except requests.RequestException:
            logger.exception('CleverTap request failed for cust_id=%s (attempt %d/%d)',
                             cust_id, attempt, max_attempts)
        if attempt < max_attempts:
            time.sleep(2 ** (attempt - 1))
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
    except Exception:
        logger.exception('Failed to update sheet status for cust_id=%s', cust_id)
        return False

def render_dashboard_html(email, total_pending, completed, activity):
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>CleverTap Unsubscribe</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 36px; font-weight: bold; color: #667eea; margin: 10px 0; }
        .stat-label { font-size: 14px; color: #666; }
        .content-card { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .content-card h2 { margin-bottom: 20px; color: #333; font-size: 20px; }
        .btn { background: #667eea; color: white; padding: 12px 30px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .btn:hover { background: #5568d3; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: bold; color: #333; }
        .status-updated { background: #d4edda; color: #155724; padding: 4px 12px; border-radius: 4px; display: inline-block; font-weight: bold; }
        .status-pending { background: #fff3cd; color: #856404; padding: 4px 12px; border-radius: 4px; display: inline-block; font-weight: bold; }
        .user-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; color: white; }
        .user-section a { background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CleverTap Unsubscribe Flow</h1>
            <p>Automated unsubscribe management for your customers</p>
        </div>

        <div class="user-section">
            <div>''' + email + '''</div>
            <a href="/logout">Sign Out</a>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">TOTAL PENDING</div>
                <div class="stat-number">''' + str(total_pending) + '''</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">COMPLETED</div>
                <div class="stat-number">''' + str(completed) + '''</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">NEXT RUN</div>
                <div class="stat-number" style="font-size: 18px;">Friday 5 PM</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">SCHEDULER STATUS</div>
                <div style="font-size: 20px; margin: 10px 0;">🟢 Running</div>
            </div>
        </div>

        <div class="content-card">
            <h2>Manual Trigger</h2>
            <button class="btn" onclick="runNow()">Run Now</button>
            <div id="status" style="margin-top: 15px;"></div>
        </div>

        <div class="content-card">
            <h2>📋 Recent Activity</h2>
            <table>
                <thead><tr><th>Email</th><th>Channel</th><th>Status</th></tr></thead>
                <tbody>'''
    for item in activity:
        status_class = 'status-updated' if item['status'].lower() == 'updated' else 'status-pending'
        html += f'''<tr><td>{item['email']}</td><td>{item['channel']}</td><td><span class="{status_class}">{item['status']}</span></td></tr>'''
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function runNow() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Processing...';
            fetch('/api/trigger', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').innerHTML = '<p style="color: green; font-weight: bold;">✓ ' + data.message + '</p>';
                    btn.disabled = false;
                    btn.textContent = 'Run Now';
                    setTimeout(() => location.reload(), 2000);
                })
                .catch(e => {
                    document.getElementById('status').innerHTML = '<p style="color: red; font-weight: bold;">✗ Error</p>';
                    btn.disabled = false;
                    btn.textContent = 'Run Now';
                });
        }
    </script>
</body>
</html>'''
    return html

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

@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_unsubscribe_stats()
    html = render_dashboard_html(
        current_user.email,
        stats['total_pending'],
        stats['completed'],
        stats.get('recent', [])
    )
    return html

def process_pending_unsubscribes():
    stats = get_unsubscribe_stats()
    pending_rows = [row for row in stats.get('activity', []) if row['status'].lower() != 'updated']
    logger.info('Processing %d pending unsubscribes', len(pending_rows))
    processed = 0
    failed = 0
    for item in pending_rows:
        cust_id = item['email']
        channel = item['channel']
        if send_to_clevertap(cust_id, channel) and update_sheet_status(cust_id, 'Updated'):
            processed += 1
        else:
            failed += 1
    logger.info('Run complete: %d processed, %d failed', processed, failed)
    return processed, failed

@app.route('/api/trigger', methods=['POST'])
@login_required
def trigger():
    processed, failed = process_pending_unsubscribes()
    return jsonify({
        'message': f'Success! {processed} processed, {failed} failed',
        'processed': processed,
        'failed': failed
    }), 200

@app.route('/api/cron', methods=['GET', 'POST'])
def cron():
    cron_secret = os.getenv('CRON_SECRET')
    auth_header = request.headers.get('Authorization', '')
    if not cron_secret or auth_header != f'Bearer {cron_secret}':
        logger.warning('Unauthorized cron request')
        return jsonify({'error': 'Unauthorized'}), 401
    processed, failed = process_pending_unsubscribes()
    return jsonify({'processed': processed, 'failed': failed}), 200

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
