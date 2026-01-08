import os
import boto3
import json
import psycopg2
from flask import Flask, jsonify

# --- Helper Function to Get Database Connection ---

# This function reads the secret credentials and connects to the database.
def get_db_connection():
    # Step 1: Retrieve the password from AWS Secrets Manager
    # The Boto3 library will automatically find your AWS credentials
    secrets_client = boto3.client('secretsmanager', region_name=os.environ['AWS_REGION'])
    secret_arn = os.environ['DB_SECRET_ARN']
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    password = json.loads(secret_response['SecretString'])['password']

    # Step 2: Connect to the PostgreSQL database
    # The database address (host) is passed in as an environment variable
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database="projectdb",
        user="projectadmin",
        password=password
    )
    return conn

# --- Flask Application Definition ---

# This is the critical line. The variable is still named 'app'.
app = Flask(__name__)

# This is your main API endpoint.
@app.route('/api/data')
def get_data():
    """
    This API endpoint now connects to the database, creates a table if needed,
    and retrieves a message from it.
    """
    try:
        # Get a connection to the database
        conn = get_db_connection()
        # 'cursor' is the object that lets you execute commands
        cur = conn.cursor()

        # Step 1: Create a table named 'greetings' if it doesn't already exist.
        # This is safe to run every time.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL
            );
        """)

        # Step 2: Check if the table is empty. If it is, add our one greeting.
        cur.execute("SELECT COUNT(*) FROM greetings;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO greetings (message) VALUES (%s);", ('Hello from the RDS Database!',))
        
        # Step 3: Commit the changes to the database (important!)
        conn.commit()

        # Step 4: Fetch the latest greeting from the table.
        cur.execute("SELECT message FROM greetings ORDER BY id DESC LIMIT 1;")
        # .fetchone()[0] gets the first column of the first row
        db_message = cur.fetchone()[0]

        # Step 5: Close the cursor and the connection
        cur.close()
        conn.close()

        # Step 6: Return the data from the database as JSON
        data = {
            'message': db_message,
            'status': 'success'
        }
        return jsonify(data)

    except Exception as e:
        # If anything goes wrong, return an error message.
        # This helps with debugging.
        print(f"An error occurred: {e}")
        return jsonify({'message': 'An error occurred connecting to the database.', 'status': 'error'}), 500

# This part is only for local testing. Gunicorn does not use it.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

