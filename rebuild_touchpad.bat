@echo off
REM ============================================================================
REM Rebuild TouchpadCapture.exe with Multi-Finger Fixes
REM ============================================================================

echo.
echo ============================================================================
echo Rebuilding TouchpadCapture.exe
echo ============================================================================
echo.
echo This will rebuild the C# touchpad capture program with:
echo   - Improved multi-finger tracking
echo   - No throttling for maximum accuracy
echo   - Better contact detection
echo.

REM Check if dotnet is installed
where dotnet >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: .NET SDK not found!
    echo Please install .NET SDK 8.0 or later from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

REM Build the Raw Input program
cd TouchpadCapture
echo Building RawInputProgram.csproj...
dotnet publish RawInputProgram.csproj -c Release -o bin

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! TouchpadCapture.exe rebuilt
    echo ========================================
    echo.
    echo The updated exe is in: TouchpadCapture\bin\
    echo.
    echo Changes in this build:
    echo   ✓ Removed JSON output throttling
    echo   ✓ Immediate multi-finger data output
    echo   ✓ Better contact tracking
    echo   ✓ Improved coordinate normalization
    echo.
    echo You can now run:
    echo   python realtime_trainer.py
    echo   python realtime_verify.py --baseline baseline.pkl
    echo.
    echo Multi-finger gestures should now work smoothly!
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    echo.
)

cd ..
pause
