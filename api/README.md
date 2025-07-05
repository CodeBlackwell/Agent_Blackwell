# Orchestrator API

A REST API interface for the multi-agent orchestrator system that allows users to execute AI-powered workflows for software development tasks.

## Quick Start

### 1. Install Dependencies

```bash
# From the project root directory
uv pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python api/orchestrator_api.py
```

The API will start on `http://localhost:8000`

### 3. Access API Documentation

Open your browser and navigate to `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Health Check
- **GET** `/health` - Check if the API is running and healthy

### Workflow Types
- **GET** `/workflow-types` - Get available workflow types (tdd, full, individual)

### Execute Workflow
- **POST** `/execute-workflow` - Start a new workflow execution
  - Returns a session ID for tracking progress

### Workflow Status
- **GET** `/workflow-status/{session_id}` - Check the status of a workflow execution
- **DELETE** `/workflow-status/{session_id}` - Delete a workflow execution record

## Usage Example

### Using the Test Client

```bash
python api/test_api_client.py
```

### Using curl

```bash
# Execute a workflow
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a Python function to calculate fibonacci numbers",
    "workflow_type": "full",
    "max_retries": 3,
    "timeout_seconds": 300
  }'

# Check workflow status (replace SESSION_ID with actual value)
curl http://localhost:8000/workflow-status/SESSION_ID
```

### Using Python

```python
import requests

# Execute a workflow
response = requests.post(
    "http://localhost:8000/execute-workflow",
    json={
        "requirements": "Create a REST API for managing tasks",
        "workflow_type": "tdd",
        "max_retries": 3,
        "timeout_seconds": 300
    }
)

session_id = response.json()["session_id"]

# Check status
status = requests.get(f"http://localhost:8000/workflow-status/{session_id}")
print(status.json())
```

## Workflow Types

1. **TDD Workflow** (`tdd`): Test-Driven Development approach
   - Planning → Design → Test Writing → Implementation → Execution → Review

2. **Full Workflow** (`full`): Complete development cycle
   - Planning → Design → Implementation → Review

3. **Individual Steps** (`individual`): Execute single workflow steps
   - Requires `step_type` parameter (planning, design, implementation, etc.)

## Testing

Run the test suite:

```bash
# Run API tests
pytest api/test_orchestrator_api.py -v

# Run with coverage
pytest api/test_orchestrator_api.py --cov=api --cov-report=html
```

## Notes

- The API runs workflows asynchronously in the background
- Use the session ID to track progress and retrieve results
- Workflow execution can take several minutes depending on complexity
- For production use, consider implementing:
  - Authentication/authorization
  - Rate limiting
  - Persistent storage for workflow results
  - WebSocket support for real-time updates