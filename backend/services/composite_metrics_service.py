# backend/services/composite_metrics_service.py
import pandas as pd
import logging
from backend import config # Import config

logger = logging.getLogger(__name__)

def calculate_composite_metrics(indicators_dict: dict) -> dict:
    # Use parameters from config
    weights = config.COMPOSITE_METRICS_WEIGHTS
    thresholds = config.COMPOSITE_METRICS_THRESHOLDS
    neutral_points = config.COMPOSITE_METRICS_NEUTRAL_POINTS
    MAX_NORMALIZED_SCORE_COMPONENT = config.COMPOSITE_MAX_NORMALIZED_SCORE_COMPONENT
    
    cos_monthly_sum, cos_weekly_sum = 0.0, 0.0
    bsi_monthly_sum, bsi_weekly_sum = 0.0, 0.0

    # ... (The rest of the calculation logic using these config parameters remains the same as your last correct version)
    for key, values_for_tf in indicators_dict.items():
        if key not in weights or values_for_tf is None: 
            logger.debug(f"Composite Metrics Service: Skipping {key}, not in weights or no data.")
            continue
        
        monthly_val = values_for_tf.get('monthly')
        weekly_val = values_for_tf.get('weekly')
        
        current_threshold = thresholds[key]
        current_neutral = neutral_points[key]
        current_weight = weights[key]

        denominator = current_threshold - current_neutral
        if abs(denominator) < 1e-6: 
            logger.warning(f"Composite Metrics: Indicator {key} has neutral point same as threshold. Skipping.")
            continue

        if monthly_val is not None and pd.notna(monthly_val):
            normalized_score_m = ((monthly_val - current_neutral) / denominator) * 100.0
            cos_contribution_m = min(MAX_NORMALIZED_SCORE_COMPONENT, max(0.0, normalized_score_m))
            cos_monthly_sum += current_weight * cos_contribution_m
            bsi_contribution_m = min(100.0, max(0.0, normalized_score_m))
            bsi_monthly_sum += current_weight * bsi_contribution_m
        else:
            logger.debug(f"Composite Metrics Service: Skipping monthly for {key}, value is None.")

        if weekly_val is not None and pd.notna(weekly_val):
            normalized_score_w = ((weekly_val - current_neutral) / denominator) * 100.0
            cos_contribution_w = min(MAX_NORMALIZED_SCORE_COMPONENT, max(0.0, normalized_score_w))
            cos_weekly_sum += current_weight * cos_contribution_w
            bsi_contribution_w = min(100.0, max(0.0, normalized_score_w))
            bsi_weekly_sum += current_weight * bsi_contribution_w
        else:
            logger.debug(f"Composite Metrics Service: Skipping weekly for {key}, value is None.")
            
    final_cos_monthly = min(100.0, max(0.0, cos_monthly_sum))
    final_cos_weekly = min(100.0, max(0.0, cos_weekly_sum))
    final_bsi_monthly = min(100.0, max(0.0, bsi_monthly_sum))
    final_bsi_weekly = min(100.0, max(0.0, bsi_weekly_sum))
            
    final_metrics = {
        "cos": {"monthly": final_cos_monthly, "weekly": final_cos_weekly},
        "bsi": {"monthly": final_bsi_monthly, "weekly": final_bsi_weekly}
    }
    
    logger.info(f"Calculated Composite Metrics: {final_metrics} (Raw sums before final clip: COS_M={cos_monthly_sum:.2f}, COS_W={cos_weekly_sum:.2f}, BSI_M={bsi_monthly_sum:.2f}, BSI_W={bsi_weekly_sum:.2f})")
    return final_metrics