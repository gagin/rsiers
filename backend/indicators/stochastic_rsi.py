# backend/indicators/stochastic_rsi.py
import pandas as pd
import numpy as np
import logging
from .rsi import calculate as calculate_rsi # Import from sibling rsi module

logger = logging.getLogger(__name__)

def calculate(ohlc_df: pd.DataFrame, rsi_period: int = 14, stoch_period: int = 14, k_smooth: int = 3) -> pd.Series:
    """Calculates Stochastic RSI (%K line) manually."""
    if 'close' not in ohlc_df.columns:
        logger.warning("StochRSI Calc: 'close' column missing.")
        return pd.Series(dtype=float, index=ohlc_df.index)

    rsi_series = calculate_rsi(ohlc_df, period=rsi_period)
    if rsi_series.isnull().all():
        logger.warning("StochRSI Calc: Underlying RSI calculation resulted in all NaNs.")
        return pd.Series(dtype=float, index=ohlc_df.index)
    
    if len(rsi_series.dropna()) < stoch_period : # Need enough non-NaN RSI values
        logger.warning(f"StochRSI Calc: Not enough valid RSI data points ({len(rsi_series.dropna())}) for stoch_period {stoch_period}.")
        return pd.Series(dtype=float, index=ohlc_df.index)

    min_rsi = rsi_series.rolling(window=stoch_period, min_periods=stoch_period).min()
    max_rsi = rsi_series.rolling(window=stoch_period, min_periods=stoch_period).max()
    
    # (Current RSI - Min RSI over stoch_period) / (Max RSI over stoch_period - Min RSI over stoch_period)
    stoch_rsi_k_raw = ((rsi_series - min_rsi) / (max_rsi - min_rsi).replace(0, np.nan)) * 100
    
    # Smooth %K
    stoch_rsi_k_smoothed = stoch_rsi_k_raw.rolling(window=k_smooth, min_periods=max(1, k_smooth)).mean() # min_periods=1 if k_smooth < stoch_period
    return stoch_rsi_k_smoothed