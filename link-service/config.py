import os

class Config:
    """
    This configuration class reads settings from the environment variables
    provided by the ECS Task Definition.
    """
    # Read the database connection details
    DATABASE_HOST = os.environ.get('DB_HOST')
    DATABASE_PORT = os.environ.get('DB_PORT', 5432) # Default to 5432 if not provided
    DATABASE_NAME = os.environ.get('DB_NAME', 'projectdb')
    DATABASE_USER = os.environ.get('DB_USER', 'projectadmin')

    # This is a placeholder for now. The service will default to a dummy URL.
    ANALYTICS_SERVICE_URL = os.environ.get('ANALYTICS_SERVICE_URL', 'http://project-alb-924486123.us-east-1.elb.amazonaws.com')

    # These are needed for the app to fetch the password from AWS Secrets Manager
    DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
    AWS_REGION = os.environ.get('AWS_REGION')

    # This is the port your application will run on, read from the environment
    PORT = os.environ.get("PORT", 5001)
