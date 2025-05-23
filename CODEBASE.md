# Bitcoin Indicator Dashboard Codebase Documentation (v0.2.2 - Refactored Backend)

This document provides an overview of the files in the Bitcoin Indicator Dashboard project, explaining their purpose and relationships after backend refactoring.

## Core Application Files

### Backend (`backend/` directory)

- **`main.py`**: The main Flask application.
  - Initializes the database via `db_utils`.
  - Defines API endpoints (`/api/indicators`, `/api/historical_time_points`).
  - Orchestrates data fetching (via `data_fetch_orchestrator`) and indicator calculation (via `indicator_calculator`) for API responses.
- **`db_utils.py`**: Handles all SQLite database interactions.
  - Defines database path (`bitcoin_daily_data.db`).
  - Initializes database schema (tables `daily_ohlcv`, `calculated_indicators`) using 'YYYY-MM-DD' text strings for date keys.
  - Provides functions to store and retrieve daily OHLCV data and full calculated indicator sets.
- **`csv_data_loader.py`**: Contains the `CSVDataLoader` class.
  - Responsible for loading and parsing all `.csv` files from the `csv/` directory.
  - Provides a method (`get_ohlcv_for_date`) to query OHLCV data for a specific date from the loaded CSV data.
- **`api_clients.py`**: Contains classes for interacting with external APIs.
  - `CoinGeckoAPI`: Fetches historical daily price/volume data from CoinGecko.
  - `KrakenAPI`: Fetches historical daily OHLCV data from Kraken.
  - Exports instantiated clients for use.
- **`data_fetch_orchestrator.py`**: Manages the logic of sourcing daily OHLCV data.
  - `fetch_and_store_daily_ohlcv`: Tries to get data for a date by checking DB, then local CSVs, then CoinGecko (for recent), then Kraken. Stores fetched data in DB.
  - `get_historical_data_for_indicators`: Assembles a historical range (e.g., 2 years) of daily OHLCV data needed for indicator calculations, using `fetch_and_store_daily_ohlcv` to fill any gaps.
- **`indicator_calculator.py`**: Contains all logic for technical analysis.
  - Functions to calculate individual indicators (RSI, StochRSI stubs, etc.) from Pandas DataFrames.
  - `resample_ohlc_data`: Converts daily data to weekly/monthly.
  - `calculate_composite_metrics_for_api`: Computes COS and BSI.
  - `calculate_price_outcomes`: Determines future price movements.
- **`__init__.py`**: Makes the `backend` directory a Python package.

### Frontend

- **`index.html`**: Single-page React application.
  - Displays the dashboard UI.
  - Fetches data from the backend API endpoints.
  - Visualizes indicators and metrics.
  - Provides the Time Machine feature with calendar control.

### Data Files (Primary Sources & Configuration)

- **`csv/` (directory)**: Contains user-provided CSV files with historical OHLCV data (e.g., `XBTUSD_1440.csv`). This is the primary source for bulk historical data.
- **`historical_data.json`**: JSON file defining significant historical market events (peaks, bottoms) used by the Time Machine feature. Includes pre-calculated indicators for these specific points.
- **`bitcoin_daily_data.db`**: SQLite database file (created/managed by the backend).
  - `daily_ohlcv` table: Stores daily open, high, low, close, volume data, keyed by 'YYYY-MM-DD' date strings. Populated by `csv_importer.py` and `api-loader.py`.
  - `calculated_indicators` table: Stores full sets of calculated weekly/monthly indicators, COS, BSI, price, and outcomes for specific dates, keyed by 'YYYY-MM-DD' date strings. Acts as a cache.

## Utility Scripts (`scripts/` directory)

