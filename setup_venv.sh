#!/bin/bash
# Setup virtual environment for trackpad biometric authentication

echo "🔧 Setting up virtual environment..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "To use the trackpad detection:"
echo "  source venv/bin/activate"
echo "  python3 detect_trackpad.py"
echo ""
echo "To run the biometric verifier:"
echo "  source venv/bin/activate"
echo "  python3 realtime_trainer.py --samples 10"
