@echo off
echo Verifying project setup...
echo.

echo Checking files...
if exist "TouchpadCapture\RawInputProgram.cs" (
    echo [OK] RawInputProgram.cs found
) else (
    echo [ERROR] RawInputProgram.cs not found
    exit /b 1
)

if exist "TouchpadCapture\RawInputProgram.csproj" (
    echo [OK] RawInputProgram.csproj found
) else (
    echo [ERROR] RawInputProgram.csproj not found
    exit /b 1
)

if exist "simple_windows_touchpad.py" (
    echo [OK] simple_windows_touchpad.py found
) else (
    echo [ERROR] simple_windows_touchpad.py not found
    exit /b 1
)

echo.
echo Checking .NET SDK...
where dotnet >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] .NET SDK found
    dotnet --version
) else (
    echo [ERROR] .NET SDK not found
    echo Please install from: https://dotnet.microsoft.com/download
    exit /b 1
)

echo.
echo ========================================
echo All checks passed!
echo ========================================
echo.
echo Ready to build. Run: build_rawinput.bat
echo.
pause
