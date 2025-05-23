# scripts/db_checker.py

import argparse
import datetime as dt # Alias for clarity
from datetime import timezone # For UTC awareness
import sqlite3
import logging
import os
import sys
import pandas as pd # Keep for pd.date_range if used extensively, or remove if only basic date math

# Adjust Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db_utils import DB_PATH, iso_string_to_date # Use iso_string_to_date for consistency

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_data_gaps(start_date_str=None, end_date_str=None, list_sources=False, generate_commands=False):
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Query date_str directly
        cursor.execute("SELECT date_str FROM daily_ohlcv ORDER BY date_str ASC")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        logger.error(f"Error querying database: {e}. Table 'daily_ohlcv' or 'date_str' column might not exist.")
        conn.close()
        return
        
    if not rows:
        logger.info("The daily_ohlcv table is empty. No data to check.")
        if start_date_str and end_date_str and generate_commands:
            try:
                s_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                e_date = dt.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if s_date <= e_date:
                    num_days = (e_date - s_date).days + 1
                    logger.info(f"Suggested command for empty DB in range: python scripts/api-loader.py --start_date={s_date.strftime('%Y-%m-%d')} --days={num_days}")
            except ValueError:
                logger.error("Invalid date format for generating command on empty DB.")
        conn.close()
        return

    # Convert 'YYYY-MM-DD' strings from DB to datetime.date objects for the set
    existing_dates = {iso_string_to_date(row[0]) for row in rows}
    conn.close() # Close connection after fetching all dates
    
    min_db_date = min(existing_dates) if existing_dates else None
    max_db_date = max(existing_dates) if existing_dates else None

    if min_db_date and max_db_date:
        logger.info(f"Database contains data from {min_db_date.strftime('%Y-%m-%d')} to {max_db_date.strftime('%Y-%m-%d')}.")
    else:
        logger.info("Database has no valid date entries.")
        return

    try:
        check_start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else min_db_date
        check_end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else max_db_date
    except ValueError:
        logger.error("Invalid start_date or end_date format. Please use YYYY-MM-DD.")
        return
    
    if not check_start_date or not check_end_date or check_start_date > check_end_date:
        logger.error("Invalid date range for checking. Ensure start_date is before or same as end_date, and DB is not empty if no range provided.")
        return

    logger.info(f"Checking for gaps from {check_start_date.strftime('%Y-%m-%d')} to {check_end_date.strftime('%Y-%m-%d')}.")

    current_iter_date = check_start_date
    missing_dates_count = 0
    gap_blocks = []
    current_gap_start = None

    while current_iter_date <= check_end_date:
        if current_iter_date not in existing_dates:
            missing_dates_count += 1
            if current_gap_start is None:
                current_gap_start = current_iter_date
        else: # current_iter_date IS in existing_dates
            if current_gap_start is not None:
                gap_end_date = current_iter_date - dt.timedelta(days=1)
                gap_blocks.append((current_gap_start, gap_end_date))
                current_gap_start = None
            
            if list_sources:
                # Re-open connection for this detail query
                conn_detail = sqlite3.connect(DB_PATH)
                cursor_detail = conn_detail.cursor()
                # Query using the date string format
                date_key_str_for_source = current_iter_date.strftime('%Y-%m-%d')
                cursor_detail.execute("SELECT source FROM daily_ohlcv WHERE date_str = ?", (date_key_str_for_source,))
                source_row = cursor_detail.fetchone()
                conn_detail.close()
                source_info = source_row[0] if source_row else "ERROR_FETCHING_SOURCE"
                logger.info(f"Data present for {current_iter_date.strftime('%Y-%m-%d')}. Source: {source_info}")

        current_iter_date += dt.timedelta(days=1)

    if current_gap_start is not None: # If the loop finished while in a gap
        gap_blocks.append((current_gap_start, check_end_date)) 

    if not gap_blocks:
        logger.info("No gaps found in the specified date range.")
    else:
        logger.warning(f"Total missing days found: {missing_dates_count}")
        logger.info("--- Identified Gaps ---")
        for start, end in gap_blocks:
            num_days_in_gap = (end - start).days + 1
            logger.warning(f"Gap: From {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} ({num_days_in_gap} days)")
            if generate_commands:
                logger.info(f"  Suggested command: python scripts/api-loader.py --start_date={start.strftime('%Y-%m-%d')} --days={num_days_in_gap}")
        logger.info("---------------------")

def main():
    parser = argparse.ArgumentParser(description="Check for data gaps in the bitcoin_daily_data.db")
    parser.add_argument("--start_date", help="Start date to check from (YYYY-MM-DD). Defaults to earliest date in DB.")
    parser.add_argument("--end_date", help="End date to check until (YYYY-MM-DD). Defaults to latest date in DB.")
    parser.add_argument("--list_sources", action="store_true", help="List the source of data for each day checked.")
    parser.add_argument("--generate_commands", action="store_true", help="Generate api-loader.py commands for missing date ranges.")
    args = parser.parse_args()

    check_data_gaps(args.start_date, args.end_date, args.list_sources, args.generate_commands)

if __name__ == "__main__":
    main()