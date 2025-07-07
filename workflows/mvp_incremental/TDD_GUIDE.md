# MVP Incremental TDD Workflow Guide

## Overview

The MVP Incremental TDD (Test-Driven Development) workflow enhances the standard MVP incremental workflow by implementing each feature using the TDD red-green-refactor cycle:

1. **Red Phase**: Write tests first that define the expected behavior (tests fail)
2. **Green Phase**: Write minimal code to make tests pass
3. **Refactor Phase**: Improve code quality while keeping tests green

## Key Benefits

- **Better Design**: Tests drive the design, resulting in more modular code
- **Built-in Documentation**: Tests serve as living documentation
- **Confidence**: Each feature is tested before moving to the next
- **Progress Tracking**: Clear red/green states show real progress
- **Reduced Debugging**: Issues are caught immediately

## How It Works

### Workflow Phases

1. **Planning Phase**: Understand requirements and create project plan
2. **Design Phase**: Create technical design with clear features
3. **TDD Implementation Phase**: For each feature:
   - Write tests that define expected behavior
   - Run tests to ensure they fail (red)
   - Implement code to make tests pass (green)
   - Refactor if needed (optional)
   - Validate implementation
4. **Integration Verification**: Ensure all features work together

### Progress Tracking

The workflow provides detailed progress tracking with TDD-specific states:

- `WRITING_TESTS` - Test writer agent is creating tests
- `TESTS_WRITTEN` - Tests have been written
- `TESTS_FAILING` - Tests are running and failing (expected - red phase)
- `IMPLEMENTING` - Coder agent is implementing to pass tests
- `TESTS_PASSING` - Tests are now passing (green phase)
- `REFACTORING` - Code is being refactored (optional)

### Test Management

The workflow includes a Test Accumulator that:
- Organizes tests by feature
- Maintains test execution order based on dependencies
- Generates combined test suites
- Provides test coverage configuration
- Creates test runner scripts

## Usage

### Basic Usage

```python
from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow

# Create input with TDD workflow type
input_data = CodingTeamInput(
    requirements="Create a calculator with add, subtract, multiply, divide functions",
    workflow_type="mvp_incremental_tdd"
)

# Execute workflow
results, report = await execute_workflow(input_data)
```

### Using the Demo Script

```bash
# With TDD enabled (default for MVP incremental)
python demo_mvp_incremental.py --preset calculator --tdd

# Or specify the TDD workflow directly
python demo_mvp_incremental.py --workflow mvp_incremental_tdd --requirements "Your requirements"
```

## Configuration

### Enable/Disable TDD

While the TDD workflow defaults to using TDD, you can control it through metadata:

```python
input_data = CodingTeamInput(
    requirements="...",
    workflow_type="mvp_incremental_tdd",
    metadata={"use_tdd": False}  # Falls back to standard implementation
)
```

### Test Configuration

The workflow respects test execution settings:

```python
input_data = CodingTeamInput(
    requirements="...",
    workflow_type="mvp_incremental_tdd",
    run_tests=True,  # Enable test execution
    metadata={
        "test_timeout": 30,  # Test execution timeout
        "coverage_minimum": 80  # Minimum coverage requirement
    }
)
```

## Output Structure

The TDD workflow generates:

1. **Implementation Files**: The actual code files
2. **Test Files**: Organized test files for each feature
3. **Test Runner Script**: `test_runner.py` for executing tests
4. **Test Report**: `TEST_REPORT.md` with test suite summary
5. **Combined Tests**: `tests/all_tests.py` with all tests

Example output structure:
```
generated/
├── calculator.py          # Implementation
├── tests/
│   ├── test_add.py       # Feature 1 tests
│   ├── test_subtract.py  # Feature 2 tests
│   └── all_tests.py      # Combined test suite
├── test_runner.py        # Test execution script
└── TEST_REPORT.md        # Test suite report
```

## Metrics and Reporting

The workflow provides enhanced metrics including:

- Features with tests written
- Features with passing tests
- Total test files and functions
- Average code coverage
- Test execution times
- Red/green phase durations

## Best Practices

1. **Write Minimal Tests**: Start with the simplest test that defines behavior
2. **One Feature at a Time**: Complete each feature's TDD cycle before moving on
3. **Keep Tests Fast**: Unit tests should run quickly for rapid feedback
4. **Test Behavior, Not Implementation**: Focus on what, not how
5. **Refactor When Green**: Only refactor when all tests are passing

## Example: Calculator with TDD

```python
# Requirements
requirements = """
Create a calculator module with:
1. Add function - adds two numbers
2. Subtract function - subtracts second from first
3. Error handling for invalid inputs
"""

# The workflow will:
# 1. Write tests for add function
# 2. Run tests (they fail - red)
# 3. Implement add function
# 4. Run tests (they pass - green)
# 5. Move to subtract function
# 6. Repeat TDD cycle
```

## Troubleshooting

### Tests Not Running
- Ensure `run_tests` is set to True in input data
- Check that test files are being generated correctly
- Verify Python test framework (pytest) is installed

### Tests Passing on First Run
- This indicates tests may not be specific enough
- Review test writer output to ensure tests check actual behavior
- Consider adding more specific test cases

### Low Test Coverage
- The workflow tracks coverage when available
- Use coverage tools in your test environment
- Consider adding integration tests for better coverage

## Advanced Features

### Custom Test Frameworks
The test writer agent adapts to different languages and frameworks:
- Python: pytest, unittest
- JavaScript: Jest, Mocha
- Java: JUnit
- Go: testing package

### Parallel Test Execution
For larger projects, tests can be configured to run in parallel:
```python
metadata={"parallel_tests": True, "test_workers": 4}
```

### Test Categories
Tests are automatically categorized as:
- Unit tests (isolated feature tests)
- Integration tests (cross-feature tests)
- End-to-end tests (full workflow tests)

## Migration from Standard MVP Incremental

To migrate existing MVP incremental workflows to TDD:

1. Change workflow type to `mvp_incremental_tdd`
2. No other changes needed - the workflow handles the rest
3. Existing validations still run after tests pass
4. Review integration continues to work as before

## Future Enhancements

Planned improvements include:
- Mutation testing support
- Property-based testing integration
- Test performance tracking
- Automatic test generation from specifications
- Visual test coverage reports