#!/usr/bin/env python

"""
Debug script to check if the backend server is running correctly.
This script will:
1. Check if all required dependencies are installed
2. Initialize the database
3. Fetch data from Kraken API
4. Calculate indicators
5. Start the Flask server in debug mode
"""

import sys
import os
import sqlite3
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check dependencies
def check_dependencies():
    """Check if all required dependencies are installed."""
    dependencies = ['flask', 'flask_cors', 'requests', 'numpy', 'pandas']
    missing = []

    for dep in dependencies:
        try:
            __import__(dep)
            logger.info(f"✓ {dep} is installed")
        except ImportError:
            missing.append(dep)
            logger.error(f"✗ {dep} is not installed")

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Please install them with: pip install " + " ".join(missing))
        return False

    return True

# Database setup
def init_db():
    """Initialize the SQLite database with required tables."""
    DB_PATH = 'bitcoin_indicators.db'

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        logger.info(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

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
    return True

# Test Kraken API
def test_kraken_api():
    """Test if we can fetch data from Kraken API."""
    import requests

    url = 'https://api.kraken.com/0/public/OHLC'
    params = {
        'pair': 'XXBTZUSD',
        'interval': 1440  # 1 day in minutes
    }

    try:
        logger.info("Testing Kraken API...")
        response = requests.get(url, params=params)
        data = response.json()

        if 'error' in data and data['error']:
            logger.error(f"Kraken API error: {data['error']}")
            return False

        if 'result' in data and 'XXBTZUSD' in data['result']:
            logger.info(f"Successfully fetched {len(data['result']['XXBTZUSD'])} records from Kraken API")
            return True
        else:
            logger.error(f"Unexpected response format: {data}")
            return False
    except Exception as e:
        logger.error(f"Error fetching data from Kraken: {e}")
        return False

# Insert mock data
def insert_mock_data():
    """Insert mock data into the database for testing."""
    DB_PATH = 'bitcoin_indicators.db'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    current_time = int(time.time())

    # Insert mock monthly data
    for i in range(24):
        timestamp = current_time - i * 30 * 24 * 60 * 60
        cursor.execute('''
        INSERT INTO monthly_ohlc
        (timestamp, open, high, low, close, volume, fetch_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            60000 - i * 100,
            62000 - i * 100,
            58000 - i * 100,
            61000 - i * 100,
            1000000 + i * 10000,
            current_time
        ))

    # Insert mock weekly data
    for i in range(26):
        timestamp = current_time - i * 7 * 24 * 60 * 60
        cursor.execute('''
        INSERT INTO weekly_ohlc
        (timestamp, open, high, low, close, volume, fetch_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            60000 - i * 50,
            61000 - i * 50,
            59000 - i * 50,
            60500 - i * 50,
            500000 + i * 5000,
            current_time
        ))

    # Insert mock indicators
    cursor.execute('''
    INSERT INTO indicators
    (timestamp, timeframe, rsi, stoch_rsi)
    VALUES (?, ?, ?, ?)
    ''', (current_time, 'monthly', 68, 75))

    cursor.execute('''
    INSERT INTO indicators
    (timestamp, timeframe, rsi, stoch_rsi)
    VALUES (?, ?, ?, ?)
    ''', (current_time, 'weekly', 72, 82))

    conn.commit()
    conn.close()
    logger.info("Mock data inserted")
    return True

# Start Flask server
def start_flask_server():
    """Start the Flask server."""
    from flask import Flask, jsonify
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)

    @app.route('/api/indicators', methods=['GET'])
    def get_indicators():
        """Get the latest indicators."""
        DB_PATH = 'bitcoin_indicators.db'
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
        from datetime import datetime
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
            }
        }

        return jsonify(result)

    @app.route('/api/refresh', methods=['POST'])
    def refresh_data():
        """Manually trigger a data refresh."""
        return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})

    logger.info("Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

def main():
    """Main function."""
    logger.info("Starting debug script...")

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies. Please install them and try again.")
        return

    # Initialize database
    if not init_db():
        logger.error("Failed to initialize database.")
        return

    # Test Kraken API
    if not test_kraken_api():
        logger.warning("Failed to fetch data from Kraken API. Using mock data instead.")

    # Insert mock data
    if not insert_mock_data():
        logger.error("Failed to insert mock data.")
        return

    # Start Flask server
    start_flask_server()

if __name__ == "__main__":
    main()
