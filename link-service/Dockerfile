# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
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

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# --- THIS IS THE FIX ---
# Install all Python dependencies from the single requirements.txt file
RUN python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Create a non-root user and assign ownership
RUN groupadd -r app && useradd -r -g app app \
  && chown -R app:app /app
USER app

# Expose the application port
EXPOSE ${PORT}

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with Gunicorn
CMD ["gunicorn", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--bind", "0.0.0.0:5001", "app:app"]
