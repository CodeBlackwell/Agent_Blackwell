# Flagship TDD Orchestrator

A demonstration of Test-Driven Development (TDD) using a custom-built orchestrator that manages the RED-YELLOW-GREEN phases automatically.

## Overview

The Flagship TDD Orchestrator showcases a clean implementation of TDD principles with:

- 🔴 **RED Phase**: Automatically writes failing tests based on requirements
- 🟡 **YELLOW Phase**: Generates minimal code to make tests pass
- 🟢 **GREEN Phase**: Runs tests and validates all are passing

## Architecture

```
Flagship/
├── agents/                  # Specialized agents for each phase
│   ├── test_writer_flagship.py    # RED: Writes failing tests
│   ├── coder_flagship.py          # YELLOW: Writes minimal code
│   └── test_runner_flagship.py    # GREEN: Runs and validates tests
├── models/                  # Data models and state management
│   └── flagship_models.py         # TDD workflow models
├── workflows/               # Workflow coordination
│   └── flagship_workflow.py       # TDD workflow management
├── configs/                 # Configuration presets
│   └── flagship_config.py         # Workflow configurations
├── generated/               # Output directory for generated code
└── flagship_orchestrator.py # Main orchestrator
```

## Quick Start

### Run the Calculator Example

```bash
# Run the pre-configured calculator example
python Flagship/example_calculator.py

# Run in interactive mode
python Flagship/example_calculator.py --interactive
```

### Direct Usage

```python
import asyncio
from Flagship.workflows.flagship_workflow import run_simple_tdd

async def main():
    requirements = "Create a function to validate email addresses"
    state = await run_simple_tdd(requirements)
    print(f"Success: {state.all_tests_passing}")

asyncio.run(main())
```

## Key Features

### Phase Management
- Automatic phase transitions based on test results
- Clear visual feedback with color-coded output
- Configurable iteration limits and timeouts

### Test-First Development
- Enforces writing tests before implementation
- Validates that tests fail before writing code
- Ensures minimal implementation to pass tests

### Real-Time Feedback
- Streaming output from each agent
- Progress indicators for each phase
- Detailed test execution results

### Configuration Options
- **Quick**: Fast iterations for simple tasks
- **Default**: Balanced for most use cases  
- **Comprehensive**: Thorough testing with more iterations
- **Demo**: Optimized for examples and demonstrations

## Example Output

```
🚀 Starting TDD Workflow
================================================================================

Requirements: Create a simple calculator with add, subtract, multiply, and divide operations

================================================================================
📍 Iteration 1
================================================================================

🔴 Entering RED Phase: Writing failing tests...
🔴 RED Phase: Writing failing tests for requirements...
Requirements: Create a simple calculator...

Test Plan:
- Test Categories: basic_operations, edge_cases, error_handling
- Number of Tests: 8
- Edge Cases: division by zero, invalid input types

Generated Test Code:
```python
import pytest
from calculator import Calculator
...
```

→→→→→→→→→→→→→→→→→→
Phase Transition: RED → YELLOW
Reason: Tests written successfully
→→→→→→→→→→→→→→→→→→

🟡 Entering YELLOW Phase: Writing minimal implementation...
...

🟢 Entering GREEN Phase: Running tests...
...

✅ All tests passed! Ready to proceed.
```

## Workflow States

The orchestrator tracks detailed state throughout the TDD cycle:

- Current phase and phase history
- Test results for each iteration
- Generated test and implementation code
- Success metrics and timing information

States are automatically saved to JSON for analysis and debugging.

## Extending the System

### Adding New Test Frameworks

Modify `flagship_config.py` to support different test frameworks:

```python
TDDWorkflowConfig(
    test_framework="unittest",  # or "nose", "doctest"
    ...
)
```

### Custom Phase Logic

Extend the agents in `agents/` to add custom behavior:

```python
class TestWriterFlagship:
    async def write_tests(self, requirements: str):
        # Add custom test generation logic
        ...
```

### New Workflow Patterns

Create variations of the TDD workflow in `workflows/`:

```python
async def run_bdd_workflow(requirements: str):
    # Behavior-Driven Development variant
    ...
```

## Best Practices

1. **Start with Clear Requirements**: The better the requirements, the better the generated tests
2. **Review Generated Tests**: Ensure tests cover all edge cases
3. **Iterate When Needed**: Use multiple iterations for complex features
4. **Monitor Progress**: Watch the real-time output to understand the process

## Phase 1 Status

This is Phase 1 of the Flagship TDD Orchestrator, focusing on:
- ✅ Core RED-YELLOW-GREEN cycle
- ✅ Minimal agent set for validation
- ✅ Basic calculator example
- ✅ Clear phase transitions
- ✅ Real-time feedback

Future phases will add:
- Advanced refactoring capabilities
- Multiple test framework support
- Code coverage analysis
- Performance optimization
- Integration with existing codebases