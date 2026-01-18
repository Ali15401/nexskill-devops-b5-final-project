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
from prometheus_flask_exporter import PrometheusMetrics  # For monitoring


# -----------------------------------------------------------------------------
# Application Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)

# CORS: allow your site’s origin (configure via env ALLOWED_ORIGIN)
# Example: ALLOWED_ORIGIN=http://project-alb-1445225992.us-east-1.elb.amazonaws.com
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://project-alb-1445225992.us-east-1.elb.amazonaws.com")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}}, supports_credentials=True)

# Optional: add default headers (flask-cors covers most cases)
@app.after_request
def add_cors_headers(resp):
    resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return resp

# Prometheus metrics
metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter(
    "url_shorten_requests",
    "Number of requests to the shorten URL endpoint"
)
redirect_counter = metrics.counter(
    "url_redirect_requests",
    "Number of requests to redirect endpoint"
)

# -----------------------------------------------------------------------------
# AWS Clients
# -----------------------------------------------------------------------------
aws_region = os.environ.get("AWS_REGION", "us-east-1")
secrets_client = boto3.client("secretsmanager", region_name=aws_region)
s3_client = boto3.client("s3", region_name=aws_region)
cloudwatch_client = boto3.client("cloudwatch", region_name=aws_region)
ssm_client = boto3.client("ssm", region_name=aws_region)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DB_SECRET_ARN = os.environ.get("DB_SECRET_ARN")         # Secrets Manager ARN containing {"password": "..."}
DB_HOST = os.environ.get("DB_HOST")                      # RDS endpoint address
DB_NAME = os.environ.get("DB_NAME", "projectdb")
DB_USER = os.environ.get("DB_USER", "projectadmin")
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))  # seconds

UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET", "nexskill-project-files-2026")

# If you want absolute short URLs in responses, set BASE_URL to your ALB:
# e.g., BASE_URL = "http://project-alb-1445225992.us-east-1.elb.amazonaws.com"
BASE_URL = os.environ.get("http://project-alb-1445225992.us-east-1.elb.amazonaws.com")  # optional


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def get_db_password_from_secret(secret_arn: str) -> str:
    if not secret_arn:
        raise RuntimeError("DB_SECRET_ARN env is not set")
    resp = secrets_client.get_secret_value(SecretId=secret_arn)
    # SecretString may be plain string or JSON; we expect {"password": "..."}
    secret_str = resp.get("SecretString", "")
    try:
        secret_json = json.loads(secret_str)
        return secret_json["password"]
    except Exception:
        # Fallback: use the raw string as password
        return secret_str


def get_db_connection():
    """
    Returns a psycopg2 connection. Caller is responsible for closing it.
    """
    if not DB_HOST:
        raise RuntimeError("DB_HOST env is not set")
    password = get_db_password_from_secret(DB_SECRET_ARN)
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=password,
        connect_timeout=DB_CONNECT_TIMEOUT,
    )
    return conn


def ensure_tables():
    """
    Create minimal tables if they do not exist.
    This helps first-run scenarios. Adjust to your real schema if needed.
    """
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
        # Don't crash app if DB isn't ready at startup; log and continue.
        print(f"[startup] ensure_tables failed: {e}")


def make_short_code(original_url: str) -> str:
    """
    Generate a short code from URL + time for uniqueness.
    """
    h = hashlib.sha256(f"{original_url}-{time.time()}".encode("utf-8")).hexdigest()
    return h[:8]  # 8 chars is usually fine; adjust if you need more space


def log_to_cloudwatch(metric_name, value, unit="Count", namespace="LinkService"):
    try:
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                }
            ],
        )
    except Exception as e:
        print(f"Failed to log CloudWatch metric {metric_name}: {e}")


def get_app_config():
    """
    Fetch config from Parameter Store. Non-fatal if params are missing.
    """
    config_params = {
        "max_upload_size": "/project/app/max-upload-size",
        "allowed_file_types": "/project/app/allowed-file-types",
    }
    config = {}
    for key, param_name in config_params.items():
        try:
            response = ssm_client.get_parameter(Name=param_name)
            config[key] = response["Parameter"]["Value"]
        except Exception as e:
            print(f"Failed to fetch parameter {param_name}: {e}")
    return config


# -----------------------------------------------------------------------------
# Health and Config
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    """
    Lightweight health endpoint. Does not require DB. Use for ALB/NLB health checks.
    """
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}), 200


@app.route("/api/config", methods=["GET"])
def config():
    """
    Optional: surface selected app config from Parameter Store.
    """
    return jsonify(get_app_config()), 200


# -----------------------------------------------------------------------------
# File Upload to S3
# -----------------------------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    file_key = f"uploads/{hashlib.md5(file.filename.encode()).hexdigest()}-{file.filename}"
    bucket_name = UPLOAD_BUCKET

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            file_key,
            ExtraArgs={"ContentType": file.content_type},
        )
        log_to_cloudwatch("FileUploads", 1)
        return jsonify({"message": "File uploaded successfully", "file_key": file_key}), 200
    except Exception as e:
        log_to_cloudwatch("FileUploadErrors", 1)
        return jsonify({"error": f"File upload failed: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# Links API
# -----------------------------------------------------------------------------
@app.route("/api/links", methods=["GET"])
def get_links():
    """
    Return recent links. Adjust LIMIT or add pagination as needed.
    """
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


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """
    Simple analytics: counts of links and clicks.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM links")
            total_links = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM link_clicks")
            total_clicks = cur.fetchone()[0]
        conn.close()
        return jsonify({"total_links": total_links, "total_clicks": total_clicks}), 200
    except Exception as e:
        print(f"get_analytics error: {e}")
        return jsonify({"total_links": 0, "total_clicks": 0, "error": str(e)}), 200


@app.route("/api/shorten", methods=["POST"])
@url_shorten_counter.count_exceptions()
def shorten_url():
    """
    Shorten a URL and return the short code and short URL.
    JSON body: { "url": "https://example.com/..." }
    """
    try:
        payload = request.get_json(silent=True) or {}
        original_url = payload.get("url")
        if not original_url:
            return jsonify({"error": "Missing 'url' in request body"}), 400

        short_code = make_short_code(original_url)

        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO links (short_code, original_url) VALUES (%s, %s)",
                (short_code, original_url),
            )
        conn.close()

        # Compose short URL (absolute if BASE_URL is set; otherwise relative path)
        short_url = f"/{short_code}"
        if BASE_URL:
            short_url = f"{BASE_URL.rstrip('/')}/{short_code}"

        log_to_cloudwatch("ShortenRequests", 1)
        return jsonify({"short_code": short_code, "short_url": short_url}), 201
    except Exception as e:
        print(f"shorten_url error: {e}")
        log_to_cloudwatch("ShortenErrors", 1)
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# Redirect Endpoint
# -----------------------------------------------------------------------------
@app.route("/<short_code>", methods=["GET"])
@redirect_counter.count_exceptions()
def redirect_url(short_code):
    """
    Redirect to the original URL by short_code and record a click.
    """
    try:
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "SELECT original_url FROM links WHERE short_code = %s",
                (short_code,),
            )
            row = cur.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": "Not found"}), 404

            original_url = row[0]

            # Record click
            cur.execute(
                "INSERT INTO link_clicks (short_code) VALUES (%s)",
                (short_code,),
            )
        conn.close()

        return redirect(original_url, code=302)
    except Exception as e:
        print(f"redirect_url error: {e}")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
# Try to initialize tables at startup; ignore failures to allow container to run
try:
    ensure_tables()
except Exception as init_err:
    print(f"Initialization warning: {init_err}")
