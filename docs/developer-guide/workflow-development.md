# Workflow Development Guide

## Overview

This guide covers the development of custom workflows in the Multi-Agent Orchestrator System. Workflows define how agents collaborate to accomplish complex tasks, from simple sequential processes to sophisticated parallel executions.

## Workflow Architecture

### Core Components

1. **Workflow Manager** (`workflows/workflow_manager.py`)
   - Routes requests to appropriate workflows
   - Manages workflow lifecycle
   - Handles error recovery

2. **Workflow Module**
   - Contains workflow-specific logic
   - Defines agent orchestration
   - Manages state and context

3. **Workflow Configuration**
   - Defines workflow parameters
   - Sets agent sequence
   - Configures retry and timeout policies

## Creating a New Workflow

### Step 1: Plan Your Workflow

Define the workflow structure:
- Identify required agents
- Determine execution order
- Plan data flow between agents
- Design error handling strategy

### Step 2: Create Workflow Directory

```bash
workflows/
└── your_workflow/
    ├── __init__.py
    ├── workflow.py          # Main workflow logic
    ├── config.py           # Configuration
    ├── validators.py       # Input validators (optional)
    └── README.md           # Documentation
```

### Step 3: Implement Workflow Configuration

```python
# workflows/your_workflow/config.py

WORKFLOW_CONFIG = {
    "name": "your_workflow",
    "description": "Description of what your workflow does",
    "version": "1.0.0",
    "agents": [
        "planner_agent",
        "designer_agent", 
        "coder_agent",
        "reviewer_agent"
    ],
    "phases": [
        {
            "name": "planning",
            "agent": "planner_agent",
            "timeout": 120,
            "retries": 2
        },
        {
            "name": "design",
            "agent": "designer_agent",
            "timeout": 180,
            "retries": 3,
            "depends_on": ["planning"]
        },
        {
            "name": "implementation",
            "agent": "coder_agent",
            "timeout": 300,
            "retries": 3,
            "depends_on": ["design"]
        },
        {
            "name": "review",
            "agent": "reviewer_agent",
            "timeout": 120,
            "retries": 1,
            "depends_on": ["implementation"]
        }
    ],
    "error_handling": {
        "continue_on_error": False,
        "fallback_workflow": None,
        "max_total_retries": 10
    },
    "output": {
        "format": "structured",
        "include_agent_outputs": True,
        "save_to_file": True
    }
}
```

### Step 4: Implement Workflow Logic

```python
# workflows/your_workflow/workflow.py

from typing import Dict, Any, AsyncGenerator
import asyncio
from workflows.base_workflow import BaseWorkflow
from .config import WORKFLOW_CONFIG

class YourWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(WORKFLOW_CONFIG)
        self.context = {}
        
    async def execute(
        self, 
        requirements: str, 
        config: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the workflow"""
        
        # Merge configurations
        workflow_config = {**self.config, **(config or {})}
        
        # Initialize context
        self.context = {
            "requirements": requirements,
            "config": workflow_config,
            "results": {},
            "errors": []
        }
        
        # Execute phases
        for phase in workflow_config["phases"]:
            try:
                async for result in self._execute_phase(phase):
                    yield result
            except Exception as e:
                if not workflow_config["error_handling"]["continue_on_error"]:
                    raise
                self.context["errors"].append({
                    "phase": phase["name"],
                    "error": str(e)
                })
        
        # Final result
        yield {
            "type": "final_result",
            "status": "completed",
            "results": self.context["results"],
            "errors": self.context["errors"]
        }
    
    async def _execute_phase(
        self, 
        phase: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a single workflow phase"""
        
        phase_name = phase["name"]
        agent_name = phase["agent"]
        
        # Check dependencies
        for dep in phase.get("depends_on", []):
            if dep not in self.context["results"]:
                raise ValueError(f"Dependency {dep} not satisfied for {phase_name}")
        
        # Prepare agent request
        agent_request = self._prepare_agent_request(phase)
        
        # Execute with retries
        for attempt in range(phase.get("retries", 1)):
            try:
                yield {
                    "type": "phase_start",
                    "phase": phase_name,
                    "agent": agent_name,
                    "attempt": attempt + 1
                }
                
                # Run agent
                result = await self._run_agent_with_timeout(
                    agent_name,
                    agent_request,
                    phase.get("timeout", 300)
                )
                
                # Store result
                self.context["results"][phase_name] = result
                
                yield {
                    "type": "phase_complete",
                    "phase": phase_name,
                    "result": result
                }
                
                break  # Success, exit retry loop
                
            except Exception as e:
                if attempt == phase.get("retries", 1) - 1:
                    raise  # Last attempt, propagate error
                    
                yield {
                    "type": "phase_retry",
                    "phase": phase_name,
                    "error": str(e),
                    "attempt": attempt + 1
                }
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Step 5: Register Workflow

```python
# workflows/workflow_manager.py

