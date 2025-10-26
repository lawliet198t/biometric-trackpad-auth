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

REM Build the Raw Input program (self-contained)
cd TouchpadCapture
echo Building RawInputProgram.csproj (self-contained)...
dotnet publish RawInputProgram.csproj -c Release -o bin

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Copying to root directory...
    cd ..
    
    REM Copy EXE
    copy "TouchpadCapture\bin\TouchpadCapture.exe" "." /Y 2>nul
    if not exist "TouchpadCapture.exe" (
        copy "TouchpadCapture\bin\RawInputProgram.exe" "TouchpadCapture.exe" /Y
    )
    
    REM Copy ALL dependencies
    echo Copying dependencies...
    copy "TouchpadCapture\bin\*.dll" "." /Y 2>nul
    copy "TouchpadCapture\bin\*.json" "." /Y 2>nul
    
    REM Copy runtime folder if it exists (for self-contained)
    if exist "TouchpadCapture\bin\runtimes" (
        echo Copying runtime files...
        xcopy "TouchpadCapture\bin\runtimes" "runtimes\" /E /I /Y /Q >nul 2>nul
    )
    
    echo.
    echo ========================================
    echo SUCCESS! TouchpadCapture.exe built
    echo ========================================
    echo.
    echo Files in root directory:
    dir TouchpadCapture.exe 2>nul
    echo.
    echo Next steps:
    echo   1. Run: python simple_windows_touchpad.py
    echo   2. Touch your touchpad to see RAW values
    echo.
    echo NOTE: Use TouchpadCapture\bin\TouchpadCapture.exe
    echo       if the root copy doesn't work
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
