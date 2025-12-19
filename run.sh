#!/bin/bash

# PDF Parser Application Startup Script

echo "Starting PDF Parser Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file not found!"
    echo "Please create a .env file with your API credentials."
    echo "You can copy .env.example as a template:"
    echo "  cp .env.example .env"
    echo ""
fi

# Start the server
echo ""
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "Frontend: Open index.html in your browser"
echo ""
python app.py


