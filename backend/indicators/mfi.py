# backend/indicators/mfi.py
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# This log line will confirm the pandas version when the module is loaded.
# Keep it for now to ensure we're not mistaken about the version.
logger.info(f"MFI Module: Pandas version being used: {pd.__version__}")

def calculate(ohlc_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Money Flow Index (MFI) manually."""
    required_cols = {'high', 'low', 'close', 'volume'}
    if not required_cols.issubset(ohlc_df.columns) or ohlc_df.isnull().all().all():
        logger.warning(f"MFI Calc: Missing required columns or all NaN data. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    if len(ohlc_df) < period + 1: 
         logger.warning(f"MFI Calc: Not enough data ({len(ohlc_df)}) for period {period}.")
         return pd.Series(dtype=float, index=ohlc_df.index)

    df_copy = ohlc_df.copy()
    for col in required_cols: # Ensure numeric types
        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    
    if df_copy[list(required_cols)].isnull().all().any():
        logger.warning(f"MFI Calc: One or more required columns became all NaN after numeric conversion.")
        return pd.Series(dtype=float, index=ohlc_df.index)

    typical_price = (df_copy['high'] + df_copy['low'] + df_copy['close']) / 3.0
    raw_money_flow = typical_price * df_copy['volume']

    money_flow_direction = typical_price.diff() 

    positive_money_flow = pd.Series(0.0, index=ohlc_df.index)
    negative_money_flow = pd.Series(0.0, index=ohlc_df.index)

    positive_mask = money_flow_direction > 0
    negative_mask = money_flow_direction < 0

    positive_money_flow.loc[positive_mask] = raw_money_flow.loc[positive_mask]
    negative_money_flow.loc[negative_mask] = raw_money_flow.loc[negative_mask]
    
    sum_pos_mf = positive_money_flow.rolling(window=period, min_periods=period).sum()
    sum_neg_mf = negative_money_flow.rolling(window=period, min_periods=period).sum()

    money_flow_ratio = sum_pos_mf / sum_neg_mf.replace(0, np.nan) 
    
    mfi_series = 100.0 - (100.0 / (1.0 + money_flow_ratio))
    
    # --- Use .loc for conditional filling, removing 'where' ---
    # Case 1: Positive flow, zero negative flow -> MFR is NaN (inf), MFI should be 100
    # We fill NaNs in mfi_series that satisfy this condition.
    condition_fill_100 = mfi_series.isnull() & (sum_pos_mf > 0) & (sum_neg_mf == 0)
    mfi_series.loc[condition_fill_100] = 100.0
    
    # Case 2: No flow (both positive and negative are zero) -> MFR is NaN, MFI set to 50
    # (This is a common convention for MFI when there's no discernible money flow)
    condition_fill_50 = mfi_series.isnull() & (sum_pos_mf == 0) & (sum_neg_mf == 0)
    mfi_series.loc[condition_fill_50] = 50.0
    
    # Case 3: Zero positive flow, some negative flow -> MFR is 0, MFI is 0
    # This is naturally handled by the MFI formula: 100 - (100 / (1+0)) = 0.
    # No specific fillna needed for this case if money_flow_ratio correctly becomes 0.

    mfi_series = mfi_series.clip(0, 100) 
    return mfi_series