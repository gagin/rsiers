#!/bin/bash

# This is a simplified start script that will:
# 1. Install required dependencies
# 2. Start the debug backend server
# 3. Start the frontend server

# Install dependencies
echo "Installing required dependencies..."
pip install flask flask-cors requests numpy pandas

# Start the debug backend server
echo "Starting the debug backend server..."
python debug_backend.py &
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
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:8000"
echo "Press Ctrl+C to stop both servers."

# Keep the script running
wait
