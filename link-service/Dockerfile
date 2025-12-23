# link-service: Python app
# Uses system Python inside container (do NOT create a venv inside Docker)
FROM python:3.11-slim

# Install minimal system deps (if your requirements need build tools, add them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for cached layer
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Recommended: ensure logs are unbuffered
ENV PYTHONUNBUFFERED=1
# Expose the port your app listens on (adjust if different)
EXPOSE 3000

# Default command: run your app
# If you run with something like `flask run` or `gunicorn`, change this line accordingly.
CMD ["python", "app.py"]
