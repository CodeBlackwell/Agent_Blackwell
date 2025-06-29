#!/bin/bash

echo "======================================"
echo "   Job Pipeline Docker Environment"
echo "======================================"
echo

# Check if .env file exists, if not create a template
check_env_file() {
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        echo "OPENAI_API_KEY=" > .env
        echo "GIT_USER=Your Name" >> .env
        echo "GIT_EMAIL=your.email@example.com" >> .env
        echo ""
        echo "⚠️  Please edit .env file and add your OPENAI_API_KEY ⚠️"
        echo ""
    fi
}

# Test a specific agent with a message
test_agent() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "Usage: $0 test <agent_name> \"<message>\""
        echo "Example: $0 test planning \"Create a todo list app\""
        exit 1
    fi
    
    agent=$1
    message=$2
    port=""
    
    # Determine port based on agent name
    case "$agent" in
        planning) port=8001 ;;
        orchestrator) port=8002 ;;
        design) port=8003 ;;
        code) port=8004 ;;
        specification) port=8005 ;;
        review) port=8006 ;;
        testing) port=8007 ;;
        *)
            echo "Unknown agent: $agent"
            echo "Available agents: planning, orchestrator, design, code, specification, review, testing"
            exit 1
            ;;
    esac
    
    echo "Testing $agent agent on port $port with message: '$message'"
    
    # Create JSON payload with proper escaping
    json_payload=$(cat <<EOF
{
  "agent": "$agent",
  "input": [
    {
      "parts": [
        {
          "content": "$message"
        }
      ]
    }
  ]
}
EOF
)
    
    # Execute the curl command
    curl -s -X POST http://localhost:$port/api/v1/run \
      -H "Content-Type: application/json" \
      -d "$json_payload" | jq .
}

# Display help information
display_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start all containers (default if no command provided)"
    echo "  down        Stop and remove all containers"
    echo "  logs [svc]  View logs for all services or a specific service"
    echo "  rebuild     Rebuild and restart all containers"
    echo "  test        Test a specific agent with a message"
    echo "  help        Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start            # Start all containers"
    echo "  $0 logs planning    # View logs for planning service"
    echo "  $0 test planning \"Create a todo list app\"  # Test planning agent"
}

# Main script execution
case "$1" in
    start|"")
        check_env_file
        echo "Starting docker services..."
        docker-compose up -d
        echo ""
        echo "✅ All services started successfully!"
        echo ""
        echo "Use '$0 logs' to view logs"
        echo "Use '$0 down' to stop services"
        ;;
    down)
        echo "Stopping docker services..."
        docker-compose down
        echo "✅ All services stopped"
        ;;
    logs)
        if [ -z "$2" ]; then
            docker-compose logs --follow
        else
            docker-compose logs --follow "$2"
        fi
        ;;
    rebuild)
        echo "Rebuilding and restarting docker services..."
        docker-compose down
        docker-compose build --no-cache --pull  # Use --no-cache to force rebuild and --pull to use the latest Dockerfile
        docker-compose up -d
        echo "✅ Rebuild complete"
        ;;
    test)
        test_agent "$2" "$3"
        ;;
    clean)
        echo "Cleaning Docker environment (removing containers, images, and volumes)..."
        docker-compose down --volumes --remove-orphans
        docker rmi $(docker images -q '*job_pipeline*') 2>/dev/null || true
        echo "✅ Clean complete. Run '$0 rebuild' to start fresh."
        ;;
    help|*)
        display_help
        ;;
esac