- **`csv_importer.py`**: Reads all CSV files from the `csv/` directory and populates the `daily_ohlcv` table in the database. Normalizes timestamps to start-of-day UTC and stores dates as 'YYYY-MM-DD'.
- **`api-loader.py`**: Fetches missing daily OHLCV data for a specified date range using the logic in `backend/data_fetch_orchestrator.py` (tries DB, CSV, CoinGecko, Kraken) and stores it.
- **`db_checker.py`**: Analyzes the `daily_ohlcv` table for date continuity, reports gaps, and can optionally generate `api-loader.py` commands to fill them.
- **`manual_data_filler.py`** (formerly `fill-in-20240331.py`): Allows manual insertion/update of OHLCV data for specific dates by editing the script's data list.

## Setup and Installation

- **`requirements.txt`**: Lists Python package dependencies (Flask, requests, pandas, numpy, etc.).
- **`setup.py`**: Legacy script for VENV setup; less relevant with current modular structure and `requirements.txt`.
- **`Makefile`**: Contains convenience commands for common tasks like installation, running servers, database operations, and Docker commands.

## Docker Support
- **`Dockerfile`**: Defines the Docker image for the backend application (runs `backend/main.py`).
- **`docker-compose.yml`**: Orchestrates the backend and frontend services for easy deployment.
- **`.dockerignore`**: Specifies files to exclude from the Docker build.
- **`docker-start.sh`**: User-friendly script to build and run the application using Docker Compose.

## Documentation
- **`PRD.txt`**: Product Requirements Document.
- **`README.md`**: Project overview, setup, and usage instructions.
- **`CODEBASE.md`**: This document.
- **`CHANGELOG.md`**: Tracks notable changes to the project.
- **`btc-rsis.png`**: Application screenshot.

## Data Flow for `/api/indicators?date=YYYY-MM-DD`
1.  `backend/main.py` receives request, normalizes date to `target_date_obj_utc`.
2.  Checks `calculated_indicators` table for `target_date_obj_utc` via `get_full_indicator_set_from_db`.
    - If recent cache hit (for today) or exact match (for historical), returns cached data.
3.  If no/stale cache:
    a.  `get_historical_data_for_indicators` (in `data_fetch_orchestrator.py`) is called for a 2-year window ending at `target_date_obj_utc`.
        i.  This function iterates daily: checks DB (`get_daily_ohlcv_from_db`), if miss, calls `fetch_and_store_daily_ohlcv`.
        ii. `fetch_and_store_daily_ohlcv`:
            1. Checks CSV (`CSVDataLoader` instance).
            2. If miss & recent, checks CoinGecko (`CoinGeckoAPI` instance).
            3. If miss or old, checks Kraken (`KrakenAPI` instance).
            4. Stores any newly fetched daily data into `daily_ohlcv` table via `store_daily_ohlcv_data`.
        iii. Returns a Pandas DataFrame of daily OHLCV data for the 2-year window.
    b.  `backend/main.py` uses this DataFrame to:
        i.  Determine `price_at_event` (last close price).
        ii. Resample to weekly/monthly (`resample_ohlc_data` in `indicator_calculator.py`).
        iii.Calculate indicators for W/M (`calculate_indicators_from_ohlc_df`).
        iv. Calculate COS/BSI (`calculate_composite_metrics_for_api`).
        v.  Calculate price outcomes (`calculate_price_outcomes`).
    c.  Stores the complete set into `calculated_indicators` table via `store_full_indicator_set`.
    d.  Returns the newly calculated set as JSON.

## Development Workflow (Refactored)

### Docker Setup (Recommended)
1.  Install Docker and Docker Compose.
2.  Run `./docker-start.sh`. Access frontend: `http://localhost:8000`.

### Local Setup
1.  Delete `bitcoin_daily_data.db` (if migrating from old schema or for a clean start).
2.  Run `make install` (or `python3 -m pip install -r requirements.txt`).
3.  Run `make init-db` (or `python3 -c "from backend.db_utils import init_db; init_db()"`).
4.  Run `make import-csv` (or `python3 scripts/csv_importer.py`) to load base historical data.
5.  Run `make check-db` to identify gaps. Use suggested commands with `python3 scripts/api-loader.py` to fill them if desired.
6.  Run `make run` to start backend and frontend. Access frontend: `http://localhost:8000`.