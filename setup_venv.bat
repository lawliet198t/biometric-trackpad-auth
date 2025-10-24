@echo off
REM Setup virtual environment for trackpad biometric authentication (Windows)

echo Setting up virtual environment for Windows...
echo.

REM Create venv if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To use the trackpad detection:
echo   venv\Scripts\activate.bat
echo   python detect_trackpad.py
echo.
echo To run the biometric verifier:
echo   venv\Scripts\activate.bat
echo   python realtime_trainer.py --samples 10
echo.
pause
