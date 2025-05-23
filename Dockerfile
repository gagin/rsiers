FROM python:3.12-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and curl for healthcheck
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for the backend API
EXPOSE 5001

# Command to run the application
CMD ["python", "simple_server.py"]
