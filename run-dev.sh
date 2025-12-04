#!/bin/bash
# Calibre-Web-AI Development Runner (OS Agnostic)
# Works on Windows (Git Bash), Linux, and macOS

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "Linux";;
        Darwin*)    echo "macOS";;
        CYGWIN*)    echo "Windows";;
        MINGW*)     echo "Windows";;
        MSYS*)      echo "Windows";;
        *)          echo "Unknown";;
    esac
}

OS=$(detect_os)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Start Calibre-Web using venv Python directly (avoids Git Bash activation issues)
echo "Starting Calibre-Web..."

if [ "$OS" = "Windows" ]; then
    # Windows: Use venv Python directly
    ./venv/Scripts/python.exe cps.py
else
    # macOS/Linux: Use venv Python directly
    ./venv/bin/python cps.py
fi
