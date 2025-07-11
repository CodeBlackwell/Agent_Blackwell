# Flagship TDD Orchestrator

A Test-Driven Development (TDD) orchestrator that implements the RED-YELLOW-GREEN phases using specialized AI agents.

## Directory Structure

```
/Flagship/
├── /agents/              # Specialized AI agents
│   ├── test_writer_flagship.py    # RED phase: Writes failing tests
│   ├── coder_flagship.py          # YELLOW phase: Writes minimal implementation
│   └── test_runner_flagship.py    # GREEN phase: Runs tests and reports results
├── /configs/             # Configuration files
│   └── flagship_config.py         # Workflow configurations (DEFAULT, QUICK, COMPREHENSIVE)
├── /models/              # Data models
│   └── flagship_models.py         # Core data structures (TDDPhase, WorkflowState, etc.)
├── /workflows/           # Workflow implementations
│   └── flagship_workflow.py       # TDD workflow coordinator
├── /tests/               # Test files
│   ├── test_*.py                  # Various test files for the system
│   ├── run_standalone_test.py    # Standalone test runner
│   └── example_calculator.py     # Example usage
├── /logs/                # System logs
│   ├── server.log                 # Server operation logs
│   ├── server_debug.log           # Debug-level logs
│   └── server_output.log          # Captured server output
├── /generated/           # Generated code output
│   └── session_*                  # Session-specific outputs with timestamps
├── /docs/                # Documentation
│   ├── README.md                  # Original documentation
│   └── SERVER_README.md           # Server-specific documentation
├── flagship_server.py    # FastAPI server providing REST endpoints
├── flagship_client.py    # CLI client for interacting with server
├── flagship_orchestrator.py  # Core orchestrator managing TDD phases
├── start_server.sh       # Server startup script
├── requirements_server.txt   # Python dependencies
└── __init__.py           # Package initialization
```

## File Purposes

### Core Components

- **flagship_orchestrator.py**: Central orchestrator that manages TDD phase transitions and coordinates agents
- **flagship_server.py**: FastAPI server exposing REST API endpoints and Server-Sent Events (SSE) for streaming
- **flagship_client.py**: Command-line interface using Click and Rich for formatted interaction with the server

### Agents Directory

- **test_writer_flagship.py**: Implements the RED phase by analyzing requirements and generating comprehensive test suites
- **coder_flagship.py**: Implements the YELLOW phase by parsing test code and generating minimal implementations
- **test_runner_flagship.py**: Implements the GREEN phase by executing pytest and reporting test results

### Support Files

- **models/flagship_models.py**: Defines data structures including TDDPhase enum, WorkflowState, PhaseTransition, TestResult
- **configs/flagship_config.py**: Contains workflow configurations with different iteration limits and settings
- **workflows/flagship_workflow.py**: Wrapper that coordinates the TDD workflow execution and maintains history

### Generated Output

All generated code is saved in timestamped session directories under `/generated/`:
- `test_generated.py`: Generated test suite from RED phase
- `implementation_generated.py`: Generated implementation from YELLOW phase
- `tdd_workflow_*.json`: Complete workflow state and history

## Usage

1. Start the server:
   ```bash
   ./start_server.sh
   # or
   python flagship_server.py
   ```

2. Use the CLI client:
   ```bash
   python flagship_client.py start "Create a calculator class with add and subtract methods"
   ```

3. Or interact via REST API:
   - POST `/tdd/start` - Start a new TDD workflow
   - GET `/tdd/status/{session_id}` - Check workflow status
   - GET `/tdd/stream/{session_id}` - Stream real-time output via SSE

## Features

- **RED-YELLOW-GREEN TDD Implementation**: Automated test-first development
- **Streaming Output**: Real-time progress updates via Server-Sent Events
- **Session Management**: Each workflow gets a unique session ID
- **Configurable Workflows**: DEFAULT, QUICK, and COMPREHENSIVE modes
- **Rich CLI Interface**: Formatted output with progress indicators
- **Generated Code Storage**: All outputs saved with timestamps