# Changelog

All notable changes to the Bitcoin Dashboard project will be documented in this file.

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
