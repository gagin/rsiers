
## File Descriptions

### Backend (`backend/` directory)

-   **`config.py`**: New. Central configuration file for parameters related to indicators (periods, smoothing), composite metrics (weights, thresholds, neutral points), API client settings (URLs, retry logic), and other application-level settings.
-   **`main.py`**: The main Flask application.
    -   Initializes the database via `db_utils.py`.
    -   Defines API endpoints: `/api/indicators`, `/api/historical_time_points`, `/api/refresh`.
    -   Delegates core logic for `/api/indicators` to `services/indicator_service.py`.
    -   Uses `services/composite_metrics_service.py` for processing `historical_data.json`.
-   **`db_utils.py`**: Handles all SQLite database interactions (`bitcoin_daily_data.db`).
    -   Defines database schema (tables `daily_ohlcv`, `calculated_indicators`).
    -   Provides functions to store/retrieve daily OHLCV and calculated indicator sets.
-   **`csv_data_loader.py`**: Contains `CSVDataLoader` class for loading and querying data from `./csv/` files.
-   **`api_clients.py`**: Contains `CoinGeckoAPI` and `KrakenAPI` classes for external data fetching. Uses URLs and retry parameters from `config.py`.
-   **`data_sources.py`**: Orchestrates fetching daily OHLCV data.
    -   `fetch_and_store_daily_ohlcv`: Prioritizes DB, then global CSV instance, then APIs.
    -   `get_historical_data_for_indicators`: Assembles historical daily OHLCV for indicator input, uses `config.HISTORICAL_DATA_YEARS`.
-   **`indicator_calculator.py`**: Orchestrates the calculation of technical indicators.
    -   Imports individual calculation modules from `backend/indicators/`.
    -   Contains wrapper functions (e.g., `calculate_rsi_series`) that fetch parameters from `config.py` (via `config.get_indicator_params`) and call the respective specialized indicator module.
    -   Includes `resample_ohlc_data` to convert daily data to weekly/monthly.
    -   `calculate_indicators_from_ohlc_df`: Main function called by services to get a dictionary of all indicator values for a given resampled OHLCV DataFrame and timeframe.
-   **`indicators/` (sub-package)**: New. Contains individual Python modules for each of the seven technical indicators.
    -   Each module (e.g., `rsi.py`, `mfi.py`) has a `calculate()` function that performs the manual calculation for that specific indicator using Pandas/NumPy.
-   **`services/` (sub-package)**: New. Contains modules for higher-level service logic.
    -   `indicator_service.py`: Encapsulates the full workflow for the `/api/indicators` endpoint (caching, data fetching orchestration, indicator calculation orchestration, composite metrics, outcomes, DB storage).
    -   `composite_metrics_service.py`: Contains `calculate_composite_metrics` for COS and BSI, using parameters from `config.py`.
    -   `outcome_service.py`: Contains `calculate_price_outcomes` for 1M, 6M, 12M price changes.

### Frontend (`index.html` and `components/` directory)

-   **`index.html`**: Single-page React application entry point. Loads React, ReactDOM, Axios, Tailwind CSS from CDNs, and Babel for in-browser JSX transpilation. Includes script tags to load individual React component files.
-   **`components/`**: New directory containing JavaScript files for individual React components (e.g., `App.js`, `Header.js`, `IndicatorTable.js`, `TimeMachine.js`, `Footer.js`, etc.), making the frontend code modular.

### Data Files & Configuration

-   **`csv/`**: Directory for user-provided CSV files with historical OHLCV data. Primary source for bulk history.
-   **`historical_data.json`**: Defines significant historical market events for the Time Machine. Values here can be generated/updated by `scripts/generate_historical_json.py`.
-   **`bitcoin_daily_data.db`**: SQLite database (created at runtime, persisted in Docker via a named volume). Stores daily OHLCV and cached calculated indicator sets.

### Utility Scripts (`scripts/` directory)

