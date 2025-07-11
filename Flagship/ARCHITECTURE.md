# Flagship TDD Orchestrator Architecture

## Overview

Flagship is a **self-contained TDD (Test-Driven Development) orchestrator** that manages the RED-YELLOW-GREEN cycle of TDD through specialized AI agents. It can operate both as a standalone system and as part of a larger workflow ecosystem.

## Self-Contained Design

Flagship is designed to be completely self-contained with all necessary components:

### Core Components

1. **Agents** (`/agents/`)
   - `test_writer_flagship.py` - Writes failing tests (RED phase)
   - `coder_flagship.py` - Writes minimal implementation (YELLOW phase)
   - `test_runner_flagship.py` - Executes tests (GREEN phase)

2. **Models** (`/models/`)
   - `flagship_models.py` - Core TDD workflow models
   - `execution_tracer.py` - Execution tracking and reporting
   - `parent_compatibility.py` - Compatibility layer for parent system

3. **Workflows** (`/workflows/`)
   - `tdd_orchestrator/` - Complete TDD workflow orchestration
     - `orchestrator.py` - Main orchestrator
     - `phase_manager.py` - Manages TDD phases
     - `agent_coordinator.py` - Coordinates agent interactions
     - `retry_coordinator.py` - Handles retries and failures
     - `metrics_collector.py` - Collects workflow metrics

4. **Utils** (`/utils/`)
   - `enhanced_file_manager.py` - File management with caching and session support
   - `command_tracer.py` - Command execution tracing

5. **Integrations** (`/integrations/`)
   - `parent_system_adapter.py` - Adapter for parent workflow system

### Key Features

- **File Management**: Enhanced file manager allows agents to read and edit existing files
- **Session Management**: Each TDD session has its own directory with complete history
- **Execution Tracing**: Comprehensive tracking of all operations
- **Streaming Output**: Real-time streaming of agent outputs
- **Retry Logic**: Intelligent retry handling for failed phases

## Usage Modes

### 1. Standalone Mode

Run directly using the flagship orchestrator:

```python
from flagship_orchestrator import FlagshipOrchestrator

orchestrator = FlagshipOrchestrator()
state = await orchestrator.run_tdd_workflow("Create a calculator")
```

Or use the convenient shell script:
```bash
./runflagship.sh "Create a calculator with add and subtract methods"
```

### 2. Server Mode

Start the API server:
```bash
python flagship_server.py  # or flagship_server_streaming.py
```

Then use the client:
```python
from flagship_client import submit_tdd_request
session_id = submit_tdd_request("Create a calculator")
```

### 3. Parent System Integration

The parent workflow system can use Flagship through the adapter:

```python
# In parent system's workflows/tdd_orchestrator.py
from Flagship.integrations.parent_system_adapter import execute_tdd_workflow_for_parent
```

## File Organization

```
Flagship/
├── agents/              # TDD phase agents
├── configs/             # Configuration files
├── generated/           # Generated code output
├── integrations/        # Parent system integration
├── models/              # Data models and structures
├── tests/               # Test suites
├── utils/               # Utility modules
├── workflows/           # Workflow orchestration
│   └── tdd_orchestrator/
├── flagship_orchestrator.py  # Main orchestrator
├── flagship_server*.py       # API servers
└── runflagship.sh           # Convenience runner
```

## Independence from Parent System

Flagship is designed to work independently:

1. **No External Dependencies**: All necessary models are included
2. **Local Agent Management**: Can run agents without parent system
3. **Self-Contained File Operations**: Built-in file manager
4. **Own Execution Tracking**: Independent tracing system

The `parent_compatibility.py` module provides compatibility when needed, but Flagship functions fully without the parent system.

## Best Practices

1. **Use Enhanced File Manager**: Agents should use the file manager for all file operations
2. **Session-Based Work**: Each TDD cycle gets its own session directory
3. **Streaming Output**: Use streaming mode for real-time feedback
4. **Review Generated Code**: Always review in `generated/session_*/`

## Future Enhancements

- [ ] Web UI for visual workflow management
- [ ] Plugin system for custom agents
- [ ] Cloud deployment support
- [ ] Advanced metrics dashboard
- [ ] Integration with CI/CD pipelines