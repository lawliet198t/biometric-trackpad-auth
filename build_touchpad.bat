@echo off
echo Building Simple TouchpadCapture.exe...
echo.

REM Check if dotnet is installed
where dotnet >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: .NET SDK not found!
    echo Please install .NET 5.0 or later from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

REM Build the simple program directly
cd TouchpadCapture
echo Building SimpleProgram.cs...
dotnet build SimpleProgram.cs -o bin

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Copying to root directory...
    cd ..
    copy "TouchpadCapture\bin\TouchpadCapture.exe" "." /Y
    copy "TouchpadCapture\bin\*.dll" "." /Y 2>nul
    
    echo.
    echo ========================================
    echo SUCCESS! TouchpadCapture.exe built
    echo ========================================
    echo.
    echo Next steps:
    echo   1. Run: python simple_windows_touchpad.py
    echo   2. Touch your touchpad to see raw values
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
