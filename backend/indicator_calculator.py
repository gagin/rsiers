# backend/indicator_calculator.py
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone, timedelta # Added timedelta

# Assuming data_sources is in the same 'backend' package
from .data_sources import fetch_and_store_daily_ohlcv 

logger = logging.getLogger(__name__)

def calculate_rsi_series(prices_series: pd.Series, period=14) -> pd.Series:
    if not isinstance(prices_series, pd.Series):
        prices_series = pd.Series(prices_series) # Ensure it's a Series

    if len(prices_series) < period + 1:
        logger.warning(f"Not enough data for RSI ({len(prices_series)} points, need {period+1}). Returning empty Series.")
        return pd.Series(dtype=float, index=prices_series.index) # Return empty series with original index if possible

    delta = prices_series.diff()
    gain = (delta.where(delta > 0, 0.0)).fillna(0.0) # Ensure fillna with float
    loss = (-delta.where(delta < 0, 0.0)).fillna(0.0) # Ensure fillna with float

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Avoid division by zero if avg_loss is 0 for a period
    rs = avg_gain / avg_loss.replace(0, 1e-10) 
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

# Placeholder indicator calculations - ensure they return Series with same index as input
def calculate_stoch_rsi_series(prices: pd.Series, period=14) -> pd.Series: 
    return pd.Series([75.0] * len(prices.index), index=prices.index)

def calculate_mfi_series(highs: pd.Series, lows: pd.Series, closes: pd.Series, volumes: pd.Series, period=14) -> pd.Series:
    return pd.Series([65.0] * len(closes.index), index=closes.index)

def calculate_crsi_series(closes: pd.Series, period=14) -> pd.Series:
    return pd.Series([82.0] * len(closes.index), index=closes.index)

def calculate_williams_r_series(highs: pd.Series, lows: pd.Series, closes: pd.Series, period=14) -> pd.Series:
    return pd.Series([-25.0] * len(closes.index), index=closes.index)

def calculate_rvi_series(opens: pd.Series, highs: pd.Series, lows: pd.Series, closes: pd.Series, period=10) -> pd.Series:
    return pd.Series([0.65] * len(closes.index), index=closes.index)

def calculate_adaptive_rsi_series(closes: pd.Series, period=14) -> pd.Series:
    return pd.Series([70.0] * len(closes.index), index=closes.index)


def resample_ohlc_data(daily_df: pd.DataFrame, rule='W-MON') -> pd.DataFrame:
    if rule == 'M': rule = 'ME'
    
    if daily_df.empty: return pd.DataFrame()
    if not isinstance(daily_df.index, pd.DatetimeIndex):
        logger.error("resample_ohlc_data expects a DataFrame with a DatetimeIndex.")
        return pd.DataFrame()
        
    resampled_parts = {}
    if 'open' in daily_df.columns: resampled_parts['open'] = daily_df['open'].resample(rule).first()
    if 'high' in daily_df.columns: resampled_parts['high'] = daily_df['high'].resample(rule).max()
    if 'low' in daily_df.columns: resampled_parts['low'] = daily_df['low'].resample(rule).min()
    if 'close' in daily_df.columns: resampled_parts['close'] = daily_df['close'].resample(rule).last()
    if 'volume' in daily_df.columns: resampled_parts['volume'] = daily_df['volume'].resample(rule).sum()
    
    if not resampled_parts: return pd.DataFrame() # No valid columns to resample
    
    resampled_df = pd.DataFrame(resampled_parts)
    return resampled_df.dropna()


def calculate_indicators_from_ohlc_df(ohlc_df: pd.DataFrame, timeframe_label: str) -> dict:
    if ohlc_df.empty or len(ohlc_df) < 15: # Need at least 15 periods for a 14-period RSI
        logger.warning(f"Not enough data in {timeframe_label} OHLC df ({len(ohlc_df)} rows) for indicators.")
        return {key: None for key in ['rsi', 'stochRsi', 'mfi', 'crsi', 'williamsR', 'rvi', 'adaptiveRsi']}

    indicators = {}
    
    # Ensure required columns exist, use NaN if not (will result in None for indicator)
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in ohlc_df.columns:
            logger.warning(f"Column '{col}' missing in {timeframe_label} OHLC df. Indicators using it will be None.")
            ohlc_df[col] = np.nan # Add column with NaNs so functions don't break

    rsi_series = calculate_rsi_series(ohlc_df['close'])
    indicators['rsi'] = rsi_series.iloc[-1] if not rsi_series.empty and pd.notna(rsi_series.iloc[-1]) else None
    
    indicators['stochRsi'] = calculate_stoch_rsi_series(ohlc_df['close']).iloc[-1] if not ohlc_df.empty else None
    indicators['mfi'] = calculate_mfi_series(ohlc_df['high'], ohlc_df['low'], ohlc_df['close'], ohlc_df['volume']).iloc[-1] if not ohlc_df.empty else None
    indicators['crsi'] = calculate_crsi_series(ohlc_df['close']).iloc[-1] if not ohlc_df.empty else None
    indicators['williamsR'] = calculate_williams_r_series(ohlc_df['high'], ohlc_df['low'], ohlc_df['close']).iloc[-1] if not ohlc_df.empty else None
    indicators['rvi'] = calculate_rvi_series(ohlc_df['open'], ohlc_df['high'], ohlc_df['low'], ohlc_df['close']).iloc[-1] if not ohlc_df.empty else None
    indicators['adaptiveRsi'] = calculate_adaptive_rsi_series(ohlc_df['close']).iloc[-1] if not ohlc_df.empty else None
    
    return {k: (v if pd.notna(v) else None) for k, v in indicators.items()}


