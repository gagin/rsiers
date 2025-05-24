# backend/services/outcome_service.py
import pandas as pd
import logging
from datetime import datetime as PyDateTime, timezone

# To avoid circular dependency if data_sources imports outcome_service,
# we perform the import of fetch_and_store_daily_ohlcv inside the function.
# from backend.data_sources import fetch_and_store_daily_ohlcv 

logger = logging.getLogger(__name__)

def calculate_price_outcomes(base_date_obj_utc: PyDateTime, base_price: float) -> dict:
    """
    Calculates price outcomes relative to base_price for 1M, 6M, 12M later.
    
    Args:
        base_date_obj_utc: The datetime object (start of day UTC) for the base price.
        base_price: The price at the base_date_obj_utc.
        
    Returns:
        A dictionary of outcomes: 
        {'1M': {'direction': str, 'percentage': float, 'price': float}, ...}
    """
    from backend.data_sources import fetch_and_store_daily_ohlcv # Import here

    if base_price is None or pd.isna(base_price) or base_price == 0: 
        logger.warning(f"Outcome Service: Cannot calculate outcomes for base_date {base_date_obj_utc.date()} due to invalid base_price: {base_price}")
        return {p: {'direction':'unknown','percentage':0.0,'price':0.0} for p in ['1M','6M','12M']}
    
    outcomes = {}
    now_utc_start_of_day = PyDateTime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)

    for period_label, months_offset in [('1M',1), ('6M',6), ('12M',12)]:
        future_date_pd = pd.Timestamp(base_date_obj_utc) + pd.DateOffset(months=months_offset)
        future_date_obj_utc = future_date_pd.to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

        if future_date_obj_utc > now_utc_start_of_day:
            logger.debug(f"Outcome Service: Future date {future_date_obj_utc.date()} for {period_label} is beyond today. Outcome unknown.")
            outcomes[period_label] = {'direction':'unknown','percentage':0.0,'price':0.0}
            continue
        
        logger.debug(f"Outcome Service: Fetching price for {period_label} outcome date {future_date_obj_utc.date()} (base date {base_date_obj_utc.date()}).")
        future_price_values, err = fetch_and_store_daily_ohlcv(future_date_obj_utc) 
        
        if future_price_values and future_price_values.get('close') is not None and pd.notna(future_price_values.get('close')):
            fp = float(future_price_values['close'])
            direction = 'up' if fp > base_price else ('down' if fp < base_price else 'flat')
            percentage = abs(((fp - base_price) / base_price) * 100.0) 
            outcomes[period_label] = {'direction':direction,'percentage':round(percentage,1),'price':round(fp,2)}
            logger.debug(f"Outcome Service: {period_label} outcome for {base_date_obj_utc.date()} -> {future_date_obj_utc.date()}: Price={fp}, Direction={direction}, Change={percentage:.1f}%")
        else:
            logger.warning(f"Outcome Service: Could not fetch price for {period_label} outcome date {future_date_obj_utc.date()} (base date {base_date_obj_utc.date()}). Error: {err}")
            outcomes[period_label] = {'direction':'unknown','percentage':0.0,'price':0.0}
    
    logger.info(f"Calculated Price Outcomes for base date {base_date_obj_utc.date()}: {outcomes}")
    return outcomes