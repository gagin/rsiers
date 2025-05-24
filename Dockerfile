FROM python:3.12-slim

WORKDIR /app

# Install curl (for healthcheck if needed, or remove if healthcheck uses internal means)
RUN apt-get update && apt-get install -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and set permissions
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy the rest of the application code
COPY . .

# Optional: Make scripts executable if you prefer, though `python script.py` doesn't require it
# RUN chmod +x /app/scripts/*.py 

EXPOSE 5001

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "backend/main.py"]