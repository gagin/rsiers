# tests/modular/test_indicator_calc.py

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Adjust Python path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"INFO: Added '{project_root}' to sys.path for module resolution.")

# Main function to test from indicator_calculator
from backend.indicator_calculator import (
    calculate_indicators_from_ohlc_df,
    resample_ohlc_data # Also needed for preparing test data
)
from backend import config as app_config # To get MIN_CANDLES_FOR_CALCULATION

def create_sample_ohlcv_df(num_days=200) -> pd.DataFrame:
    base_start_date = datetime(2023, 1, 1) 
    start_date = base_start_date - timedelta(days=num_days -1)
    dates = pd.date_range(start_date, periods=num_days, freq='D', tz='UTC')
    price_path = 1000 + np.cumsum(np.random.normal(0, 5, num_days)) 
    price_path = np.maximum(price_path, 50) 
    data = {
        'open': price_path - np.random.rand(num_days) * 10,
        'close': price_path,
        'high': price_path + np.random.rand(num_days) * 10,
        'low': price_path - np.random.rand(num_days) * 20, 
        'volume': np.random.rand(num_days) * 1000 + 500 
    }
    df = pd.DataFrame(data, index=dates)
    df['high'] = df[['high', 'open', 'close']].max(axis=1)
    df['low'] = df[['low', 'open', 'close']].min(axis=1)
    first_open_val = df['close'].iloc[0] * (1 - np.random.uniform(0, 0.02)) 
    df['open'] = df['close'].shift(1) 
    df.iloc[0, df.columns.get_loc('open')] = first_open_val 
    print(f"--- Sample Daily OHLCV DataFrame ({num_days} days, last 5 rows): ---")
    print(df.tail())
    print("-" * 50)
    return df

def print_indicator_results_dict(title: str, results_dict: dict):
    print(f"\n--- {title} ---")
    if results_dict:
        for key, value in results_dict.items():
            val_str = f"{value:.2f}" if isinstance(value, (int, float)) and pd.notna(value) else str(value)
            print(f"  {key.ljust(12)}: {val_str}")
    else:
        print("  Calculation returned None or empty dictionary.")
    print("-" * 50)


if __name__ == "__main__":
    print(f"Executing test script from: {os.path.abspath(__file__)}")
    print("Testing `calculate_indicators_from_ohlc_df` for different timeframes...\n")
    
    sample_daily_df = create_sample_ohlcv_df(num_days=730) # Approx 2 years for good resampling

    # Test Weekly calculations
    sample_weekly_df = resample_ohlc_data(sample_daily_df, rule='W-MON')
    if not sample_weekly_df.empty and len(sample_weekly_df) >= app_config.MIN_CANDLES_FOR_CALCULATION:
        print(f"\n--- Sample Weekly OHLCV (first 3, last 3 rows, len={len(sample_weekly_df)}): ---")
        print(pd.concat([sample_weekly_df.head(3), sample_weekly_df.tail(3)]))
        weekly_indicators = calculate_indicators_from_ohlc_df(sample_weekly_df, timeframe_label='weekly')
        print_indicator_results_dict("Weekly Indicator Set Results", weekly_indicators)
    else:
        print(f"\n--- Skipping WEEKLY Indicator Set: Not enough resampled data (found {len(sample_weekly_df)}, need {app_config.MIN_CANDLES_FOR_CALCULATION}) ---")

    # Test Monthly calculations
    sample_monthly_df = resample_ohlc_data(sample_daily_df, rule='ME')
    if not sample_monthly_df.empty and len(sample_monthly_df) >= app_config.MIN_CANDLES_FOR_CALCULATION:
        print(f"\n--- Sample Monthly OHLCV (first 3, last 3 rows, len={len(sample_monthly_df)}): ---")
        print(pd.concat([sample_monthly_df.head(3), sample_monthly_df.tail(3)]))
        monthly_indicators = calculate_indicators_from_ohlc_df(sample_monthly_df, timeframe_label='monthly')
        print_indicator_results_dict("Monthly Indicator Set Results", monthly_indicators)
    else:
        print(f"\n--- Skipping MONTHLY Indicator Set: Not enough resampled data (found {len(sample_monthly_df)}, need {app_config.MIN_CANDLES_FOR_CALCULATION}) ---")
           
    print("\nTest script finished.")