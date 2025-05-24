# backend/data_sources.py
import time
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np
from backend import config

# Imports from sibling modules within the 'backend' package
from .db_utils import store_daily_ohlcv_data, get_daily_ohlcv_from_db, iso_string_to_date
from .csv_data_loader import CSVDataLoader # Import the class
from .api_clients import coingecko_api_client, kraken_api_client # Import instances

logger = logging.getLogger(__name__)

# Instantiate CSVDataLoader ONCE, when the module is loaded.
# This assumes the CSV files don't change during the runtime of the application.
# If they do, a more complex refresh mechanism for global_csv_loader would be needed.
global_csv_loader = CSVDataLoader()
logger.info("Data_sources: Global CSVDataLoader instance created and CSVs pre-loaded.")

def fetch_and_store_daily_ohlcv(date_obj_utc: datetime):
    """
    Orchestrates fetching daily OHLCV, prioritizing local CSV, then CoinGecko, then Kraken.
    Stores data in DB if found.
    Returns (values_dict, error_message_or_none).
    'values_dict' contains o,h,l,c,v,source but NOT the date/timestamp itself.
    """
    # USE THE GLOBAL INSTANCE: global_csv_loader
    # REMOVED: local_csv_loader = CSVDataLoader() 
    
    date_obj_utc = date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str_log = date_obj_utc.strftime('%Y-%m-%d') 

    logger.debug(f"Orchestrator: Checking CSV for {date_str_log} using global CSV instance.")
    csv_values = global_csv_loader.get_ohlcv_for_date(date_obj_utc)
    if csv_values:
        store_daily_ohlcv_data(date_obj_utc, {**csv_values}) # Pass datetime and values dict
        logger.info(f"Orchestrator: Found and stored data for {date_str_log} from CSV (source: {csv_values.get('source')}).")
        return csv_values, None

    logger.info(f"Orchestrator: Data for {date_str_log} not found in CSV. Attempting APIs.")
    # Apply a slightly longer delay if CSV fails, as API calls are slower.
    # The original 1.5s delay was here, but might be better before each API type.
    
    now_utc_start_of_day = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    days_ago = (now_utc_start_of_day - date_obj_utc).days
    
    if 0 <= days_ago <= 365: # CoinGecko for data within the last year
        logger.info(f"Orchestrator: Attempting CoinGecko for recent date {date_str_log}.")
        time.sleep(1.2) # Delay before CoinGecko call
        cg_values = coingecko_api_client.get_ohlcv_for_date(date_obj_utc)
        if cg_values:
            store_daily_ohlcv_data(date_obj_utc, {**cg_values})
            logger.info(f"Orchestrator: Found and stored data for {date_str_log} from CoinGecko.")
            return cg_values, None
        else:
            logger.warning(f"Orchestrator: CoinGecko failed for {date_str_log} after all retries. Now trying Kraken.")
    else:
        logger.info(f"Orchestrator: Date {date_str_log} is older than 365 days ({days_ago} days ago). Skipping CoinGecko, trying Kraken directly.")
    
    logger.info(f"Orchestrator: Attempting Kraken for {date_str_log}.")
    time.sleep(1.2) # Delay before Kraken call
    kraken_values = kraken_api_client.get_ohlcv_for_date(date_obj_utc)
    if kraken_values:
        store_daily_ohlcv_data(date_obj_utc, {**kraken_values})
        logger.info(f"Orchestrator: Found and stored data for {date_str_log} from Kraken.")
        return kraken_values, None
    
    final_error_msg = f"Data not found for {date_str_log} in any source (CSV, CoinGecko, Kraken)."
    logger.error(f"Orchestrator: {final_error_msg}")
    return None, final_error_msg


def get_historical_data_for_indicators(end_date_utc: datetime, years=None) -> pd.DataFrame:
    if years is None:
        years = config.HISTORICAL_DATA_YEARS # Use from config if not specified
    start_date_utc = end_date_utc - timedelta(days=years*365)
    # Ensure dates are normalized to start of day UTC for the range
    norm_start_date_utc = start_date_utc.replace(hour=0,minute=0,second=0,microsecond=0)
    norm_end_date_utc = end_date_utc.replace(hour=0,minute=0,second=0,microsecond=0)
    
    date_range = pd.date_range(
        start=norm_start_date_utc, 
        end=norm_end_date_utc, 
        freq='D', tz='UTC'
    )
    all_daily_data_dicts = []
    
    # Debug: Log the DB path being used by this process
    # This import needs to be here to avoid circular dependency if DB_PATH is logged at module level
    from .db_utils import DB_PATH 
    logger.debug(f"get_historical_data_for_indicators is using DB_PATH: {DB_PATH}")

    for date_in_range_dt_obj in date_range:
        # date_in_range_dt_obj is a pandas.Timestamp. get_daily_ohlcv_from_db expects datetime.datetime.
        # Convert pandas.Timestamp to python datetime.datetime, ensuring it's UTC.
        # While .date() conversion worked for keying, being explicit with datetime obj might be safer.
        py_datetime_obj_utc = date_in_range_dt_obj.to_pydatetime()

        db_entry_dict = get_daily_ohlcv_from_db(py_datetime_obj_utc) 
        if db_entry_dict:
            # Ensure the 'date_str' from DB is correctly converted to a datetime.date object for indexing
            # The 'date_str' is 'YYYY-MM-DD'
            db_entry_dict['datetime_obj_for_index'] = iso_string_to_date(db_entry_dict['date_str'])
            all_daily_data_dicts.append(db_entry_dict)
        else:
            # DB miss, try to fetch and store
            logger.info(f"Orchestrator: DB miss for {py_datetime_obj_utc.date()}. Will attempt fetch_and_store.")
            fetched_values_dict, error = fetch_and_store_daily_ohlcv(py_datetime_obj_utc)
            if fetched_values_dict:
                entry_to_append = fetched_values_dict.copy()
                # The date for indexing should be the date we were trying to fetch for
                entry_to_append['datetime_obj_for_index'] = py_datetime_obj_utc.date() 
                all_daily_data_dicts.append(entry_to_append)
            else:
                logger.warning(f"Orchestrator: Could not fetch data for {py_datetime_obj_utc.date()} for indicator window. Error: {error}")
    
    if not all_daily_data_dicts: 
        logger.warning(f"Orchestrator: No daily data found for the range {norm_start_date_utc.date()} to {norm_end_date_utc.date()} for indicator calculation.")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_daily_data_dicts)
    if 'datetime_obj_for_index' not in df.columns:
        logger.error("Orchestrator: 'datetime_obj_for_index' column missing after data assembly. Cannot create DataFrame for indicators.")
        return pd.DataFrame()
    
    # Ensure 'datetime_obj_for_index' is pd.Timestamp UTC for set_index
    df['datetime_obj_for_index'] = pd.to_datetime(df['datetime_obj_for_index'], utc=True)
    df.set_index('datetime_obj_for_index', inplace=True)
    
    # Drop columns that might have come from DB ('date_str', 'timestamp') or were intermediate
    df.drop(columns=['date_str', 'timestamp', 'fetched_at', 'source'], inplace=True, errors='ignore') 
    
    # Ensure essential OHLCV columns exist and are numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in df.columns: 
            df[col] = pd.NA # Use pandas NA for missing numeric data
        df[col] = pd.to_numeric(df[col], errors='coerce') # Coerce converts problematic values to NaT/NaN
    
    return df.sort_index()