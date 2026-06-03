import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

logger.info("[STARTUP] App initialized")

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/')
def index():
    return {'message': 'App is running - Step 1 complete!'}, 200

if __name__ == '__main__':
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    port = int(os.getenv('PORT', 8000))
    logger.info(f"[STARTUP] Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
