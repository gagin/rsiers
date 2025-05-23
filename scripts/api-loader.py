# scripts/api-loader.py
import argparse
import datetime as dt # Alias to avoid conflict with datetime class from datetime module
from datetime import timezone # Explicitly import timezone
import time
import logging
import os
import sys

# Adjust Python path to include the project root so backend modules can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports from shared backend modules
from backend.db_utils import init_db as init_db_main, get_daily_ohlcv_from_db
from backend.data_sources import fetch_and_store_daily_ohlcv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Populate bitcoin_daily_data.db from external APIs via backend modules.")
    parser.add_argument("--start_date", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--days", required=True, type=int, help="Number of days to fetch data for.")
    args = parser.parse_args()

    # Ensure the database and tables are initialized using the shared utility
    init_db_main() 

    try:
        start_dt_naive = dt.datetime.strptime(args.start_date, "%Y-%m-%d")
        # Convert to datetime object, ensure it's UTC and start of day
        start_dt_utc = start_dt_naive.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    except ValueError:
        logger.error("Invalid start_date format. Please use YYYY-MM-DD.")
        return

    logger.info(f"API Loader: Starting data load: Start Date={args.start_date}, Days={args.days}")

    for i in range(args.days):
        # Calculate current date for this iteration
        current_date_utc = start_dt_utc + dt.timedelta(days=i)
        
        logger.info(f"API Loader: Processing date: {current_date_utc.strftime('%Y-%m-%d')}")
        
        api_call_attempted_for_this_date = False

        # Check DB using the datetime object; db_utils will handle string conversion for query
        db_data = get_daily_ohlcv_from_db(current_date_utc) 
        if db_data:
            logger.info(f"API Loader: Data for {current_date_utc.strftime('%Y-%m-%d')} already in DB. Source: {db_data.get('source')}. Skipping API fetch.")
        else:
            logger.info(f"API Loader: Data for {current_date_utc.strftime('%Y-%m-%d')} not in DB. Attempting fetch via backend.data_sources.")
            api_call_attempted_for_this_date = True
            
            # fetch_and_store_daily_ohlcv expects a datetime object
            fetched_data_values, error_message = fetch_and_store_daily_ohlcv(current_date_utc)
            
            if fetched_data_values: # This is the dict of ohlcv values, not the db storage dict
                logger.info(f"API Loader: Successfully fetched and stored data for {current_date_utc.strftime('%Y-%m-%d')} from source: {fetched_data_values.get('source')}.")
            else:
                logger.error(f"API Loader: Failed to get data for {current_date_utc.strftime('%Y-%m-%d')}. Error: {error_message}")
        
        if api_call_attempted_for_this_date and (i < args.days - 1):
            logger.info(f"API Loader: Waiting for 3 seconds before processing next date (API call was attempted for {current_date_utc.strftime('%Y-%m-%d')})...")
            time.sleep(3)
        elif not api_call_attempted_for_this_date and (i < args.days - 1) :
            # Optional: a very short delay or no delay if data was found in DB
            # time.sleep(0.1) 
            pass


    logger.info("API Loader: Data loading process finished.")

if __name__ == "__main__":
    main()