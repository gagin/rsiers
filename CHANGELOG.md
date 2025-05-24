# Changelog

All notable changes to the Bitcoin Dashboard project will be documented in this file.

## [0.3.0] - 2024-05-23 

### Added
- **Configuration File (`backend/config.py`):** Centralized configuration for indicator parameters, composite metric weights/thresholds/neutral points, API client settings, and other application settings.
- **Modular Indicator Calculations (`backend/indicators/`):**
    - Each of the seven technical indicators (RSI, StochRSI, MFI, CRSI, Williams %R, RVI, AdaptiveRSI) now has its calculation logic encapsulated in its own Python module within the `backend/indicators/` directory.
    - Implementations are now manual using Pandas/NumPy, removing external TA library dependencies (like `stock-indicators` or `pandas-ta`'s direct use).
- **Dedicated Service Layer (`backend/services/`):**
    - `indicator_service.py`: Orchestrates fetching/calculating full indicator sets for API responses.
    - `composite_metrics_service.py`: Handles calculation of COS and BSI, now using parameters from `config.py`.
    - `outcome_service.py`: Handles calculation of future price outcomes.
- **Docker Entrypoint Script (`docker-entrypoint.sh`):**
    - Automates database schema initialization and data seeding (CSVs, manual filler scripts) on first container run with an empty volume.
    - Uses a marker file (`.db_seeded_marker`) to prevent re-seeding on subsequent starts.
- **Calculation Verification Script (`tests/modular/test_indicator_calc.py`):**
    - Script to test the main indicator calculation pathway (`calculate_indicators_from_ohlc_df`) for weekly and monthly timeframes using sample data.
- **Makefile Target `import-all-sources`:** New make target to initialize the DB and run all primary data import scripts (CSVs, manual fillers).

### Changed
- **Refactored `backend/indicator_calculator.py`:**
    - Now acts as an orchestrator, importing individual indicator modules from `backend/indicators/`.
    - Wrapper functions call the respective indicator modules, fetching parameters from `config.py` based on timeframe.
    - Dynamically adjusts parameters (e.g., CRSI `rank_len`, StochRSI periods, AdaptiveRSI KAMA periods) for monthly vs. weekly calculations to better suit available data length (typically 2 years of daily history).
    - `calculate_composite_metrics_for_api` and `calculate_price_outcomes` moved to their respective service files.
- **Refactored `backend/main.py`:**
    - Slimmed down API endpoint logic, delegating core work to services in `backend/services/`.
    - `/api/historical_time_points` endpoint now uses `composite_metrics_service.calculate_composite_metrics` to ensure consistency and remove legacy 'tsi' handling.
- **Composite Metrics Calculation (`composite_metrics_service.py`):**
    - Unified normalization logic for all indicators contributing to COS, ensuring they are scaled appropriately relative to their neutral points and thresholds before weighting.
    - Williams %R is now correctly normalized for COS.
- **Docker Configuration:**
    - `Dockerfile`: Updated `CMD` to `["python", "backend/main.py"]`. Added `ENTRYPOINT` to use `docker-entrypoint.sh`. Removed `make` dependency from the image, as entrypoint now calls Python scripts directly.
    - `docker-compose.yml`: Updated backend service `command` to `python backend/main.py`. Database volume path corrected to `/app`. Healthcheck and startup parameters refined.
- **`Makefile`:**
    - Added `manual-fill-main` and `manual-fill-specific` targets.
    - Updated `load-gaps` target for better command execution.
- **Logging:** Improved logging across various modules for better diagnostics, including pandas version checks and intermediate calculation steps for debugging.
- **Indicator Implementations:** All indicators are now manually implemented, providing full control and transparency, and removing previous external library issues.

### Fixed
- Resolved `TypeError: NDFrame.fillna() got an unexpected keyword argument 'where'` in MFI calculation by using a universally compatible `.loc` based conditional fill. (Though this was a symptom of a suspected environment issue with pandas versions, the fix is robust).
- Corrected various `ImportError` issues related to module refactoring and script execution paths.
    - Fixed `ImportError` for `resample_ohlc_data` in `scripts/generate_historical_json.py`.
    - Fixed `SyntaxError: invalid syntax` in `api_clients.py` related to an alias.
- Addressed `TypeError: calculate_stoch_rsi_series() got an unexpected keyword argument 'rsi_length'` by aligning wrapper function signatures and calls in `indicator_calculator.py` and test scripts.
- Resolved issue where monthly StochRSI, CRSI, and AdaptiveRSI were consistently `null` by:
    - Adjusting `MIN_CANDLES_FOR_CALCULATION`.
    - Implementing timeframe-specific (shorter) parameters for these indicators when calculating on monthly data.
    - Refining data length checks within individual indicator calculation modules.
- Ensured `IndicatorTable.js` on the frontend is more robust against `null` or non-numeric indicator values to prevent `.toFixed()` errors, especially when exiting Time Machine mode.

## [0.2.2] - 2024-05-23

### Changed
- **Backend Refactoring**:
  - Split backend logic into modular files: `main.py`, `db_utils.py`, `csv_data_loader.py`, `api_clients.py`, `data_fetch_orchestrator.py`, `indicator_calculator.py` located in a new `backend/` directory.
  - Updated `app2.py` to `backend/main.py` to serve as the main Flask application.
  - Database schema (`daily_ohlcv`, `calculated_indicators`) now uses 'YYYY-MM-DD' TEXT strings for date keys instead of integer timestamps, normalized to 00:00:00 UTC. `init_db` in `db_utils.py` handles table creation and adds `calculated_at` column if missing (manual DB deletion recommended for timestamp type change).
  - `CSVDataLoader` now instantiated locally in `fetch_and_store_daily_ohlcv` to ensure fresh CSV loading context.
  - Improved logging in data fetching an_d CSV loading processes for better diagnostics.
  - Kraken API client (`KrakenAPI.get_ohlcv_for_date`) updated to attempt fetching a slightly wider window if an exact 00:00:00 UTC candle is not immediately found for the target date.
- **Utility Scripts (`scripts/` directory)**:
  - Renamed `fill-in-20240331.py` to `manual_data_filler.py` for generic use.
  - All scripts (`api-loader.py`, `csv_importer.py`, `db_checker.py`, `manual_data_filler.py`) updated to use the new backend modules and handle 'YYYY-MM-DD' date strings.
  - `db_checker.py` now outputs suggested `api-loader.py` commands for identified data gaps.
- **Makefile**: Updated to reflect new script names, `backend/main.py` usage, and added new targets (`init-db`, `import-csv`, `check-db`, `load-gaps`, `manual-fill`). Python interpreter explicitly set to `python3`.
- **README.md & CODEBASE.md**: Updated to reflect the new project structure, data flow, and script functionalities.

### Fixed
- Resolved `NameError: name 'iso_string_to_date' is not defined` in `backend/data_sources.py` by adding the missing import from `backend.db_utils`.
- Addressed Pandas `FutureWarning` for 'M' resampling by changing to 'ME' (Month End) in `indicator_calculator.py`.
- Mitigated potential `TypeError: Cannot read properties of undefined (reading 'monthly')` on frontend by ensuring backend returns structured error + available data (like price) instead of a hard 500 error if full indicators can't be calculated due to insufficient history.

## [0.2.1] - 2024-05-23

### Added
- Added detailed logging for CoinGecko API calls and responses
- Added a debug button in the footer to show API call status in the console
- Added tracking of successful and failed API calls
- Added helper function to check if dates are in the future
- Added more accurate UI indicators for when interpolated data is being used

### Changed
- Removed monthly/weekly selector buttons, now always showing both timeframes
- Moved the Refresh/Retry button to the right side of the header
- Updated status indicators to accurately show when interpolated data is being used
- Improved error handling for CoinGecko API calls
- Enhanced date formatting for the CoinGecko API
- Updated UI to clearly indicate when interpolated data is being used instead of actual API data

### Fixed
- Fixed issue with incorrect price data being displayed for certain dates
- Fixed misleading UI that showed "Historical Data from CoinGecko API" even when using interpolated data
- Fixed Babel parsing errors by using proper React.Fragment syntax

## [0.2.0] - Initial Release

### Features
- Bitcoin technical indicators dashboard
- Real-time data from Kraken API
- Historical data visualization
- Time machine feature to view past market conditions
- Composite Overbought Score (COS)
- Bull Strength Index (BSI)
- Responsive design
- Automatic fallback to mock data when backend is unavailable
