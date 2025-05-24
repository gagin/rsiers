# backend/indicator_calculator.py
import pandas as pd
import numpy as np
import logging
from datetime import datetime as PyDateTime, timezone, timedelta

# Import individual calculator functions from the new modules
from backend.indicators import rsi
from backend.indicators import stochastic_rsi 
from backend.indicators import mfi
from backend.indicators import connors_rsi
from backend.indicators import williams_r
from backend.indicators import rvi
from backend.indicators import adaptive_rsi

# Import config
from backend import config # Assuming config.py is in backend/

logger = logging.getLogger(__name__)

# Helper to get the last valid value from a Series
def _get_last_value_from_series(series: pd.Series):
    if series is not None and not series.empty:
        last_valid_idx = series.last_valid_index()
        if last_valid_idx is not None:
            value = series.loc[last_valid_idx]
            return value if pd.notna(value) else None
    return None

# --- Wrapper functions calling the new indicator modules ---
# These wrappers will now fetch params from config.

def calculate_rsi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("rsi", timeframe_label)
    return rsi.calculate(ohlc_df, period=params.get("period", 14))

def calculate_stoch_rsi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("stochRsi", timeframe_label)
    return stochastic_rsi.calculate(ohlc_df, 
                                    rsi_period=params.get("rsi_period", 14), 
                                    stoch_period=params.get("stoch_period", 14), 
                                    k_smooth=params.get("k_smooth", 3))

def calculate_mfi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("mfi", timeframe_label)
    return mfi.calculate(ohlc_df, period=params.get("period", 14))

def calculate_crsi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("crsi", timeframe_label)
    # Dynamic adjustment of rank_len based on actual data length for this timeframe
    # This is better done here where ohlc_df is available.
    dynamic_rank_len = params.get("rank_len", 100) # Start with configured/default
    if timeframe_label == 'monthly':
        dynamic_rank_len = min(params.get("rank_len", 12), max(5, len(ohlc_df) - 10)) 
    elif timeframe_label == 'weekly':
        dynamic_rank_len = min(params.get("rank_len", 50), max(10, len(ohlc_df) - 10))
    
    return connors_rsi.calculate(ohlc_df, 
                                 rsi_short_len=params.get("rsi_short_len", 3), 
                                 rsi_streak_len=params.get("rsi_streak_len", 2), 
                                 rank_len=dynamic_rank_len) # Use dynamically adjusted rank_len

def calculate_williams_r_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("williamsR", timeframe_label)
    return williams_r.calculate(ohlc_df, period=params.get("period", 14))

def calculate_rvi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("rvi", timeframe_label)
    return rvi.calculate(ohlc_df, period=params.get("period", 10))

def calculate_adaptive_rsi_series(ohlc_df: pd.DataFrame, timeframe_label: str = None) -> pd.Series:
    params = config.get_indicator_params("adaptiveRsi", timeframe_label)
    return adaptive_rsi.calculate(ohlc_df, 
                                  period=params.get("period", 14), 
                                  kama_n=params.get("kama_n", 10), 
                                  kama_fast_ema=params.get("kama_fast_ema", 2), 
                                  kama_slow_ema=params.get("kama_slow_ema", 30))


# --- Core Orchestration and Other Utility Functions ---

