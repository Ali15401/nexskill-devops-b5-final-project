# Use an official lightweight Python image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependencies file first to leverage Docker layer caching
COPY requirements.txt .

# Install the Python dependencies (Flask and Gunicorn)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 5000
EXPOSE 5000

# THE FINAL, CORRECTED COMMAND:
# This uses 'exec' to make Gunicorn the main process, which is a container best practice.
# It also explicitly sets the number of workers.
CMD ["gunicorn", "--workers=1", "--bind", "0.0.0.0:5000", "app:app"]