from workflows.your_workflow.workflow import YourWorkflow

WORKFLOW_REGISTRY = {
    # ... existing workflows ...
    "your_workflow": YourWorkflow,
}
```

## Advanced Workflow Patterns

### 1. Parallel Execution

```python
async def _execute_parallel_phases(
    self, 
    phases: List[Dict[str, Any]]
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute multiple phases in parallel"""
    
    tasks = []
    for phase in phases:
        task = asyncio.create_task(self._execute_phase_async(phase))
        tasks.append((phase["name"], task))
    
    # Gather results
    for phase_name, task in tasks:
        try:
            result = await task
            yield {
                "type": "parallel_phase_complete",
                "phase": phase_name,
                "result": result
            }
        except Exception as e:
            yield {
                "type": "parallel_phase_error",
                "phase": phase_name,
                "error": str(e)
            }
```

### 2. Conditional Execution

```python
async def _execute_conditional_phase(
    self, 
    phase: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute phase based on conditions"""
    
    condition = phase.get("condition")
    if condition:
        # Evaluate condition
        if not self._evaluate_condition(condition):
            yield {
                "type": "phase_skipped",
                "phase": phase["name"],
                "reason": "Condition not met"
            }
            return
    
    # Execute phase normally
    async for result in self._execute_phase(phase):
        yield result

def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
    """Evaluate workflow conditions"""
    if condition["type"] == "result_contains":
        phase_result = self.context["results"].get(condition["phase"])
        return condition["value"] in str(phase_result)
    elif condition["type"] == "error_count":
        return len(self.context["errors"]) < condition["max_errors"]
    # Add more condition types as needed
    return True
```

### 3. Dynamic Agent Selection

```python
async def _select_agent_dynamically(
    self, 
    phase: Dict[str, Any]
) -> str:
    """Select agent based on runtime conditions"""
    
    if phase.get("dynamic_agent"):
        selector = phase["dynamic_agent"]
        
        if selector["type"] == "based_on_input":
            # Select based on input characteristics
            if "API" in self.context["requirements"]:
                return "api_specialist_agent"
            elif "UI" in self.context["requirements"]:
                return "ui_specialist_agent"
            else:
                return "general_coder_agent"
                
        elif selector["type"] == "load_balanced":
            # Select least loaded agent
            return await self._get_least_loaded_agent(selector["agents"])
    
    return phase["agent"]  # Default agent
```

### 4. Checkpoint and Resume

```python
class CheckpointableWorkflow(BaseWorkflow):
    async def execute_with_checkpoint(
        self, 
        requirements: str,
        checkpoint_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with checkpoint support"""
        
        # Load checkpoint if provided
        if checkpoint_id:
            self.context = await self._load_checkpoint(checkpoint_id)
            start_phase = self._find_resume_phase()
        else:
            self.context = self._initialize_context(requirements)
            start_phase = 0
        
        # Execute from checkpoint
        phases = self.config["phases"][start_phase:]
        for phase in phases:
            async for result in self._execute_phase(phase):
                yield result
                
            # Save checkpoint after each phase
            await self._save_checkpoint()
    
    async def _save_checkpoint(self) -> str:
        """Save workflow state"""
        checkpoint_id = f"checkpoint_{self.context['session_id']}"
        # Save to persistent storage
        await save_to_storage(checkpoint_id, self.context)
        return checkpoint_id
    
    async def _load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Load workflow state"""
        return await load_from_storage(checkpoint_id)
```

## Workflow Testing

### 1. Unit Tests

```python
# tests/unit/workflows/test_your_workflow.py

import pytest
from workflows.your_workflow.workflow import YourWorkflow

@pytest.mark.asyncio
async def test_workflow_initialization():
    workflow = YourWorkflow()
    assert workflow.config["name"] == "your_workflow"
    assert len(workflow.config["phases"]) == 4

@pytest.mark.asyncio
async def test_phase_execution():
    workflow = YourWorkflow()
    phase = workflow.config["phases"][0]
    
    results = []
    async for result in workflow._execute_phase(phase):
        results.append(result)
    
    assert len(results) >= 2  # start and complete events
    assert results[0]["type"] == "phase_start"
    assert results[-1]["type"] == "phase_complete"
```

### 2. Integration Tests

```python
# tests/integration/workflows/test_your_workflow_integration.py

@pytest.mark.asyncio
async def test_full_workflow_execution():
    workflow = YourWorkflow()
    requirements = "Create a simple calculator API"
    
    results = []
    async for result in workflow.execute(requirements):
        results.append(result)
    
    # Verify all phases executed
    phase_names = [r["phase"] for r in results if r["type"] == "phase_complete"]
    assert "planning" in phase_names
    assert "design" in phase_names
    assert "implementation" in phase_names
    assert "review" in phase_names
    
    # Verify final result
    final_result = results[-1]
    assert final_result["type"] == "final_result"
    assert final_result["status"] == "completed"
```

### 3. Mock Testing

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_workflow_with_mocked_agents():
    workflow = YourWorkflow()
    
    # Mock agent execution
    with patch.object(workflow, '_run_agent_with_timeout') as mock_agent:
        mock_agent.return_value = {"status": "success", "output": "mocked"}
        
        results = []
        async for result in workflow.execute("test requirements"):
            results.append(result)
        
        # Verify agents were called
        assert mock_agent.call_count == 4  # One per phase
```

## Performance Optimization

### 1. Caching Agent Results

```python
from functools import lru_cache
import hashlib

class CachedWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        self.cache = {}
    
    async def _run_agent_cached(
        self, 
        agent_name: str, 
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run agent with caching"""
        
        # Generate cache key
        cache_key = self._generate_cache_key(agent_name, request)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Run agent
        result = await self._run_agent(agent_name, request)
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def _generate_cache_key(self, agent_name: str, request: Dict[str, Any]) -> str:
        """Generate deterministic cache key"""
        content = f"{agent_name}:{json.dumps(request, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
```

### 2. Resource Pooling

```python
class PooledWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        self.agent_pool = self._create_agent_pool()
    
    def _create_agent_pool(self) -> Dict[str, List[Any]]:
        """Create pool of agent instances"""
        pool = {}
        for agent_name in self.config["agents"]:
            # Create multiple instances
            pool[agent_name] = [
                self._create_agent(agent_name) 
                for _ in range(3)
            ]
        return pool
    
    async def _get_agent_from_pool(self, agent_name: str) -> Any:
        """Get available agent from pool"""
        # Implement round-robin or least-recently-used selection
        return self.agent_pool[agent_name][0]
```

## Monitoring and Observability

### 1. Workflow Metrics

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WorkflowMetrics:
    workflow_name: str
    start_time: datetime
    end_time: datetime = None
    phase_durations: Dict[str, float] = None
    error_count: int = 0
    retry_count: int = 0
    
    def calculate_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

class MetricsWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        self.metrics = None
    
    async def execute(self, requirements: str) -> AsyncGenerator[Dict[str, Any], None]:
        self.metrics = WorkflowMetrics(
            workflow_name=self.config["name"],
            start_time=datetime.now(),
            phase_durations={}
        )
        
        try:
            async for result in super().execute(requirements):
                # Track phase durations
                if result["type"] == "phase_complete":
                    self.metrics.phase_durations[result["phase"]] = result.get("duration", 0)
                yield result
        finally:
            self.metrics.end_time = datetime.now()
            await self._report_metrics()
```

### 2. Distributed Tracing

```python
import opentelemetry
from opentelemetry import trace

class TracedWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        self.tracer = trace.get_tracer(__name__)
    
    async def _execute_phase(self, phase: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute phase with tracing"""
        with self.tracer.start_as_current_span(f"phase_{phase['name']}") as span:
            span.set_attribute("phase.name", phase["name"])
            span.set_attribute("phase.agent", phase["agent"])
            
            try:
                async for result in super()._execute_phase(phase):
                    yield result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
```

## Best Practices

1. **Keep Workflows Simple**: Each workflow should have a clear, single purpose
2. **Use Configuration**: Make workflows configurable rather than hardcoding values
3. **Handle Errors Gracefully**: Always plan for failure scenarios
4. **Document Thoroughly**: Include examples and use cases
5. **Test Extensively**: Cover unit, integration, and edge cases
6. **Monitor Performance**: Track metrics and optimize bottlenecks
7. **Version Workflows**: Use semantic versioning for workflow changes
8. **Maintain Backwards Compatibility**: Support old workflow versions when possible

## Related Documentation

- [Architecture Overview](architecture/README.md)
- [Agent Development](agent-development.md)
- [Testing Guide](testing-guide.md)
- [Workflow Configuration](../reference/workflow-configuration.md)