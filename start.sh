#!/bin/bash

# Twitter Analytics Quick Start Script

echo "🐦 Twitter Archive Analytics - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 is installed"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "Choose an option:"
echo "1) Run Quick Analysis (CLI)"
echo "2) Run Advanced Analysis (CLI)"
echo "3) Launch Interactive Dashboard (Web)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Running Quick Analysis..."
        python3 analyzer.py
        ;;
    2)
        echo ""
        echo "Running Advanced Analysis..."
        read -p "Enter path to Twitter archive folder: " archive_path
        python3 advanced_analyzer.py "$archive_path"
        ;;
    3)
        echo ""
        echo "Launching Dashboard..."
        echo "Opening in your default browser..."
        streamlit run dashboard.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

