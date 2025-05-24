# backend/main.py
import sys
import os
import logging
import json
from datetime import datetime, timezone

# Adjust Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(current_dir)
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from flask import Flask, jsonify, request
from flask_cors import CORS

# Imports from our backend modules
from backend.db_utils import (
    init_db, DB_PATH 
)
from backend.services.indicator_service import get_indicator_data
from backend.services.composite_metrics_service import calculate_composite_metrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- API Endpoints ---
@app.route('/api/indicators', methods=['GET'])
def get_indicators_api():
    date_param = request.args.get('date')
    target_date_obj_utc = None

    if date_param:
        try:
            if 'T' in date_param:
                 target_date_obj_utc = datetime.fromisoformat(date_param.replace('Z', '+00:00')).astimezone(timezone.utc)
            else:
                 target_date_obj_utc = datetime.strptime(date_param, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            target_date_obj_utc = target_date_obj_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            logger.error(f"API: Invalid date format received: {date_param}")
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD or full ISO.'}), 400
    else:
        target_date_obj_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    service_response_dict = get_indicator_data(target_date_obj_utc)
    status_code = service_response_dict.pop('http_status_code', 200)
    return jsonify(service_response_dict), status_code


@app.route('/api/historical_time_points', methods=['GET'])
def get_historical_time_points_api():
    historical_data_path = os.path.join(project_root_dir, 'historical_data.json')
    
    if not os.path.exists(historical_data_path):
        logger.error(f"API: Historical data file not found at {historical_data_path}")
        return jsonify({'error': 'Historical data file not found.'}), 404
    
    try:
        with open(historical_data_path, 'r') as f:
            data = json.load(f) 

        time_points = data.get("timePoints", [])
        for point in time_points:
            if "indicators" in point and isinstance(point["indicators"], dict):
                # Always recalculate composite metrics if indicators are present
                # This ensures 'bsi' is used and values are consistent with current logic.
                point["compositeMetrics"] = calculate_composite_metrics(point["indicators"])
            elif not isinstance(point.get("compositeMetrics"), dict) or \
                 not ("cos" in point.get("compositeMetrics") and "bsi" in point.get("compositeMetrics")):
                # If indicators are missing, or compositeMetrics are malformed/missing,
                # default to a standard empty structure for compositeMetrics.
                logger.warning(f"Historical point {point.get('name', point.get('date'))} lacked valid indicators or compositeMetrics; defaulting compositeMetrics.")
                point["compositeMetrics"] = {'cos': {'monthly':0,'weekly':0}, 'bsi': {'monthly':0,'weekly':0}}
            
            # Remove any legacy 'tsi' key explicitly, if it somehow still exists after above processing
            if "compositeMetrics" in point and "tsi" in point["compositeMetrics"]:
                del point["compositeMetrics"]["tsi"]
                logger.debug(f"Removed legacy 'tsi' key from historical point: {point.get('name', point.get('date'))}")

        data["timePoints"] = time_points
        return jsonify(data)
    
    except FileNotFoundError:
        logger.error(f"API: Historical data file not found during open: {historical_data_path}")
        return jsonify({'error': 'Historical data file could not be opened.'}), 404
    except json.JSONDecodeError:
        logger.error(f"API: Error decoding JSON from historical_data.json: {historical_data_path}")
        return jsonify({'error': 'Historical data file is not valid JSON.'}), 500
    except Exception as e:
        logger.error(f"API: Error reading/processing historical_data.json: {e}", exc_info=True)
        return jsonify({'error': 'Could not load historical time points due to an internal error.'}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data_api():
    logger.info("API: Manual refresh endpoint called. Data for 'today' will be re-evaluated on next GET /api/indicators if cache is stale.")
    return jsonify({'status': 'success', 'message': 'Refresh signal received. Data is fetched on demand by /api/indicators.'})

if __name__ == '__main__':
    logger.info(f"MAIN_APP: Attempting to initialize DB. Using DB_PATH defined in db_utils: {os.path.abspath(DB_PATH)}")
    init_db() 
    
    logger.info(f"MAIN_APP: Starting Flask app. Script: {__file__}, CWD: {os.getcwd()}")
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)