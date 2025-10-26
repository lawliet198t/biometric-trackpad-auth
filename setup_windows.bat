@echo off
REM ============================================================================
REM Windows Touchpad Biometric Authentication - Complete Setup
REM ============================================================================
REM This script will:
REM   1. Check for .NET SDK
REM   2. Create Python virtual environment
REM   3. Install Python dependencies
REM   4. Build the TouchpadCapture.exe
REM ============================================================================

echo.
echo ============================================================================
echo Windows Touchpad Biometric Authentication - Setup
echo ============================================================================
echo.

REM ============================================================================
REM Step 1: Check .NET SDK
REM ============================================================================
echo [1/5] Checking .NET SDK...
where dotnet >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] .NET SDK not found!
    echo.
    echo Please install .NET SDK 8.0 or later from:
    echo https://dotnet.microsoft.com/download
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

dotnet --version
echo [OK] .NET SDK found
echo.

REM ============================================================================
REM Step 2: Create Python Virtual Environment
REM ============================================================================
echo [2/5] Setting up Python virtual environment...

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Failed to create virtual environment
        echo Make sure Python 3.7+ is installed
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM ============================================================================
REM Step 3: Install Python Dependencies
REM ============================================================================
echo [3/5] Installing Python dependencies...
call venv\Scripts\activate.bat

pip install --upgrade pip >nul 2>nul
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM ============================================================================
REM Step 4: Build TouchpadCapture.exe
REM ============================================================================
echo [4/5] Building TouchpadCapture.exe...

cd TouchpadCapture
dotnet publish RawInputProgram.csproj -c Release -o bin >nul 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo [OK] TouchpadCapture.exe built successfully
echo.

REM ============================================================================
REM Setup Complete
REM ============================================================================
echo.
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Next steps:
echo.
echo   1. Train your biometric baseline:
echo      venv\Scripts\activate.bat
echo      python realtime_trainer.py
echo.
echo   2. Run biometric verification:
echo      venv\Scripts\activate.bat
echo      python realtime_verify.py --baseline baseline.pkl
echo.
echo   3. View raw touchpad data (optional):
echo      venv\Scripts\activate.bat
echo      python simple_windows_touchpad.py
echo.
echo ============================================================================
echo.
pause
