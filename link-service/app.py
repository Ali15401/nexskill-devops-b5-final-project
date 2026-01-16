import os
import boto3
import json
import psycopg2
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import hashlib
import requests
from prometheus_flask_exporter import PrometheusMetrics # For monitoring

# --- Application Setup ---

app = Flask(__name__)
CORS(app)

# --- NEW: Monitoring Setup ---
# This creates the /metrics endpoint for Prometheus
metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter(
    'url_shorten_requests', 
    'Number of requests to the shorten URL endpoint'
)
# ---------------------------

# --- Database Connection Function (Corrected for AWS) ---

def get_db_connection():
    # These variables are injected by the ECS Task Definition in Terraform
    aws_region = os.environ.get('AWS_REGION')
    secret_arn = os.environ.get('DB_SECRET_ARN')
    db_host = os.environ.get('DB_HOST')

    # Fetch the password from AWS Secrets Manager
    secrets_client = boto3.client('secretsmanager', region_name=aws_region)
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    db_password = json.loads(secret_response['SecretString'])['password']

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        host=db_host,
        database="projectdb",
        user="projectadmin",
        password=db_password
    )
    return conn

# --- Database Initialization (To be run once) ---
# This is a helper function. In a real app, you'd run this from a separate script.
def init_db():
    conn = get_db_connection()
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
    conn.close()

# --- Helper Function ---
def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.json
    original_url = data.get('url')
    
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    
    # NEW: Increment the monitoring counter
    url_shorten_counter.inc()
    
    short_code = generate_short_code(original_url)
    
    try:
        conn = get_db_connection()
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
        conn.close()
        
        return jsonify({'short_code': short_code, 'short_url': f'/{short_code}'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'SELECT original_url FROM links WHERE short_code = %s',
            (short_code,)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'URL not found'}), 404
            
        original_url = result[0]
        # We will ignore the analytics service for now to keep things simple
        return redirect(original_url)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/links', methods=['GET'])
def get_all_links():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT original_url, short_code, created_at FROM links ORDER BY created_at DESC')
        links = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([{'original_url': link[0], 'short_code': link[1], 'created_at': link[2].isoformat()} for link in links]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Gunicorn runs the 'app' object, so this __main__ block is not used in ECS
if __name__ == '__main__':
    # This is for local testing only
    # You would need to set the environment variables locally for this to work
    init_db()
    # The PORT is set by Gunicorn in the Dockerfile CMD, not here
    app.run(host='0.0.0.0', port=5001)
