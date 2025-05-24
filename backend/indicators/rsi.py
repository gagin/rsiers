# backend/indicators/rsi.py
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate(ohlc_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI) manually using Wilder's Smoothing.
    """
    if 'close' not in ohlc_df.columns or ohlc_df['close'].isnull().all():
        logger.warning(f"RSI Calc: 'close' column missing or all NaN. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    
    close_prices = ohlc_df['close'].copy() # Work on a copy
    if len(close_prices) < period + 1: # Need at least period + 1 for the first diff
        logger.warning(f"RSI Calc: Not enough data ({len(close_prices)}) for period {period}.")
        return pd.Series(dtype=float, index=ohlc_df.index)

    delta = close_prices.diff()
    # delta.iloc[0] is NaN. Valid changes start from index 1.

    gain = delta.copy()
    loss = delta.copy()
    
    gain[gain < 0] = 0.0
    loss[loss > 0] = 0.0
    loss = loss.abs()

    avg_gain = pd.Series(np.nan, index=close_prices.index)
    avg_loss = pd.Series(np.nan, index=close_prices.index)

    # Calculate initial SMA for the first avg_gain and avg_loss
    # This value will be at ohlc_df.index[period]
    avg_gain.iloc[period] = gain.iloc[1:period+1].mean()
    avg_loss.iloc[period] = loss.iloc[1:period+1].mean()
    
    # Wilder's smoothing for subsequent values
    for i in range(period + 1, len(close_prices)):
        if pd.isna(avg_gain.iloc[i-1]) or pd.isna(avg_loss.iloc[i-1]): # Propagate NaN if previous avg is NaN
            avg_gain.iloc[i] = np.nan
            avg_loss.iloc[i] = np.nan
            continue
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
    
    rs = avg_gain / avg_loss.replace(0, np.nan) 
    rsi_series = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi_series