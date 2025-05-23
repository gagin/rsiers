# scripts/csv_importer.py

import argparse
import datetime as dt 
from datetime import timezone
import logging
import os
import sys
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db_utils import init_db as init_db_main, store_daily_ohlcv_data
from backend.csv_data_loader import CSV_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_csv_to_db(csv_filepath):
    count_imported = 0
    count_skipped = 0
    try:
        df = pd.read_csv(csv_filepath, header=None, names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades'])
        if df.empty:
            logger.info(f"CSV file {csv_filepath} is empty. Skipping.")
            return 0, 0

        logger.info(f"Processing {len(df)} rows from {csv_filepath}...")

        for index, row in df.iterrows():
            try:
                ts_sec = int(row['timestamp'])
                # Convert Unix timestamp to datetime object, ensure it's UTC
                dt_obj_utc = dt.datetime.fromtimestamp(ts_sec, tz=timezone.utc)
                # Normalize to start of day for consistent keying, db_utils will handle string conversion
                dt_obj_utc_start_of_day = dt_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)

                data_values = { # This is the dict format expected by store_daily_ohlcv_data's second arg
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'source': 'csv_import',
                }
                # store_daily_ohlcv_data expects a datetime object for the date key
                store_daily_ohlcv_data(dt_obj_utc_start_of_day, data_values)
                count_imported += 1
            except ValueError as ve:
                logger.error(f"Skipping row due to ValueError in {csv_filepath} at row {index+1}: {row.values.tolist()}. Error: {ve}")
                count_skipped +=1
            except Exception as e:
                logger.error(f"Error processing row in {csv_filepath} at row {index+1}: {row.values.tolist()}. Error: {e}")
                count_skipped +=1
                
        logger.info(f"Finished processing {csv_filepath}. Imported/Replaced: {count_imported}, Skipped: {count_skipped}")
        return count_imported, count_skipped
        
    except pd.errors.EmptyDataError:
        logger.warning(f"CSV file {csv_filepath} is empty or unreadable. Skipping.")
        return 0, 0
    except Exception as e:
        logger.error(f"Failed to read or process CSV file {csv_filepath}: {e}")
        return 0, 0

def main():
    parser = argparse.ArgumentParser(description="Import historical Bitcoin data from CSV files into the database.")
    parser.add_argument("--csv_directory", default=CSV_DIR, help=f"Directory containing CSV files (default: {CSV_DIR})")
    args = parser.parse_args()

    init_db_main() 

    if not os.path.isdir(args.csv_directory):
        logger.error(f"CSV directory not found: {args.csv_directory}")
        return

    logger.info(f"Starting CSV import from directory: {args.csv_directory}")
    total_imported_all_files = 0
    total_skipped_all_files = 0

    for filename in os.listdir(args.csv_directory):
        if filename.lower().endswith(".csv"):
            filepath = os.path.join(args.csv_directory, filename)
            logger.info(f"Importing data from: {filepath}")
            imported, skipped = import_csv_to_db(filepath)
            total_imported_all_files += imported
            total_skipped_all_files += skipped
            if imported == 0 and skipped == 0:
                 # Check if file was truly empty or just had processing issues
                try:
                    if not pd.read_csv(filepath).empty:
                         logger.warning(f"No records processed from non-empty file: {filepath}. Check format or content for parsing errors.")
                except pd.errors.EmptyDataError:
                    pass # Already logged as empty by import_csv_to_db
                except Exception as e_read:
                    logger.warning(f"Could not re-check if file {filepath} was empty due to read error: {e_read}")


    logger.info(f"CSV import process finished. Total records imported/replaced: {total_imported_all_files}, Total records skipped: {total_skipped_all_files}")

if __name__ == "__main__":
    main()