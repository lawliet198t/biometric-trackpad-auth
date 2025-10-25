# Simple Windows Touchpad - Direct Raw Values

This is a simplified approach that directly reads raw touchpad contact data without complex abstractions.

## How It Works

1. **C# Program** (`SimpleProgram.cs`): Uses WPF Touch events to capture raw X, Y, ContactId
2. **Python Reader** (`simple_windows_touchpad.py`): Reads JSON output from C# subprocess

## Raw Data Format

The C# program outputs JSON with raw touchpad values:

```json
{
  "Type": "contacts",
  "Contacts": [
    {
      "ContactId": 0,
      "X": 245.5,
      "Y": 312.8,
      "Timestamp": 1698765432100
    }
  ]
}
```

## Quick Start

### 1. Build the C# Program

```bash
# Windows
build_touchpad.bat
```

This creates `TouchpadCapture.exe`

### 2. Run the Python Reader

```bash
python simple_windows_touchpad.py
```

### 3. Touch Your Touchpad

Raw values will be printed:

```
[14:23:45] 2 contact(s):
  Contact 0: X=245.5, Y=312.8
  Contact 1: X=567.2, Y=423.1
```

## Use in Your Program

```python
from simple_windows_touchpad import SimpleTouchpadReader

# Create reader
reader = SimpleTouchpadReader()
reader.start()

# Read contacts
while True:
    contacts = reader.read_contacts()
    
    if contacts:
        for contact in contacts:
            contact_id = contact['ContactId']
            x = contact['X']
            y = contact['Y']
            
            # Use raw values directly
            print(f"Finger {contact_id}: ({x}, {y})")
    
    time.sleep(0.016)  # 60 FPS

reader.stop()
```

## Advantages

- **Simple**: No complex abstractions or reflection
- **Direct**: Raw X, Y values straight from Windows Touch API
- **Fast**: Minimal processing overhead
- **Reliable**: Uses standard WPF Touch events

## Raw Values

- **X, Y**: Pixel coordinates relative to window (0-800, 0-600 by default)
- **ContactId**: Unique ID for each finger (0, 1, 2, ...)
- **Timestamp**: Unix timestamp in milliseconds

## Integration

To use these raw values in your biometric system:

1. Read contacts with `reader.read_contacts()`
2. Extract X, Y, ContactId from each contact
3. Normalize coordinates if needed
4. Feed directly into your feature extraction

No need for complex gesture tracking or visualization unless you want it!
