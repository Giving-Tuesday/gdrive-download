#!/bin/bash
# Build script for GDrive Tools GUI application (macOS/Linux)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Building GDrive Tools GUI application..."
echo "Project directory: $PROJECT_DIR"

cd "$PROJECT_DIR"

# Ensure we're in a virtual environment or install deps
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not in a virtual environment. Consider activating one."
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e .
pip install pyinstaller

# Run PyInstaller
echo "Running PyInstaller..."
pyinstaller packaging/gdrive-gui.spec --clean --distpath dist/

# Show result
echo ""
echo "Build complete!"

if [ "$(uname)" == "Darwin" ]; then
    echo "Application bundle: $PROJECT_DIR/dist/GDrive Tools.app"
    if [ -d "$PROJECT_DIR/dist/GDrive Tools.app" ]; then
        echo "Size: $(du -sh "$PROJECT_DIR/dist/GDrive Tools.app" | cut -f1)"
        echo ""
        echo "To run: open \"$PROJECT_DIR/dist/GDrive Tools.app\""
    fi
else
    echo "Executable: $PROJECT_DIR/dist/GDrive Tools"
    if [ -f "$PROJECT_DIR/dist/GDrive Tools" ]; then
        echo "Size: $(du -h "$PROJECT_DIR/dist/GDrive Tools" | cut -f1)"
    fi
fi
