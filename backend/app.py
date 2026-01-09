import os
import boto3
import json
import psycopg2
from flask import Flask, jsonify

# --- Helper Function to Get Database Connection ---

def get_db_connection():
    # Retrieve the password from AWS Secrets Manager
    secrets_client = boto3.client('secretsmanager', region_name=os.environ['AWS_REGION'])
    secret_arn = os.environ['DB_SECRET_ARN']
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    password = json.loads(secret_response['SecretString'])['password']

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database="projectdb",
        user="projectadmin",
        password=password
    )
    return conn

# --- Flask Application Definition ---

app = Flask(__name__)

# --- API Endpoints ---

# Main API endpoint to get data from the database
@app.route('/api/data')
def get_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create table if it doesn't exist and insert a default message
        cur.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL
            );
        """)
        cur.execute("SELECT COUNT(*) FROM greetings;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO greetings (message) VALUES (%s);", ('Hello from the RDS Database!',))
        conn.commit()

        # Fetch the latest greeting
        cur.execute("SELECT message FROM greetings ORDER BY id DESC LIMIT 1;")
        db_message = cur.fetchone()[0]

        cur.close()
        conn.close()

        data = {
            'message': db_message,
            'status': 'success'
        }
        return jsonify(data)
    except Exception as e:
        print(f"An 
