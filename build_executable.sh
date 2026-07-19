#!/bin/bash

# Build script for AB Seeds Inventory Desktop Application
# This script creates a standalone executable using PyInstaller

set -e

echo "=== Building AB Seeds Inventory Desktop Application ==="

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller --break-system-packages
fi

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf dist/ build/

# Build the executable
echo "Building executable..."
python3 -m PyInstaller \
    --name "ABSeedsInventory" \
    --windowed \
    --icon=app/static/images/icon.png \
    --add-data "app/templates:app/templates" \
    --add-data "app/static:app/static" \
    --hidden-import "flaskwebgui" \
    --hidden-import "waitress" \
    run_desktop.py

echo "Build complete!"
echo "Executable located in: dist/ABSeedsInventory"
echo "You can run it with: ./dist/ABSeedsInventory/ABSeedsInventory"

# Note about requirements
echo ""
echo "NOTE: For full functionality, ensure all dependencies are installed:"
echo "- Flask>=3.0"
echo "- bcrypt>=4.0"
echo "- python-dotenv>=1.0"
echo "- pytest>=8.0"
echo "- flaskwebgui>=1.0.0"
echo "- waitress>=3.0.0"
echo "- pyturso>=0.7.0"
