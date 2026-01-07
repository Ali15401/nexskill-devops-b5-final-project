# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install OS-level build deps for packages like psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY link-service/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (do this after installing deps to use Docker cache)
COPY link-service /app

# Create a non-root user and set ownership
RUN groupadd -r app && useradd -r -g app app \
  && chown -R app:app /app

USER app

# Expose port
EXPOSE ${PORT}

# Basic healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT}/health || exit 1

# Use gunicorn for production
CMD ["sh", "-c", "exec gunicorn --workers 3 --worker-class gthread --threads 4 --bind 0.0.0.0:${PORT} app:app"]
