@echo off
echo Patching RawInput.Touchpad to add JSON output...
echo.

set SOURCE_FILE=RawInput.Touchpad\Source\RawInput.Touchpad\MainWindow.xaml.cs

if not exist "%SOURCE_FILE%" (
    echo Error: Source file not found: %SOURCE_FILE%
    echo Run build_touchpad.bat first to clone the repository.
    pause
    exit /b 1
)

echo Found source file: %SOURCE_FILE%
echo.
echo Creating backup...
copy "%SOURCE_FILE%" "%SOURCE_FILE%.backup"

echo.
echo Instructions:
echo.
echo 1. Open the file in an editor:
echo    %SOURCE_FILE%
echo.
echo 2. Find the method that processes contacts (likely in WndProc or similar)
echo.
echo 3. Add this code where contacts are received:
echo.
echo    // JSON output for Python
echo    var json = System.Text.Json.JsonSerializer.Serialize(new {
echo        Type = "contacts",
echo        Contacts = contacts.Select(c =^> new {
echo            ContactId = c.ContactId,
echo            X = c.X,
echo            Y = c.Y,
echo            Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
echo        })
echo    });
echo    Console.WriteLine(json);
echo    Console.Out.Flush();
echo.
echo 4. Save and rebuild:
echo    cd RawInput.Touchpad\Source
echo    dotnet build -c Release
echo.
echo 5. Copy the new DLL:
echo    copy RawInput.Touchpad\Source\RawInput.Touchpad\bin\Release\net5.0-windows\RawInput.Touchpad.dll .
echo.

pause

echo.
echo Opening file in notepad...
notepad "%SOURCE_FILE%"
