# Integration Tests

This directory contains integration tests that verify end-to-end functionality of workflows.

## Tests

- `test_incremental_workflow.py` - Tests the complete incremental workflow with a scientific calculator project
  - Creates a multi-feature calculator API specification
  - Runs through the entire incremental workflow
  - Verifies code generation and saves results

- `test_realtime_output.py` - Tests the real-time agent output display functionality
  - Demonstrates step-by-step agent interactions
  - Shows how agent inputs/outputs are displayed in real-time

## Running Tests

```bash
# Make sure the orchestrator is running first:
python orchestrator/orchestrator_agent.py

# Then run individual tests:
python tests/integration/test_incremental_workflow.py
python tests/integration/test_realtime_output.py

# Or using pytest
pytest tests/integration/
```

## Test Outputs

Test results are saved to `tests/outputs/` with timestamps for debugging and analysis.