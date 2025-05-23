# backend/csv_data_loader.py
import os
import logging
import pandas as pd
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Define constants relative to project root
# Assuming this file is in backend/, and csv/ is in project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(PROJECT_ROOT, 'csv/')

class CSVDataLoader:
    def __init__(self, csv_dir_path=CSV_DIR):
        self.csv_dir = csv_dir_path
        self.df = None # DataFrame with DatetimeIndex (UTC)
        self.min_date_in_csv = None
        self.max_date_in_csv = None
        
        logger.info(f"CSVDataLoader: Initializing with csv_dir_path: {csv_dir_path}")
        logger.info(f"CSVDataLoader: Resolved self.csv_dir to: {self.csv_dir}")
        if os.path.exists(self.csv_dir) and os.path.isdir(self.csv_dir):
            logger.info(f"CSVDataLoader: Directory {self.csv_dir} exists.")
            try:
                files_in_dir = os.listdir(self.csv_dir)
                logger.info(f"CSVDataLoader: Files in {self.csv_dir}: {files_in_dir}")
                if not any(f.lower().endswith(".csv") for f in files_in_dir):
                    logger.warning(f"CSVDataLoader: No .csv files found in {self.csv_dir}")
            except Exception as e:
                logger.error(f"CSVDataLoader: Error listing files in {self.csv_dir}: {e}")
        else:
            logger.error(f"CSVDataLoader: Directory {self.csv_dir} DOES NOT EXIST or is not a directory.")
            
        self._load_all_csvs()

    def _load_all_csvs(self):
        all_dfs = []
        if not os.path.isdir(self.csv_dir): 
            return # Already logged in __init__
        
        found_csv_files_in_loop = False
        for filename in os.listdir(self.csv_dir):
            if filename.lower().endswith(".csv"):
                found_csv_files_in_loop = True
                filepath = os.path.join(self.csv_dir, filename) 
                logger.debug(f"CSVDataLoader: Attempting to load CSV: {filepath}")
                try:
                    temp_df = pd.read_csv(
                        filepath, 
                        header=None, 
                        names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades'],
                        dtype={'timestamp': str, 'open': str, 'high': str, 'low': str, 'close': str, 'volume': str, 'trades': str},
                        keep_default_na=False, na_values=[''] 
                    )
                    if temp_df.empty:
                        logger.warning(f"CSVDataLoader: CSV file {filepath} is empty or contains no data rows.")
                        continue

                    temp_df['timestamp'] = pd.to_numeric(temp_df['timestamp'], errors='coerce')
                    temp_df['open'] = pd.to_numeric(temp_df['open'], errors='coerce')
                    temp_df['high'] = pd.to_numeric(temp_df['high'], errors='coerce')
                    temp_df['low'] = pd.to_numeric(temp_df['low'], errors='coerce')
                    temp_df['close'] = pd.to_numeric(temp_df['close'], errors='coerce')
                    temp_df['volume'] = pd.to_numeric(temp_df['volume'], errors='coerce')
                    
                    temp_df.dropna(subset=['timestamp', 'open', 'high', 'low', 'close', 'volume'], inplace=True)
                    if temp_df.empty:
                        logger.warning(f"CSVDataLoader: No valid numeric data rows found in {filepath} after conversion.")
                        continue

                    temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], unit='s', utc=True).dt.normalize()
                    all_dfs.append(temp_df)
                except Exception as e:
                    logger.error(f"CSVDataLoader: Error loading or processing CSV file {filepath}: {e}")
        
        if not found_csv_files_in_loop and os.path.isdir(self.csv_dir):
            logger.warning(f"CSVDataLoader: No files ending with .csv found in directory: {self.csv_dir}")

        if all_dfs:
            self.df = pd.concat(all_dfs).drop_duplicates(subset=['timestamp']).set_index('timestamp').sort_index()
            logger.info(f"CSVDataLoader: Loaded {len(self.df)} unique records from CSV files.")
            if not self.df.empty:
                self.min_date_in_csv = self.df.index.min().date()
                self.max_date_in_csv = self.df.index.max().date()
                logger.info(f"CSVDataLoader: CSV data range: {self.min_date_in_csv} to {self.max_date_in_csv}")
            if not self.df.index.is_monotonic_increasing:
                 logger.warning("CSVDataLoader: DataFrame index is not monotonically increasing. Sorting again.")
                 self.df.sort_index(inplace=True)
        else:
            if found_csv_files_in_loop: # Only log this if CSVs were found but resulted in no data
                 logger.warning(f"CSVDataLoader: No valid data loaded from CSV files in {self.csv_dir}, though .csv files were present.")

    def get_ohlcv_for_date(self, date_obj_utc: datetime): 
        if self.df is None or self.df.empty:
            logger.debug(f"CSVDataLoader: DataFrame is None or empty. Cannot fetch {date_obj_utc.date()}.")
            return None
        
        target_date_date = date_obj_utc.date()

        if self.min_date_in_csv and self.max_date_in_csv:
            if not (self.min_date_in_csv <= target_date_date <= self.max_date_in_csv):
                logger.debug(f"CSVDataLoader: Requested date {target_date_date} is outside CSV range ({self.min_date_in_csv} - {self.max_date_in_csv}).")
                return None
        
        try:
            day_start_utc_dt_obj = date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if day_start_utc_dt_obj in self.df.index:
                row = self.df.loc[day_start_utc_dt_obj]
                logger.debug(f"CSVDataLoader: Exact timestamp match found for {target_date_date} in CSV.")
                return {'open': row['open'], 'high': row['high'], 'low': row['low'],
                        'close': row['close'], 'volume': row['volume'], 'source': 'csv_exact'}
            else: # Fallback for days that might not have 00:00:00 UTC entry
                data_on_day = self.df[self.df.index.date == target_date_date]
                if not data_on_day.empty:
                    row = data_on_day.iloc[0] 
                    logger.debug(f"CSVDataLoader: Found data for {target_date_date} within the day (first entry timestamp: {data_on_day.index[0]}). Using this for day start.")
                    return {'open': row['open'], 'high': row['high'], 'low': row['low'],
                            'close': row['close'], 'volume': row['volume'], 'source': 'csv_day_match'}
                else:
                    logger.debug(f"CSVDataLoader: No data found for {target_date_date} in CSV, either by exact timestamp or by date match.")
                    
        except KeyError: 
            logger.debug(f"CSVDataLoader: KeyError for {target_date_date}. Date not in CSV index.")
            return None
        except Exception as e:
            logger.error(f"CSVDataLoader: Error accessing CSV data for {target_date_date}: {e}")
            return None
        return None

# Global instance to be imported by other modules if they need direct CSV access,
# though data_fetch_orchestrator will usually instantiate it.
# If multiple scripts import this, they'll share this instance unless they create their own.
csv_data_loader_instance = CSVDataLoader()