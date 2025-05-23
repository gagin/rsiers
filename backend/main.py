# backend/main.py
import sys
import os
import time # Keep time for cache checking
import logging
import json
from datetime import datetime, timezone, date as DtDate # Keep DtDate for clarity on date operations
import pandas as pd

# Adjust Python path to correctly import sibling modules when run directly
# This assumes 'main.py' is in 'backend/' and project root is one level up.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(current_dir)
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from flask import Flask, jsonify, request
from flask_cors import CORS

# Imports from our backend modules
from backend.db_utils import (
    init_db, get_full_indicator_set_from_db, store_full_indicator_set,
    date_to_iso_string, iso_string_to_date # Utility functions for date conversion
)
from backend.data_sources import get_historical_data_for_indicators, fetch_and_store_daily_ohlcv
from backend.indicator_calculator import (
    resample_ohlc_data, 
    calculate_indicators_from_ohlc_df,
    calculate_composite_metrics_for_api,
    calculate_price_outcomes
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- API Endpoints ---
@app.route('/api/indicators', methods=['GET'])
def get_indicators_api():
    date_param = request.args.get('date')
    target_date_obj_utc = None # This will be a datetime object representing start of day UTC

    if date_param:
        try:
            # Frontend might send full ISO string with T and Z, or just YYYY-MM-DD
            if 'T' in date_param: # More specific check for full ISO string
                 target_date_obj_utc = datetime.fromisoformat(date_param.replace('Z', '+00:00')).astimezone(timezone.utc)
            else: # Assume YYYY-MM-DD
                 target_date_obj_utc = datetime.strptime(date_param, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            target_date_obj_utc = target_date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            logger.error(f"API: Invalid date format received: {date_param}")
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD or full ISO.'}), 400
    else: # "Today"
        target_date_obj_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    is_today = target_date_obj_utc.date() == datetime.now(timezone.utc).date()
    
    # Use the datetime object for DB interaction, db_utils will handle string conversion
    cached_data = get_full_indicator_set_from_db(target_date_obj_utc) 
    
    if cached_data and (not is_today or (cached_data.get('calculated_at') and (time.time() - cached_data['calculated_at'] < 3600))):
        logger.info(f"API: Returning cached indicators for {target_date_obj_utc.date()}")
        # Format from DB row (which is already a dict) to API response
        indicators_response = {
            'rsi': {'monthly': cached_data['rsi_monthly'], 'weekly': cached_data['rsi_weekly']},
            'stochRsi': {'monthly': cached_data['stoch_rsi_monthly'], 'weekly': cached_data['stoch_rsi_weekly']},
            'mfi': {'monthly': cached_data['mfi_monthly'], 'weekly': cached_data['mfi_weekly']},
            'crsi': {'monthly': cached_data['crsi_monthly'], 'weekly': cached_data['crsi_weekly']},
            'williamsR': {'monthly': cached_data['williams_r_monthly'], 'weekly': cached_data['williams_r_weekly']},
            'rvi': {'monthly': cached_data['rvi_monthly'], 'weekly': cached_data['rvi_weekly']},
            'adaptiveRsi': {'monthly': cached_data['adaptive_rsi_monthly'], 'weekly': cached_data['adaptive_rsi_weekly']},
        }
        composite_metrics_response = {
            'cos': {'monthly': cached_data['cos_monthly'], 'weekly': cached_data['cos_weekly']},
            'bsi': {'monthly': cached_data['bsi_monthly'], 'weekly': cached_data['bsi_weekly']},
        }
        outcomes_response = {
            '1M': {'direction': cached_data['outcome_1m_direction'], 'percentage': cached_data['outcome_1m_percentage'], 'price': cached_data['outcome_1m_price']},
            '6M': {'direction': cached_data['outcome_6m_direction'], 'percentage': cached_data['outcome_6m_percentage'], 'price': cached_data['outcome_6m_price']},
            '12M': {'direction': cached_data['outcome_12m_direction'], 'percentage': cached_data['outcome_12m_percentage'], 'price': cached_data['outcome_12m_price']},
        }
        # The date_str from DB is already YYYY-MM-DD. Use target_date_obj_utc for full ISO string.
        last_update_iso = target_date_obj_utc.isoformat().replace('+00:00', 'Z')

        return jsonify({
            'lastUpdate': last_update_iso,
            'indicators': indicators_response,
            'compositeMetrics': composite_metrics_response,
            'price': cached_data['price_at_event'],
            'outcomes': outcomes_response,
            'name': target_date_obj_utc.strftime('%Y-%m-%d') + (" (Today)" if is_today else " (Historical)"),
            'description': f"Data from DB for {target_date_obj_utc.date()}",
            'isCustomDate': not is_today
        })

    logger.info(f"API: Cache miss or stale for {target_date_obj_utc.date()}. Calculating indicators.")
    # Expects datetime object
    daily_df = get_historical_data_for_indicators(target_date_obj_utc, years=2) 

    if daily_df.empty or len(daily_df) < 60: # Min periods for meaningful monthly indicators
        # Try to get at least the current price for the target date
        price_at_event_values, err_msg = fetch_and_store_daily_ohlcv(target_date_obj_utc) # Expects datetime
        price_val = price_at_event_values.get('close') if price_at_event_values else None
        
        error_message_detail = f'Not enough historical daily data (found {len(daily_df)}) to calculate full indicators for {target_date_obj_utc.date()}'
        if price_val is None:
            error_message_detail += f'. Also could not fetch current price for the day. Last error: {err_msg}'
            return jsonify({'error': error_message_detail}), 404
        
        # If price is available but not enough data for indicators, return price and outcomes
        outcomes_for_no_indicators = calculate_price_outcomes(target_date_obj_utc, price_val) # Expects datetime
        last_update_iso_err = target_date_obj_utc.isoformat().replace('+00:00', 'Z')
        return jsonify({
            'error': error_message_detail, # Explain in error field, but still provide available data
            'lastUpdate': last_update_iso_err,
            'indicators': {k: {'monthly':None, 'weekly':None} for k in ['rsi','stochRsi','mfi','crsi','williamsR','rvi','adaptiveRsi']},
            'compositeMetrics': {'cos': {'monthly':0,'weekly':0}, 'bsi': {'monthly':0,'weekly':0}},
            'price': price_val,
            'outcomes': outcomes_for_no_indicators,
            'name': target_date_obj_utc.strftime('%Y-%m-%d') + (" (Today)" if is_today else " (Historical)"),
            'description': f"Price data for {target_date_obj_utc.date()}, full indicators unavailable due to insufficient history.",
            'isCustomDate': not is_today
        }), 200 # Return 200 because some data (price) is available


    # Determine price at event from the last day of the fetched historical window
    price_at_event = daily_df['close'].iloc[-1] if not daily_df.empty and 'close' in daily_df.columns and pd.notna(daily_df['close'].iloc[-1]) else None
    if price_at_event is None: # Should be rare if daily_df is not empty and has data
        current_day_data, _ = fetch_and_store_daily_ohlcv(target_date_obj_utc) # Expects datetime
        if current_day_data and current_day_data.get('close') is not None:
            price_at_event = current_day_data['close']
        else:
            return jsonify({'error': f'Could not determine price for {target_date_obj_utc.date()} for indicators.'}), 404
    
    weekly_ohlc_df = resample_ohlc_data(daily_df, 'W-MON')
    monthly_ohlc_df = resample_ohlc_data(daily_df, 'ME') # Use 'ME' for Month End

    indicators_m = calculate_indicators_from_ohlc_df(monthly_ohlc_df, 'monthly')
    indicators_w = calculate_indicators_from_ohlc_df(weekly_ohlc_df, 'weekly')
    
    api_indicators_format = {key: {'monthly': indicators_m.get(key), 'weekly': indicators_w.get(key)} for key in indicators_m}
    composite_metrics = calculate_composite_metrics_for_api(api_indicators_format)
    outcomes = calculate_price_outcomes(target_date_obj_utc, price_at_event) # Expects datetime

    # Store using datetime object; db_utils handles conversion to string
    store_full_indicator_set(target_date_obj_utc, price_at_event, indicators_m, indicators_w, composite_metrics, outcomes)

    last_update_iso_calc = target_date_obj_utc.isoformat().replace('+00:00', 'Z')
    return jsonify({
        'lastUpdate': last_update_iso_calc,
        'indicators': api_indicators_format,
        'compositeMetrics': composite_metrics,
        'price': price_at_event,
        'outcomes': outcomes,
        'name': target_date_obj_utc.strftime('%Y-%m-%d') + (" (Today)" if is_today else " (Historical)"),
        'description': f"Data calculated for {target_date_obj_utc.date()}",
        'isCustomDate': not is_today
    })

@app.route('/api/historical_time_points', methods=['GET'])
def get_historical_time_points_api():
    project_root_local = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Relative to this main.py
    historical_data_path = os.path.join(project_root_local, 'historical_data.json')
    
    if not os.path.exists(historical_data_path):
        return jsonify({'error': 'Historical data file not found.'}), 404
    try:
        with open(historical_data_path, 'r') as f:
            data = json.load(f)
        for point in data.get("timePoints", []):
            if "indicators" in point and "compositeMetrics" not in point:
                 point["compositeMetrics"] = calculate_composite_metrics_for_api(point["indicators"])
            elif "compositeMetrics" not in point:
                 point["compositeMetrics"] = {'cos': {'monthly':0,'weekly':0}, 'bsi': {'monthly':0,'weekly':0}}
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error reading/processing historical_data.json: {e}")
        return jsonify({'error': 'Could not load historical time points.'}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data_api():
    # This endpoint is largely conceptual now, as /api/indicators handles on-demand fetching/caching.
    # For a true proactive refresh, a background job would be better.
    # We could trigger a calculation for "today" here if needed.
    today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    # Force a re-calculation for today by clearing any recent cache temporarily (not implemented here)
    # Or simply call the logic that get_indicators_api would use for today.
    # For now, just returning a success message.
    logger.info("Manual refresh triggered. Data for 'today' will be re-evaluated on next GET /api/indicators if cache is stale.")
    return jsonify({'status': 'success', 'message': 'Data for today will be re-evaluated if necessary on next request. Data is fetched on demand.'})

if __name__ == '__main__':
    # Ensure DB is initialized when app starts
    # init_db() should be robust to multiple calls
    init_db() 
    logger.info(f"Starting Flask app {__file__} from backend/main.py on port 5001")
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)