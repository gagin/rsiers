# Bitcoin Indicator Dashboard Codebase Documentation

This document provides an overview of the files in the Bitcoin Indicator Dashboard project, explaining their purpose and relationships.

## Core Application Files

### Backend

- **`app.py`** - Main backend application that:
  - Fetches data from Kraken API
  - Calculates technical indicators
  - Stores data in SQLite database
  - Provides API endpoints for the frontend

- **`simple_server.py`** - Simplified Flask server with mock data for testing or when Kraken API is unavailable

### Frontend

- **`index.html`** - Single-page React application that:
  - Displays the dashboard UI
  - Fetches data from the backend API
  - Visualizes indicators and metrics
  - Provides the time machine feature

### Data

- **`historical_data.json`** - Contains historical Bitcoin market data for the time machine feature:
  - Significant market peaks and bottoms
  - Technical indicators at those points
  - Price outcomes 1, 6, and 12 months later

## Utility Scripts

- **`generate_historical_metrics.py`** - Calculates COS and BSI metrics for historical data points

- **`update_historical_bsi.py`** - Updates the BSI (Bull Strength Index) values in historical_data.json

- **`test_api.py`** - Tests the backend API endpoints to ensure they're working correctly

## Setup and Installation

- **`requirements.txt`** - Lists Python package dependencies

- **`setup.py`** - Sets up a virtual environment and installs dependencies (useful for Windows users)

- **`install_dependencies.py`** - Provides detailed installation steps for dependencies, supporting both Conda and pip

## Startup Scripts

- **`Makefile`** - Contains commands for common tasks:
  - Installing dependencies
  - Running the application
  - Testing the API
  - Cleaning up temporary files

- **`fix_and_run.sh`** - Main script to run the application on Unix-like systems:
  - Installs dependencies
  - Creates a simple server if needed
  - Starts both backend and frontend servers

- **`start.bat`** - Main script to run the application on Windows

- **`start_frontend.sh`** - Script to run only the frontend (with mock data)

- **`create_server.sh`** - Creates the simple server if it doesn't exist

## Docker Support

- **`Dockerfile`** - Defines how to build the Docker image for the application

- **`docker-compose.yml`** - Orchestrates the backend and frontend services:
  - Sets up the backend API service
  - Sets up the frontend web server
  - Configures networking between services
  - Manages persistent data volume

- **`.dockerignore`** - Specifies files to exclude from the Docker build context

- **`docker-start.sh`** - Convenience script to start the application with Docker Compose

## Development and Debugging

- **`debug_backend.py`** - Debugging version of app.py that:
  - Checks dependencies
  - Initializes the database
  - Tests the Kraken API
  - Inserts mock data if needed
  - Starts a Flask server in debug mode

## Documentation

- **`PRD.txt`** - Product Requirements Document detailing the application's requirements and features

- **`README.md`** - Project documentation with setup instructions and feature overview

- **`CODEBASE.md`** - This file, documenting the codebase structure

- **`btc-rsis.png`** - Screenshot of the application for documentation

## File Relationships

- The frontend (`index.html`) communicates with the backend (`app.py` or `simple_server.py`) via API calls
- The backend stores data in an SQLite database (`bitcoin_indicators.db`, created at runtime)
- The time machine feature uses data from `historical_data.json`
- The startup scripts (`fix_and_run.sh`, `start.bat`, etc.) orchestrate the application startup
- The utility scripts (`generate_historical_metrics.py`, `update_historical_bsi.py`) manage data processing

## Development Workflow

### Standard Setup
1. Use `make install` or `setup.py` to set up the environment
2. Use `make run` or `fix_and_run.sh` to start the application
3. Access the frontend at http://localhost:8000
4. Use `test_api.py` to verify the backend is working correctly
5. Use `update_historical_bsi.py` to update BSI values if needed

### Docker Setup
1. Install Docker and Docker Compose
2. Run `./docker-start.sh` to build and start the application
3. Access the frontend at http://localhost:8000
4. View logs with `docker-compose logs -f`
5. Stop the application with `docker-compose down`
