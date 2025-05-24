# backend/indicators/connors_rsi.py
import pandas as pd
import numpy as np
import logging
from .rsi import calculate as calculate_rsi # Import from sibling rsi module

logger = logging.getLogger(__name__)

def calculate(ohlc_df: pd.DataFrame, rsi_short_len: int = 3, rsi_streak_len: int = 2, rank_len: int = 100) -> pd.Series:
    """Calculates ConnorsRSI manually."""
    if 'close' not in ohlc_df.columns or ohlc_df['close'].isnull().all():
        logger.warning(f"CRSI Calc: 'close' column missing or all NaN. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    # rank_len is usually the longest lookback. Add buffer for other calcs.
    if len(ohlc_df) < rank_len + rsi_short_len + rsi_streak_len + 5: 
        logger.warning(f"CRSI Calc: Not enough data ({len(ohlc_df)}) for combined periods.")
        return pd.Series(dtype=float, index=ohlc_df.index)
        
    close = ohlc_df['close']

    # 1. RSI(Close, rsi_short_len)
    rsi1 = calculate_rsi(ohlc_df, period=rsi_short_len)

    # 2. RSI(Streak, rsi_streak_len)
    close_diff = close.diff() # close_diff[0] is NaN
    streaks = pd.Series(0.0, index=ohlc_df.index) # Initialize with 0.0 for float type

    for i in range(1, len(close)): # Iterate based on original close length
        current_idx = ohlc_df.index[i]
        prev_idx = ohlc_df.index[i-1]
        
        if pd.isna(close_diff.loc[current_idx]): # Should only be the first diff
            streaks.loc[current_idx] = 0.0
            continue

        if close_diff.loc[current_idx] > 0: # Price increased
            streaks.loc[current_idx] = streaks.loc[prev_idx] + 1 if streaks.loc[prev_idx] > 0 else 1.0
        elif close_diff.loc[current_idx] < 0: # Price decreased
            streaks.loc[current_idx] = streaks.loc[prev_idx] - 1 if streaks.loc[prev_idx] < 0 else -1.0
        else: # Price unchanged
            streaks.loc[current_idx] = 0.0
    
    streak_df = pd.DataFrame({'close': streaks.fillna(0)}, index=ohlc_df.index) 
    rsi_streak = calculate_rsi(streak_df, period=rsi_streak_len)

    # 3. PercentRank(ROC(Close,1), rank_len)
    roc1 = close.pct_change(periods=1) * 100 
    roc1 = roc1.fillna(0) # Fill first NaN for rolling rank
    
    # Calculate percentile rank
    # x.rank(pct=True).iloc[-1] gets the rank of the last element in the window
    percent_rank_roc = roc1.rolling(window=rank_len, min_periods=rank_len).apply(
        lambda x_window: pd.Series(x_window).rank(pct=True, method='average').iloc[-1] * 100 if pd.Series(x_window).notna().any() else np.nan,
        raw=False 
    )
    
    crsi_series = (rsi1 + rsi_streak + percent_rank_roc) / 3.0
    return crsi_series