#!/bin/bash

# This script creates a simple Flask server if it doesn't exist

if [ ! -f simple_server.py ]; then
  echo "Creating simple_server.py..."
  cat > simple_server.py << 'EOF'
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
from datetime import datetime
import argparse
import signal
import sys

# Parse command line arguments
parser = argparse.ArgumentParser(description='Start the Flask server')
parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
args = parser.parse_args()

app = Flask(__name__)
CORS(app)

# Mock data
mock_data = {
    'lastUpdate': datetime.now().isoformat(),
    'indicators': {
        'rsi': {
            'monthly': 68,
            'weekly': 72
        },
        'stochRsi': {
            'monthly': 75,
            'weekly': 82
        },
        'mfi': {
            'monthly': 65,
            'weekly': 78
        },
        'crsi': {
            'monthly': 82,
            'weekly': 88
        },
        'williamsR': {
            'monthly': -25,
            'weekly': -18
        },
        'rvi': {
            'monthly': 0.65,
            'weekly': 0.72
        },
        'adaptiveRsi': {
            'monthly': 70,
            'weekly': 75
        }
    }
}

@app.route('/api/indicators', methods=['GET'])
def get_indicators():
    return jsonify(mock_data)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    mock_data['lastUpdate'] = datetime.now().isoformat()
    return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})

if __name__ == '__main__':
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        # Clean up any resources here
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Starting Flask server on http://localhost:{args.port}")
    print("Press Ctrl+C to exit gracefully")
    
    # Use threaded=False to avoid some multiprocessing issues
    app.run(debug=True, host='0.0.0.0', port=args.port, threaded=False)
EOF
  echo "simple_server.py created successfully!"
fi
