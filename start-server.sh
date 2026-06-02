#!/bin/bash

# Kill any existing Flask processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

# Navigate to the project directory
cd /Users/sabhy/Desktop/GitHub/clevertap-unsubscribe-flow

# Start Flask app in background
echo "Starting CleverTap Unsubscribe Flow..."
python3 app.py > /tmp/flask_app.log 2>&1 &

# Wait for server to start
sleep 3

# Check if server is responding
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Server started successfully!"
    echo "Opening dashboard at http://localhost:8000"
    open -a "Google Chrome" http://localhost:8000
else
    echo "✗ Server failed to start. Check /tmp/flask_app.log for details."
fi
