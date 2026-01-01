#!/bin/bash

# Twitter Analytics Quick Start Script

echo "🐦 Twitter Archive Analytics - Quick Start"
echo "=========================================="
echo ""

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ Loaded environment from .env"
fi

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
echo "📥 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check API mode and setup Rettiwt service if needed
if [ "$TWITTER_OFFICIAL" != "true" ]; then
    echo ""
    echo "🔌 API Mode: Rettiwt-API (Free)"
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo "⚠️  Node.js is not installed. Required for Rettiwt-API mode."
        echo "   Install from: https://nodejs.org/"
        echo "   Or set TWITTER_OFFICIAL=true in .env to use official API"
    else
        echo "✓ Node.js is installed"
        
        # Install Rettiwt service dependencies if needed
        if [ ! -d "rettiwt-service/node_modules" ]; then
            echo "📥 Installing Rettiwt service dependencies..."
            cd rettiwt-service && npm install --silent && cd ..
            echo "✓ Rettiwt service dependencies installed"
        fi
    fi
else
    echo ""
    echo "🔌 API Mode: Official Twitter API"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Choose an option:"
echo "1) Run Quick Analysis (CLI)"
echo "2) Run Advanced Analysis (CLI)"
echo "3) Launch Interactive Dashboard (Web)"
echo "4) Start Rettiwt Service (for free API mode)"
echo ""
read -p "Enter choice (1-4): " choice

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
        streamlit run main.py
        ;;
    4)
        echo ""
        echo "Starting Rettiwt Service..."
        cd rettiwt-service && npm start
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
