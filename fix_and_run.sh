#!/bin/bash

# This script will:
# 1. Install dependencies directly
# 2. Create a simple Flask server with mock data
# 3. Start both the backend and frontend servers

# Install dependencies directly
echo "Installing dependencies directly..."
pip install flask flask-cors requests numpy pandas

# Check if installation was successful
python -c "import flask, flask_cors, requests, numpy, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Failed to install dependencies. Please install them manually:"
  echo "pip install flask flask-cors requests numpy pandas"
  exit 1
fi

echo "Dependencies installed successfully!"

# Create a simple Flask server file
echo "Creating a simple Flask server..."
cat > simple_server.py << 'EOF'
from flask import Flask, jsonify
from flask_cors import CORS
import time
from datetime import datetime

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
    # Use port 5001 instead of 5000 to avoid conflicts with AirPlay on macOS
    port = 5001
    print(f"Starting Flask server on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
EOF

# Start the backend server
echo "Starting the backend server..."
python simple_server.py &
BACKEND_PID=$!

# Wait for the backend to start
sleep 2

# Start the frontend server
echo "Starting the frontend server..."
python -m http.server 8000 &
FRONTEND_PID=$!

# Function to handle script termination
function cleanup {
  echo "Stopping servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

echo "Servers are running!"
echo "Backend: http://localhost:5001"
echo "Frontend: http://localhost:8000"
echo "Press Ctrl+C to stop both servers."

# Keep the script running
wait
