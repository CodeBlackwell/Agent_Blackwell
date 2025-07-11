#!/bin/bash
# Run Flagship TDD Orchestrator - Complete automation script
# Usage: ./runflagship.sh [optional description] [--streaming]
# Example: ./runflagship.sh "Create a temperature converter" --streaming

# Configuration
PORT=8100
SERVER_URL="http://localhost:$PORT"
DEFAULT_REQUEST="Create a Calculator class with methods for add, subtract, multiply, and divide. The divide method should handle division by zero by raising a ValueError."
USE_STREAMING=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
USER_REQUEST=""
for arg in "$@"; do
    if [ "$arg" = "--streaming" ]; then
        USE_STREAMING=true
    elif [ "$arg" = "--restart" ]; then
        # Keep for compatibility
        true
    else
        if [ -z "$USER_REQUEST" ]; then
            USER_REQUEST="$arg"
        else
            USER_REQUEST="$USER_REQUEST $arg"
        fi
    fi
done

# Use default if no request provided
if [ -z "$USER_REQUEST" ]; then
    echo -e "${YELLOW}No description provided. Using default: Calculator application${NC}"
    USER_REQUEST="$DEFAULT_REQUEST"
else
    echo -e "${GREEN}Using provided description: $USER_REQUEST${NC}"
fi

if [ "$USE_STREAMING" = true ]; then
    echo -e "${BLUE}Streaming mode enabled${NC}"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 Flagship TDD Orchestrator Runner${NC}"
echo -e "${BLUE}   Enhanced Version with Requirements Analysis${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to check if server is running
is_server_running() {
    curl -s -o /dev/null -w "%{http_code}" "$SERVER_URL/health" | grep -q "200"
}

# Function to kill process on port
kill_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}Killing existing process on port $port...${NC}"
        PIDS=$(lsof -ti:$port)
        for PID in $PIDS; do
            kill -TERM $PID 2>/dev/null || true
            sleep 0.5
            kill -KILL $PID 2>/dev/null || true
        done
        sleep 1
    fi
}

# Function to start server in background
start_server() {
    echo -e "${YELLOW}Starting Flagship server...${NC}"
    
    # Kill any existing process on the port
    kill_port $PORT
    
    # Start server in background and redirect output to log
    if [ "$USE_STREAMING" = true ]; then
        python run_enhanced_flagship.py --streaming > server.log 2>&1 &
    else
        # Use launcher to ensure proper imports
        python run_enhanced_flagship.py > server.log 2>&1 &
    fi
    SERVER_PID=$!
    
    # Wait for server to be ready
    echo -n "Waiting for server to be ready"
    for i in {1..30}; do
        if is_server_running; then
            echo ""
            echo -e "${GREEN}✅ Server is running (PID: $SERVER_PID)${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo -e "${RED}❌ Server failed to start. Check server.log for details${NC}"
    return 1
}

