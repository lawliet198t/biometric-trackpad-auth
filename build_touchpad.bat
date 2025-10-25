@echo off
echo Building Windows Touchpad Capture...
echo.

REM Step 1: Clone and build RawInput.Touchpad if needed
if not exist "RawInput.Touchpad" (
    echo Cloning RawInput.Touchpad...
    git clone --depth 1 https://github.com/emoacht/RawInput.Touchpad.git
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to clone repository
        exit /b 1
    )
)

echo.
echo Building RawInput.Touchpad library...
cd RawInput.Touchpad\Source
dotnet build -c Release
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build RawInput.Touchpad
    cd ..\..
    exit /b 1
)
cd ..\..

REM Copy the DLL to our project
echo.
echo Copying DLL...
copy "RawInput.Touchpad\Source\RawInput.Touchpad\bin\Release\net5.0-windows\RawInput.Touchpad.dll" "." /Y

REM Step 2: Build our console app
echo.
echo Building TouchpadCapture console app...
cd TouchpadCapture
dotnet build -c Release
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build TouchpadCapture
    cd ..
    exit /b 1
)
cd ..

REM Copy the EXE and all dependencies
echo.
echo Copying EXE and dependencies...
copy "TouchpadCapture\bin\Release\net5.0-windows\TouchpadCapture.exe" "." /Y
copy "TouchpadCapture\bin\Release\net5.0-windows\*.dll" "." /Y
copy "TouchpadCapture\bin\Release\net5.0-windows\*.json" "." /Y 2>nul

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Files created:
echo   - TouchpadCapture.exe
echo   - RawInput.Touchpad.dll
echo.
echo Test it: TouchpadCapture.exe
echo.
