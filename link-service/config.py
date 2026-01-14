import os

class Config:
    # Read the database credentials from the environment variables provided by ECS
    DATABASE_HOST = os.environ.get('DB_HOST')
    DATABASE_PORT = os.environ.get('DB_PORT', 5432) # Default to 5432 if not set
    DATABASE_NAME = os.environ.get('DB_NAME', 'projectdb')
    DATABASE_USER = os.environ.get('DB_USER', 'projectadmin')

    # This is a placeholder. For now, we will not deploy the analytics service.
    ANALYTICS_SERVICE_URL = os.environ.get('ANALYTICS_SERVICE_URL', 'http://localhost:9999') # Default to a dummy URL

    # Note: The password will be handled directly in the app.py to fetch from Secrets Manager
    # We just need to make sure the app knows where to look for the secret ARN.
    DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
    AWS_REGION = os.environ.get('AWS_REGION')
