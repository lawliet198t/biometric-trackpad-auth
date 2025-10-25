@echo off
echo Checking installed .NET runtimes...
echo.

dotnet --list-runtimes

echo.
echo ============================================================
echo.

dotnet --list-sdks

echo.
echo ============================================================
echo.
echo If you see "Microsoft.WindowsDesktop.App" in the list above,
echo WPF is installed.
echo.
echo If not, close this terminal and open a NEW one, then run:
echo   python check_wpf.py
echo.

pause
