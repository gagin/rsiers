#!/bin/bash

# This script just starts the frontend server
echo "Starting the frontend server..."
python -m http.server 8000

echo "Frontend server is running at http://localhost:8000"
echo "Press Ctrl+C to stop the server."
