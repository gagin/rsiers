@echo off
setlocal

REM Run the setup script to ensure dependencies are installed
echo Setting up environment...
python setup.py

REM Activate virtual environment
call venv\Scripts\activate

REM Verify numpy is installed
echo Verifying numpy installation...
python -c "import numpy; print('NumPy version:', numpy.__version__)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo NumPy is not installed correctly. Installing manually...
    pip install numpy

    REM Verify again
    python -c "import numpy; print('NumPy version:', numpy.__version__)" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install NumPy. Please install it manually and try again.
        exit /b 1
    )
)

REM Start the backend server
echo Starting the backend server...
start /B cmd /c "python app.py"

REM Wait for the backend to start
timeout /t 2 /nobreak > nul

REM Start the frontend server
echo Starting the frontend server...
start /B cmd /c "python -m http.server 8000"

echo Servers are running!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:8000
echo Press Ctrl+C to stop the servers.
echo Close this window when you're done.

REM Keep the window open
pause > nul
