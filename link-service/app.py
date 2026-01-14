from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
import hashlib
import requests
from config import Config  # It now correctly imports from the config.py we just made
import logging
import os
import signal
from contextlib import contextmanager
import boto3  # Ensure boto3 is imported
import json   # Ensure json is imported

app = Flask(__name__)
CORS(app)

# Logging setup
log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger("link-service")

db_pool = None

# --- THIS FUNCTION IS NOW CORRECTED ---
def init_db_pool():
    global db_pool
    if db_pool is None:
        logger.info("Initializing DB connection pool")
        
        # Step 1: Fetch the password from AWS Secrets Manager using the ARN from config
        secrets_client = boto3.client('secretsmanager', region_name=Config.AWS_REGION)
        secret_response = secrets_client.get_secret_value(SecretId=Config.DB_SECRET_ARN)
        db_password = json.loads(secret_response['SecretString'])['password']

        # Step 2: Create the connection pool using the fetched password
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=int(os.environ.get("DB_POOL_MAX", 10)),
            host=Config.DATABASE_HOST,
            port=Config.DATABASE_PORT,
            database=Config.DATABASE_NAME,
            user=Config.DATABASE_USER,
            password=db_password  # Use the password we fetched from Secrets Manager
        )
    return db_pool

@contextmanager
def get_db_conn():
    pool_ref = init_db_pool()
    conn = pool_ref.getconn()
    try:
        yield conn
    finally:
        try:
            pool_ref.putconn(conn)
        except Exception as e:
            logger.exception("Error returning connection to pool: %s", e)

# The rest of your app.py file remains exactly the same...
# (init_db, generate_short_code, health, shorten_url, redirect_url, etc.)

def init_db():
    logger.info("Initializing DB schema if needed")
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id SERIAL PRIMARY KEY,
                original_url TEXT NOT NULL,
                short_code VARCHAR(10) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
    logger.info("DB init complete")

def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json(silent=True) or {}
    original_url = data.get('url')
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    short_code = generate_short_code(original_url)
    try:
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT short_code FROM links WHERE original_url = %s', (original_url,))
            existing = cur.fetchone()
            if existing:
                short_code = existing[0]
            else:
                cur.execute(
                    'INSERT INTO links (original_url, short_code) VALUES (%s, %s)',
                    (original_url, short_code)
                )
                conn.commit()
            cur.close()
        short_url = f'/{short_code}'
        return jsonify({'short_code': short_code, 'short_url': short_url}), 201
    except Exception as e:
        logger.exception("Error shortening URL: %s", e)
        return jsonify({'error': 'internal error'}), 500

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    try:
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT original_url FROM links WHERE short_code = %s', (short_code,))
            result = cur.fetchone()
            cur.close()
        if result:
            original_url = result[0]
            try:
                requests.post(
                    f'{Config.ANALYTICS_SERVICE_URL}/api/track',
                    json={'short_code': short_code},
                    timeout=2
                )
            except Exception:
                logger.debug("Analytics tracking failed for %s", short_code, exc_info=True)
            return redirect(original_url)
        else:
            return jsonify({'error': 'URL not found'}), 404
    except Exception as e:
        logger.exception("Error redirecting short code %s: %s", short_code, e)
        return jsonify({'error': 'internal error'}), 500

@app.route('/api/links', methods=['GET'])
def get_all_links():
    try:
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT original_url, short_code, created_at FROM links ORDER BY created_at DESC')
            links = cur.fetchall()
            cur.close()
        return jsonify([{'original_url': link[0], 'short_code': link[1], 'created_at': link[2].isoformat()} for link in links]), 200
    except Exception as e:
        logger.exception("Error fetching links: %s", e)
        return jsonify({'error': 'internal error'}), 500

def shutdown_pool(signum, frame):
    global db_pool
    logger.info("Received signal %s - closing DB pool", signum)
    try:
        if db_pool:
            db_pool.closeall()
            logger.info("DB pool closed")
    except Exception:
        logger.exception("Error closing DB pool")

signal.signal(signal.SIGTERM, shutdown_pool)
signal.signal(signal.SIGINT, shutdown_pool)

if __name__ == '__main__':
    init_db_pool()
    init_db()
    port = int(os.environ.get("PORT", Config.PORT))
    app.run(host='0.0.0.0', port=port, debug=False)
