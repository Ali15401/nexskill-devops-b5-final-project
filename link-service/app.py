import os
import boto3
import json
import psycopg2
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import hashlib
import requests
from prometheus_flask_exporter import PrometheusMetrics  # For monitoring
from datetime import datetime

# --- Application Setup ---
app = Flask(__name__)
# Secure CORS only for specific origins in production
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")  # Default to "*"
CORS(app, origins=ALLOWED_ORIGINS)  # Allow only specified origins

# --- Monitoring Setup ---
metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter(
    'url_shorten_requests', 
    'Number of requests to the shorten URL endpoint'
)

# --- Database Connection Function ---
def get_db_connection():
    try:
        # Fetch environment variables
        aws_region = os.environ.get('AWS_REGION')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        db_host = os.environ.get('DB_HOST')

        # Fetch database credentials from AWS Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        db_password = secret_data['password']

        # Establish connection to the PostgreSQL database
        conn = psycopg2.connect(
            host=db_host,
            database="projectdb",
            user="projectadmin",
            password=db_password
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")

# --- Helper Functions ---
# Generate a short URL from the original URL
def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

# Initialize the database (to create tables)
def init_db():
    try:
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
    except Exception as e:
        raise Exception(f"Database initialization error: {str(e)}")

# --- API Endpoints ---
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint to monitor service availability."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/shorten', methods=['POST'])
@url_shorten_counter.count_exceptions()  # Increment metric even for exceptions
def shorten_url():
    """Shorten a URL and return the short code."""
    data = request.json
    original_url = data.get('url')
    
    if not original_url:
        return

