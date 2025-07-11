#!/bin/bash
# Start the Flagship TDD Orchestrator Server

PORT=8100

echo "🚀 Starting Flagship TDD Orchestrator Server..."
echo "================================================"
echo "Server will run at: http://localhost:$PORT"
echo "API docs at: http://localhost:$PORT/docs"
echo "================================================"
echo ""

# Check if we're in the Flagship directory
if [ ! -f "flagship_server.py" ]; then
    echo "Error: Must run from the Flagship directory"
    exit 1
fi

# Check if port is in use and kill the process if needed
check_and_kill_port() {
    local port=$1
    
    # Check if port is in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use. Attempting to free it..."
        
        # Get PIDs using the port
        PIDS=$(lsof -ti:$port)
        
        if [ ! -z "$PIDS" ]; then
            for PID in $PIDS; do
                echo "Killing process $PID..."
                kill -TERM $PID 2>/dev/null || true
                sleep 0.5
                # Force kill if still running
                kill -KILL $PID 2>/dev/null || true
            done
            echo "✅ Port $port has been freed"
            sleep 1  # Give OS time to release the port
        fi
    else
        echo "✅ Port $port is available"
    fi
}

# Kill any process on port 8100
check_and_kill_port $PORT

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing server dependencies..."
    pip install -r requirements_server.txt
fi

# Start the server
echo ""
echo "Starting server..."
python flagship_server.py