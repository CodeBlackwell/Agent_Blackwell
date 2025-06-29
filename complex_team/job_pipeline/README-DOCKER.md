# Dockerized Job Pipeline

This document explains how to use the Docker setup for the Job Pipeline system, which eliminates the need to manually start multiple agent servers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. Make sure Docker is running on your system
2. Run the provided helper script:
   ```bash
   chmod +x run-docker.sh
   ./run-docker.sh
   ```

The script will:
1. Check for a `.env` file and create one if it doesn't exist
2. Start all the required services in Docker containers
3. Provide instructions for viewing logs and stopping the services

## Environment Configuration

Before starting the Docker environment, make sure your `.env` file contains:

```
OPENAI_API_KEY=your_openai_api_key_here
GIT_USER=Your Name
GIT_EMAIL=your.email@example.com
```

## Services

The Dockerized setup includes the following services:

- **Planning Agent**: Port 8001
- **Orchestrator Agent**: Port 8002
- **Specification Agent**: Port 8005
- **Design Agent**: Port 8003
- **Code Agent**: Port 8004
- **Review Agent**: Port 8006
- **Testing Agent**: Port 8007
- **MCP Git Tools**: For Git integration
- **UI**: Port 8501 (Optional web interface)
- **Client**: Test client for interacting with agents

## Usage

### Starting the System

```bash
./run-docker.sh
```

### Viewing Logs

```bash
# View all logs
./run-docker.sh logs

# View logs for a specific service
./run-docker.sh logs planning
```

### Stopping the System

```bash
./run-docker.sh down
```

### Rebuilding Containers

If you make changes to the code or dependencies:

```bash
./run-docker.sh rebuild
```

## Testing the System

Once all containers are running, you can:

1. Access the UI at http://localhost:8501 (if enabled)
2. Use the client to send requests:

```python
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

async with Client(base_url="http://localhost:8001") as client:
    async for event in client.run_stream(
        agent="planner",
        input=[Message(parts=[MessagePart(content="Create a simple Flask API with endpoints for user management")])]
    ):
        if hasattr(event, "content"):
            print(event.content, end="", flush=True)
```

## Docker Configuration Details

- **Virtual Environment**: Uses uv to create a proper virtual environment inside the container
- **State Persistence**: Mounts `./state` directory to maintain state across container restarts
- **Git Integration**: Mounts Git configuration for PR creation
- **Environment Variables**: Uses dotenv for loading environment variables

## Troubleshooting

- **Permission Issues**: If you encounter permission issues with mounted volumes, check file permissions on your host system
- **Network Issues**: If services can't communicate, ensure all containers are on the same Docker network
- **API Key Errors**: Verify your `.env` file contains the correct API keys

## Troubleshooting Docker Builds

### Common Build Issues

#### Package Installation Errors

If you encounter build errors like `error: package directory 'agents' does not exist`, it typically means there's an issue with the order of operations in the Docker build process. To fix this:

```bash
# Perform a clean rebuild
./run-docker.sh clean
./run-docker.sh rebuild
```

The clean command removes all containers, images, and volumes related to the job pipeline, allowing for a fresh start.

#### Environment Configuration Issues

If you see errors related to missing API keys or environment variables:

1. Check that your `.env` file contains the required variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GIT_USER=Your Name
   GIT_EMAIL=your.email@example.com
   ```

2. Make sure the environment variables are properly passed to the containers:
   ```bash
   # Verify environment variables in a running container
   docker exec -it job_pipeline_planning_1 env | grep OPENAI
   ```

#### Port Conflict Issues

If you encounter port conflicts:

```bash
# Check what's using the conflicting port (example for port 8001)
lsof -i :8001

# Stop the Docker services and restart
./run-docker.sh down
./run-docker.sh start
```

### Advanced Troubleshooting

For more persistent issues:

1. Inspect the Docker build logs:
   ```bash
   docker-compose build --no-cache --progress=plain
   ```

2. Access a running container for debugging:
   ```bash
   docker exec -it job_pipeline_planning_1 /bin/bash
   ```

3. Check for Docker network issues:
   ```bash
   docker network inspect job_pipeline_default
   ```

Always follow the project's virtual environment and configuration principles even when debugging inside containers.
