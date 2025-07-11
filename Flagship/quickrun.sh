#!/bin/bash
# Quick run script for Flagship TDD - Simplified version
# Usage: ./quickrun.sh [description]

PORT=8100
SERVER_URL="http://localhost:$PORT"

# Default to calculator if no args
REQUEST="${*:-Create a Calculator class with add, subtract, multiply, and divide methods}"

echo "🚀 Flagship TDD Quick Run"
echo "Request: $REQUEST"
echo ""

# Kill any existing server
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start server in background
echo "Starting server..."
python flagship_server.py > /tmp/flagship_server.log 2>&1 &
SERVER_PID=$!

# Wait for server
echo -n "Waiting for server"
for i in {1..10}; do
    if curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 1
done

# Submit request
echo "Submitting request..."
RESPONSE=$(curl -s -X POST "$SERVER_URL/tdd/start" \
    -H "Content-Type: application/json" \
    -d "{\"requirements\": \"$REQUEST\"}")

SESSION_ID=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
    echo "Failed to start workflow"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "Session: $SESSION_ID"
echo ""
echo "--- Output ---"

# Stream output
curl -s -N "$SERVER_URL/tdd/stream/$SESSION_ID" | while read -r line; do
    if echo "$line" | grep -q '"text":'; then
        echo "$line" | sed 's/.*"text":"\(.*\)".*/\1/' | sed 's/\\n/\n/g'
    fi
done

# Get final status
echo ""
echo "--- Results ---"
curl -s "$SERVER_URL/tdd/status/$SESSION_ID" | \
    python3 -m json.tool | \
    grep -E '"(status|all_tests_passing|iterations|duration)"'

# Cleanup
kill $SERVER_PID 2>/dev/null

echo ""
echo "✨ Done! Check generated/session_$SESSION_ID/ for files"