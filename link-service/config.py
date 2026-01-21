import os

# configure these 4 values from repository secret. If you want to run project on localhost then put values here.
class Config:
    DATABASE_HOST = os.getenv('DB_HOST', '<DB_HOST>') 
    DATABASE_PORT = os.getenv('DB_PORT', '5432')
    DATABASE_NAME = os.getenv('DB_NAME', '<DB_NAME>')
    DATABASE_USER = os.getenv('DB_USER', '<DB_USER>')
    DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '<DB_PASSWORD>')
    ANALYTICS_SERVICE_URL = os.getenv(
        "ANALYTICS_SERVICE_URL",
        "http://devops-alb-1571320511.us-east-2.elb.amazonaws.com/api/analytics"
    )
    PORT = int(os.getenv('PORT', 3000))
