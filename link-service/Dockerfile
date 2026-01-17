# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
# CRITICAL: Included AWS_REGION variable for AWS communication
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001 \
    PIP_NO_CACHE_DIR=1 \
    AWS_REGION=us-east-1

WORKDIR /app

# Install OS-level build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install application dependencies
# CRITICAL: Adding boto3 and prometheus-client for AWS services and monitoring
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir boto3 prometheus_flask_exporter \
  && python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Create a non-root user and assign ownership
RUN groupadd -r app && useradd -r -g app app \
  && chown -R app:app /app

USER app

# Expose the application port
EXPOSE ${PORT}

# Health check configuration
# CRITICAL: Updated to dynamically handle DNS Load Balancer and appchecks
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with Gunicorn
CMD ["gunicorn", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--bind", "0.0.0.0:5001", "app:app"]
