#!/bin/bash
# Script to run agent workers with Docker Compose

set -e

# Default values
MODE="individual"
ACTION="up"
DETACH="-d"

# Function to display usage
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Run agent workers using Docker Compose"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE       Worker mode: 'individual' (separate containers) or 'combined' (all in one)"
    echo "  -a, --action ACTION   Docker Compose action: 'up', 'down', 'restart', 'logs', 'ps'"
    echo "  -f, --foreground      Run in foreground (don't detach)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --mode individual --action up     # Start individual workers in detached mode"
    echo "  $0 --mode combined --action up -f    # Start combined worker in foreground"
    echo "  $0 --action down                     # Stop all workers"
    echo "  $0 --action logs                     # Show logs for all workers"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -f|--foreground)
            DETACH=""
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate mode
if [[ "$MODE" != "individual" && "$MODE" != "combined" ]]; then
    echo "Error: Invalid mode '$MODE'. Must be 'individual' or 'combined'."
    show_usage
    exit 1
fi

# Set Docker Compose file
COMPOSE_FILE="docker-compose.workers.yml"

# Check if Docker Compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Error: Docker Compose file '$COMPOSE_FILE' not found."
    exit 1
fi

# Check if OPENAI_API_KEY is set
if [[ -z "$OPENAI_API_KEY" && "$ACTION" == "up" ]]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set."
    echo "The workers may not function correctly without an API key."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Set services based on mode
if [[ "$MODE" == "combined" ]]; then
    SERVICES="redis orchestrator all-workers"
    PROFILE="--profile all-in-one"
else
    SERVICES="redis orchestrator spec-worker design-worker coding-worker review-worker test-worker"
    PROFILE=""
fi

# Execute Docker Compose command
case $ACTION in
    up)
        echo "Starting agent workers in $MODE mode..."
        docker-compose -f $COMPOSE_FILE $PROFILE up $DETACH $SERVICES
        ;;
    down)
        echo "Stopping agent workers..."
        docker-compose -f $COMPOSE_FILE down
        ;;
    restart)
        echo "Restarting agent workers in $MODE mode..."
        docker-compose -f $COMPOSE_FILE $PROFILE restart $SERVICES
        ;;
    logs)
        echo "Showing logs for agent workers..."
        docker-compose -f $COMPOSE_FILE logs -f $SERVICES
        ;;
    ps)
        echo "Showing status of agent workers..."
        docker-compose -f $COMPOSE_FILE ps
        ;;
    *)
        echo "Error: Invalid action '$ACTION'."
        show_usage
        exit 1
        ;;
esac

echo "Done."
