# Bitcoin Indicator Dashboard Makefile

# Default Python interpreter
PYTHON := python3 
# Default port for the backend server (Flask app in backend/main.py)
BACKEND_PORT := 5001
# Default port for the frontend server (simple HTTP server for index.html)
FRONTEND_PORT := 8000

.PHONY: help install run run-frontend run-backend clean \
        docker-build docker-run docker-stop \
        init-db import-csv check-db load-gaps \
        manual-fill-main manual-fill-specific import-all-sources

help:
	@echo "Bitcoin Indicator Dashboard (Refactored)"
	@echo ""
	@echo "Available commands:"
	@echo "  make help                  - Show this help message"
	@echo "  make install               - Install Python dependencies from requirements.txt"
	@echo "  make run                   - Run both backend (backend/main.py) and frontend servers"
	@echo "  make run-frontend          - Run only the frontend server"
	@echo "  make run-backend           - Run only the backend server (backend/main.py)"
	@echo "  make init-db               - Initialize/Verify the database schema"
	@echo "  make import-csv            - Import data from CSV files in ./csv/ into the database"
	@echo "  make manual-fill-main      - Run the primary manual data filler (scripts/manual_data_filler.py)"
	@echo "  make manual-fill-specific  - Run the specific 2024-03-31 data filler (scripts/fill-in-20240331.py)"
	@echo "  make import-all-sources    - Initialize DB, then import CSVs and run ALL manual filler scripts"
	@echo "  make check-db              - Check for data gaps in the database"
	@echo "  make load-gaps             - Interactively load data for gaps identified by db-checker (uses api-loader)"
	@echo "  make clean                 - Remove __pycache__ directories and the SQLite database file"
	@echo "  make docker-build          - Build Docker image for the application"
	@echo "  make docker-run            - Run application with Docker Compose (recommended)"
	@echo "  make docker-stop           - Stop Docker containers"
	@echo ""
	@echo "Utility Scripts (run directly or via make targets):"
	@echo "  scripts/api-loader.py --start_date YYYY-MM-DD --days N"
	@echo "  scripts/csv_importer.py"
	@echo "  scripts/db_checker.py [--start_date YYYY-MM-DD] [--end_date YYYY-MM-DD] [--generate_commands]"
	@echo "  scripts/manual_data_filler.py (edit this script to add/change data)"
	@echo "  scripts/fill-in-20240331.py (edit this script if needed)"
	@echo "  scripts/generate_historical_json.py (to regenerate historical_data.json)"
	@echo ""
	@echo "Environment variables:"
	@echo "  PYTHON           - Python interpreter (default: python3)"
	@echo "  BACKEND_PORT     - Port for the backend server (default: 5001)"
	@echo "  FRONTEND_PORT    - Port for the frontend server (default: 8000)"

install:
	@echo "Installing dependencies from requirements.txt using $(PYTHON)..."
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

init-db:
	@echo "Initializing database schema (if needed)..."
	$(PYTHON) -c "from backend.db_utils import init_db; init_db()"
	@echo "Database schema initialized/verified."

import-csv: init-db
	@echo "Importing data from CSV files..."
	$(PYTHON) scripts/csv_importer.py
	@echo "CSV import complete."

check-db:
	@echo "Checking database for data gaps..."
	$(PYTHON) scripts/db_checker.py --generate_commands

load-gaps:
	@echo "Running db_checker to identify gaps and generate commands..."
	@$(PYTHON) scripts/db_checker.py --generate_commands || true
	@echo ""
	@echo "Review the suggested 'api-loader.py' commands above."
	@read -p "Do you want to run these commands to fill gaps? (yes/N): " choice; \
	if [ "$$choice" = "yes" ] || [ "$$choice" = "y" ]; then \
		echo "Generating commands and executing them (you may need to copy-paste if this doesn't work directly)..."; \
		$(PYTHON) scripts/db_checker.py --generate_commands | grep 'python scripts/api-loader.py' | sed 's/^.*Suggested command: //' | xargs -I CMD $(PYTHON) CMD; \
	else \
		echo "Skipping automatic gap filling. Please run manually if needed."; \
	fi

manual-fill-main: init-db
	@echo "Running main manual data filler script (scripts/manual_data_filler.py)..."
	@echo "NOTE: Ensure it's configured with the data you want to add."
	$(PYTHON) scripts/manual_data_filler.py

manual-fill-specific: init-db
	@echo "Running specific manual data filler script (scripts/fill-in-20240331.py)..."
	@echo "NOTE: Ensure it's configured with the data you want to add."
	$(PYTHON) scripts/fill-in-20240331.py

import-all-sources: init-db import-csv manual-fill-main manual-fill-specific
	@echo "All primary data sources (CSV, main manual fills, specific manual fills) imported."
	@echo "Run 'make check-db' to identify any remaining gaps for api-loader."

run-backend: init-db
	@echo "Starting backend server (backend/main.py) on port $(BACKEND_PORT)..."
	$(PYTHON) backend/main.py

run-frontend:
	@echo "Starting frontend server on port $(FRONTEND_PORT)..."
	@echo "Serving ./index.html and related static assets."
	cd . && $(PYTHON) -m http.server $(FRONTEND_PORT)

run: init-db
	@echo "Starting both backend and frontend servers..."
	@echo "Starting backend..."
	$(PYTHON) backend/main.py & \
	BACKEND_PID=$$!; \
	echo "Backend server (backend/main.py) started with PID $$BACKEND_PID on port $(BACKEND_PORT)"; \
	sleep 2; \
	echo "Starting frontend..."
	cd . && $(PYTHON) -m http.server $(FRONTEND_PORT) & \
	FRONTEND_PID=$$!; \
	echo "Frontend server started with PID $$FRONTEND_PID on port $(FRONTEND_PORT)"; \
	echo ""; \
	echo "Application URLs:"; \
	echo "  Backend API: http://localhost:$(BACKEND_PORT)"; \
	echo "  Frontend:    http://localhost:$(FRONTEND_PORT)"; \
	echo ""; \
	echo "Press Ctrl+C to stop both servers."; \
	trap "echo ''; echo 'Shutting down servers...'; kill $$BACKEND_PID $$FRONTEND_PID 2>/dev/null || true; exit" INT TERM; \
	wait $$BACKEND_PID || wait $$FRONTEND_PID 

clean:
	@echo "Cleaning up..."
	@rm -f bitcoin_daily_data.db bitcoin_daily_data.db-journal 
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleanup complete!"

docker-build:
	@echo "Building Docker image (ensure Dockerfile uses backend/main.py)..."
	docker-compose build

docker-run:
	@echo "Starting application with Docker Compose..."
	@echo "Ensure your docker-compose.yml command is: python backend/main.py"
	docker-compose up -d
	@echo "Application started! Frontend at http://localhost:$(FRONTEND_PORT)"
	@echo "To view logs, run: docker-compose logs -f"

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down