def calculate_composite_metrics_for_api(indicators_dict: dict) -> dict:
    weights = {"stochRsi": 0.30, "crsi": 0.20, "mfi": 0.20, "rsi": 0.15, "williamsR": 0.10, "rvi": 0.03, "adaptiveRsi": 0.02}
    thresholds = {"rsi": 70, "stochRsi": 80, "mfi": 70, "crsi": 90, "williamsR": -20, "rvi": 0.7, "adaptiveRsi": 70}
    cos_monthly, cos_weekly = 0.0, 0.0
    bsi_monthly, bsi_weekly = 0.0, 0.0

    for key, values in indicators_dict.items():
        if key not in weights or values.get('monthly') is None or values.get('weekly') is None:
            continue
        
        monthly_val, weekly_val = values['monthly'], values['weekly']
        threshold_val, weight_val = thresholds[key], weights[key]

        norm_m = (100.0 if monthly_val <= threshold_val else (abs(monthly_val)/abs(threshold_val))*100.0 if abs(threshold_val)>1e-6 else 0.0) if key=='williamsR' else ((monthly_val/threshold_val)*100.0 if abs(threshold_val)>1e-6 else 0.0)
        cos_monthly += weight_val * norm_m
        norm_w = (100.0 if weekly_val <= threshold_val else (abs(weekly_val)/abs(threshold_val))*100.0 if abs(threshold_val)>1e-6 else 0.0) if key=='williamsR' else ((weekly_val/threshold_val)*100.0 if abs(threshold_val)>1e-6 else 0.0)
        cos_weekly += weight_val * norm_w

        neutral_m, neutral_w = (threshold_val*0.5 if key!='williamsR' else -50.0), (threshold_val*0.5 if key!='williamsR' else -50.0)
        den_m, den_w = (threshold_val-neutral_m if abs(threshold_val-neutral_m)>1e-6 else 1e-6), (threshold_val-neutral_w if abs(threshold_val-neutral_w)>1e-6 else 1e-6)
        if key == 'williamsR':
            den_m_wr, den_w_wr = (neutral_m-threshold_val if abs(neutral_m-threshold_val)>1e-6 else 1e-6), (neutral_w-threshold_val if abs(neutral_w-threshold_val)>1e-6 else 1e-6)
            dist_m, dist_w = min(100.0,max(0.0,(neutral_m-monthly_val)/den_m_wr*100.0)), min(100.0,max(0.0,(neutral_w-weekly_val)/den_w_wr*100.0))
        else:
            dist_m, dist_w = min(100.0,max(0.0,(monthly_val-neutral_m)/den_m*100.0)), min(100.0,max(0.0,(weekly_val-neutral_w)/den_w*100.0))
        bsi_monthly += dist_m * weight_val; bsi_weekly += dist_w * weight_val
            
    return {"cos": {"monthly":min(100.0,max(0.0,cos_monthly)), "weekly":min(100.0,max(0.0,cos_weekly))},
            "bsi": {"monthly":min(100.0,max(0.0,bsi_monthly)), "weekly":min(100.0,max(0.0,bsi_weekly))}}

def calculate_price_outcomes(base_date_obj_utc: datetime, base_price: float) -> dict:
    """Calculates price outcomes relative to base_price for 1M, 6M, 12M later."""
    # base_date_obj_utc should be datetime object (start of day UTC)
    if base_price is None: 
        return {p: {'direction':'unknown','percentage':0.0,'price':0.0} for p in ['1M','6M','12M']}
    
    outcomes = {}
    now_utc_start_of_day = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)

    for period_label, months_offset in [('1M',1), ('6M',6), ('12M',12)]:
        # Calculate future date using pandas DateOffset for correct month arithmetic
        future_date_pd = pd.Timestamp(base_date_obj_utc) + pd.DateOffset(months=months_offset)
        # Convert back to datetime object, ensuring it's start of day UTC
        future_date_obj_utc = future_date_pd.to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

        if future_date_obj_utc > now_utc_start_of_day:
            outcomes[period_label] = {'direction':'unknown','percentage':0.0,'price':0.0}
            continue
        
        # fetch_and_store_daily_ohlcv expects a datetime object
        future_price_values, err = fetch_and_store_daily_ohlcv(future_date_obj_utc) 
        
        if future_price_values and future_price_values.get('close') is not None:
            fp = future_price_values['close']
            direction = 'up' if fp > base_price else ('down' if fp < base_price else 'flat')
            percentage = abs(((fp - base_price) / base_price) * 100.0) if base_price != 0 else 0.0
            outcomes[period_label] = {'direction':direction,'percentage':round(percentage,1),'price':round(fp,2)}
        else:
            logger.warning(f"Could not fetch price for {period_label} outcome date {future_date_obj_utc.date()}. Error: {err}")
            outcomes[period_label] = {'direction':'unknown','percentage':0.0,'price':0.0}
    return outcomes