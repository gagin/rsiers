# backend/indicators/williams_r.py
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate(ohlc_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Williams %R manually."""
    required_cols = {'high', 'low', 'close'}
    if not required_cols.issubset(ohlc_df.columns) or ohlc_df.isnull().all().all():
        logger.warning(f"Williams %R Calc: Missing required columns or all NaN data. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    if len(ohlc_df) < period:
         logger.warning(f"Williams %R Calc: Not enough data ({len(ohlc_df)}) for period {period}.")
         return pd.Series(dtype=float, index=ohlc_df.index)

    highest_high = ohlc_df['high'].rolling(window=period, min_periods=period).max()
    lowest_low = ohlc_df['low'].rolling(window=period, min_periods=period).min()
    close = ohlc_df['close']

    # (Highest High - Current Close) / (Highest High - Lowest Low)
    numerator = highest_high - close
    denominator = (highest_high - lowest_low).replace(0, np.nan) # Avoid division by zero

    williams_r = (numerator / denominator) * -100.0
    return williams_r