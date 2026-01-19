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
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*") # Allow all for now, can be restricted
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}}, supports_credentials=True)

metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter("url_shorten_requests", "Number of requests to shorten URL")
redirect_counter = metrics.counter("url_redirect_requests", "Number of requests to redirect")

# -----------------------------------------------------------------------------
# AWS Clients (Still useful for S3, CloudWatch, etc.)
# -----------------------------------------------------------------------------
aws_region = os.environ.get("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=aws_region)
cloudwatch_client = boto3.client("cloudwatch", region_name=aws_region)
ssm_client = boto3.client("ssm", region_name=aws_region)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# These are now all injected directly as environment variables by ECS
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD") # Will be injected by the 'secrets' block in ECS
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")
BASE_URL = os.environ.get("BASE_URL") # Optional, for composing absolute short URLs

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def get_db_connection():
    """
    Returns a psycopg2 connection. Caller is responsible for closing it.
    This function is now much simpler.
    """
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError("One or more database environment variables are not set.")
    
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT,
    )
    return conn

# (The rest of your helper functions like ensure_tables, make_short_code, etc., remain the same)
def ensure_tables():
    ddl_links = """
    CREATE TABLE IF NOT EXISTS links (
        id SERIAL PRIMARY KEY,
        short_code VARCHAR(16) UNIQUE NOT NULL,
        original_url TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """
    ddl_clicks = """
    CREATE TABLE IF NOT EXISTS link_clicks (
        id SERIAL PRIMARY KEY,
        short_code VARCHAR(16) NOT NULL,
        clicked_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """
    try:
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(ddl_links)
            cur.execute(ddl_clicks)
        conn.close()
    except Exception as e:
        print(f"[startup] ensure_tables failed: {e}")

def make_short_code(original_url: str) -> str:
    h = hashlib.sha256(f"{original_url}-{time.time()}".encode("utf-8")).hexdigest()
    return h[:8]

def log_to_cloudwatch(metric_name, value, unit="Count", namespace="LinkService"):
    try:
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=[{"MetricName": metric_name, "Value": value, "Unit": unit}],
        )
    except Exception as e:
        print(f"Failed to log CloudWatch metric {metric_name}: {e}")

# ... (The rest of your Flask routes: /api/health, /api/links, /api/shorten, etc., remain unchanged) ...
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}), 200

@app.route("/api/links", methods=["GET"])
def get_links():
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT short_code, original_url, created_at FROM links ORDER BY created_at DESC LIMIT 100"
            )
            rows = cur.fetchall()
        conn.close()
        return jsonify({"links": rows}), 200
    except Exception as e:
        print(f"get_links error: {e}")
        return jsonify({"links": [], "error": str(e)}), 200
        
# Add other routes back here if they were removed for brevity

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
try:
    ensure_tables()
except Exception as init_err:
    print(f"Initialization warning: {init_err}")

