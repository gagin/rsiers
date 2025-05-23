# Bitcoin Indicator Dashboard (v0.2.2 - Refactored Backend)

A web application that displays various technical indicators for Bitcoin to help identify potential sell signals. The application fetches historical and recent data, calculates technical indicators, and displays them in a user-friendly dashboard.

<a href="btc-rsis.png" target="_blank">
  <img src="btc-rsis.png" alt="Bitcoin Indicator Dashboard Screenshot" height="400" />
</a>

*Screenshot of the Bitcoin Indicator Dashboard (click to view full size)*

## Project Origin
This project is vibecoded: Original PRD by Grok 3, Implementation by Augment with Sonnet 3.7.

## Features
- Displays key technical indicators for Bitcoin (RSI, with stubs for StochRSI, MFI, etc.)
- Shows monthly and weekly values for all indicators.
- Composite Metrics: Composite Overbought Score (COS) & Bull Strength Index (BSI).
- Enhanced Time Machine: View indicators for historical dates using calendar control, with price outcomes.
- Data Sources:
    1.  Primary: Local CSV files (`./csv/`) for historical OHLCV data.
    2.  Secondary: CoinGecko API for recent daily data (past 365 days) if not in CSV.
    3.  Tertiary: Kraken API as a fallback if other sources fail.
- Database: SQLite (`bitcoin_daily_data.db`) for storing daily OHLCV and calculated indicator sets.
- Backend: Python/Flask, serving data and calculations, with a modular structure.
- Frontend: Single-page React application.
- Utility scripts for data management (CSV import, API loading, DB checks).

## Architecture

The application has been refactored for better maintainability:

1.  **Backend (`backend/` directory)**:
    *   `main.py`: Main Flask application serving API endpoints.
    *   `db_utils.py`: Handles SQLite database interactions (schema, data storage/retrieval using 'YYYY-MM-DD' date strings).
    *   `csv_data_loader.py`: Manages loading and querying data from local CSV files.
    *   `api_clients.py`: Contains classes for interacting with CoinGecko and Kraken APIs.
    *   `data_fetch_orchestrator.py`: Orchestrates data fetching from different sources (DB, CSV, APIs) and prepares data for indicator calculation.
    *   `indicator_calculator.py`: Contains logic for technical indicator calculations (RSI implemented, others as stubs), resampling, composite scores, and price outcomes.
2.  **Frontend (`index.html`)**:
    *   React-based single-page application for UI and data visualization.
3.  **Data Storage (`bitcoin_daily_data.db`)**:
    *   SQLite database storing daily OHLCV prices (keyed by 'YYYY-MM-DD' strings) and calculated historical indicator sets.
4.  **Primary Historical Data (`csv/` directory)**:
    *   Contains CSV files (e.g., `XBTUSD_1440.csv`) with historical daily OHLCV data. This is the primary source for bulk historical data.
5.  **Historical Events (`historical_data.json`)**:
    *   JSON file with predefined significant market events for the Time Machine feature.
6.  **Utility Scripts (`scripts/` directory)**:
    *   `csv_importer.py`: Imports all data from CSV files in the `./csv/` directory into the database.
    *   `api-loader.py`: Fetches data from APIs (CoinGecko/Kraken) to fill gaps not covered by CSVs for specified date ranges.
    *   `db_checker.py`: Checks the database for missing daily data and can suggest `api-loader.py` commands to fill gaps.
    *   `manual_data_filler.py`: Allows direct insertion of OHLCV data for specific dates (requires editing the script).

## Setup and Installation

### Prerequisites
- Docker and Docker Compose (recommended)
- Python 3.9+ (Python 3.12 recommended) if not using Docker
- Pip (Python package installer)
- Make (optional, for using Makefile convenience targets)

### Option 1: Using Docker (Recommended)
Ensures consistency and avoids local environment issues.
1.  Ensure Docker and Docker Compose are installed.
2.  Run the start script: `/bin/bash docker-start.sh`
    *   This builds the Docker image (using `backend/main.py` as the entry point for the backend service) and starts services.
3.  Access:
    *   Frontend: `http://localhost:8000`
    *   Backend API: `http://localhost:5001`
4.  Logs: `docker-compose logs -f` | Stop: `docker-compose down`

**Note for Docker:** Ensure your `Dockerfile` `CMD` is `["python", "backend/main.py"]` and `docker-compose.yml` backend service command is `python backend/main.py`.

### Option 2: Using Makefile (Local Environment)
1.  **Install Python dependencies:**
    ```bash
    make install
    ```
2.  **Database Setup & Initial Data Load (Run these once, or if DB is deleted):**
    *   **(Important)** If you have an old `bitcoin_daily_data.db` with integer timestamps, **delete it manually first.**
    *   Initialize the database (creates tables with new 'YYYY-MM-DD' date string schema):
        ```bash
        make init-db
        ```
    *   Import all data from your CSV files:
        ```bash
        make import-csv
        ```
3.  **Check for and fill remaining data gaps (Optional but recommended):**
    *   Identify missing dates:
        ```bash
        make check-db 
        ``` 
        (This runs `db_checker.py --generate_commands`)
    *   Use the suggested `python3 scripts/api-loader.py ...` commands to fill gaps, or use `make load-gaps` for an interactive approach.
4.  **Run the application:**
    ```bash
    make run
    ```
    This starts `backend/main.py` and a simple frontend server.

### Option 3: Manual Setup (Local Environment)
1.  **Install Python dependencies:** `python3 -m pip install -r requirements.txt`
2.  **Database Setup & Initial Data Load:**
    *   **Delete any old `bitcoin_daily_data.db` file.**
    *   Initialize DB: `python3 -c "from backend.db_utils import init_db; init_db()"`
    *   Import CSVs: `python3 scripts/csv_importer.py`
3.  **Fill Gaps (Optional):**
    *   Check: `python3 scripts/db_checker.py --generate_commands`
    *   Load: `python3 scripts/api-loader.py --start_date YYYY-MM-DD --days N` (as suggested by checker)
4.  **Start Backend:** `python3 backend/main.py` (Terminal 1)
5.  **Start Frontend:** `python3 -m http.server 8000` (Terminal 2, from project root)

### Utility Scripts
Located in `scripts/`. Run from project root (e.g., `python3 scripts/script_name.py`).
*   **`csv_importer.py`**: Populates `daily_ohlcv` from `./csv/`.
*   **`db_checker.py`**: Checks for gaps in `daily_ohlcv`. Use `--generate_commands`.
*   **`api-loader.py`**: Fills `daily_ohlcv` gaps using APIs for a date range.
*   **`manual_data_filler.py`**: Manually insert specific OHLCV data (edit script first).

## Troubleshooting
- **"No module named 'backend.xxx'"**: Run Python commands from the project root. `PYTHONPATH` might need adjustment if running scripts directly from subdirectories in complex setups.
- **Database Schema Issues**: If SQLite errors like "no such column" or type mismatches occur after code changes, the recommended fix is to:
    1. Delete `bitcoin_daily_data.db`.
    2. Run `make init-db` (or its Python equivalent).
    3. Re-run `make import-csv`.
- **API Rate Limiting**: The system has basic retry and delay logic. For extensive backfilling, run `api-loader.py` in smaller batches for `--days`.