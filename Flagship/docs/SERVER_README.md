# Flagship TDD Orchestrator Server

The custom-built server for the RED-YELLOW-GREEN TDD workflow orchestration.

## Architecture

The Flagship server provides:
- **REST API** for workflow management
- **Streaming output** for real-time phase updates
- **Async workflow execution** in the background
- **In-memory workflow storage** (can be extended to persistent storage)

## Starting the Server

### Quick Start
```bash
cd Flagship
./start_server.sh
```

### Manual Start
```bash
cd Flagship
pip install -r requirements_server.txt
python flagship_server.py
```

The server will start on `http://localhost:8100`

## API Endpoints

### Core Endpoints

- `POST /tdd/start` - Start a new TDD workflow
- `GET /tdd/status/{session_id}` - Get workflow status
- `GET /tdd/stream/{session_id}` - Stream workflow output (SSE)
- `GET /workflows` - List all workflows
- `DELETE /workflows/{session_id}` - Delete a workflow
- `GET /health` - Health check
- `GET /phases` - Get TDD phase information

### API Documentation

Interactive API docs are available at:
- Swagger UI: `http://localhost:8100/docs`
- ReDoc: `http://localhost:8100/redoc`

## Using the Client

### Command Line Interface

```bash
# Start a new workflow
python flagship_client.py start "Create a palindrome checker function"

# Check status
python flagship_client.py status tdd_20250710_120000

# List all workflows
python flagship_client.py list

# Show TDD phases
python flagship_client.py phases

# Interactive mode
python flagship_client.py interactive
```

### Python API

```python
import asyncio
from flagship_client import FlagshipClient

async def run_workflow():
    async with FlagshipClient() as client:
        # Start workflow
        session_id = await client.start_workflow(
            "Create a calculator with add and subtract",
            config_type="quick"
        )
        
        # Stream output
        async for event in client.stream_output(session_id):
            print(event.get("text", ""))
        
        # Get final status
        status = await client.get_status(session_id)
        print(f"Completed: {status['results']['all_tests_passing']}")

asyncio.run(run_workflow())
```

## Example API Calls

### Start a workflow
```bash
curl -X POST http://localhost:8100/tdd/start \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a function to validate email addresses",
    "config_type": "default"
  }'
```

### Check status
```bash
curl http://localhost:8100/tdd/status/{session_id}
```

### Stream output
```bash
curl -N http://localhost:8100/tdd/stream/{session_id}
```

## Configuration

The server uses configuration from `configs/flagship_config.py`:

```python
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8100,
    "max_workflows": 100,
    "workflow_timeout": 600,  # 10 minutes
}
```

## Workflow Execution

1. **Client submits requirements** via REST API
2. **Server creates workflow session** and starts background task
3. **Orchestrator runs TDD phases**:
   - 🔴 RED: Generate failing tests
   - 🟡 YELLOW: Write minimal implementation
   - 🟢 GREEN: Run tests and validate
4. **Output streams to client** in real-time
5. **Results saved** to `generated/session_{id}/`

## Extending the Server

### Add Persistent Storage

Replace the in-memory `workflows` dict with a database:

```python
# Example with SQLite
import aiosqlite

async def save_workflow(session_id: str, data: dict):
    async with aiosqlite.connect("workflows.db") as db:
        await db.execute(
            "INSERT INTO workflows VALUES (?, ?)",
            (session_id, json.dumps(data))
        )
```

### Add Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Verify token logic
    pass

@app.post("/tdd/start", dependencies=[Depends(verify_token)])
async def start_tdd_workflow(...):
    # Protected endpoint
```

### Add WebSocket Support

```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # Stream updates via WebSocket
```

## Monitoring

Check server health:
```bash
curl http://localhost:8100/health
```

View active workflows:
```bash
python flagship_client.py list | grep running
```

## Troubleshooting

1. **Port already in use**: Change port in `SERVER_CONFIG`
2. **Import errors**: Run `pip install -r requirements_server.txt`
3. **Workflow timeouts**: Increase `timeout_seconds` in config
4. **Memory issues**: Implement cleanup for old workflows