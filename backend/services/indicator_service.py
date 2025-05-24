# backend/services/indicator_service.py
import time
import logging
from datetime import datetime, timezone
import pandas as pd

from backend.db_utils import (
    get_full_indicator_set_from_db, store_full_indicator_set, DB_PATH
)
from backend.data_sources import get_historical_data_for_indicators, fetch_and_store_daily_ohlcv
from backend.indicator_calculator import ( # This now only contains individual indicator wrappers and resampling
    resample_ohlc_data,
    calculate_indicators_from_ohlc_df,
)
# Import new service functions
from backend.services.composite_metrics_service import calculate_composite_metrics
from backend.services.outcome_service import calculate_price_outcomes


logger = logging.getLogger(__name__)

def _format_db_data_for_api(cached_data: dict, target_date_obj_utc: datetime, is_today: bool) -> dict:
    # ... (this helper function remains the same)
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
    last_update_iso = target_date_obj_utc.isoformat().replace('+00:00', 'Z')

    return {
        'lastUpdate': last_update_iso,
        'indicators': indicators_response,
        'compositeMetrics': composite_metrics_response,
        'price': cached_data['price_at_event'],
        'outcomes': outcomes_response,
        'name': target_date_obj_utc.strftime('%Y-%m-%d') + (" (Today)" if is_today else " (Historical)"),
        'description': f"Data from DB for {target_date_obj_utc.date()}",
        'isCustomDate': not is_today,
        'http_status_code': 200
    }


def get_indicator_data(target_date_obj_utc: datetime):
    is_today = target_date_obj_utc.date() == datetime.now(timezone.utc).date()
    date_str_log = target_date_obj_utc.strftime('%Y-%m-%d')

    logger.info(f"INDICATOR_SERVICE: Request for date: {date_str_log}. Is today: {is_today}")
    logger.debug(f"INDICATOR_SERVICE: Using DB_PATH: {DB_PATH}")

    cached_data = get_full_indicator_set_from_db(target_date_obj_utc)

    if cached_data and (not is_today or (cached_data.get('calculated_at') and (time.time() - cached_data['calculated_at'] < 3600))):
        logger.info(f"INDICATOR_SERVICE: Cache hit for {date_str_log}. Returning cached data.")
        return _format_db_data_for_api(cached_data, target_date_obj_utc, is_today)

    logger.info(f"INDICATOR_SERVICE: Cache miss or stale for {date_str_log}. Proceeding with calculation.")
    daily_df = get_historical_data_for_indicators(target_date_obj_utc, years=2)

    if daily_df.empty or len(daily_df) < 60: 
        logger.warning(f"INDICATOR_SERVICE: Not enough historical daily data (found {len(daily_df)}) for {date_str_log}.")
        price_at_event_values, err_msg = fetch_and_store_daily_ohlcv(target_date_obj_utc)
        price_val = price_at_event_values.get('close') if price_at_event_values else None
        
        error_message_detail = f'Not enough historical daily data (found {len(daily_df)}) to calculate full indicators for {date_str_log}'
        if price_val is None:
            error_message_detail += f'. Also could not fetch current price for the day. Last error: {err_msg}'
            return {'error': error_message_detail, 'price': None, 'http_status_code': 500}
        
        # Use the new outcome_service
        outcomes_for_no_indicators = calculate_price_outcomes(target_date_obj_utc, price_val)
        last_update_iso_err = target_date_obj_utc.isoformat().replace('+00:00', 'Z')
        return {
            'error_message': error_message_detail,
            'lastUpdate': last_update_iso_err,
            'indicators': {k: {'monthly':None, 'weekly':None} for k in ['rsi','stochRsi','mfi','crsi','williamsR','rvi','adaptiveRsi']},
            'compositeMetrics': {'cos': {'monthly':0,'weekly':0}, 'bsi': {'monthly':0,'weekly':0}}, # Default empty
            'price': price_val,
            'outcomes': outcomes_for_no_indicators,
            'name': date_str_log + (" (Today)" if is_today else " (Historical)"),
            'description': f"Price data for {date_str_log}, full indicators unavailable due to insufficient history.",
            'isCustomDate': not is_today,
            'http_status_code': 200 
        }

    price_at_event = daily_df['close'].iloc[-1] if not daily_df.empty and 'close' in daily_df.columns and pd.notna(daily_df['close'].iloc[-1]) else None
    if price_at_event is None:
        current_day_data, _ = fetch_and_store_daily_ohlcv(target_date_obj_utc)
        if current_day_data and current_day_data.get('close') is not None:
            price_at_event = current_day_data['close']
        else:
            logger.error(f"INDICATOR_SERVICE: Could not determine price for {date_str_log} for indicators.")
            return {'error': f'Could not determine price for {date_str_log} for indicators.', 'price': None, 'http_status_code': 500}

    weekly_ohlc_df = resample_ohlc_data(daily_df, 'W-MON')
    monthly_ohlc_df = resample_ohlc_data(daily_df, 'ME')

    indicators_m = calculate_indicators_from_ohlc_df(monthly_ohlc_df, 'monthly')
    indicators_w = calculate_indicators_from_ohlc_df(weekly_ohlc_df, 'weekly')
    
    api_indicators_format = {key: {'monthly': indicators_m.get(key), 'weekly': indicators_w.get(key)} for key in indicators_m.keys()} # Use .keys() from one dict
    
    # Use the new composite_metrics_service
    composite_metrics = calculate_composite_metrics(api_indicators_format)
    # Use the new outcome_service
    outcomes = calculate_price_outcomes(target_date_obj_utc, price_at_event)

    store_full_indicator_set(target_date_obj_utc, price_at_event, indicators_m, indicators_w, composite_metrics, outcomes)
    logger.info(f"INDICATOR_SERVICE: Successfully calculated and stored indicators for {date_str_log}.")

    last_update_iso_calc = target_date_obj_utc.isoformat().replace('+00:00', 'Z')
    return {
        'lastUpdate': last_update_iso_calc,
        'indicators': api_indicators_format,
        'compositeMetrics': composite_metrics,
        'price': price_at_event,
        'outcomes': outcomes,
        'name': date_str_log + (" (Today)" if is_today else " (Historical)"),
        'description': f"Data calculated for {date_str_log}",
        'isCustomDate': not is_today,
        'http_status_code': 200
    }