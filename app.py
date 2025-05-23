import sys
import os
import logging
from datetime import datetime
import time
import threading
import sqlite3

# Set up error handling for imports
try:
    from flask import Flask, jsonify, request
except ImportError:
    print("Error: Flask is not installed. Please run 'pip install flask'")
    sys.exit(1)

try:
    from flask_cors import CORS
except ImportError:
    print("Error: Flask-CORS is not installed. Please run 'pip install flask-cors'")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: Requests is not installed. Please run 'pip install requests'")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Error: NumPy is not installed. Please run 'pip install numpy'")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("Error: Pandas is not installed. Please run 'pip install pandas'")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DB_PATH = 'bitcoin_indicators.db'

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create OHLC data tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_ohlc (
        timestamp INTEGER PRIMARY KEY,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        fetch_time INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weekly_ohlc (
        timestamp INTEGER PRIMARY KEY,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        fetch_time INTEGER
    )
    ''')

    # Create indicators table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        timeframe TEXT,
        rsi REAL,
        stoch_rsi REAL,
        mfi REAL,
        crsi REAL,
        williams_r REAL,
        rvi REAL,
        adaptive_rsi REAL,
        cos REAL,
        bsi REAL
    )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Kraken API functions
def fetch_kraken_ohlc(pair, interval):
    """Fetch OHLC data from Kraken API."""
    url = 'https://api.kraken.com/0/public/OHLC'
    params = {
        'pair': pair,
        'interval': interval
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'error' in data and data['error']:
            logger.error(f"Kraken API error: {data['error']}")
            return None

        if 'result' in data and pair in data['result']:
            return data['result'][pair]
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error fetching data from Kraken: {e}")
        return None

def store_ohlc_data(timeframe, data):
    """Store OHLC data in the database."""
    if not data:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    table_name = f"{timeframe}_ohlc"
    current_time = int(time.time())

    try:
        for entry in data:
            # Kraken OHLC format: [time, open, high, low, close, vwap, volume, count]
            cursor.execute(f'''
            INSERT OR REPLACE INTO {table_name}
            (timestamp, open, high, low, close, volume, fetch_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(entry[0]),
                float(entry[1]),
                float(entry[2]),
                float(entry[3]),
                float(entry[4]),
                float(entry[6]),
                current_time
            ))

        conn.commit()
        logger.info(f"Stored {len(data)} {timeframe} OHLC records")
        return True
    except Exception as e:
        logger.error(f"Error storing {timeframe} data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fetch_and_store_data():
    """Fetch data from Kraken and store it in the database."""
    pair = 'XXBTZUSD'
    monthly_interval = 43200  # 30 days in minutes
    weekly_interval = 10080   # 7 days in minutes

    # Fetch and store monthly data
    monthly_data = fetch_kraken_ohlc(pair, monthly_interval)
    monthly_success = store_ohlc_data('monthly', monthly_data)

    # Fetch and store weekly data
    weekly_data = fetch_kraken_ohlc(pair, weekly_interval)
    weekly_success = store_ohlc_data('weekly', weekly_data)

    if monthly_success and weekly_success:
        # Calculate and store indicators
        calculate_and_store_indicators()
        return True
    return False

# Technical indicator calculation functions
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index."""
    prices = np.array(prices)
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down if down != 0 else float('inf')
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up/down if down != 0 else float('inf')
        rsi[i] = 100. - 100./(1. + rs)

    return rsi[-1]

def calculate_stoch_rsi(prices, period=14, smooth_k=3, smooth_d=3):
    """Calculate Stochastic RSI."""
    # Calculate RSI
    prices = np.array(prices)
    rsi_values = []
    for i in range(len(prices) - period + 1):
        rsi_values.append(calculate_rsi(prices[i:i+period], period))

    rsi_values = np.array(rsi_values)

    # Calculate Stochastic RSI
    if len(rsi_values) < period:
        return 50  # Not enough data

    min_rsi = np.min(rsi_values[-period:])
    max_rsi = np.max(rsi_values[-period:])

    if max_rsi == min_rsi:
        return 50  # Avoid division by zero

    stoch = (rsi_values[-1] - min_rsi) / (max_rsi - min_rsi) * 100
    return stoch

def get_ohlc_data(timeframe):
    """Get OHLC data from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {timeframe}_ohlc ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    data = {
        'timestamps': [row['timestamp'] for row in rows],
        'opens': [row['open'] for row in rows],
        'highs': [row['high'] for row in rows],
        'lows': [row['low'] for row in rows],
        'closes': [row['close'] for row in rows],
        'volumes': [row['volume'] for row in rows]
    }

    return data

def calculate_and_store_indicators():
    """Calculate indicators and store them in the database."""
    # Get OHLC data
    monthly_data = get_ohlc_data('monthly')
    weekly_data = get_ohlc_data('weekly')

    if not monthly_data or not weekly_data:
        logger.error("Missing data for indicator calculation")
        return False

    # Calculate indicators (simplified for now)
    monthly_rsi = calculate_rsi(monthly_data['closes'])
    weekly_rsi = calculate_rsi(weekly_data['closes'])

    monthly_stoch_rsi = calculate_stoch_rsi(monthly_data['closes'])
    weekly_stoch_rsi = calculate_stoch_rsi(weekly_data['closes'])

    # Store in database (simplified)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current_time = int(time.time())

    # Store monthly indicators
    cursor.execute('''
    INSERT INTO indicators
    (timestamp, timeframe, rsi, stoch_rsi)
    VALUES (?, ?, ?, ?)
    ''', (current_time, 'monthly', monthly_rsi, monthly_stoch_rsi))

    # Store weekly indicators
    cursor.execute('''
    INSERT INTO indicators
    (timestamp, timeframe, rsi, stoch_rsi)
    VALUES (?, ?, ?, ?)
    ''', (current_time, 'weekly', weekly_rsi, weekly_stoch_rsi))

    conn.commit()
    conn.close()

    logger.info("Calculated and stored indicators")
    return True

# Background data refresh
def scheduled_data_refresh():
    """Periodically refresh data from Kraken."""
    while True:
        logger.info("Scheduled data refresh starting")
        fetch_and_store_data()
        logger.info("Scheduled data refresh completed")
        time.sleep(300)  # 5 minutes

# API routes
@app.route('/api/indicators', methods=['GET'])
def get_indicators():
    """Get the latest indicators."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the latest monthly indicators
    cursor.execute('''
    SELECT * FROM indicators
    WHERE timeframe = 'monthly'
    ORDER BY timestamp DESC
    LIMIT 1
    ''')
    monthly = cursor.fetchone()

    # Get the latest weekly indicators
    cursor.execute('''
    SELECT * FROM indicators
    WHERE timeframe = 'weekly'
    ORDER BY timestamp DESC
    LIMIT 1
    ''')
    weekly = cursor.fetchone()

    conn.close()

    if not monthly or not weekly:
        return jsonify({'error': 'No indicator data available'}), 404

    # Format the response
    result = {
        'lastUpdate': datetime.fromtimestamp(max(monthly['timestamp'], weekly['timestamp'])).isoformat(),
        'indicators': {
            'rsi': {
                'monthly': monthly['rsi'],
                'weekly': weekly['rsi']
            },
            'stochRsi': {
                'monthly': monthly['stoch_rsi'],
                'weekly': weekly['stoch_rsi']
            }
            # Add other indicators as they are implemented
        }
    }

    return jsonify(result)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually trigger a data refresh."""
    success = fetch_and_store_data()
    if success:
        return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to refresh data'}), 500

# Global variable to control the background thread
should_exit = False

# Modified background data refresh function with exit check
def scheduled_data_refresh():
    """Periodically refresh data from Kraken."""
    global should_exit
    while not should_exit:
        logger.info("Scheduled data refresh starting")
        fetch_and_store_data()
        logger.info("Scheduled data refresh completed")

        # Check for exit signal every second for 5 minutes
        for _ in range(300):  # 5 minutes = 300 seconds
            if should_exit:
                break
            time.sleep(1)

# Initialize and start the app
if __name__ == '__main__':
    import signal
    import sys

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        global should_exit
        logger.info("Shutting down gracefully...")
        should_exit = True
        # Give the background thread time to exit
        time.sleep(2)
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize the database
    init_db()

    # Start the background refresh thread
    refresh_thread = threading.Thread(target=scheduled_data_refresh)
    refresh_thread.daemon = True
    refresh_thread.start()

    logger.info("Starting Flask app on port 5001")
    logger.info("Press Ctrl+C to exit gracefully")

    # Start the Flask app with threaded=False to avoid multiprocessing issues
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)
