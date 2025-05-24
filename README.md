# Bitcoin Indicator Dashboard (v0.3.0)

A web application that displays various technical indicators for Bitcoin to help identify potential sell signals. The application fetches historical and recent data, calculates technical indicators, and displays them in a user-friendly dashboard.

<a href="btc-rsis.png" target="_blank">
  <img src="btc-rsis.png" alt="Bitcoin Indicator Dashboard Screenshot" height="400" />
</a>

*Screenshot of the Bitcoin Indicator Dashboard (click to view full size)*

## Project Origin
This project is vibecoded: Original PRD by Grok 3, Implementation by Augment with Sonnet 3.7; Gemini 2.5 Pro Preview 05-06

## Key Features (v0.3.0)
- **Manual Indicator Implementations:** All 7 technical indicators (RSI, StochRSI, MFI, CRSI, Williams %R, RVI, AdaptiveRSI) are now manually implemented in Python, removing external TA library dependencies.
- **Modular Backend:**
    - Indicator calculations are split into individual modules (`backend/indicators/`).
    - Core logic is organized into services (`backend/services/`) for indicators, composite metrics, and price outcomes.
    - Centralized configuration in `backend/config.py`.
- **Shows Monthly and Weekly Values:** For all indicators.
- **Composite Metrics:** Composite Overbought Score (COS) & Bull Strength Index (BSI) with refined normalization.
- **Enhanced Time Machine:** View indicators for historical dates using calendar control, with price outcomes.
- **Data Sources Hierarchy:**
    1.  Primary: Local CSV files (`./csv/`) for bulk historical OHLCV data.
    2.  Secondary: CoinGecko API for recent daily data (past 365 days) if not in CSV/DB.
    3.  Tertiary: Kraken API as a fallback.
- **Database:** SQLite (`bitcoin_daily_data.db`) for storing daily OHLCV and calculated indicator sets.
- **Automated Docker Data Seeding:** On first run with an empty volume, the Docker entrypoint script automatically initializes the database schema and imports data from CSVs and manual filler scripts.
- **Frontend:** Single-page React application.
- **Utility Scripts:** For data management (CSV import, API loading, DB checks, manual fills, historical JSON generation).

## Architecture (v0.3.0)

The application has been significantly refactored for modularity and maintainability:

1.  **Backend (`backend/` directory)**:
    *   `config.py`: Central configuration for parameters, API keys (if any in future), etc.
    *   `main.py`: Main Flask application serving API endpoints.
    *   `db_utils.py`: Handles SQLite database interactions.
    *   `csv_data_loader.py`: Manages loading data from local CSV files.
    *   `api_clients.py`: Classes for CoinGecko and Kraken APIs.
    *   `data_sources.py`: Orchestrates data fetching from DB, CSV, and APIs.
    *   `indicator_calculator.py`: Main orchestrator for indicator calculations. Imports and uses:
        *   **`indicators/` (sub-directory):** Contains individual modules for each technical indicator (e.g., `rsi.py`, `mfi.py`), all manually implemented.
    *   **`services/` (sub-directory):**
        *   `indicator_service.py`: Core logic for `/api/indicators`.
        *   `composite_metrics_service.py`: Calculates COS and BSI.
        *   `outcome_service.py`: Calculates price outcomes.
2.  **Frontend (`index.html` & `components/` directory)**:
    *   React-based single-page application. UI components are split into separate `.js` files in the `components/` directory.
3.  **Data Storage (`bitcoin_daily_data.db`)**:
    *   SQLite database storing daily OHLCV prices and calculated indicator sets. Persisted via a Docker named volume.
4.  **Primary Data Sources**:
    *   `csv/`: User-provided CSV files for bulk historical data.
    *   `scripts/manual_data_filler.py` & `scripts/fill-in-20240331.py`: For manual data entries.
5.  **Historical Events Definition (`historical_data.json`)**:
    *   JSON file for predefined Time Machine events. Can be regenerated using `scripts/generate_historical_json.py`.
6.  **Utility Scripts (`scripts/` directory)**:
    *   `csv_importer.py`: Imports data from `./csv/`.
    *   `manual_data_filler.py`, `fill-in-20240331.py`: For manual data entries.
    *   `generate_historical_json.py`: Recalculates and generates `historical_data.json` based on current indicator logic.
    *   `api-loader.py`: For ad-hoc fetching to fill data gaps.
    *   `db_checker.py`: Checks for data gaps in the database.
7.  **Testing (`tests/modular/test_indicator_calc.py`)**:
    *   A script for verifying the output of the main indicator calculation pathway.

## Setup and Installation

### Prerequisites
- Docker and Docker Compose (highly recommended for ease of use and consistency).
- Python 3.9+ (Python 3.12 recommended) if developing locally without Docker.
- Pip (Python package installer).
- Make (optional, for using Makefile convenience targets for local development).

