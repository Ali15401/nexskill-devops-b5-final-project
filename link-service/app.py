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
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*") # Good for testing, can be restricted later
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}}, supports_credentials=True)

metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter("url_shorten_requests", "Number of requests to shorten URL")
redirect_counter = metrics.counter("url_redirect_requests", "Number of requests to redirect")

# -----------------------------------------------------------------------------
# AWS Clients
# -----------------------------------------------------------------------------
aws_region = os.environ.get("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=aws_region)
cloudwatch_client = boto3.client("cloudwatch", region_name=aws_region)
ssm_client = boto3.client("ssm", region_name=aws_region)

# -----------------------------------------------------------------------------
# Configuration from Environment Variables
# -----------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD") # Injected by ECS 'secrets'
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")
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
                        id SERIAL PRIMARY KEY,
                        short_code VARCHAR(16) UNIQUE NOT NULL,
                        original_url TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS link_clicks (
                        id SERIAL PRIMARY KEY,
                        short_code VARCHAR(16) NOT NULL,
                        clicked_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
            conn.close()
            print("Database tables checked/created successfully.")
            return True # Success
        except Exception as e:
            print(f"DB connection failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    # If all retries fail, raise an error to stop the application
    raise RuntimeError("Could not connect to the database after multiple retries.")

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

# -----------------------------------------------------------------------------
# Flask Routes
# -----------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}), 200

@app.route("/api/links", methods=["GET"])
def get_links():
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT short_code, original_url, created_at FROM links ORDER BY created_at DESC LIMIT 100")
            rows = cur.fetchall()
        conn.close()
        return jsonify({"links": [dict(row) for row in rows]}), 200 # Ensure JSON serializable
    except Exception as e:
        print(f"get_links error: {e}")
        return jsonify({"links": [], "error": str(e)}), 500

@app.route("/api/shorten", methods=["POST"])
@url_shorten_counter.count_exceptions()
def shorten_url():
    try:
        payload = request.get_json(silent=True) or {}
        original_url = payload.get("url")
        if not original_url:
            return jsonify({"error": "Missing 'url' in request body"}), 400

        short_code = make_short_code(original_url)
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("INSERT INTO links (short_code, original_url) VALUES (%s, %s)", (short_code, original_url))
        conn.close()

        short_url = f"/{short_code}"
        if BASE_URL:
            short_url = f"{BASE_URL.rstrip('/')}/{short_code}"

        log_to_cloudwatch("ShortenRequests", 1)
        return jsonify({"short_code": short_code, "short_url": short_url}), 201
    except Exception as e:
        print(f"shorten_url error: {e}")
        log_to_cloudwatch("ShortenErrors", 1)
        return jsonify({"error": str(e)}), 500

@app.route("/<short_code>", methods=["GET"])
@redirect_counter.count_exceptions()
def redirect_url(short_code):
    try:
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT original_url FROM links WHERE short_code = %s", (short_code,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": "Not found"}), 404
            
            original_url = row[0]
            cur.execute("INSERT INTO link_clicks (short_code) VALUES (%s)", (short_code,))
        conn.close()
        return redirect(original_url, code=302)
    except Exception as e:
        print(f"redirect_url error: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Startup Logic
# -----------------------------------------------------------------------------
if __name__ != "__main__":
    # This block runs when Gunicorn starts the app.
    # We run the table check here. If it fails after all retries, the app will crash,
    # and the "Worker failed to boot" error will have a clear cause in the logs.
    ensure_tables_with_retry()

