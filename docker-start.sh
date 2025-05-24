#!/bin/bash

# This script starts the Bitcoin Indicator Dashboard using Docker Compose

# ... (Docker and Docker Compose checks remain the same) ...

# Print banner
echo "=================================================="
echo "  Bitcoin Indicator Dashboard - Docker Edition"
echo "  Project Version: 0.2.2 (Refactored Backend)" # Updated version
echo "=================================================="
echo ""

# Build and start the containers
echo "Starting Bitcoin Indicator Dashboard with Docker Compose..."
docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo "Bitcoin Indicator Dashboard is now running!"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001/api/indicators" # More specific API example
    echo ""
    echo "NOTE: On first run with an empty database volume, the database will be initialized"
    echo "with its schema. However, historical data from CSVs or manual fillers is NOT"
    echo "automatically imported by this 'docker-compose up' command."
    echo "To populate data, you may need to run import scripts manually inside the container, e.g.:"
    echo "  docker exec btc-dashboard-backend python scripts/csv_importer.py"
    echo "  docker exec btc-dashboard-backend python scripts/manual_data_filler.py"
    echo "  (Or use 'make' targets if 'make' is available in the container image)"
    echo ""
    echo "To view logs, run: docker-compose logs -f"
    echo "To stop the application, run: docker-compose down"
    echo "To remove the database volume (DANGER: DELETES DB DATA), run: docker-compose down -v"
else
    echo "Failed to start the application. Check the logs for more information."
    docker-compose logs
fi