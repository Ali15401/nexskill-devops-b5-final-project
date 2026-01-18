# Use an official Python runtime as the base image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001 \
    PIP_NO_CACHE_DIR=1 \
    AWS_REGION=us-east-1

WORKDIR /app

# OS-level deps for psycopg2 and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps
# Ensure requirements.txt includes:
# flask, flask-cors, gunicorn, boto3, prometheus-flask-exporter, psycopg2-binary (or psycopg2)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r /app/requirements.txt

# App code
COPY . /app

# Non-root user
RUN groupadd -r app && useradd -r -g app app \
 && chown -R app:app /app
USER app

# Expose port
EXPOSE ${PORT}

# Health check (matches /api/health in app.py)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--bind", "0.0.0.0:${PORT}", "app:app"]
