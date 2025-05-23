# backend/db_utils.py
import sqlite3
import logging
import time
import os
from datetime import datetime, timezone, date as DtDate # For type hinting

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'bitcoin_daily_data.db')

def date_to_iso_string(date_obj: DtDate) -> str:
    """Converts a date object to 'YYYY-MM-DD' ISO string."""
    return date_obj.strftime('%Y-%m-%d')

def iso_string_to_date(date_str: str) -> DtDate:
    """Converts 'YYYY-MM-DD' ISO string to a date object."""
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def init_db():
    """Initializes the database and ensures the schema is up-to-date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create daily_ohlcv table with TEXT date if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_ohlcv (
        date_str TEXT PRIMARY KEY,  -- 'YYYY-MM-DD' string, representing 00:00:00 UTC
        open REAL, high REAL, low REAL, close REAL, volume REAL,
        source TEXT, fetched_at INTEGER
    )
    ''')

    # Create calculated_indicators table with TEXT date if it doesn't exist
    # And ensure 'calculated_at' column is present if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calculated_indicators';")
    table_exists = cursor.fetchone()

    if not table_exists:
        cursor.execute('''
        CREATE TABLE calculated_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date_str TEXT UNIQUE, price_at_event REAL,
            rsi_monthly REAL, rsi_weekly REAL, stoch_rsi_monthly REAL, stoch_rsi_weekly REAL,
            mfi_monthly REAL, mfi_weekly REAL, crsi_monthly REAL, crsi_weekly REAL,
            williams_r_monthly REAL, williams_r_weekly REAL, rvi_monthly REAL, rvi_weekly REAL,
            adaptive_rsi_monthly REAL, adaptive_rsi_weekly REAL,
            cos_monthly REAL, cos_weekly REAL, bsi_monthly REAL, bsi_weekly REAL,
            outcome_1m_direction TEXT, outcome_1m_percentage REAL, outcome_1m_price REAL,
            outcome_6m_direction TEXT, outcome_6m_percentage REAL, outcome_6m_price REAL,
            outcome_12m_direction TEXT, outcome_12m_percentage REAL, outcome_12m_price REAL,
            calculated_at INTEGER
        )
        ''')
        logger.info("Table 'calculated_indicators' created with 'date_str' (TEXT) and 'calculated_at' column.")
    else:
        # Check for 'calculated_at' column and add if missing
        cursor.execute("PRAGMA table_info(calculated_indicators);")
        columns = [info[1] for info in cursor.fetchall()]
        if 'calculated_at' not in columns:
            logger.info("Adding 'calculated_at' column to 'calculated_indicators' table.")
            cursor.execute("ALTER TABLE calculated_indicators ADD COLUMN calculated_at INTEGER;")
        else:
            logger.info("'calculated_at' column already exists in 'calculated_indicators' table.")
        
        # Check if timestamp column needs to be date_str (this simple check won't migrate data, assumes fresh start after manual delete if type was wrong)
        if 'timestamp' in columns and 'date_str' not in columns:
             logger.warning("Old 'timestamp' column found and 'date_str' missing. Manual DB deletion and re-creation is recommended for schema update to TEXT dates.")
        elif 'date_str' not in columns: # If neither exists, something is very wrong.
             logger.error("Critical schema error: 'date_str' column is missing and 'timestamp' integer column not found either in calculated_indicators. Manual DB intervention required.")


    conn.commit()
    conn.close()
    logger.info(f"Database {DB_PATH} initialized/verified.")

# --- store_daily_ohlcv_data ---
def store_daily_ohlcv_data(date_obj_utc: datetime, data_values: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure we are using just the date part, normalized to a string
    date_key_str = date_to_iso_string(date_obj_utc.date()) 
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO daily_ohlcv
        (date_str, open, high, low, close, volume, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date_key_str, data_values['open'], data_values['high'],
            data_values['low'], data_values['close'], data_values['volume'],
            data_values['source'], int(time.time())
        ))
        conn.commit()
        logger.info(f"Stored/Replaced daily_ohlcv for date {date_key_str} from {data_values['source']}")
    except Exception as e:
        logger.error(f"Error storing daily_ohlcv for date {date_key_str}: {e}")
    finally:
        conn.close()

# --- get_daily_ohlcv_from_db ---
def get_daily_ohlcv_from_db(date_obj_utc: datetime):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    date_key_str = date_to_iso_string(date_obj_utc.date())
    cursor.execute("SELECT * FROM daily_ohlcv WHERE date_str = ?", (date_key_str,))
    row = cursor.fetchone()
    conn.close()
    if row:
        logger.debug(f"DB GET: Found daily_ohlcv for {date_key_str}.")
        return dict(row)
    logger.debug(f"DB GET: No daily_ohlcv for {date_key_str}.")
    return None

# --- store_full_indicator_set ---
def store_full_indicator_set(date_obj_utc: datetime, price_at_event, indicators_m, indicators_w, composite_metrics, outcomes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date_key_str = date_to_iso_string(date_obj_utc.date())
    current_calc_time = int(time.time())
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO calculated_indicators (
                date_str, price_at_event,
                rsi_monthly, rsi_weekly, stoch_rsi_monthly, stoch_rsi_weekly,
                mfi_monthly, mfi_weekly, crsi_monthly, crsi_weekly,
                williams_r_monthly, williams_r_weekly, rvi_monthly, rvi_weekly,
                adaptive_rsi_monthly, adaptive_rsi_weekly,
                cos_monthly, cos_weekly, bsi_monthly, bsi_weekly,
                outcome_1m_direction, outcome_1m_percentage, outcome_1m_price,
                outcome_6m_direction, outcome_6m_percentage, outcome_6m_price,
                outcome_12m_direction, outcome_12m_percentage, outcome_12m_price,
                calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date_key_str, price_at_event,
            indicators_m.get('rsi'), indicators_w.get('rsi'), indicators_m.get('stochRsi'), indicators_w.get('stochRsi'),
            indicators_m.get('mfi'), indicators_w.get('mfi'), indicators_m.get('crsi'), indicators_w.get('crsi'),
            indicators_m.get('williamsR'), indicators_w.get('williamsR'), indicators_m.get('rvi'), indicators_w.get('rvi'),
            indicators_m.get('adaptiveRsi'), indicators_w.get('adaptiveRsi'),
            composite_metrics['cos']['monthly'], composite_metrics['cos']['weekly'],
            composite_metrics['bsi']['monthly'], composite_metrics['bsi']['weekly'],
            outcomes['1M']['direction'], outcomes['1M']['percentage'], outcomes['1M']['price'],
            outcomes['6M']['direction'], outcomes['6M']['percentage'], outcomes['6M']['price'],
            outcomes['12M']['direction'], outcomes['12M']['percentage'], outcomes['12M']['price'],
            current_calc_time
        ))
        conn.commit()
        logger.info(f"Stored/Replaced calculated_indicators for date {date_key_str}")
    except Exception as e:
        logger.error(f"Error storing calculated_indicators for date {date_key_str}: {e}")
    finally:
        conn.close()

# --- get_full_indicator_set_from_db ---
def get_full_indicator_set_from_db(date_obj_utc: datetime):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    date_key_str = date_to_iso_string(date_obj_utc.date())
    cursor.execute("SELECT * FROM calculated_indicators WHERE date_str = ?", (date_key_str,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None