# Function to submit TDD request
submit_request() {
    local requirements="$1"
    
    echo -e "${YELLOW}Submitting TDD request...${NC}"
    
    # Create request JSON
    REQUEST_JSON=$(cat <<EOF
{
    "requirements": "$requirements",
    "config_type": "default",
    "stream_output": true
}
EOF
)
    
    # Submit request and capture session ID
    RESPONSE=$(curl -s -X POST "$SERVER_URL/tdd/start" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON")
    
    # Extract session ID
    SESSION_ID=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$SESSION_ID" ]; then
        echo -e "${RED}❌ Failed to get session ID${NC}"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo -e "${GREEN}✅ Session created: $SESSION_ID${NC}"
    echo "$SESSION_ID"  # Return the session ID
}

# Function to stream workflow output
stream_output() {
    local session_id="$1"
    
    echo ""
    echo -e "${BLUE}📺 Streaming TDD workflow output...${NC}"
    echo -e "${BLUE}=================================${NC}"
    
    # Track if we got any output
    local got_output=false
    
    # Stream output using curl with timeout
    curl -s -N --max-time 60 "$SERVER_URL/tdd/stream/$session_id" | while IFS= read -r line; do
        got_output=true
        # Skip empty lines
        [ -z "$line" ] && continue
        
        # Parse JSON line
        if echo "$line" | grep -q '"type":"status"'; then
            # Final status
            STATUS=$(echo "$line" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
            if [ "$STATUS" = "completed" ]; then
                echo -e "\n${GREEN}✅ Workflow completed successfully!${NC}"
            else
                echo -e "\n${RED}❌ Workflow failed${NC}"
                # Try to extract error message
                ERROR=$(echo "$line" | grep -o '"error":"[^"]*' | cut -d'"' -f4)
                [ -n "$ERROR" ] && echo -e "${RED}Error: $ERROR${NC}"
            fi
        elif echo "$line" | grep -q '"text":'; then
            # Regular output text
            TEXT=$(echo "$line" | sed 's/.*"text":"\(.*\)".*/\1/' | sed 's/\\n/\n/g' | sed 's/\\t/\t/g')
            echo -e "$TEXT"
        else
            # Debug: show unparsed lines
            # echo "Debug: $line"
            :
        fi
    done
    
    # Check if curl failed
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to stream output (connection timeout or error)${NC}"
    fi
}

# Function to get final results
get_results() {
    local session_id="$1"
    
    echo ""
    echo -e "${BLUE}📊 Final Results${NC}"
    echo -e "${BLUE}===============${NC}"
    
    # Get workflow status
    STATUS_RESPONSE=$(curl -s "$SERVER_URL/tdd/status/$session_id")
    
    # Check if response is valid
    if [ -z "$STATUS_RESPONSE" ]; then
        echo -e "${RED}No response from server${NC}"
        return 1
    fi
    
    # Debug: show raw response if needed
    # echo "Raw response: $STATUS_RESPONSE"
    
    # Parse and display results with error handling
    echo "$STATUS_RESPONSE" | python3 -c "
import json
import sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f'Error parsing JSON: {e}')
    print('Raw response:', sys.stdin.read())
    sys.exit(1)

results = data.get('results')
if results is None:
    results = {}

print(f\"Status: {data.get('status', 'unknown')}\")

# Handle both possible result structures
if isinstance(results, dict):
    print(f\"All Tests Passing: {results.get('all_tests_passing', False)}\")
    print(f\"Iterations: {results.get('iterations', 0)}\")
    print(f\"Test Summary: {results.get('test_summary', {})}\")
    print(f\"Duration: {results.get('duration', 0):.1f} seconds\")
    print(f\"Generated Tests: {results.get('generated_tests', 0)} file(s)\")
    print(f\"Generated Code: {results.get('generated_code', 0)} file(s)\")
else:
    print(f\"Results: {results}\")
" || echo -e "${RED}Failed to parse results${NC}"
}

# Function to show generated files
show_generated_files() {
    local session_id="$1"
    
    echo ""
    echo -e "${BLUE}📁 Generated Files${NC}"
    echo -e "${BLUE}=================${NC}"
    
    # Look for generated files
    GEN_DIR="generated/$session_id"
    if [ -d "$GEN_DIR" ]; then
        echo "Files in $GEN_DIR:"
        ls -la "$GEN_DIR"
        
        # Check for execution report
        if [ -f "$GEN_DIR/execution_report_$session_id.json" ]; then
            echo -e "\n${GREEN}📊 Execution report generated!${NC}"
            echo "View detailed tracing information in: $GEN_DIR/execution_report_$session_id.json"
        fi
        
        # Offer to show the files
        echo ""
        read -p "Would you like to see the generated code? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -f "$GEN_DIR/test_generated.py" ]; then
                echo -e "\n${YELLOW}=== TESTS ===${NC}"
                cat "$GEN_DIR/test_generated.py"
            fi
            
            if [ -f "$GEN_DIR/implementation_generated.py" ]; then
                echo -e "\n${YELLOW}=== IMPLEMENTATION ===${NC}"
                cat "$GEN_DIR/implementation_generated.py"
            fi
        fi
    else
        echo "No generated files found at $GEN_DIR"
    fi
}

# Main execution
main() {
    # Check if we're in the Flagship directory
    if [ ! -f "flagship_server.py" ]; then
        echo -e "${RED}Error: Must run from the Flagship directory${NC}"
        exit 1
    fi
    
    # Start server if not running
    if ! is_server_running; then
        if ! start_server; then
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Server already running${NC}"
    fi
    
    # Submit the request
    SESSION_ID=$(submit_request "$USER_REQUEST" | tail -n1)
    if [ $? -ne 0 ] || [ -z "$SESSION_ID" ]; then
        echo -e "${RED}Failed to submit request${NC}"
        exit 1
    fi
    
    # Wait a moment for processing to start
    sleep 2
    
    # Stream the output
    stream_output "$SESSION_ID"
    
    # Wait a bit for the workflow to complete
    sleep 2
    
    # Get final results
    get_results "$SESSION_ID"
    
    # Show generated files
    show_generated_files "$SESSION_ID"
    
    echo ""
    echo -e "${GREEN}✨ Done!${NC}"
    
    # Ask if user wants to keep server running
    echo ""
    read -p "Keep server running? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Stopping server...${NC}"
        if [ ! -z "$SERVER_PID" ]; then
            kill $SERVER_PID 2>/dev/null || true
        else
            kill_port $PORT
        fi
        echo -e "${GREEN}Server stopped${NC}"
    else
        echo -e "${GREEN}Server still running at $SERVER_URL${NC}"
    fi
}

# Trap to cleanup on exit
trap 'echo -e "\n${YELLOW}Interrupted. Cleaning up...${NC}"; kill $SERVER_PID 2>/dev/null || true; exit 1' INT TERM

# Run main function
main