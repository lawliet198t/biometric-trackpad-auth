@echo off
echo Building Raw Input Touchpad Capture...
echo.

REM Check if dotnet is installed
where dotnet >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: .NET SDK not found!
    echo Please install .NET 5.0 or later from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

REM Build the Raw Input program
cd TouchpadCapture
echo Building RawInputProgram.csproj...
dotnet build RawInputProgram.csproj -c Release -o bin

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Copying to root directory...
    cd ..
    copy "TouchpadCapture\bin\TouchpadCapture.exe" "." /Y 2>nul
    if not exist "TouchpadCapture.exe" (
        copy "TouchpadCapture\bin\RawInputProgram.exe" "TouchpadCapture.exe" /Y
    )
    copy "TouchpadCapture\bin\*.dll" "." /Y 2>nul
    
    echo.
    echo ========================================
    echo SUCCESS! TouchpadCapture.exe built
    echo ========================================
    echo.
    echo This uses the REAL Raw Input API!
    echo.
    echo Next steps:
    echo   1. Run: python simple_windows_touchpad.py
    echo   2. Touch your touchpad to see RAW values
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    echo.
    cd ..
)

pause
