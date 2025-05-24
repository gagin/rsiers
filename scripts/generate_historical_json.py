# scripts/generate_historical_json.py
import datetime as dt
from datetime import timezone
import json
import logging
import os
import sys
import pandas as pd 
import time 

# Adjust Python path to include the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"INFO: Added '{project_root}' to sys.path for module resolution in generate_historical_json.py")

# Backend imports
from backend.db_utils import init_db as init_db_main, DB_PATH
from backend.data_sources import get_historical_data_for_indicators, fetch_and_store_daily_ohlcv

# Corrected imports for indicator calculations and services
from backend.indicator_calculator import (
    resample_ohlc_data, 
    calculate_indicators_from_ohlc_df, 
)
from backend.services.composite_metrics_service import calculate_composite_metrics 
from backend.services.outcome_service import calculate_price_outcomes 


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Define Significant Historical Events ---
SIGNIFICANT_EVENTS_DEFINITIONS = [
    {
        "id": 1, "date_str": "2017-12-17", "name": "2017 Bull Run Peak",
        "description": "Peak of the explosive 2017 bull run, driven by retail FOMO and ICO mania."
    },
    {
        "id": 2, "date_str": "2018-12-15", "name": "2018 Bear Market Bottom",
        "description": "Bottom of the prolonged bear market following the 2017 peak."
    },
    {
        "id": 3, "date_str": "2020-03-12", "name": "COVID-19 Crash ('Black Thursday')",
        "description": "Sharp market-wide crash at the onset of the COVID-19 pandemic."
    },
    {
        "id": 4, "date_str": "2021-04-14", "name": "2021 First Peak (Coinbase IPO)",
        "description": "First major peak of the 2021 bull market, around the time of the Coinbase direct listing."
    },
    {
        "id": 5, "date_str": "2021-11-10", "name": "2021 All-Time High (Futures ETF)",
        "description": "The all-time high (as of late 2021), driven by various factors including ProShares Bitcoin Strategy ETF launch."
    },
    {
        "id": 6, "date_str": "2022-11-21", "name": "FTX Collapse Bottom (Consolidated)",
        "description": "Consolidated bottom after the FTX exchange collapse."
    },
    {
        "id": 7, "date_str": "2024-03-14", "name": "Spot ETF Approval Peak (Early 2024)",
        "description": "New all-time high in early 2024 following the approval of Spot Bitcoin ETFs in the US."
    }
]