-   **`csv_importer.py`**: Imports data from all CSVs in `./csv/` into the `daily_ohlcv` table.
-   **`manual_data_filler.py` & `fill-in-20240331.py`**: Allow manual insertion/update of OHLCV data for specific dates.
-   **`api-loader.py`**: Fetches missing daily OHLCV data for a specified date range using the backend's data sourcing logic.
-   **`db_checker.py`**: Analyzes `daily_ohlcv` table for gaps and can suggest `api-loader.py` commands.
-   **`generate_historical_json.py`**: New. Script to programmatically generate/update `historical_data.json` by calculating all indicators, composites, and outcomes for predefined historical event dates using the application's current logic.

### Testing (`tests/modular/` directory)

-   **`test_indicator_calc.py`**: New. A script for functional testing of the main indicator calculation pathway (`calculate_indicators_from_ohlc_df`), using sample data for weekly and monthly timeframes.

### Setup, Build, and Deployment

-   **`requirements.txt`**: Lists Python package dependencies.
-   **`Makefile`**: Contains convenience commands for local development (installation, running servers, database operations, data imports, Docker commands). Includes new `import-all-sources` target.
-   **`Dockerfile`**: Defines the Docker image for the backend application. Now uses `docker-entrypoint.sh`.
-   **`docker-compose.yml`**: Orchestrates backend and frontend services. Database data is persisted in a named volume (`bitcoin_db_data`).
-   **`docker-entrypoint.sh`**: New. Script executed when the Docker container starts. Handles database schema initialization and automatic data seeding (CSVs, manual fillers) on first run with an empty volume, using a marker file to prevent re-seeding.
-   **`docker-start.sh`**: Host script to build and run the application using Docker Compose.

### Documentation
-   **`PRD.txt`**: Product Requirements Document.
-   **`README.md`**: Project overview, setup, and usage instructions (updated for v0.3.0).
-   **`CODEBASE.md`**: This document (updated for v0.3.0).
-   **`CHANGELOG.md`**: Tracks notable changes (updated for v0.3.0).

## Data Flow for `/api/indicators?date=YYYY-MM-DD` (v0.3.0)

1.  `backend/main.py` (`get_indicators_api` route) receives request.
2.  Calls `get_indicator_data(target_date_obj_utc)` in `backend/services/indicator_service.py`.
3.  **`indicator_service.py` (`get_indicator_data`):**
    a.  Checks `calculated_indicators` DB table for cached data. If fresh cache hit, formats and returns.
    b.  If no/stale cache:
        i.  Calls `get_historical_data_for_indicators` (in `backend/data_sources.py`) for a N-year window (from `config.py`) of daily OHLCV data. This involves:
            1.  Checking DB (`get_daily_ohlcv_from_db`).
            2.  If miss, checking global CSV instance (`CSVDataLoader`).
            3.  If miss, trying CoinGecko/Kraken APIs (`api_clients.py`).
            4.  Storing any newly fetched daily data into `daily_ohlcv` DB table.
            5.  Returns a Pandas DataFrame of daily OHLCV.
        ii. Determines `price_at_event` (usually last close from the daily DataFrame or fetched for the target date).
        iii.Calls `resample_ohlc_data` (in `backend/indicator_calculator.py`) to get weekly and monthly OHLCV DataFrames.
        iv. Calls `calculate_indicators_from_ohlc_df` (in `backend/indicator_calculator.py`) for both weekly and monthly DataFrames. This function:
            1.  Fetches parameters from `backend/config.py` based on `timeframe_label`.
            2.  Calls wrapper functions (e.g., `calculate_rsi_series`) which in turn call the `calculate()` methods in the respective `backend/indicators/*.py` modules.
        v.  Calls `calculate_composite_metrics` (from `backend/services/composite_metrics_service.py`).
        vi. Calls `calculate_price_outcomes` (from `backend/services/outcome_service.py`).
    c.  Stores the complete new set (price, indicators, composites, outcomes) into `calculated_indicators` DB table via `store_full_indicator_set`.
    d.  Formats and returns the data.
4.  `backend/main.py` receives the dictionary from the service and returns it as a JSON response.

This structure provides a clear separation of concerns and a more maintainable and configurable backend.