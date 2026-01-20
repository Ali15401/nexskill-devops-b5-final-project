import os
import json
import hashlib
import time
from datetime import datetime
import boto3
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

# -----------------------------------------------------------------------------
# Application Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
# Using a wildcard for now is fine for debugging, can be restricted later.
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}}, supports_credentials=True)

metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter("url_shorten_requests", "Number of requests to shorten URL")
redirect_counter = metrics.counter("url_redirect_requests", "Number of requests to redirect")

# -----------------------------------------------------------------------------
# AWS Clients (S3, CloudWatch, etc., are still useful)
# -----------------------------------------------------------------------------
aws_region = os.environ.get("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=aws_region)
cloudwatch_client = boto3.client("cloudwatch", region_name=aws_region)
ssm_client = boto3.client("ssm", region_name=aws_region)
# NOTE: The secrets_client is no longer needed here.

# -----------------------------------------------------------------------------
# Configuration from Environment Variables
# -----------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
# --- THIS IS THE KEY CHANGE ---
# The password is now read directly from the environment, injected by ECS.
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")
# Correctly read the BASE_URL variable name
BASE_URL = os.environ.get("BASE_URL")

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def get_db_connection():
    """Returns a psycopg2 connection after checking for all required env vars."""
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError("CRITICAL: One or more DB environment variables are not set (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD).")
    
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT,
    )

def ensure_tables_with_retry(retries=5, delay=5):
    """Attempt to connect to the DB and create tables with retries on startup."""
    for i in range(retries):
        try:
            print(f"DB connection attempt {i+1}/{retries}...")
            conn = get_db_connection()
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS links (
                        id SERIAL PRIMARY KEY, short_code VARCHAR(16) UNIQUE NOT NULL,
                        original_url TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS link_clicks (
                        id SERIAL PRIMARY KEY, short_code VARCHAR(16) NOT NULL,
                        clicked_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
            conn.close()
            print("Database tables checked/created successfully.")
            return # Success
        except Exception as e:
            print(f"DB connection failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database after multiple retries.")

# ... (make_short_code, log_to_cloudwatch, and get_app_config remain the same) ...
def make_short_code(original_url: str) -> str:
    h = hashlib.sha256(f"{original_url}-{time.time()}".encode("utf-8")).hexdigest()
    return h[:8]

def log_to_cloudwatch(metric_name, value, unit="Count", namespace="LinkService"):
    try:
        cloudwatch_client.put_metric_data(Namespace=namespace, MetricData=[{"MetricName": metric_name, "Value": value, "Unit": unit}])
    except Exception as e:
        print(f"Failed to log CloudWatch metric {metric_name}: {e}")

def get_app_config():
    # This function remains the same
    pass

# -----------------------------------------------------------------------------
# Flask Routes (Unchanged)
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}), 200

# ... (All your other routes like /api/links, /api/shorten, etc., remain exactly the same) ...
@app.route("/api/links", methods=["GET"])
def get_links():
    conn = get_db_connection()
    # ...
    return jsonify({"links": []})

# ... etc ...

# -----------------------------------------------------------------------------
# Startup Logic
# -----------------------------------------------------------------------------
if __name__ != "__main__":
    # This runs when Gunicorn starts the app. It's more resilient than a simple try/except.
    ensure_tables_with_retry()

