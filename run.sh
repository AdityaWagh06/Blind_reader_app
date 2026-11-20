#!/bin/bash

echo ""
echo "========================================"
echo "   Blind Reader Assistant Launcher"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "ERROR: Python 3.9 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements if needed
echo "Checking requirements..."
python -m pip install -q -r requirements.txt || { echo "ERROR: Failed to install requirements"; exit 1; }

# Run the application
echo ""
echo "Starting Blind Reader Assistant..."
echo "Open the URL below in your web browser"
echo "URL: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the application"
echo ""
python app.py 