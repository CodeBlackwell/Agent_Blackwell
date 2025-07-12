# Testing Patterns for Multi-Agent Orchestrator

This document provides comprehensive testing patterns and guidelines for the multi-agent orchestrator system, established during Phase 1 of Operation Moonlight.

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Structure](#test-structure)
4. [Unit Testing Patterns](#unit-testing-patterns)
5. [Integration Testing Patterns](#integration-testing-patterns)
6. [Mocking Strategies](#mocking-strategies)
7. [Performance Testing](#performance-testing)
8. [Error Testing](#error-testing)
9. [Best Practices](#best-practices)
10. [Templates and Examples](#templates-and-examples)

## Overview

The testing framework for the multi-agent orchestrator follows a layered approach:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test workflow execution and agent interactions
- **Performance Tests**: Ensure workflows meet timing requirements
- **Error Tests**: Verify proper error handling and recovery

## Testing Philosophy

### Key Principles

1. **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it
2. **Isolation**: Each test should be independent and not rely on other tests
3. **Clarity**: Test names should clearly describe what is being tested
4. **Coverage**: Aim for >90% code coverage with meaningful tests
5. **Speed**: Unit tests should run quickly (<100ms per test)

### Test Pyramid

```
        /\
       /  \  E2E Tests (5%)
      /----\
     /      \ Integration Tests (25%)
    /--------\
   /          \ Unit Tests (70%)
  /____________\
```

## Test Structure

### Directory Layout

```
tests/
├── unit/
│   ├── workflows/
│   │   ├── test_individual_workflow.py
│   │   └── test_[workflow_name]_workflow.py
│   ├── agents/
│   │   └── test_[agent_name]_agent.py
│   └── core/
│       ├── test_exceptions.py
│       └── test_logging.py
├── integration/
│   ├── workflows/
│   │   └── test_[workflow_name]_integration.py
│   └── api/
│       └── test_api_integration.py
├── fixtures/
│   ├── workflow_fixtures.py
│   └── agent_fixtures.py
├── utils/
│   └── workflow_test_helpers.py
└── templates/
    └── workflow_test_template.py
```

### Test Naming Conventions

- Test files: `test_[module_name].py`
- Test classes: `Test[ClassName]`
- Test methods: `test_[what_is_being_tested]`

Examples:
- `test_execute_planning_step_success`
- `test_workflow_timeout_handling`
- `test_retry_logic_on_agent_failure`

## Unit Testing Patterns

### Pattern 1: Testing Workflow Execution

```python
@pytest.mark.asyncio
async def test_workflow_execution_success(self, executor, mock_input_data, mock_tracer):
    """Test successful workflow execution."""
    # Arrange
    mock_result = {"content": "Success", "success": True}
    
    with patch('core.migration.run_team_member_with_tracking',
              new_callable=AsyncMock, return_value=mock_result):
        
        # Act
        results, report = await executor.execute(mock_input_data, mock_tracer)
        
        # Assert
        assert len(results) == 1
        assert results[0].output == str(mock_result)
        mock_tracer.complete_execution.assert_called_once()
```

### Pattern 2: Testing Error Handling

```python
@pytest.mark.asyncio
async def test_agent_error_handling(self, executor, mock_input_data, mock_tracer):
    """Test proper handling of agent errors."""
    # Arrange
    error = AgentError("Agent failed", "test_agent")
    
    with patch('core.migration.run_team_member_with_tracking',
              side_effect=error):
        
        # Act & Assert
        with pytest.raises(WorkflowError) as exc_info:
            await executor.execute(mock_input_data, mock_tracer)
        
        assert "Agent failed" in str(exc_info.value)
        assert exc_info.value.workflow_type == "Individual"
```

### Pattern 3: Testing Configuration

```python
def test_configuration_loading(self):
    """Test configuration is properly loaded."""
    # Arrange
    mock_config = {
        "timeout": 1200,
        "steps": {"planning": {"timeout": 600}}
    }
    
    with patch('get_config_manager') as mock_cm:
        mock_cm.return_value.get_workflow_config.return_value = mock_config
        
        # Act
        executor = WorkflowExecutor()
        
        # Assert
        assert executor.workflow_config == mock_config
```

## Integration Testing Patterns

### Pattern 1: End-to-End Workflow Testing

```python
@pytest.mark.asyncio
async def test_full_workflow_execution(self, setup_infrastructure, mock_agent_responses):
    """Test complete workflow from start to finish."""
    for step in ["planning", "design", "implementation"]:
        # Arrange
        input_data = CodingTeamInput(
            requirements="Build calculator API",
            step_type=step
        )
        
        with patch('core.migration.run_team_member_with_tracking',
                  return_value=mock_agent_responses[step]):
            
            # Act
            executor = IndividualWorkflowExecutor()
            results, report = await executor.execute(input_data)
            
            # Assert
            assert len(results) == 1
            assert report is not None
```

### Pattern 2: Performance Testing

```python
@pytest.mark.asyncio
async def test_workflow_performance(self, setup_infrastructure):
    """Test workflow completes within time limits."""
    # Arrange
    async def fast_agent(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"content": "Fast response", "success": True}
    
    with patch('core.migration.run_team_member_with_tracking',
              side_effect=fast_agent):
        
        # Act
        start = time.time()
        executor = WorkflowExecutor()
        await executor.execute(input_data)
        duration = time.time() - start
        
        # Assert
        assert duration < 1.0  # Should complete in under 1 second
```

## Mocking Strategies

### Strategy 1: Mock Agent Responses

```python
@pytest.fixture
def mock_agent_runner():
    """Create a mock agent runner with predefined responses."""
    responses = {
        "planner_agent": {"content": "Plan created", "success": True},
        "coder_agent": {"content": "Code implemented", "success": True}
    }
    
    async def mock_run(agent_name, requirements, context):
        return responses.get(agent_name, {"content": "Default", "success": True})
    
    return mock_run
```

### Strategy 2: Mock Tracer

```python
@pytest.fixture
def mock_tracer():
    """Create a mock workflow tracer."""
    tracer = Mock(spec=WorkflowExecutionTracer)
    tracer.execution_id = "test_123"
    tracer.start_step = Mock(return_value="step_123")
    tracer.complete_step = Mock()
    tracer.complete_execution = Mock()
    tracer.get_report = Mock(return_value=Mock())
    return tracer
```

### Strategy 3: Partial Mocking

```python
def test_with_partial_mock(self):
    """Test with partial mocking of dependencies."""
    with patch.object(WorkflowExecutor, '_run_agent') as mock_run:
        # Only mock the agent execution, leave rest intact
        mock_run.return_value = "Mocked result"
        
        executor = WorkflowExecutor()
        result = executor.process_step("planning")
        
        assert result == "Mocked result"
```

## Performance Testing

### Benchmark Pattern

```python
from tests.utils.workflow_test_helpers import PerformanceBenchmark

@pytest.mark.asyncio
async def test_workflow_performance_benchmark(self):
    """Benchmark workflow performance."""
    with PerformanceBenchmark("Individual Workflow") as benchmark:
        executor = WorkflowExecutor()
        await executor.execute(input_data)
    
    benchmark.assert_faster_than(5.0)  # Must complete in 5 seconds
```

### Load Testing Pattern

```python
@pytest.mark.asyncio
async def test_concurrent_workflow_execution(self):
    """Test multiple workflows running concurrently."""
    tasks = []
    
    for i in range(10):
        input_data = CodingTeamInput(
            requirements=f"Test {i}",
            workflow_type="individual"
        )
        tasks.append(executor.execute(input_data))
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    assert len(results) == 10
    assert duration < 30.0  # All should complete within 30 seconds
```

## Error Testing

### Pattern 1: Timeout Testing

```python
@pytest.mark.asyncio
async def test_timeout_handling(self, executor):
    """Test timeout is properly handled."""
    async def slow_agent(*args):
        await asyncio.sleep(10)
    
    executor.workflow_config["timeout"] = 0.1
    
    with patch('run_team_member_with_tracking', side_effect=slow_agent):
        with pytest.raises(AgentTimeoutError):
            await executor.execute(input_data)
```

### Pattern 2: Retry Testing

```python
@pytest.mark.asyncio
async def test_retry_on_transient_failure(self, executor):
    """Test retry logic on transient failures."""
    call_count = 0
    
    async def flaky_agent(*args):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return {"content": "Success", "success": True}
    
    with patch('run_team_member_with_tracking', side_effect=flaky_agent):
        results, _ = await executor.execute(input_data)
        
        assert len(results) == 1
        assert call_count == 3
```

## Best Practices

### 1. Use Fixtures Effectively

```python
@pytest.fixture
def create_input_data():
    """Factory fixture for creating test input data."""
    def _create(requirements="Test", workflow_type="individual", **kwargs):
        return CodingTeamInput(
            requirements=requirements,
            workflow_type=workflow_type,
            **kwargs
        )
    return _create
```

### 2. Test Data Builders

```python
class TestDataBuilder:
    """Builder for creating test data."""
    
    @staticmethod
    def create_agent_response(content="Test", success=True, **kwargs):
        return {
            "content": content,
            "success": success,
            "messages": [],
            **kwargs
        }
```

### 3. Assertion Helpers

```python
def assert_workflow_completed_successfully(results, report):
    """Assert workflow completed with expected results."""
    assert len(results) > 0
    assert all(r.output for r in results)
    assert report is not None
    if hasattr(report, 'status'):
        assert report.status == 'completed'
```

### 4. Cleanup and Isolation

```python
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Ensure clean state after each test."""
    yield
    # Cleanup code here
    error_handler = get_error_handler()
    error_handler.clear_history()
```

## Templates and Examples

### Workflow Test Template

See `/tests/templates/workflow_test_template.py` for a complete template that includes:

- Basic test structure
- Common test cases (success, timeout, error, retry)
- Fixture setup
- Integration test patterns

### Quick Start Example

```python
# tests/unit/workflows/test_my_workflow.py
import pytest
from workflows.my_workflow import MyWorkflowExecutor

class TestMyWorkflow:
    @pytest.fixture
    def executor(self):
        return MyWorkflowExecutor()
    
    @pytest.mark.asyncio
    async def test_basic_execution(self, executor):
        # Your test here
        pass
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=workflows --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/workflows/test_individual_workflow.py
```

### Run with verbose output
```bash
pytest -v
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

## Continuous Improvement

1. **Review test failures**: Don't just fix the code, improve the test
2. **Add tests for bugs**: Every bug fix should include a test
3. **Refactor tests**: Keep tests clean and maintainable
4. **Monitor coverage**: Maintain >90% coverage
5. **Performance regression**: Track test execution times

---

This testing framework provides a solid foundation for ensuring the reliability and quality of the multi-agent orchestrator system. Follow these patterns and adapt them as needed for your specific workflows.