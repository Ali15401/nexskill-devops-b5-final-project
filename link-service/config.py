import os

class Config:
    DATABASE_HOST = os.getenv('DB_HOST', '8.222.170.22')
    DATABASE_PORT = os.getenv('DB_PORT', '5432')
    DATABASE_NAME = os.getenv('DB_NAME', 'urlshortener')
    DATABASE_USER = os.getenv('DB_USER', 'postgres')
    DATABASE_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    ANALYTICS_SERVICE_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:4000')
    PORT = int(os.getenv('PORT', 3000))