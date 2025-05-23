# Bitcoin Indicator Dashboard Makefile

# Default Python interpreter
PYTHON := python
# Default port for the backend server
BACKEND_PORT := 5001
# Default port for the frontend server
FRONTEND_PORT := 8000

.PHONY: help install run run-frontend run-backend clean test

help:
	@echo "Bitcoin Indicator Dashboard"
	@echo ""
	@echo "Available commands:"
	@echo "  make help         - Show this help message"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run both backend and frontend servers"
	@echo "  make run-frontend - Run only the frontend server (mock data)"
	@echo "  make run-backend  - Run only the backend server"
	@echo "  make clean        - Remove temporary files and database"
	@echo "  make test         - Run tests"
	@echo ""
	@echo "Environment variables:"
	@echo "  PYTHON         - Python interpreter to use (default: python)"
	@echo "  BACKEND_PORT   - Port for the backend server (default: 5001)"
	@echo "  FRONTEND_PORT  - Port for the frontend server (default: 8000)"

install:
	@echo "Installing dependencies..."
	@if command -v conda >/dev/null 2>&1 && [ -n "$$CONDA_PREFIX" ]; then \
		echo "Conda environment detected: $$CONDA_PREFIX"; \
		echo "Installing dependencies with Conda and pip..."; \
		conda install -y flask requests numpy pandas; \
		$(PYTHON) -m pip install flask-cors; \
	else \
		echo "Using system Python. Installing dependencies with pip..."; \
		$(PYTHON) -m pip install flask flask-cors requests numpy pandas; \
	fi
	@echo "Dependencies installed successfully!"

run-backend:
	@echo "Starting backend server on port $(BACKEND_PORT)..."
	@./create_server.sh
	@$(PYTHON) simple_server.py --port $(BACKEND_PORT)

run-frontend:
	@echo "Starting frontend server on port $(FRONTEND_PORT)..."
	@$(PYTHON) -m http.server $(FRONTEND_PORT)

run:
	@echo "Starting both backend and frontend servers..."
	@$(PYTHON) simple_server.py --port $(BACKEND_PORT) & \
	BACKEND_PID=$$!; \
	echo "Backend server started with PID $$BACKEND_PID"; \
	sleep 2; \
	$(PYTHON) -m http.server $(FRONTEND_PORT) & \
	FRONTEND_PID=$$!; \
	echo "Frontend server started with PID $$FRONTEND_PID"; \
	echo "Servers are running!"; \
	echo "Backend: http://localhost:$(BACKEND_PORT)"; \
	echo "Frontend: http://localhost:$(FRONTEND_PORT)"; \
	echo "Press Ctrl+C to stop both servers."; \
	trap "echo 'Shutting down servers...'; kill -TERM $$BACKEND_PID $$FRONTEND_PID 2>/dev/null; sleep 1; exit" INT TERM; \
	wait

clean:
	@echo "Cleaning up..."
	@rm -f *.db *.sqlite *.sqlite3
	@rm -rf __pycache__
	@echo "Cleanup complete!"

test:
	@echo "Running tests..."
	@$(PYTHON) test_api.py --port $(BACKEND_PORT)
	@echo "Tests complete!"
