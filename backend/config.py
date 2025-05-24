# backend/config.py

# --- General Settings ---
LOG_LEVEL = "INFO" # e.g., "DEBUG", "INFO", "WARNING"

# --- Data Fetching ---
# Number of years of daily data to fetch for calculating indicators
HISTORICAL_DATA_YEARS = 2

# --- Indicator Calculation Parameters ---

# Minimum number of data points (candles) required in a resampled OHLCV DataFrame
# before attempting to calculate any indicators for that period.
# If a resampled monthly_df has fewer rows than this, all monthly indicators will be None.
MIN_CANDLES_FOR_CALCULATION = 20 # Was 30, then 20. Let's keep it at 20 for now.

# Default parameters (can be used for weekly or if not overridden by timeframe-specific)
DEFAULT_INDICATOR_PARAMS = {
    "rsi": {"period": 14},
    "stochRsi": {"rsi_period": 14, "stoch_period": 14, "k_smooth": 3},
    "mfi": {"period": 14},
    "crsi": {"rsi_short_len": 3, "rsi_streak_len": 2, "rank_len": 100}, # Note: rank_len is long
    "williamsR": {"period": 14},
    "rvi": {"period": 10}, # RVI main line period
    "adaptiveRsi": {"period": 14, "kama_n": 10, "kama_fast_ema": 2, "kama_slow_ema": 30}
}

# Timeframe-specific parameter overrides
# These will be used if the timeframe_label matches.
TIMEFRAME_SPECIFIC_PARAMS = {
    "monthly": {
        "stochRsi": {"rsi_period": 7, "stoch_period": 7, "k_smooth": 3},
        # CRSI rank_len for monthly: dynamically set based on available data later,
        # but we can provide a target max if desired, or a flag to calculate it.
        # For now, let's aim for a smaller default if we were to hardcode.
        "crsi": {"rsi_short_len": 3, "rsi_streak_len": 2, "rank_len": 12}, # Target for ~24 months of data
        "adaptiveRsi": {"period": 14, "kama_n": 5, "kama_fast_ema": 2, "kama_slow_ema": 10} # Shorter KAMA
    },
    "weekly": {
        # CRSI rank_len for weekly:
        "crsi": {"rsi_short_len": 3, "rsi_streak_len": 2, "rank_len": 50}, # Reduced from 100
        # Other weekly params can use defaults or be specified here if different
    }
}

# --- Composite Metrics Calculation Parameters ---
COMPOSITE_METRICS_WEIGHTS = {
    "stochRsi": 0.30, 
    "crsi": 0.20, 
    "mfi": 0.20, 
    "rsi": 0.15, 
    "williamsR": 0.10, 
    "rvi": 0.03, 
    "adaptiveRsi": 0.02
}

COMPOSITE_METRICS_THRESHOLDS = {
    "rsi": 70, 
    "stochRsi": 80, 
    "mfi": 70, 
    "crsi": 90, 
    "williamsR": -20, 
    "rvi": 0.7, 
    "adaptiveRsi": 70
}

COMPOSITE_METRICS_NEUTRAL_POINTS = {
    "rsi": 50.0, 
    "stochRsi": 50.0, 
    "mfi": 50.0, 
    "crsi": 50.0, 
    "williamsR": -50.0,
    "rvi": 0.0, 
    "adaptiveRsi": 50.0
}

# Max individual normalized score component for COS (allows "extreme" readings to have more impact)
COMPOSITE_MAX_NORMALIZED_SCORE_COMPONENT = 150.0


# --- API Client Configuration ---
COINGECKO_API_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_RETRIES = 3
COINGECKO_DELAY = 2 # seconds, initial delay

KRAKEN_API_BASE_URL = "https://api.kraken.com/0/public/OHLC"
KRAKEN_RETRIES = 3
KRAKEN_DELAY_SECONDS = 1

# You can add other configurations here, e.g., database path if you want it configurable,
# though DB_PATH is currently derived in db_utils.py.

# Helper function to get parameters for a specific indicator and timeframe
def get_indicator_params(indicator_key: str, timeframe_label: str = None) -> dict:
    """
    Returns the parameters for a given indicator, considering timeframe overrides.
    """
    params = DEFAULT_INDICATOR_PARAMS.get(indicator_key, {}).copy()
    if timeframe_label and timeframe_label in TIMEFRAME_SPECIFIC_PARAMS:
        timeframe_params = TIMEFRAME_SPECIFIC_PARAMS[timeframe_label].get(indicator_key, {})
        params.update(timeframe_params) # Override defaults with timeframe-specific ones

    # Special dynamic adjustment for CRSI rank_len based on timeframe
    # This needs the actual length of the ohlc_df for the timeframe, so it's better handled
    # in calculate_indicators_from_ohlc_df where that length is known.
    # Here, we just return the statically configured (or default) rank_len.
    # The dynamic adjustment will happen in indicator_calculator.py.

    return params