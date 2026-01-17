import os
import boto3
import json
import psycopg2
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import hashlib
from prometheus_flask_exporter import PrometheusMetrics  # For monitoring

# --- Application Setup ---
app = Flask(__name__)
CORS(app)

# --- Monitoring Setup ---
metrics = PrometheusMetrics(app)
url_shorten_counter = metrics.counter(
    'url_shorten_requests',
    'Number of requests to the shorten URL endpoint'
)

# AWS Clients
aws_region = os.environ.get('AWS_REGION', 'us-east-1')
secrets_client = boto3.client('secretsmanager', region_name=aws_region)
s3_client = boto3.client('s3', region_name=aws_region)
cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
ssm_client = boto3.client('ssm', region_name=aws_region)

# --- Database Connection Function ---
def get_db_connection():
    secret_arn = os.environ.get('DB_SECRET_ARN')
    db_host = os.environ.get('DB_HOST')

    # Fetch the password from AWS Secrets Manager
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    db_password = json.loads(secret_response['SecretString'])['password']

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        database="projectdb",
        user="projectadmin",
        password=db_password
    )
    return conn

# --- New: Fetch Configurations from Parameter Store ---
def get_app_config():
    config_params = {
        'max_upload_size': '/project/app/max-upload-size',
        'allowed_file_types': '/project/app/allowed-file-types'
    }

    config = {}
    for key, param_name in config_params.items():
        try:
            response = ssm_client.get_parameter(Name=param_name)
            config[key] = response['Parameter']['Value']
        except Exception as e:
            print(f"Failed to fetch parameter {param_name}: {e}")
    return config

# --- File Upload to S3 & Endpoint ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    file_key = f"uploads/{hashlib.md5(file.filename.encode()).hexdigest()}-{file.filename}"
    bucket_name = "nexskill-project-files-2026"

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            file_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        log_to_cloudwatch('FileUploads', 1)
        return jsonify({'message': 'File uploaded successfully', 'file_key': file_key}), 200
    except Exception as e:
        log_to_cloudwatch('FileUploadErrors', 1)
        return jsonify({'error': f"File upload failed: {str(e)}"}), 500

# --- Log Custom Metrics to CloudWatch ---
def log_to_cloudwatch(metric_name, value, unit='Count', namespace='LinkService'):
    try:
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit
                }
            ]
        )
    except Exception as e:
        print(f"Failed to log CloudWatch metric {metric_name}: {e}")

# --- Remainder of the API is unchanged (shortening URLs, fetching links, etc.) ---
@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    ...

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    ...