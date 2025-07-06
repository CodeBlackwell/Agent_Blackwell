#!/bin/bash
set -e

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "Waiting for $service_name to be ready..."
    while ! nc -z $host $port; do
        sleep 1
    done
    echo "$service_name is ready!"
}

# Determine which service to run based on environment variable
SERVICE=${SERVICE:-orchestrator}

case $SERVICE in
    orchestrator)
        echo "Starting Orchestrator service..."
        exec python orchestrator/orchestrator_agent.py
        ;;
    api)
        echo "Starting API service..."
        # Wait for orchestrator to be ready
        wait_for_service orchestrator 8080 "Orchestrator"
        exec python api/orchestrator_api.py
        ;;
    frontend)
        echo "Starting Frontend service..."
        # Wait for API to be ready
        wait_for_service api 8000 "API"
        exec python frontend/serve.py
        ;;
    *)
        echo "Unknown service: $SERVICE"
        echo "Valid services: orchestrator, api, frontend"
        exit 1
        ;;
esac