def resample_ohlc_data(daily_df: pd.DataFrame, rule='W-MON') -> pd.DataFrame:
    # ... (This function remains unchanged)
    if daily_df.empty:
        logger.warning("resample_ohlc_data: Input daily_df is empty. Returning empty DataFrame.")
        return pd.DataFrame()
    if not isinstance(daily_df.index, pd.DatetimeIndex):
        logger.error("resample_ohlc_data expects a DataFrame with a DatetimeIndex.")
        return pd.DataFrame()
    if not daily_df.index.is_monotonic_increasing:
        logger.warning("resample_ohlc_data: DataFrame index is not monotonically increasing. Sorting.")
        daily_df = daily_df.sort_index()
        
    valid_rules = {'W-MON', 'ME'} 
    if rule not in valid_rules:
        logger.error(f"resample_ohlc_data: Invalid rule '{rule}'. Using 'W-MON' for weekly, 'ME' for monthly.")
        if 'M' in rule.upper(): rule = 'ME'
        else: rule = 'W-MON'

    resampled_parts = {}
    if 'open' in daily_df.columns: resampled_parts['open'] = daily_df['open'].resample(rule).first()
    if 'high' in daily_df.columns: resampled_parts['high'] = daily_df['high'].resample(rule).max()
    if 'low' in daily_df.columns: resampled_parts['low'] = daily_df['low'].resample(rule).min()
    if 'close' in daily_df.columns: resampled_parts['close'] = daily_df['close'].resample(rule).last()
    if 'volume' in daily_df.columns: resampled_parts['volume'] = daily_df['volume'].resample(rule).sum()
    
    if not resampled_parts:
        logger.warning("resample_ohlc_data: No valid OHLCV columns to resample (open, high, low, close, volume). Returning empty DataFrame.")
        return pd.DataFrame()
    
    resampled_df = pd.DataFrame(resampled_parts)
    resampled_df.dropna(subset=['open', 'high', 'low', 'close'], how='all', inplace=True)
    
    if resampled_df.empty:
        logger.warning(f"Resampling with rule '{rule}' resulted in an empty DataFrame. Original daily_df length: {len(daily_df)}")
    else:
        index_info = f"Resampled index from {resampled_df.index.min()} to {resampled_df.index.max()}" if not resampled_df.empty else "Empty Index"
        logger.info(f"Resampled data with rule '{rule}'. Original daily_df len: {len(daily_df)}, Resampled len: {len(resampled_df)}. {index_info}")
    return resampled_df


def calculate_indicators_from_ohlc_df(ohlc_df: pd.DataFrame, timeframe_label: str) -> dict:
    date_info_str = ohlc_df.index[-1].strftime('%Y-%m-%d') if not ohlc_df.empty and isinstance(ohlc_df.index, pd.DatetimeIndex) else "N/A"

    # Use MIN_CANDLES_FOR_CALCULATION from config
    if ohlc_df.empty or len(ohlc_df) < config.MIN_CANDLES_FOR_CALCULATION: 
        logger.warning(f"Not enough data in {timeframe_label} OHLC df ({len(ohlc_df)} rows, need at least {config.MIN_CANDLES_FOR_CALCULATION}) for date ending {date_info_str}. All indicators for this period will be None.")
        return {key: None for key in config.DEFAULT_INDICATOR_PARAMS.keys()}

    indicators_results = {}
    df_for_calc = ohlc_df.copy() 

    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in df_for_calc.columns:
            df_for_calc[col] = np.nan
        else: 
            df_for_calc[col] = pd.to_numeric(df_for_calc[col], errors='coerce')
    
    if 'close' not in df_for_calc.columns or df_for_calc['close'].isnull().all():
        logger.error(f"Critical: 'close' prices are all NaN or missing in {timeframe_label} OHLC df for {date_info_str} after prep.")
        return {key: None for key in config.DEFAULT_INDICATOR_PARAMS.keys()}

    # Call wrapper functions, passing timeframe_label for parameter selection
    series_dict = {
        'rsi': calculate_rsi_series(df_for_calc, timeframe_label), 
        'stochRsi': calculate_stoch_rsi_series(df_for_calc, timeframe_label),
        'mfi': calculate_mfi_series(df_for_calc, timeframe_label), 
        'crsi': calculate_crsi_series(df_for_calc, timeframe_label),
        'williamsR': calculate_williams_r_series(df_for_calc, timeframe_label), 
        'rvi': calculate_rvi_series(df_for_calc, timeframe_label), 
        'adaptiveRsi': calculate_adaptive_rsi_series(df_for_calc, timeframe_label)
    }
    
    for key, series_data in series_dict.items():
        indicators_results[key] = _get_last_value_from_series(series_data)
            
    logger.info(f"Calculated indicators for {timeframe_label} ending {date_info_str}: { {k: round(v, 2) if v is not None and pd.notna(v) else None for k, v in indicators_results.items()} }")
    return {k: (v if pd.notna(v) else None) for k, v in indicators_results.items()}