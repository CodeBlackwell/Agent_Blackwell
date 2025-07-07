# TDD Workflow Tests

This directory contains tests specific to the Test-Driven Development (TDD) workflow implementation.

## Overview

These tests validate the TDD workflow functionality, including:
- Red-Green-Refactor cycle implementation
- Test-first development approach
- Single directory generation per workflow run
- Integration with all agents in TDD mode

## Test Files

### test_tdd_integration.py
Complete integration test for the TDD workflow with file management. Tests the full flow from test writing through implementation with actual test execution.

**Key Features Tested:**
- File management integration
- Project directory coordination
- Test execution in RED and GREEN phases
- TDD cycle iterations

**Usage:**
```bash
python tests/tdd/test_tdd_integration.py
```

### test_tdd_single_directory.py
Verifies that the TDD workflow creates only one directory per run, even with multiple iterations.

**Key Features Tested:**
- Single session directory creation
- Directory reuse across TDD iterations
- Project path persistence
- File accumulation in one location

**Usage:**
```bash
python tests/tdd/test_tdd_single_directory.py
```

### test_tdd_enhanced.py
Tests the enhanced TDD workflow features with comprehensive validation.

**Key Features Tested:**
- Enhanced TDD cycle management
- Test failure detection
- Implementation iteration tracking
- Coverage reporting

**Usage:**
```bash
python tests/tdd/test_tdd_enhanced.py
```

## Prerequisites

1. **Orchestrator Running**: The orchestrator must be running on port 8080
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

2. **Test Framework**: Pytest must be installed for test execution
   ```bash
   pip install pytest
   ```

3. **Environment**: Virtual environment should be activated
   ```bash
   source .venv/bin/activate
   ```

## Running All TDD Tests

Using the unified runner:
```bash
python run.py test tdd
```

Or directly:
```bash
python -m pytest tests/tdd/ -v
```

## Test Output

Test results and artifacts are saved to:
- `generated/` - Generated project directories
- `tests/outputs/` - Test execution logs and reports
- Session-specific directories with timestamps

## Common Issues

1. **"Orchestrator not running"**: Start the orchestrator first
2. **"Module not found"**: Ensure virtual environment is activated
3. **"Test runner not found"**: Install pytest with `pip install pytest`

## Adding New TDD Tests

When adding new TDD workflow tests:
1. Follow the naming convention: `test_tdd_*.py`
2. Use the standard test structure with async functions
3. Import from `workflows.tdd.tdd_workflow`
4. Add the test to the test runner configuration if needed