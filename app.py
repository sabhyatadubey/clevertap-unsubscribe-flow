import os
import logging
from flask import Flask, jsonify, url_for, redirect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

logger.info("[STARTUP] App initialized")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/')
def index():
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
        return {'message': f'Login successful! Email: {email}'}, 200
    except Exception as e:
        return {'error': str(e)}, 400

if __name__ == '__main__':
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    port = int(os.getenv('PORT', 8000))
    logger.info(f"[STARTUP] Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
