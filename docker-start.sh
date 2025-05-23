#!/bin/bash

# This script starts the Bitcoin Indicator Dashboard using Docker Compose

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Print banner
echo "=================================================="
echo "  Bitcoin Indicator Dashboard - Docker Edition"
echo "  A vibecoded project: PRD by Grok, Code by Augment"
echo "=================================================="
echo ""

# Build and start the containers
echo "Starting Bitcoin Indicator Dashboard with Docker Compose..."
docker-compose up --build -d

# Check if containers started successfully
if [ $? -eq 0 ]; then
    echo "Bitcoin Indicator Dashboard is now running!"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001"
    echo ""
    echo "New Features:"
    echo "- Enhanced Time Machine with calendar control"
    echo "- Foldable indicator table with detailed descriptions"
    echo "- Technical analysis explanation with sarcastic tone"
    echo "- Bull Strength Index (BSI) replacing TSI"
    echo ""
    echo "To view logs, run: docker-compose logs -f"
    echo "To stop the application, run: docker-compose down"
else
    echo "Failed to start the application. Check the logs for more information."
    docker-compose logs
fi
