# Bitcoin Indicator Dashboard

A web application that displays various technical indicators for Bitcoin to help identify potential sell signals. The application fetches data from the Kraken API, calculates technical indicators, and displays them in a user-friendly dashboard.

## Features

- Fetches real-time Bitcoin price data from the Kraken API
- Calculates and displays key technical indicators:
  - Relative Strength Index (RSI)
  - Stochastic RSI
  - Money Flow Index (MFI)
  - Connors RSI
  - Williams %R
  - Relative Vigor Index (RVI)
  - Adaptive RSI
- Shows both monthly and weekly values for all indicators
- Provides composite metrics:
  - Composite Overbought Score (COS)
  - Trend Strength Index (TSI)
- Stores historical data in SQLite database
- Automatically refreshes data every 5 minutes
- Fallback to mock data when backend is unavailable
- Clear visual indicator showing data source (Live Kraken Data or Mock Data)

## Architecture

The application consists of two main components:

1. **Backend (Python/Flask)**
   - Fetches data from Kraken API
   - Stores data in SQLite database
   - Calculates technical indicators
   - Provides API endpoints for the frontend

2. **Frontend (HTML/JavaScript/React)**
   - Displays the dashboard UI
   - Fetches data from the backend API
   - Visualizes indicators and metrics

## Setup and Installation

### Prerequisites

- Python 3.7+ (Python 3.12 recommended)
- Node.js (optional, for development)

### Option 1: Frontend Only with Mock Data (Simplest)

This option runs only the frontend with mock data, requiring no backend setup:

```bash
./start_frontend.sh
```

Then access the application at http://localhost:8000. The application will display mock data with an indicator showing "Mock Data" in the footer.

### Option 2: Full Application with Backend

This option runs both the backend and frontend servers:

```bash
./fix_and_run.sh
```

The script will:
1. Install all required dependencies
2. Start a simple Flask backend server on port 5001 (avoiding conflicts with AirPlay on macOS)
3. Start the frontend server on port 8000

Then access the application at http://localhost:8000. If the backend is working correctly, you'll see "Live Kraken Data" in the footer.

### Option 3: Manual Setup

#### 1. Create and activate a virtual environment:

##### On macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

##### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### 2. Install the required Python packages:
```bash
pip install flask flask-cors requests numpy pandas
```

#### 3. Start the backend server:
```bash
python simple_server.py
```

The server will run on http://localhost:5001

#### 4. In a separate terminal, start the frontend server:
```bash
python -m http.server 8000
```

Then access the application at http://localhost:8000

## API Endpoints

- `GET /api/indicators` - Get the latest calculated indicators
- `POST /api/refresh` - Manually trigger a data refresh

## Data Storage

The application uses SQLite for data storage with the following tables:

- `monthly_ohlc` - Monthly OHLC data
- `weekly_ohlc` - Weekly OHLC data
- `indicators` - Calculated indicators

## Troubleshooting

### "No module named 'numpy'" or Other Package Errors

If you encounter dependency errors, try the following solutions:

1. **Run the direct installation script**:
   ```bash
   python install_dependencies.py
   ```
   This script will install all dependencies directly, bypassing pip's dependency resolution.

2. **Manual installation**:
   ```bash
   pip install wheel
   pip install numpy
   pip install pandas
   pip install flask
   pip install flask-cors
   pip install requests
   ```

3. **Python Version Compatibility**:
   - The application has been updated to work with Python 3.12
   - If you're using an older Python version (3.7-3.11), the application should still work
   - If you encounter issues with specific package versions, try installing without version constraints

### "Address already in use" Error on Port 5000 (macOS)

On macOS, port 5000 is often used by the AirPlay Receiver service, which can cause conflicts when trying to run the Flask server.

1. **Solution 1**: Use the updated scripts
   - The `fix_and_run.sh` script and `simple_server.py` have been updated to use port 5001 instead of 5000

2. **Solution 2**: Disable AirPlay Receiver
   - Go to System Preferences → General → AirDrop & Handoff
   - Disable the 'AirPlay Receiver' service

3. **Solution 3**: Manually specify a different port
   - When running the Flask server manually, specify a different port:
   ```bash
   python app.py --port 5001
   ```

### "Mock Data" Indicator

If you see "Mock Data" in the footer of the application, it means:
1. The backend server is not running, or
2. The backend server is not accessible from the frontend

To fix this:
1. Make sure the backend server is running on port 5001
2. Check for any network or firewall issues
3. If you want to use real data, run the full application with `./fix_and_run.sh`

### System-specific issues

- **Windows**: Make sure you have the Microsoft Visual C++ Build Tools installed
- **macOS**: You might need to install Xcode Command Line Tools
- **Linux**: You might need to install python3-dev package

## Future Improvements

- Add more technical indicators
- Implement user authentication
- Add historical charts for each indicator
- Create alert system for overbought conditions
- Improve error handling and retry logic
- Add unit tests
- Add support for more cryptocurrencies
- Implement a more robust backend with scheduled data collection
- Add export functionality for indicator data
- Create mobile-responsive design for better mobile experience
- Implement WebSockets for real-time updates

## License

MIT
