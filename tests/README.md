# Test Organization

This directory contains all tests for the multi-agent system, organized by test type.

## Directory Structure

```
tests/
├── unit/               # Unit tests for individual components
│   └── incremental/    # Tests for incremental workflow components
│       ├── test_feature_parser.py    # Feature parser tests
│       └── ...
│
├── integration/        # Integration tests for workflows
│   ├── test_incremental_workflow.py  # Full incremental workflow test
│   ├── test_realtime_output.py       # Real-time output display test
│   └── ...
│
├── debug/              # Debug utilities
│   └── debug_incremental_parser.py   # Parser debugging tool
│
└── outputs/            # Test execution results (auto-generated)
    └── ...
```

## Running Tests

### Using the Unified Runner (Recommended)
```bash
# Run all tests
python run.py test all

# Run specific category
python run.py test unit
python run.py test integration
python run.py test workflow

# Run with options
python run.py test all -v    # Verbose output
python run.py test all -p    # Parallel execution
python run.py test unit       # Quick tests only
```

### Running Individual Tests
```bash
# Unit tests
python tests/unit/incremental/test_feature_parser.py

# Integration tests (ensure orchestrator is running first)
python orchestrator/orchestrator_agent.py  # In one terminal
python tests/integration/test_incremental_workflow.py  # In another

# Debug scripts
python tests/debug/debug_incremental_parser.py
```

## Test Categories

- **Unit Tests** (`tests/unit/`): Fast, isolated tests for individual components
- **Integration Tests** (`tests/integration/`): End-to-end workflow tests
- **Debug Scripts** (`tests/debug/`): Utilities for troubleshooting issues
- **Workflow Tests** (`test_workflows.py`): Comprehensive workflow validation
- **Agent Tests** (`run_agent_tests.py`): Individual agent functionality tests
- **Executor Tests** (`test_executor_*.py`): Code execution validation

## Test Outputs

All test results are saved to `tests/outputs/` with timestamps for analysis:
- Session logs: `tests/outputs/session_[timestamp]/`
- Results JSON: `tests/outputs/[test_name]/results_[timestamp].json`
- Generated code: `generated/app_generated_[timestamp]/`

## Adding New Tests

1. **Unit Tests**: Add to appropriate subdirectory in `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/`
3. **Update run.py**: Add new test categories if needed
4. **Follow naming convention**: `test_*.py` for test files
5. **Use appropriate imports**: Update sys.path relative to test location