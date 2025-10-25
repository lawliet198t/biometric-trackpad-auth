@echo off
echo Checking .NET Installation...
echo.

echo ========================================
echo .NET SDK (for building)
echo ========================================
dotnet --version
if %ERRORLEVEL% EQU 0 (
    echo [OK] .NET SDK is installed
) else (
    echo [ERROR] .NET SDK not found
)

echo.
echo ========================================
echo .NET Runtimes (for running apps)
echo ========================================
dotnet --list-runtimes
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Checking for Desktop Runtime...
    dotnet --list-runtimes | findstr "WindowsDesktop" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] .NET Desktop Runtime is installed
    ) else (
        echo [ERROR] .NET Desktop Runtime NOT found
        echo.
        echo You need to install .NET Desktop Runtime!
        echo Download from: https://dotnet.microsoft.com/download/dotnet/8.0
        echo Look for ".NET Desktop Runtime 8.0.x"
    )
) else (
    echo [ERROR] Cannot check runtimes
)

echo.
echo ========================================
echo Summary
echo ========================================
dotnet --list-runtimes | findstr "WindowsDesktop" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ready to run TouchpadCapture.exe
    echo.
    echo Next step: python simple_windows_touchpad.py
) else (
    echo [ACTION NEEDED] Install .NET Desktop Runtime
    echo.
    echo Option 1: Install Runtime (Recommended)
    echo   Download: https://dotnet.microsoft.com/download/dotnet/8.0
    echo   Look for: .NET Desktop Runtime 8.0.x
    echo.
    echo Option 2: Rebuild as self-contained
    echo   Run: rebuild.bat
)

echo.
pause
