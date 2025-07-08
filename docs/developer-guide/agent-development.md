# Agent Development Guide

## Overview

This guide provides comprehensive information for developing new agents or extending existing agents in the Multi-Agent Orchestrator System. Agents are the core workers that perform specialized tasks within workflows.

## Agent Architecture

### Base Agent Structure

All agents inherit from a common base pattern and implement the Agent Communication Protocol (ACP):

```python
from typing import AsyncGenerator
import asyncio

class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.capabilities = []
        
    async def process_request(self, request: dict) -> AsyncGenerator[str, None]:
        """Process incoming requests and yield responses"""
        # Validate request
        if not self._validate_request(request):
            yield "Error: Invalid request format"
            return
            
        # Process request
        async for response in self._execute_task(request):
            yield response
            
    def _validate_request(self, request: dict) -> bool:
        """Validate incoming request structure"""
        return "task" in request and "context" in request
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        """Execute the agent's main task - to be implemented by subclasses"""
        raise NotImplementedError
```

## Creating a New Agent

### Step 1: Define Agent Structure

Create a new directory under `agents/`:

```
agents/
└── your_agent/
    ├── __init__.py
    ├── your_agent.py
    ├── test_your_agent_debug.py
    └── README.md
```

### Step 2: Implement Agent Logic

```python
# agents/your_agent/your_agent.py
from typing import AsyncGenerator
import asyncio
from agents.base_agent import BaseAgent

class YourAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="your_agent",
            role="Specialized task description"
        )
        self.capabilities = [
            "capability_1",
            "capability_2"
        ]
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        """Main task execution logic"""
        task = request.get("task")
        context = request.get("context", {})
        
        # Initial response
        yield f"Starting {self.role} for task: {task}\n"
        
        # Process task
        try:
            result = await self._process_specific_task(task, context)
            yield f"Result: {result}\n"
        except Exception as e:
            yield f"Error: {str(e)}\n"
            
    async def _process_specific_task(self, task: str, context: dict) -> str:
        """Agent-specific processing logic"""
        # Implement your agent's core functionality here
        await asyncio.sleep(1)  # Simulate processing
        return f"Processed: {task}"
```

### Step 3: Register with ACP

Add your agent to the orchestrator's agent registry:

```python
# orchestrator/agent_registry.py
from agents.your_agent import YourAgent

AGENT_REGISTRY = {
    # ... existing agents ...
    "your_agent": YourAgent,
}
```

## Agent Communication

### Request Format

Agents receive requests in this format:

```python
{
    "task": "Task description",
    "context": {
        "previous_results": {},
        "workflow_phase": "current_phase",
        "configuration": {}
    },
    "metadata": {
        "session_id": "uuid",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### Response Format

Agents should yield responses as strings:

```python
async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
    yield "Status: Processing request\n"
    yield "Progress: 50%\n"
    yield "Result: Task completed successfully\n"
```

## Best Practices

### 1. Streaming Responses

Always use async generators for incremental output:

```python
async def process_large_task(self, data: list) -> AsyncGenerator[str, None]:
    total = len(data)
    for i, item in enumerate(data):
        result = await self._process_item(item)
        yield f"Progress: {i+1}/{total} - {result}\n"
        
    yield "Task completed!\n"
```

### 2. Error Handling

Implement comprehensive error handling:

```python
async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
    try:
        # Validate inputs
        if not self._validate_inputs(request):
            yield "Error: Invalid input format\n"
            return
            
        # Process with timeout
        result = await asyncio.wait_for(
            self._process(request),
            timeout=60.0
        )
        yield f"Success: {result}\n"
        
    except asyncio.TimeoutError:
        yield "Error: Task timed out\n"
    except Exception as e:
        yield f"Error: Unexpected error - {str(e)}\n"
```

### 3. Context Awareness

Utilize workflow context effectively:

```python
def _use_context(self, context: dict) -> dict:
    # Access previous agent results
    planner_output = context.get("previous_results", {}).get("planner", {})
    
    # Check workflow configuration
    config = context.get("configuration", {})
    max_retries = config.get("max_retries", 3)
    
    # Maintain state across requests
    self.state = context.get("agent_state", {})
    
    return {
        "using_context": True,
        "previous_data": planner_output
    }
