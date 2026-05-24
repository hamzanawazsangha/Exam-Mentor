#!/usr/bin/env bash
# Run the entire CSS/PMS Exam Portal

echo "=================================="
echo "CSS/PMS Exam Preparation Portal"
echo "=================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Ensuring dependencies are installed..."
pip install -q flask flask-cors sqlalchemy openai requests python-dotenv chromadb 2>/dev/null

# Navigate to backend
cd backend

# Start Flask server
echo "=================================="
echo "Starting Flask Server..."
echo "=================================="
echo ""
echo "Server running at: http://127.0.0.1:5000"
echo "Dashboard: http://127.0.0.1:5000/dashboard"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

python main.py
