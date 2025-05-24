# backend/indicators/rvi.py
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate(ohlc_df: pd.DataFrame, period: int = 10) -> pd.Series:
    """Calculates Relative Vigor Index (RVI) main line manually."""
    required_cols = {'open', 'high', 'low', 'close'}
    if not required_cols.issubset(ohlc_df.columns) or ohlc_df.isnull().all().all():
        logger.warning(f"RVI Calc: Missing required columns or all NaN data. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    if len(ohlc_df) < period : # SMA lookback
         logger.warning(f"RVI Calc: Not enough data ({len(ohlc_df)}) for period {period}.")
         return pd.Series(dtype=float, index=ohlc_df.index)

    numerator = ohlc_df['close'] - ohlc_df['open']
    denominator = (ohlc_df['high'] - ohlc_df['low']).replace(0, np.nan) # Avoid division by zero
    
    rvi_val = numerator / denominator # Individual RVI values for each bar
    
    # Standard RVI is often a symmetric Wilder's MA of these values, or SMA.
    # Let's use SMA for simplicity as specified in some common definitions for the main line.
    rvi_sma = rvi_val.rolling(window=period, min_periods=period).mean() 
    return rvi_sma