# backend/indicators/adaptive_rsi.py
import pandas as pd
import numpy as np
import logging
from .rsi import calculate as calculate_rsi # Import from sibling rsi module

logger = logging.getLogger(__name__)

def calculate_kama(series: pd.Series, n_period: int = 10, fast_ema_period: int = 2, slow_ema_period: int = 30, timeframe_label_for_debug: str = "") -> pd.Series: # Add debug label
    if series.isnull().all() or len(series.dropna()) < n_period + 1:
        logger.warning(f"KAMA Calc ({timeframe_label_for_debug}): Not enough data or all NaN. Len dropna: {len(series.dropna())}, n_period: {n_period}")
        return pd.Series(np.nan, index=series.index)

    change = series.diff(n_period).abs()
    volatility_sum_abs_diff = series.diff().abs().rolling(window=n_period, min_periods=n_period).sum()
    
    er = change / volatility_sum_abs_diff.replace(0, np.nan) 
    er = er.fillna(0) 

    sc_fast = 2.0 / (fast_ema_period + 1.0)
    sc_slow = 2.0 / (slow_ema_period + 1.0)
    
    smoothing_constant = (er * (sc_fast - sc_slow) + sc_slow)**2
    
    kama = pd.Series(np.nan, index=series.index)
    first_valid_sc_idx = smoothing_constant.first_valid_index()

    # ---- START DEBUG LOGGING for KAMA ----
    if timeframe_label_for_debug == "monthly_adaptive":
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Input Series Tail:\n{series.tail()}")
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Change Tail:\n{change.tail()}")
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Volatility Sum Tail:\n{volatility_sum_abs_diff.tail()}")
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): ER Tail:\n{er.tail()}")
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Smoothing Constant Tail:\n{smoothing_constant.tail()}")
        logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): First valid SC index: {first_valid_sc_idx}")
    # ---- END DEBUG LOGGING for KAMA ----

    if first_valid_sc_idx is None: 
        logger.warning(f"KAMA Calc ({timeframe_label_for_debug}): Could not find valid smoothing constant.")
        return kama 

    kama_start_index_pos = series.index.get_loc(first_valid_sc_idx)
    
    if kama_start_index_pos < len(series):
        kama.iloc[kama_start_index_pos] = series.iloc[kama_start_index_pos]
        if timeframe_label_for_debug == "monthly_adaptive": logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Initialized KAMA at {first_valid_sc_idx} with {kama.iloc[kama_start_index_pos]}")

        for i in range(kama_start_index_pos + 1, len(series)):
            idx_current = series.index[i]
            idx_prev = series.index[i-1]
            
            if pd.notna(kama.loc[idx_prev]) and \
               pd.notna(smoothing_constant.loc[idx_current]) and \
               pd.notna(series.loc[idx_current]):
                kama.loc[idx_current] = kama.loc[idx_prev] + \
                                        smoothing_constant.loc[idx_current] * \
                                        (series.loc[idx_current] - kama.loc[idx_prev])
            else: 
                kama.loc[idx_current] = kama.loc[idx_prev] # Propagate if issues
                if timeframe_label_for_debug == "monthly_adaptive": logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Propagating KAMA for {idx_current} due to NaN inputs (prev_kama:{pd.notna(kama.loc[idx_prev])}, sc:{pd.notna(smoothing_constant.loc[idx_current])}, price:{pd.notna(series.loc[idx_current])})")
        if timeframe_label_for_debug == "monthly_adaptive": logger.debug(f"KAMA Monthly ({timeframe_label_for_debug}): Final KAMA tail:\n{kama.tail()}")
    else:
        logger.warning(f"KAMA Calc ({timeframe_label_for_debug}): first_valid_sc_idx out of bounds.")
        
    return kama


def calculate(ohlc_df: pd.DataFrame, period: int = 14, kama_n: int = 10, kama_fast_ema: int = 2, kama_slow_ema: int = 30) -> pd.Series:
    timeframe_debug_label = "monthly_adaptive" if len(ohlc_df) < 50 else "weekly_adaptive" # Simple label for KAMA debug
    logger.info(f"AdaptiveRSI Calc ({timeframe_debug_label}): Using RSI of KAMA-smoothed prices. KAMA params: n={kama_n}, fast={kama_fast_ema}, slow={kama_slow_ema}. RSI period={period}")

    if 'close' not in ohlc_df.columns or ohlc_df['close'].isnull().all():
        logger.warning(f"AdaptiveRSI Calc ({timeframe_debug_label}): 'close' column missing or all NaN. Len: {len(ohlc_df)}")
        return pd.Series(dtype=float, index=ohlc_df.index)
    
    # Adjusted length check for KAMA + RSI
    # KAMA itself needs kama_n for diff, kama_n for rolling sum -> at least kama_n.
    # Then iterative KAMA needs some points. RSI needs `period`.
    min_len_kama = kama_n + 1 # For diff(n) and first value of rolling(n)
    min_len_rsi_on_kama = period +1
    if len(ohlc_df.dropna(subset=['close'])) < min_len_kama + min_len_rsi_on_kama: # Check based on non-NaN close values
        logger.warning(f"AdaptiveRSI Calc ({timeframe_debug_label}): Not enough data ({len(ohlc_df.dropna(subset=['close']))}) for KAMA(n={kama_n}) + RSI({period}).")
        return pd.Series(dtype=float, index=ohlc_df.index)

    kama_series = calculate_kama(ohlc_df['close'], n_period=kama_n, 
                                 fast_ema_period=kama_fast_ema, slow_ema_period=kama_slow_ema,
                                 timeframe_label_for_debug=timeframe_debug_label)

    if kama_series.isnull().all():
        logger.warning(f"AdaptiveRSI Calc ({timeframe_debug_label}): KAMA calculation resulted in all NaNs. Falling back to standard RSI.")
        return calculate_rsi(ohlc_df, period=period)

    kama_df_for_rsi = pd.DataFrame({'close': kama_series}, index=ohlc_df.index)
    adaptive_rsi_series = calculate_rsi(kama_df_for_rsi, period=period)
    
    if adaptive_rsi_series.isnull().all():
         logger.warning(f"AdaptiveRSI Calc ({timeframe_debug_label}): RSI on KAMA resulted in all NaNs. Falling back to standard RSI on original close.")
         return calculate_rsi(ohlc_df, period=period) 
         
    return adaptive_rsi_series