### Option 1: Using Docker (Recommended)
This method ensures a consistent environment and handles dependencies and data seeding.

1.  Ensure Docker and Docker Compose are installed.
2.  Make the start script executable: `chmod +x docker-start.sh`
3.  Run the start script:
    ```bash
    ./docker-start.sh
    ```
    *   This builds the Docker image and starts the backend and frontend services.
    *   **On the very first run with a new (or empty) `bitcoin_db_data` volume, the `docker-entrypoint.sh` script will automatically:**
        *   Initialize the database schema (`bitcoin_daily_data.db`).
        *   Import data from all CSV files in the `./csv/` directory.
        *   Run both manual data filler scripts (`scripts/manual_data_filler.py` and `scripts/fill-in-20240331.py`).
        *   A marker file (`.db_seeded_marker`) is created in the volume to prevent re-seeding on subsequent container starts.
4.  **Access:**
    *   Frontend: `http://localhost:8000`
    *   Backend API (example): `http://localhost:5001/api/indicators`
5.  **Manage Services:**
    *   View logs: `docker-compose logs -f`
    *   Stop services: `docker-compose down`
    *   Stop services and remove data volume (forces re-seed on next start): `docker-compose down -v`

### Option 2: Using Makefile (Local Development)
Useful if you prefer not to use Docker for local development.

1.  **Install Python dependencies:**
    ```bash
    make install
    ```
2.  **Database Setup & Full Initial Data Load (Run once, or if DB is deleted/corrupted):**
    *   **(Important)** If migrating from an older schema, delete `bitcoin_daily_data.db` manually first.
    *   This single command initializes the DB, imports CSVs, and runs both manual filler scripts:
        ```bash
        make import-all-sources
        ```
3.  **Check for and fill remaining data gaps (Optional but recommended):**
    *   Identify missing dates and get suggested `api-loader.py` commands:
        ```bash
        make check-db 
        ```
    *   Interactively run suggested commands to fill gaps:
        ```bash
        make load-gaps
        ```
4.  **Run the application:**
    ```bash
    make run
    ```
    This starts `backend/main.py` and a simple Python HTTP server for the frontend.

### Option 3: Manual Local Setup
Follow individual script steps if not using Docker or Make. Refer to the `Makefile` targets for the sequence of operations.

## Utility Scripts
Located in `scripts/`. Run from project root (e.g., `python3 scripts/script_name.py`).
*   **`csv_importer.py`**: Populates `daily_ohlcv` table from `./csv/` directory.
*   **`manual_data_filler.py` / `fill-in-20240331.py`**: For manually defined data entries.
*   **`db_checker.py`**: Checks for gaps in `daily_ohlcv`. `--generate_commands` is useful.
*   **`api-loader.py`**: Fills `daily_ohlcv` gaps using APIs for a specified date range.
*   **`generate_historical_json.py`**: Regenerates the `historical_data.json` file by calculating indicators for predefined historical event dates.

## Troubleshooting
- **"No module named 'backend.xxx'"**: Ensure Python commands/scripts are run from the project root directory. The test script in `tests/modular/` has path adjustments.
- **Database Issues (Local Setup):** If encountering schema errors or data inconsistencies after code changes, the safest bet is often to delete `bitcoin_daily_data.db`, then run `make import-all-sources`. For Docker, `docker-compose down -v` will clear the database volume, and it will be re-seeded on the next start.
- **API Rate Limiting (for `api-loader.py` or `generate_historical_json.py`):** The scripts include basic delays. For extensive backfilling, run `api-loader.py` in smaller date range batches.

## TODO / Future Enhancements
- **Extract UI Constants:** Move hardcoded text like indicator descriptions, tooltips, and UI labels from `IndicatorTable.js` and other components into a separate configuration file (e.g., `components/ui_config.js` or a JSON file) for easier management and potential internationalization.
- **Centralize Version Number:** The application version number (currently "v0.3.0") is duplicated in `CHANGELOG.md`, `README.md`, and potentially the frontend UI (`Header.js`). Implement a way to define this in one place (e.g., `backend/config.py` or a dedicated version file) and have other parts of the application (and documentation build process, if any) read from it.
- **Implement True Adaptive RSI:** The current "Adaptive RSI" uses RSI on KAMA-smoothed prices. A more sophisticated adaptive RSI would dynamically adjust its lookback period based on market volatility (e.g., using KAMA's Efficiency Ratio).
- **Signal Line for RVI:** The RVI calculation currently provides the main RVI line. Consider adding its typical signal line (e.g., a 4-period SMA of RVI) for more complete analysis.
- **Unit Tests for Indicators:** While `tests/modular/test_indicator_calc.py` provides good functional verification, true unit tests for each individual indicator calculation in `backend/indicators/` with known inputs and outputs would improve robustness.
- **Frontend Build System:** For more complex frontend development, consider integrating a build system like Vite or Create React App instead of relying on CDN scripts and Babel standalone.