@echo off
echo Rebuilding with self-contained runtime...
echo.

REM Clean old build
if exist "TouchpadCapture\bin" (
    echo Cleaning old build...
    rmdir /s /q "TouchpadCapture\bin"
)

if exist "TouchpadCapture.exe" (
    del /q "TouchpadCapture.exe"
)

REM Build new version
call build_rawinput.bat
