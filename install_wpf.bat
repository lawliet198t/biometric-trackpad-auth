@echo off
echo Installing .NET Desktop Runtime (includes WPF)...
echo.

winget install Microsoft.DotNet.DesktopRuntime.5 --silent --accept-source-agreements --accept-package-agreements

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ .NET Desktop Runtime installed successfully!
    echo.
    echo Now run: python test_windows_multitouch.py
) else (
    echo.
    echo ⚠️  Installation may have issues
    echo.
    echo Try manually:
    echo https://dotnet.microsoft.com/download/dotnet/5.0
    echo Download: .NET Desktop Runtime 5.0
)

pause
