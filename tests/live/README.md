# Live Test Infrastructure for MVP Incremental TDD Workflow

## Overview

This directory contains a comprehensive live testing framework that validates the MVP Incremental TDD workflow using real execution instead of mocks. The tests progressively increase in complexity from simple calculators to advanced distributed systems.

## Test Levels

### 1. **Simple Tests** (< 30 seconds each)
- Basic calculator implementation
- Hello World REST API
- String manipulation utilities

### 2. **Moderate Tests** (1-2 minutes each)
- TODO list REST API with CRUD operations
- CSV/JSON data processing
- Linked list data structure

### 3. **Complex Tests** (3-5 minutes each)
- Blog API with authentication and database
- Task scheduling system with concurrency
- Multi-level caching system

### 4. **Advanced Tests** (5-10 minutes each)
- Microservice orchestration system
- Distributed task queue (Celery-like)

### 5. **Edge Cases** (Variable duration)
- Resilient API with chaos testing
- Unicode text processing
- Concurrent state management

## Quick Start

### Prerequisites
- Python 3.9+
- Docker installed and running
- Orchestrator server running (`python orchestrator/orchestrator_agent.py`)

### Running Tests

#### Quick Verification
```bash
# Run a quick test to verify setup
python tests/live/run_live_tests.py --quick
```

#### Interactive Mode
```bash
# Choose tests interactively
python tests/live/run_live_tests.py
```

#### Run Specific Levels
```bash
# Run simple tests only
python tests/live/run_live_tests.py --levels simple

# Run simple and moderate tests
python tests/live/run_live_tests.py --levels simple moderate

# Run all tests (warning: takes ~30+ minutes)
python tests/live/run_live_tests.py --all
```

#### Parallel Execution
```bash
# Run tests in parallel for faster execution
python tests/live/run_live_tests.py --levels simple moderate --parallel
```

## Test Structure

```
tests/live/
├── test_runner.py           # Main test orchestration engine
├── test_categories.py       # Test definitions and complexity levels
├── test_fixtures.py         # Helper utilities and data generators
├── run_live_tests.py        # CLI entry point
├── level1_simple/           # Simple test implementations
│   └── test_calculator.py
├── level2_moderate/         # Moderate test implementations
│   └── test_todo_api.py
└── outputs/                 # Test execution results
    └── session_*/           # Timestamped session outputs
```

## How It Works

1. **Test Definition**: Each test is defined in `test_categories.py` with:
   - Requirements specification
   - Expected files to generate
   - Validation criteria
   - Docker-based execution tests

2. **Workflow Execution**: Tests use the actual `execute_workflow()` function to:
   - Generate code using the TDD workflow
   - Follow RED-YELLOW-GREEN phases
   - Produce real implementation files

3. **Validation**: Each test validates:
   - All expected files are generated
   - Code passes its own tests in Docker
   - API endpoints work correctly (for web services)
   - Edge cases are handled properly

4. **Performance Monitoring**: Tests track:
   - Execution time per phase
   - Resource usage
   - Success/failure rates
   - Generated code metrics

## Test Results

Results are saved in the `outputs/` directory with:
- `test_results.json`: Machine-readable results
- `test_report.md`: Human-readable markdown report
- Generated code artifacts
- Performance metrics

## Writing New Tests

To add a new test:

1. Add test definition to `TEST_CATALOG` in `test_categories.py`
2. Specify requirements, validations, and expected behavior
3. Create test implementation file if needed for complex scenarios
4. Run the test using the test runner

Example test definition:
```python
{
    "name": "my_test",
    "file": "test_my_test.py",
    "requirements": "Create a ... using TDD that ...",
    "workflow_type": "mvp_incremental",
    "timeout": 180,
    "validations": [
        {"type": "file_exists", "path": "generated/main.py"},
        {"type": "docker_test", "image": "python:3.9", "command": "pytest"}
    ]
}
```

## Troubleshooting

### Docker Issues
- Ensure Docker daemon is running: `docker ps`
- Check Docker permissions: `docker run hello-world`

### Test Failures
- Check session output directory for detailed logs
- Review generated code in `outputs/session_*/generated/`
- Ensure orchestrator server is running

### Performance Issues
- Use `--parallel` flag for faster execution
- Run specific test levels instead of all tests
- Monitor Docker resource usage

## CI/CD Integration

For continuous integration:
```bash
# Run basic tests with CI-friendly output
python tests/live/run_live_tests.py --levels simple moderate --quiet

# Check exit code
if [ $? -eq 0 ]; then
    echo "Tests passed"
else
    echo "Tests failed"
fi
```

## Advanced Usage

### Custom Output Directory
```bash
python tests/live/run_live_tests.py --levels simple --output-dir /tmp/test_results
```

### List Available Tests
```bash
python tests/live/run_live_tests.py --list
```

### Running Individual Test Files
```bash
# Run calculator test directly
python tests/live/level1_simple/test_calculator.py

# Run TODO API test directly  
python tests/live/level2_moderate/test_todo_api.py
```

## Future Enhancements

- [ ] Add test result visualization dashboard
- [ ] Implement test result comparison between runs
- [ ] Add code quality metrics (complexity, coverage)
- [ ] Create test templates for common patterns
- [ ] Add distributed test execution support