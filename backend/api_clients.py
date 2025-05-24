# backend/api_clients.py
import time
import logging
import requests
from datetime import datetime, timezone # Ensure timezone is imported from datetime
from backend import config 

logger = logging.getLogger(__name__)

class CoinGeckoAPI:
    def get_ohlcv_for_date(self, date_obj_utc: datetime, 
                           retries=config.COINGECKO_RETRIES, 
                           delay=config.COINGECKO_DELAY):
        date_str_coingecko_format = date_obj_utc.strftime('%d-%m-%Y')
        url = f"{config.COINGECKO_API_BASE_URL}/coins/bitcoin/history?date={date_str_coingecko_format}&localization=false"
        for attempt in range(retries):
            try:
                # Apply delay logic: initial delay * attempt for simple linear backoff,
                # or delay * (2**attempt) for exponential if preferred for rate limits.
                # For now, simple incremental delay based on attempt number.
                time.sleep(delay * attempt if attempt > 0 else 0) 
                logger.info(f"CoinGeckoAPI: Fetching history for {date_str_coingecko_format} (Date: {date_obj_utc.date()}), Attempt {attempt + 1}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get('market_data') and data['market_data'].get('current_price') and data['market_data']['current_price'].get('usd'):
                    price = data['market_data']['current_price']['usd']
                    volume = data['market_data'].get('total_volume', {}).get('usd', 0)
                    return {'open': price, 'high': price, 'low': price, 'close': price, 
                            'volume': volume, 'source': 'coingecko'}
                else: 
                    logger.warning(f"CoinGeckoAPI: No price data for {date_str_coingecko_format}. Response: {str(data)[:200]}")
                    return None
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429: 
                    current_retry_delay = delay * (2 ** (attempt + 1)) # Exponential backoff for rate limit
                    logger.warning(f"CoinGeckoAPI: Rate limit hit for {date_str_coingecko_format} (Attempt {attempt + 1}). Retrying in {current_retry_delay}s...")
                    if attempt == retries - 1: 
                        logger.error(f"CoinGeckoAPI: Error after {retries} retries for {date_str_coingecko_format}: {e}")
                        return None
                    time.sleep(current_retry_delay) 
                    continue
                logger.error(f"CoinGeckoAPI: HTTP error for {date_str_coingecko_format}: {e} - Response: {str(e.response.text)[:200]}"); return None
            except requests.exceptions.RequestException as e: # More general network issues
                logger.error(f"CoinGeckoAPI: Request error for {date_str_coingecko_format}: {e}")
                if attempt == retries - 1: return None
                time.sleep(delay * (attempt + 1)) # Simple linear backoff for other request errors
            except Exception as e: 
                logger.error(f"CoinGeckoAPI: Unexpected error for {date_str_coingecko_format}: {e}", exc_info=True); return None
        return None


class KrakenAPI:
    def get_ohlcv_for_date(self, date_obj_utc: datetime, pair='XXBTZUSD', interval=1440, 
                           retries=config.KRAKEN_RETRIES, 
                           delay_seconds=config.KRAKEN_DELAY_SECONDS):
        target_day_start_ts = int(date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        current_since_ts = target_day_start_ts 

        url = config.KRAKEN_API_BASE_URL
        
        for attempt in range(retries):
            if attempt > 0 and current_since_ts == target_day_start_ts: 
                logger.info(f"KrakenAPI: Retrying with 'since' as 1 day earlier for {date_obj_utc.date()}")
                current_since_ts = target_day_start_ts - (24 * 60 * 60)
            
            params = {'pair': pair, 'interval': interval, 'since': current_since_ts}

            try:
                if attempt > 0: time.sleep(delay_seconds * (2**attempt)) 
                
                logger.info(f"KrakenAPI: Attempt {attempt+1} for {pair} on {date_obj_utc.strftime('%Y-%m-%d')} (Target TS: {target_day_start_ts}, using since={current_since_ts})")
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                if 'error' in data and data['error']:
                    error_str = str(data['error'])
                    logger.error(f"KrakenAPI: API error for {date_obj_utc.date()}: {error_str}")
                    if "EAPI:Rate limit exceeded" in error_str and attempt < retries - 1:
                        current_retry_delay = delay_seconds * (2**(attempt + 1))
                        logger.info(f"KrakenAPI: Rate limit, retrying in {current_retry_delay}s...")
                        time.sleep(current_retry_delay)
                        continue 
                    return None 

                result_pair_key = pair
                if pair not in data.get('result', {}):
                    alt_pair = pair.replace("XXBT", "XBT") if "XXBT" in pair else pair.replace("XBT", "XXBT")
                    if alt_pair in data.get('result', {}):
                        result_pair_key = alt_pair
                    else:
                        result_pair_key = None

                if result_pair_key and data['result'].get(result_pair_key):
                    candles = data['result'][result_pair_key]
                    if not candles and attempt == 0 and current_since_ts == target_day_start_ts:
                        logger.warning(f"KrakenAPI: No candles returned for {date_obj_utc.date()} with precise since={target_day_start_ts}. Will retry with earlier 'since'.")
                        continue 

                    for candle_data_list in candles:
                        if int(candle_data_list[0]) == target_day_start_ts:
                            logger.info(f"KrakenAPI: Found exact match for TS {target_day_start_ts} for date {date_obj_utc.date()}")
                            return {'open': float(candle_data_list[1]), 'high': float(candle_data_list[2]),
                                    'low': float(candle_data_list[3]), 'close': float(candle_data_list[4]), 
                                    'volume': float(candle_data_list[6]), 'source': 'kraken'}
                    
                    if current_since_ts < target_day_start_ts: 
                        for candle_data_list in candles:
                            candle_ts = int(candle_data_list[0])
                            # Use datetime.timezone.utc directly
                            candle_dt_utc = datetime.fromtimestamp(candle_ts, tz=timezone.utc)
                            if candle_dt_utc.date() == date_obj_utc.date():
                                logger.warning(f"KrakenAPI: No exact 00:00 UTC candle for {date_obj_utc.date()}. Using first available candle for that day (starts at {candle_dt_utc.time()}).")
                                return {'open': float(candle_data_list[1]), 'high': float(candle_data_list[2]),
                                        'low': float(candle_data_list[3]), 'close': float(candle_data_list[4]), 
                                        'volume': float(candle_data_list[6]), 'source': 'kraken_adjusted_time'}
                    
                    logger.warning(f"KrakenAPI: No suitable candle found for {date_obj_utc.date()} (Target TS: {target_day_start_ts}). Returned (up to 2): {str(candles[:2])[:200]}")
                    return None 
                else:
                    logger.warning(f"KrakenAPI: No data for {result_pair_key or pair} or unexpected format for {date_obj_utc.date()}. Response: {str(data)[:200]}")
                    return None
            except requests.exceptions.HTTPError as e:
                logger.error(f"KrakenAPI: HTTP error {e.response.status_code} for {date_obj_utc.date()}: {str(e.response.text)[:200]}")
                if e.response.status_code in [500,502,503,504,520] and attempt < retries-1: continue
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"KrakenAPI: Request error for {date_obj_utc.date()}: {e}")
                if attempt == retries - 1: return None
                time.sleep(delay_seconds * (attempt+1))
            except Exception as e:
                logger.error(f"KrakenAPI: Unexpected error for {date_obj_utc.date()}: {e}", exc_info=True)
                return None
        return None

coingecko_api_client = CoinGeckoAPI()
kraken_api_client = KrakenAPI()