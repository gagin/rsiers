#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install required dependencies
echo "Installing required dependencies..."
pip install flask flask-cors requests pandas

# Verify all dependencies are installed
echo "Verifying dependencies..."
python -c "import numpy, pandas, flask, flask_cors, requests; print('All dependencies are installed')"
if [ $? -ne 0 ]; then
  echo "Some dependencies are missing. Please install them manually."
  exit 1
fi

# Start the backend server
echo "Starting the backend server..."
python app.py &
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
  deactivate
  exit
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

echo "Servers are running!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:8000"
echo "Press Ctrl+C to stop both servers."

# Keep the script running
wait