```

### 4. Testing

Create comprehensive test suites:

```python
# agents/your_agent/test_your_agent_debug.py
import asyncio
from your_agent import YourAgent

async def test_basic_functionality():
    agent = YourAgent()
    request = {
        "task": "Test task",
        "context": {}
    }
    
    responses = []
    async for response in agent.process_request(request):
        responses.append(response)
        print(response)
        
    assert len(responses) > 0
    assert "Success" in responses[-1] or "completed" in responses[-1]

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
```

## Integration with Workflows

### Adding to Existing Workflows

1. Update workflow configuration:

```python
# workflows/your_workflow/config.py
WORKFLOW_AGENTS = [
    "planner_agent",
    "your_agent",  # Add your agent
    "reviewer_agent"
]
```

2. Define agent interaction:

```python
# workflows/your_workflow/workflow.py
async def execute_your_agent_phase(request: dict, context: dict):
    agent_request = {
        "task": f"Process: {request['requirements']}",
        "context": context
    }
    
    result = await run_agent("your_agent", agent_request)
    return result
```

## Advanced Features

### 1. State Management

```python
class StatefulAgent(BaseAgent):
    def __init__(self):
        super().__init__("stateful_agent", "Stateful processing")
        self.state = {}
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        session_id = request.get("metadata", {}).get("session_id")
        
        # Maintain state per session
        if session_id not in self.state:
            self.state[session_id] = {"counter": 0}
            
        self.state[session_id]["counter"] += 1
        yield f"Request #{self.state[session_id]['counter']}\n"
```

### 2. External Service Integration

```python
class ExternalServiceAgent(BaseAgent):
    def __init__(self):
        super().__init__("external_agent", "External service integration")
        self.api_client = self._setup_client()
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        yield "Connecting to external service...\n"
        
        try:
            result = await self.api_client.process(request["task"])
            yield f"External result: {result}\n"
        except Exception as e:
            yield f"External service error: {str(e)}\n"
```

### 3. Parallel Processing

```python
class ParallelAgent(BaseAgent):
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        tasks = request.get("tasks", [])
        
        yield f"Processing {len(tasks)} tasks in parallel...\n"
        
        # Create parallel tasks
        async_tasks = [
            self._process_single_task(task) 
            for task in tasks
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*async_tasks)
        
        for i, result in enumerate(results):
            yield f"Task {i+1}: {result}\n"
```

## Performance Optimization

### 1. Caching

```python
from functools import lru_cache

class CachedAgent(BaseAgent):
    @lru_cache(maxsize=100)
    def _expensive_computation(self, input_data: str) -> str:
        # Expensive computation cached
        return process_data(input_data)
```

### 2. Resource Management

```python
class ResourceAwareAgent(BaseAgent):
    def __init__(self):
        super().__init__("resource_agent", "Resource-aware processing")
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent operations
        
    async def _process_with_limit(self, item):
        async with self.semaphore:
            return await self._process_item(item)
```

## Debugging and Monitoring

### 1. Logging

```python
import logging

class LoggingAgent(BaseAgent):
    def __init__(self):
        super().__init__("logging_agent", "Agent with logging")
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        self.logger.info(f"Processing request: {request.get('task')}")
        yield "Processing...\n"
        
        try:
            result = await self._process(request)
            self.logger.info(f"Success: {result}")
            yield f"Result: {result}\n"
        except Exception as e:
            self.logger.error(f"Error: {str(e)}", exc_info=True)
            yield f"Error occurred: {str(e)}\n"
```

### 2. Metrics

```python
import time

class MetricsAgent(BaseAgent):
    def __init__(self):
        super().__init__("metrics_agent", "Agent with metrics")
        self.metrics = {"total_requests": 0, "total_time": 0}
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        async for response in self._process(request):
            yield response
            
        elapsed = time.time() - start_time
        self.metrics["total_time"] += elapsed
        yield f"Processed in {elapsed:.2f}s\n"
```

## Related Documentation

- [Architecture Overview](architecture/README.md)
- [Workflow Development](workflow-development.md)
- [Testing Guide](testing-guide.md)
- [Agent Interfaces](../reference/agent-interfaces.md)