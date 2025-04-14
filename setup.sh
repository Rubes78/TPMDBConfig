#!/bin/bash

echo "Installing TPM Python environment..."

cd "$(dirname "$0")" || exit

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing required Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo "To run your import:"
echo "    source venv/bin/activate"
echo "    python import.py"
echo ""
