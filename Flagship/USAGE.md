# Flagship TDD Orchestrator - Usage Guide

This guide covers how to use the Flagship TDD Orchestrator for Test-Driven Development workflows.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Server Operations](#server-operations)
3. [Client Usage](#client-usage)
4. [REST API Reference](#rest-api-reference)
5. [Examples](#examples)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Start the Server

```bash
cd /Users/lechristopherblackwell/Desktop/Ground_up/rebuild/Flagship
python flagship_server.py
```

The server will start on `http://localhost:8100`

### 2. Run Your First TDD Workflow

In a new terminal:

```bash
python flagship_client.py start "Create a calculator class with add and subtract methods"
```

### 3. Check Results

Generated code is saved in `generated/session_tdd_[timestamp]/`

## Server Operations

### Starting the Server

```bash
# Option 1: Direct Python
python flagship_server.py

# Option 2: Using start script
./start_server.sh

# Option 3: Custom host/port
python flagship_server.py --host 0.0.0.0 --port 8200
```

### Server Endpoints

- **Health Check**: `http://localhost:8100/health`
- **API Documentation**: `http://localhost:8100/docs`
- **Redoc Documentation**: `http://localhost:8100/redoc`

### Monitoring Server Logs

```bash
# View real-time logs
tail -f logs/server.log

# View debug logs
tail -f logs/server_debug.log

# View captured output
tail -f logs/server_output.log
```

## Client Usage

### Basic Commands

```bash
# Start a new TDD workflow
python flagship_client.py start "Your requirements here"

# Start with specific configuration
python flagship_client.py start "Your requirements" --config QUICK

# Available configurations: DEFAULT, QUICK, COMPREHENSIVE
```

### Client Output

The client displays:
- 🔴 **RED Phase**: Test generation
- 🟡 **YELLOW Phase**: Implementation writing
- 🟢 **GREEN Phase**: Test execution
- ✅ **Summary**: Results and file locations

### Example Client Sessions

```bash
# Simple function
python flagship_client.py start "Create a greet function that returns 'Hello, {name}!'"

# Class with methods
python flagship_client.py start "Create a TodoList class with add, remove, and list methods"

# API endpoint
python flagship_client.py start "Create a FastAPI endpoint /users that returns a list of users"
```

## REST API Reference

### Start TDD Workflow

**POST** `/tdd/start`

```bash
curl -X POST http://localhost:8100/tdd/start \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a calculator with add method",
    "config": "DEFAULT"
  }'
```

Response:
```json
{
  "session_id": "tdd_20250710_183209_327286",
  "message": "TDD workflow started",
  "stream_url": "/tdd/stream/tdd_20250710_183209_327286"
}
```

### Check Workflow Status

**GET** `/tdd/status/{session_id}`

```bash
curl http://localhost:8100/tdd/status/tdd_20250710_183209_327286
```

Response:
```json
{
  "session_id": "tdd_20250710_183209_327286",
  "status": "completed",
  "current_phase": "GREEN",
  "iteration": 1,
  "test_results": {
    "total": 8,
    "passed": 8,
    "failed": 0
  }
}
```

### Stream Real-time Output

**GET** `/tdd/stream/{session_id}`

```bash
# Using curl with Server-Sent Events
curl -N http://localhost:8100/tdd/stream/tdd_20250710_183209_327286

# Using Python
import requests

response = requests.get(
    'http://localhost:8100/tdd/stream/tdd_20250710_183209_327286',
    stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### List Active Workflows

**GET** `/tdd/workflows`

```bash
curl http://localhost:8100/tdd/workflows
```

## Examples

### 1. Calculator Implementation

```bash
python flagship_client.py start "Create a Calculator class with methods:
- add(a, b): returns sum
- subtract(a, b): returns difference
- multiply(a, b): returns product
- divide(a, b): returns quotient, raises error for division by zero"
```

### 2. Data Structure Implementation

```bash
python flagship_client.py start "Create a Stack data structure with:
- push(item): adds item to top
- pop(): removes and returns top item
- peek(): returns top item without removing
- is_empty(): returns True if stack is empty
- size(): returns number of items"
```

### 3. REST API Endpoint

```bash
python flagship_client.py start "Create a FastAPI application with:
- GET /items: returns list of items
- GET /items/{id}: returns specific item
- POST /items: creates new item
- DELETE /items/{id}: deletes item"
```

### 4. File Processing Function

```bash
python flagship_client.py start "Create a function process_csv(filename) that:
- Reads a CSV file
- Validates data format
- Returns parsed data as list of dictionaries
- Handles file not found errors"
```

## Configuration

### Workflow Configurations

Edit `configs/flagship_config.py` to modify:

- **DEFAULT**: Standard workflow (3 iterations max)
- **QUICK**: Fast workflow (1 iteration max)
- **COMPREHENSIVE**: Thorough workflow (5 iterations max)

### Configuration Parameters

```python
{
    "max_iterations": 3,          # Maximum RED-YELLOW-GREEN cycles
    "test_timeout": 30,           # Test execution timeout (seconds)
    "allow_refactoring": True,    # Enable GREEN phase refactoring
    "strict_tdd": True,           # Enforce failing tests first
    "verbose_output": True        # Detailed logging
}
```

### Environment Variables

```bash
# Set custom port
export FLAGSHIP_PORT=8200

# Set custom host
export FLAGSHIP_HOST=0.0.0.0

# Enable debug mode
export FLAGSHIP_DEBUG=true
```

## Troubleshooting

### Common Issues

#### Server Won't Start

```bash
# Check if port is in use
lsof -i :8100

# Kill process using port
kill -9 $(lsof -t -i:8100)
```

#### Import Errors

```bash
# Ensure you're in the correct directory
cd /Users/lechristopherblackwell/Desktop/Ground_up/rebuild/Flagship

# Install dependencies
pip install -r requirements_server.txt
```

#### Tests Not Running

```bash
# Check pytest is installed
pip install pytest

# Verify test file generation
ls -la generated/session_*/test_generated.py
```

### Debug Mode

Enable detailed logging:

```bash
# Start server in debug mode
python flagship_server.py --debug

# Check debug logs
tail -f logs/server_debug.log
```

### Manual Testing

Test individual components:

```bash
cd tests/

# Test orchestrator directly
python test_orchestrator_direct.py

# Run standalone test
python run_standalone_test.py

# Test specific phase
python test_flagship.py
```

## Advanced Usage

### Programmatic API Usage

```python
from flagship_orchestrator import FlagshipTDDOrchestrator
from configs.flagship_config import WorkflowConfigs

# Create orchestrator
orchestrator = FlagshipTDDOrchestrator()

# Run workflow
result = await orchestrator.run_tdd_workflow(
    requirements="Create a hello world function",
    config=WorkflowConfigs.DEFAULT
)

print(f"Generated tests: {result.phases[0].output}")
print(f"Generated code: {result.phases[1].output}")
```

### Custom Agent Integration

```python
from agents.test_writer_flagship import TestWriterFlagship

# Use agent directly
test_writer = TestWriterFlagship()
async for chunk in test_writer.write_tests("Create add function"):
    print(chunk, end='')
```

### Batch Processing

```bash
# Process multiple requirements
for req in "calculator" "todo_list" "api_endpoint"; do
    python flagship_client.py start "Create a $req implementation"
    sleep 2
done
```

## Output Files

Generated files are saved in timestamped directories:

```
generated/session_tdd_20250710_183209_327286/
├── test_generated.py          # Generated test suite
├── implementation_generated.py # Generated implementation
└── tdd_workflow_*.json        # Complete workflow history
```

### Viewing Results

```bash
# List all sessions
ls -la generated/

# View latest generated tests
cat generated/session_tdd_*/test_generated.py | tail -n 50

# View implementation
cat generated/session_tdd_*/implementation_generated.py

# Parse workflow JSON
python -m json.tool generated/session_tdd_*/tdd_workflow_*.json
```

## Tips and Best Practices

1. **Clear Requirements**: Be specific about methods, parameters, and expected behavior
2. **Start Simple**: Begin with basic functionality, then add complexity
3. **Use Examples**: Include example inputs/outputs in requirements
4. **Check Logs**: Monitor server logs for detailed execution information
5. **Iterate**: Use the generated code as a starting point for further development

## Getting Help

- View API documentation: `http://localhost:8100/docs`
- Check server health: `http://localhost:8100/health`
- Review logs in `logs/` directory
- Examine generated code in `generated/` directory