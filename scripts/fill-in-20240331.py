# scripts/manual_data_filler.py

import datetime as dt # Alias datetime module
from datetime import timezone # Explicitly import timezone
import logging
import os
import sys

# Adjust Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db_utils import init_db as init_db_main, store_daily_ohlcv_data, DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DATA TO BE MANUALLY FILLED ---
# Add dictionaries to this list for each day you want to manually insert/update.
# Ensure the date_str format matches what datetime.strptime expects (e.g., "%b %d, %Y").
data_to_fill = [
    {
        "date_str": "Mar 31, 2024", # Example: Data for March 31, 2024
        "open_str": "69,647.78",
        "high_str": "71,377.78",
        "low_str": "69,624.87",
        "close_str": "71,333.65", # Using 'Close', not 'Adj Close'
        "volume_str": "20,050,941,373",
        "source": "manual_fill_yahoo_finance" # Specify your actual source
    },
    # Example for another day:
    # {
    #     "date_str": "Mar 30, 2024",
    #     "open_str": "69,893.45",
    #     "high_str": "70,355.49",
    #     "low_str": "69,601.06",
    #     "close_str": "69,645.30",
    #     "volume_str": "17,130,241,883",
    #     "source": "manual_fill_yahoo_finance"
    # }
]

def parse_value(value_str: str) -> float:
    """Removes commas and converts to float."""
    return float(str(value_str).replace(',', ''))

def main():
    logger.info(f"Starting manual data fill script. DB: {DB_PATH}")
    init_db_main() # Ensure tables exist with the correct schema

    if not data_to_fill:
        logger.info("No data specified in the 'data_to_fill' list. Exiting.")
        return

    entries_processed = 0
    entries_failed = 0

    for entry in data_to_fill:
        try:
            # Parse the date string (e.g., "Mar 31, 2024")
            date_obj_naive = dt.datetime.strptime(entry["date_str"], "%b %d, %Y")
            # Convert to datetime object, ensure it's UTC and start of day
            date_obj_utc_start_of_day = date_obj_naive.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

            ohlcv_values = {
                'open': parse_value(entry["open_str"]),
                'high': parse_value(entry["high_str"]),
                'low': parse_value(entry["low_str"]),
                'close': parse_value(entry["close_str"]),
                'volume': parse_value(entry["volume_str"]),
                'source': entry["source"],
            }
            
            logger.info(f"Attempting to store data for {entry['date_str']} (Normalized UTC date: {date_obj_utc_start_of_day.strftime('%Y-%m-%d')})")
            # store_daily_ohlcv_data expects a datetime object for the date key, and a dict of values
            store_daily_ohlcv_data(date_obj_utc_start_of_day, ohlcv_values)
            entries_processed +=1

        except ValueError as ve:
            logger.error(f"Skipping entry due to ValueError parsing data for '{entry['date_str']}': {ve}")
            entries_failed +=1
        except Exception as e:
            logger.error(f"An unexpected error occurred processing entry for '{entry['date_str']}': {e}", exc_info=True)
            entries_failed +=1

    logger.info(f"Manual data fill script finished. Processed: {entries_processed}, Failed: {entries_failed}")

if __name__ == "__main__":
    main()