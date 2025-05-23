# backend/data_sources.py
import time
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np

# Imports from sibling modules within the 'backend' package
from .db_utils import store_daily_ohlcv_data, get_daily_ohlcv_from_db, iso_string_to_date
from .csv_data_loader import CSVDataLoader # Import the class
from .api_clients import coingecko_api_client, kraken_api_client # Import instances

logger = logging.getLogger(__name__)

def fetch_and_store_daily_ohlcv(date_obj_utc: datetime):
    """
    Orchestrates fetching daily OHLCV, prioritizing local CSV, then CoinGecko, then Kraken.
    Stores data in DB if found.
    Returns (values_dict, error_message_or_none).
    'values_dict' contains o,h,l,c,v,source but NOT the date/timestamp itself.
    """
    # Instantiate CSVDataLoader locally to ensure it's fresh or uses its potentially pre-loaded data correctly.
    # This also means CSVDataLoader.__init__ logging will appear each time this function is called.
    local_csv_loader = CSVDataLoader() 
    
    date_obj_utc = date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str_log = date_obj_utc.strftime('%Y-%m-%d') 

    logger.debug(f"Orchestrator: Checking CSV for {date_str_log}")
    csv_values = local_csv_loader.get_ohlcv_for_date(date_obj_utc)
    if csv_values:
        store_daily_ohlcv_data(date_obj_utc, {**csv_values}) # Pass datetime and values dict
        logger.info(f"Orchestrator: Found and stored data for {date_str_log} from CSV (source: {csv_values.get('source')}).")
        return csv_values, None

    logger.info(f"Orchestrator: Data for {date_str_log} not found in CSV. Attempting APIs.")
    time.sleep(1.5) 
    
    now_utc_start_of_day = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    days_ago = (now_utc_start_of_day - date_obj_utc).days
    
    if 0 <= days_ago <= 365:
        logger.info(f"Orchestrator: Attempting CoinGecko for recent date {date_str_log}.")
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
    kraken_values = kraken_api_client.get_ohlcv_for_date(date_obj_utc)
    if kraken_values:
        store_daily_ohlcv_data(date_obj_utc, {**kraken_values})
        logger.info(f"Orchestrator: Found and stored data for {date_str_log} from Kraken.")
        return kraken_values, None
    
    final_error_msg = f"Data not found for {date_str_log} in any source (CSV, CoinGecko, Kraken)."
    logger.error(f"Orchestrator: {final_error_msg}")
    return None, final_error_msg


def get_historical_data_for_indicators(end_date_utc: datetime, years=2) -> pd.DataFrame:
    start_date_utc = end_date_utc - timedelta(days=years*365)
    date_range = pd.date_range(
        start=start_date_utc.replace(hour=0,minute=0,second=0,microsecond=0), 
        end=end_date_utc.replace(hour=0,minute=0,second=0,microsecond=0), 
        freq='D', tz='UTC'
    )
    all_daily_data_dicts = []
    
    for date_in_range_dt_obj in date_range:
        db_entry_dict = get_daily_ohlcv_from_db(date_in_range_dt_obj) 
        if db_entry_dict:
            db_entry_dict['datetime_obj_for_index'] = iso_string_to_date(db_entry_dict['date_str']) 
            all_daily_data_dicts.append(db_entry_dict)
        else:
            fetched_values_dict, error = fetch_and_store_daily_ohlcv(date_in_range_dt_obj)
            if fetched_values_dict:
                entry_to_append = fetched_values_dict.copy()
                entry_to_append['datetime_obj_for_index'] = date_in_range_dt_obj.date() 
                all_daily_data_dicts.append(entry_to_append)
            else:
                logger.warning(f"Orchestrator: Could not fetch data for {date_in_range_dt_obj.date()} for indicator window. Error: {error}")
    
    if not all_daily_data_dicts: 
        logger.warning(f"Orchestrator: No daily data found for the range ending {end_date_utc.date()} for indicator calculation.")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_daily_data_dicts)
    if 'datetime_obj_for_index' not in df.columns:
        logger.error("Orchestrator: 'datetime_obj_for_index' column missing. Cannot create DataFrame.")
        return pd.DataFrame()
    
    df.set_index(pd.to_datetime(df['datetime_obj_for_index'], utc=True), inplace=True)
    df.drop(columns=['datetime_obj_for_index', 'date_str', 'timestamp'], inplace=True, errors='ignore') 
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in df.columns: df[col] = pd.NA 
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.sort_index()