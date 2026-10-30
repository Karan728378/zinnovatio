#!/usr/bin/env bash
# Parali Mitra Unix/Linux/macOS Launcher
set -e

echo "🌾 Starting Parali Mitra on $(uname -s)..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

$PYTHON_CMD launcher.py
