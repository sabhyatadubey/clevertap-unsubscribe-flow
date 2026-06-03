import os
import json
import base64
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

logger.info("[STARTUP] Flask app initialized")

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

logger.info("[STARTUP] OAuth initialized")

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
ALLOWED_EMAILS = os.getenv('ALLOWED_EMAILS', '').split(',') if os.getenv('ALLOWED_EMAILS') else []
logger.info(f"[STARTUP] Allowed emails: {ALLOWED_EMAILS}")

# Routes
@app.route('/login')
def login():
    """Redirect to Google OAuth"""
    logger.info("[LOGIN] User clicked login")
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    try:
        logger.info("[AUTHORIZE] Processing OAuth callback")
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            logger.error("[AUTHORIZE] No user info from Google")
            return redirect(url_for('login'))

        email = user_info.get('email', '')
        logger.info(f"[AUTHORIZE] User email: {email}")

        # Check if email is allowed
        if ALLOWED_EMAILS:
            is_allowed = any(email.endswith(domain.strip()) for domain in ALLOWED_EMAILS)
            logger.info(f"[AUTHORIZE] Is allowed: {is_allowed}")
            if not is_allowed:
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
        logger.info(f"[AUTHORIZE] User {email} logged in successfully")
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"[AUTHORIZE] Error: {e}", exc_info=True)
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    logger.info("[LOGOUT] User logged out")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Dashboard page"""
    logger.info(f"[DASHBOARD] User {current_user.email} accessed dashboard")
    return render_template('dashboard.html', user=current_user)

@app.route('/health')
def health():
    """Health check"""
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    logger.info("[STARTUP] Starting Flask app")
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    port = int(os.getenv('PORT', 8000))
    logger.info(f"[STARTUP] Mode: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    app.run(host='0.0.0.0', port=port, debug=False)