def generate_historical_point_data(event_def: dict) -> dict:
    """
    Generates the full data structure for a single historical event.
    Price at event will be fetched.
    """
    logger.info(f"Processing event: {event_def['name']} for date {event_def['date_str']}")

    try:
        event_date_obj_utc = dt.datetime.strptime(event_def['date_str'], "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
    except ValueError:
        logger.error(f"Invalid date format for event {event_def['name']}: {event_def['date_str']}. Skipping.")
        return None

    logger.info(f"Fetching price_at_event for {event_def['name']} on {event_def['date_str']}...")
    ohlcv_data, err = fetch_and_store_daily_ohlcv(event_date_obj_utc) 
    
    if ohlcv_data and ohlcv_data.get('close') is not None:
        price_at_event = float(ohlcv_data['close'])
        source_of_price = ohlcv_data.get('source', 'fetched_unknown')
        logger.info(f"Fetched price_at_event for {event_def['name']}: {price_at_event} (source: {source_of_price})")
    else:
        logger.error(f"Could not fetch price_at_event for {event_def['name']} on {event_def['date_str']}. Error: {err}. Skipping event.")
        return None

    logger.info(f"Fetching 2-year historical daily data ending on {event_def['date_str']}...")
    daily_df = get_historical_data_for_indicators(event_date_obj_utc, years=2)

    # Initialize with all expected keys to prevent issues if some indicators are all None
    indicator_keys = ['rsi', 'stochRsi', 'mfi', 'crsi', 'williamsR', 'rvi', 'adaptiveRsi']
    api_indicators_format = {key: {'monthly': None, 'weekly': None} for key in indicator_keys}
    # Initialize composite_metrics with a default structure
    composite_metrics = calculate_composite_metrics(api_indicators_format) # Will result in 0s

    if daily_df.empty or len(daily_df) < 20: # A general minimum; individual indicators have own checks
        logger.warning(f"Not enough historical daily data (found {len(daily_df)}) to calculate full indicators for {event_def['name']}. Indicators will be null, composites will be default.")
    else:
        logger.info(f"Successfully fetched {len(daily_df)} days of historical data for {event_def['name']}.")
        
        monthly_ohlc_df = resample_ohlc_data(daily_df, 'ME') 
        weekly_ohlc_df = resample_ohlc_data(daily_df, 'W-MON')

        logger.info(f"Monthly df length for {event_def['name']}: {len(monthly_ohlc_df)}")
        if not monthly_ohlc_df.empty : logger.debug(f"Monthly df tail for {event_def['name']}:\n{monthly_ohlc_df.tail(3)}")
        logger.info(f"Weekly df length for {event_def['name']}: {len(weekly_ohlc_df)}")
        if not weekly_ohlc_df.empty : logger.debug(f"Weekly df tail for {event_def['name']}:\n{weekly_ohlc_df.tail(3)}")

        indicators_m_raw = calculate_indicators_from_ohlc_df(monthly_ohlc_df, 'monthly')
        indicators_w_raw = calculate_indicators_from_ohlc_df(weekly_ohlc_df, 'weekly')
        
        for key in indicator_keys:
            api_indicators_format[key]['monthly'] = indicators_m_raw.get(key)
            api_indicators_format[key]['weekly'] = indicators_w_raw.get(key)

        composite_metrics = calculate_composite_metrics(api_indicators_format)
        logger.info(f"Calculated indicators and composite metrics for {event_def['name']}.")

    logger.info(f"Calculating price outcomes for {event_def['name']} based on fetched price {price_at_event} (source: {source_of_price})...")
    outcomes = calculate_price_outcomes(event_date_obj_utc, price_at_event)
    logger.info(f"Calculated outcomes for {event_def['name']}: {outcomes}")

    historical_point = {
        "id": event_def["id"],
        "date": event_def["date_str"],
        "name": event_def["name"],
        "price": price_at_event, 
        "description": event_def["description"],
        "outcomes": outcomes,
        "indicators": api_indicators_format, 
        "compositeMetrics": composite_metrics
    }
    return historical_point

def main():
    logger.info(f"HISTORICAL_JSON_GENERATOR: Script starting. Using DB_PATH: {os.path.abspath(DB_PATH)}")
    init_db_main() 

    all_time_points = []
    INTER_EVENT_DELAY_SECONDS = 3 

    for event_def in SIGNIFICANT_EVENTS_DEFINITIONS:
        logger.info(f"--- Processing: {event_def['name']} ({event_def['date_str']}) ---")
        point_data = generate_historical_point_data(event_def)
        if point_data:
            all_time_points.append(point_data)
        
        logger.info(f"--- Finished processing: {event_def['name']} ---")
        if event_def != SIGNIFICANT_EVENTS_DEFINITIONS[-1]: 
            logger.info(f"Sleeping for {INTER_EVENT_DELAY_SECONDS} seconds before next event...\n")
            time.sleep(INTER_EVENT_DELAY_SECONDS)
        else:
            logger.info("\n")

    final_json_structure = {"timePoints": all_time_points}

    print("\n\n--- Generated historical_data.json content (from 2017 onwards, prices fetched) ---")
    print(json.dumps(final_json_structure, indent=2))
    print("--- End of content ---")

    # Ensure the output filename matches your previous preference or is distinct
    output_filename = "generated_historical_data_2017_onwards_v2.json" 
    with open(output_filename, 'w') as f:
        json.dump(final_json_structure, f, indent=2)
    logger.info(f"Generated data saved to {output_filename}")

if __name__ == "__main__":
    main()