# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular multi-agent system that orchestrates specialized AI agents to collaborate on software development tasks. The system implements the Agent Communication Protocol (ACP) architecture with a team of specialized agents (Planner, Designer, Coder, Test Writer, Reviewer, and Executor) working together through configurable workflows.

## Core Architecture

The system follows a **modular, single-server architecture** with these key components:

1. **Orchestrator Agent** (`orchestrator/orchestrator_agent.py`): Central coordinator managing workflows via `EnhancedCodingTeamTool`
2. **Workflow Manager** (`workflows/workflow_manager.py`): Dispatches requests to appropriate workflow modules
3. **Specialized Agents** (in `agents/` directory): Each agent handles specific development tasks
4. **Shared Data Models** (`shared/data_models.py`): Common data structures for agent communication
5. **REST API** (`api/orchestrator_api.py`): External interface for submitting workflow requests

## Key Commands

### Running the System

```bash
# Set up virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the orchestrator server (ACP server on port 8080)
python orchestrator/orchestrator_agent.py

# Start the REST API server (HTTP API on port 8000)
python api/orchestrator_api.py
```

### Testing Commands

```bash
# 🚀 RECOMMENDED: Use the unified test runner
./test_runner.py              # Run all tests
./test_runner.py unit         # Run only unit tests  
./test_runner.py -p           # Run all tests in parallel
./test_runner.py --quick      # Run fast tests only
./test_runner.py -l           # List all test categories

# Individual test commands (if needed)
python tests/run_agent_tests.py      # Run agent tests
python tests/test_workflows.py       # Run workflow tests
pytest tests/unit/                   # Run unit tests
pytest tests/integration/            # Run integration tests
```

See [TEST_GUIDE.md](TEST_GUIDE.md) for comprehensive testing documentation.

### Visualization Commands

```bash
# Generate workflow visualizations (focused version - system overview & flow graphs only)
python workflows/workflow_visualizer_v4.py

# Options:
python workflows/workflow_visualizer_v4.py --help                # Show all options
python workflows/workflow_visualizer_v4.py --system-only         # System overview only
python workflows/workflow_visualizer_v4.py --workflow tdd        # Single workflow flow
python workflows/workflow_visualizer_v4.py --output-dir custom   # Custom output directory
```

## Workflow Types

- **TDD Workflow**: Planning → Design → Test Writing → Implementation → Execution → Review
- **Full Workflow**: Planning → Design → Implementation → Review  
- **MVP Incremental Workflow**: Feature-by-feature implementation with validation and reviews (10 phases - see [MVP Incremental Phases](docs/mvp_incremental_phases.md))
- **Individual Steps**: Execute single agent steps (planning, design, implementation, etc.)

## Important Configuration

- **Workflow Config** (`workflows/workflow_config.py`): Review retry settings, execution timeouts
- **Generated Code Path**: `./generated/` (configured in workflow_config.py)
- **Test Outputs**: `tests/outputs/session_[TIMESTAMP]/`
- **Logs**: `logs/[TIMESTAMP]/`
- **Output Display Config** (`orchestrator/orchestrator_configs.py`):
  - `mode`: "detailed" or "summary" - controls verbosity of agent outputs
  - `max_input_chars`: Maximum characters to display for inputs (default: 1000)
  - `max_output_chars`: Maximum characters to display for outputs (default: 2000)
  - `export_interactions`: Whether to save interactions to JSON (default: true)

## Development Guidelines

1. **Agent Implementation**:
   - Each agent is a self-contained module in `agents/[agent_name]/`
   - Agents communicate through standardized ACP protocol
   - Use streaming (`AsyncGenerator`) for incremental output

2. **Adding New Workflows**:
   - Create new module in `workflows/[workflow_name]/`
   - Register in `workflow_manager.py`
   - Follow existing patterns for consistency

3. **Testing**:
   - Use the unified test runner: `./test_runner.py`
   - Test individual agents with `test_[agent]_debug.py` files
   - Use workflow tests to validate end-to-end flows
   - All test artifacts saved in `tests/outputs/`
   - See comprehensive [TEST_GUIDE.md](TEST_GUIDE.md) for details

4. **Error Handling**:
   - Max review retries: 3 (auto-approves after)
   - TDD max total retries: 10
   - Execution timeout: 60 seconds

## Key Data Flow

1. **Input**: User requirements → Orchestrator
2. **Processing**: Orchestrator → Workflow Manager → Individual Agents
3. **Review Loop**: Each agent output → Reviewer → Approval/Revision
4. **Output**: Final code/artifacts → `generated/` directory

## Environment Setup

Create a `.env` file with required API keys (use `.env.example` as template).

## Monitoring and Debugging

- Progress tracking built into workflows
- Agent outputs saved individually in test sessions
- Comprehensive session reports with metrics
- Visual workflow diagrams in `docs/workflow_visualizations/`

## Real-Time Agent Output Display

The system now provides step-by-step visibility into agent interactions:

### Features
- **Real-time display** of each agent's input and output as they execute
- **Configurable verbosity** via `OUTPUT_DISPLAY_CONFIG` in `orchestrator_configs.py`
- **Automatic truncation** of long inputs/outputs with character counts
- **Review notifications** showing approval/revision status
- **Retry notifications** when agents need to revise their work
- **Execution timing** for each agent interaction
- **JSON export** of all interactions to `logs/{session_id}_interactions.json`

### Testing Real-Time Output
```bash
# Run the test script to see real-time output in action
python test_realtime_output.py
```

### Output Modes
- **Detailed Mode**: Shows up to 1000 chars of input and 2000 chars of output
- **Summary Mode**: Shows condensed view with 200 chars of input and 300 chars of output

### Example Output
```
================================================================================
🤖 AGENT #1: PLANNER_AGENT [14:23:15]
--------------------------------------------------------------------------------
📥 INPUT:
----------------------------------------
Use the TDD workflow to create a simple calculator API...

⏳ Processing...

📤 OUTPUT:
----------------------------------------
Here's my plan for the calculator API:
1. Set up FastAPI project structure
2. Define endpoint schemas...

✅ COMPLETED in 2.34 seconds
================================================================================
```

## REST API Integration

The system now includes a REST API that exposes the orchestrator functionality for external applications.

### API Endpoints

- **POST /execute-workflow**: Submit code generation requests
- **GET /workflow-status/{session_id}**: Track workflow progress and retrieve results
- **GET /workflow-types**: List available workflow types
- **GET /health**: Health check endpoint

### Key Integration Points

1. **Direct Workflow Execution**: The API uses `execute_workflow()` from `workflows/workflow_manager.py` directly, bypassing the orchestrator tool layer
2. **Async Background Processing**: Workflows run in background tasks to prevent HTTP timeouts
3. **Session-based Tracking**: Each workflow gets a unique session ID for monitoring
4. **In-memory Storage**: MVP uses in-memory storage for workflow status (replace with persistent storage for production)

### Common Integration Issues and Fixes

1. **Import Error: `run_agent`**
   - Issue: `workflows/incremental/feature_orchestrator.py` tried to import non-existent `run_agent`
   - Fix: Changed to `run_team_member` from `orchestrator/orchestrator_agent.py`

2. **Method Signature Error: `complete_step()`**
   - Issue: `WorkflowExecutionTracer.complete_step()` was called with invalid `success` parameter
   - Fix: Changed to use `error` parameter instead: `tracer.complete_step(step_id, {"error": msg}, error=msg)`

3. **Report Serialization Error**
   - Issue: `WorkflowExecutionReport` has no `to_dict()` method
   - Fix: Use `to_json()` method instead for serialization

4. **Missing Dependencies**
   - Issue: Docker Python package not installed
   - Fix: `uv pip install docker`

### Testing the API

```bash
# Quick test
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Create a simple calculator", "workflow_type": "full"}'

# Monitor progress
curl http://localhost:8000/workflow-status/{session_id}

# Run demo script
python api/demo_api_usage.py
```

### Important Notes

- Always ensure both servers are running (orchestrator on 8080, API on 8000)
- Generated code is saved in `generated/app_generated_[timestamp]/`
- The API calls workflow functions directly, not through the orchestrator tool
- Workflow execution includes fallback to standard coder when incremental coding fails

## 🧪 Comprehensive Testing

The codebase includes a robust testing framework with multiple test types and a unified test runner.

### Unified Test Runner

The `test_runner.py` script provides a centralized, user-friendly interface for all tests:

```bash
# Run all tests
./test_runner.py

# Run specific test categories
./test_runner.py unit              # Unit tests only
./test_runner.py unit integration  # Unit and integration tests
./test_runner.py workflow agent    # Workflow and agent tests

# Advanced options
./test_runner.py -p               # Run tests in parallel
./test_runner.py --quick          # Quick tests only (unit)
./test_runner.py -v               # Verbose output
./test_runner.py --ci             # CI mode (no emojis)
./test_runner.py -l               # List all test categories
```

### Test Categories

1. **🔬 Unit Tests** (`tests/unit/`)
   - Framework: pytest
   - Fast, isolated component tests
   - Focus: Error analyzer, feature parser, retry strategies, etc.

2. **🔗 Integration Tests** (`tests/integration/`)
   - Framework: pytest
   - Component interaction tests
   - Focus: Workflow integration, API integration

3. **🔄 Workflow Tests** (`tests/test_workflows.py`)
   - Framework: Standalone scripts
   - End-to-end workflow validation
   - Supports different complexity levels

4. **🤖 Agent Tests** (`tests/run_agent_tests.py`)
   - Framework: Custom test runner
   - Individual agent functionality
   - Debug scripts for each agent

5. **⚡ Executor Tests** (`tests/test_executor_*.py`)
   - Framework: Mixed (unittest/standalone)
   - Code execution validation
   - Docker integration tests

6. **🌐 API Tests** (`api/test_*.py`)
   - Framework: Mixed (pytest/standalone)
   - REST endpoint validation
   - Client integration tests

### Testing Best Practices

1. **Before Running Tests**:
   - Start orchestrator server: `python orchestrator/orchestrator_agent.py`
   - Start API server (for API tests): `python api/orchestrator_api.py`
   - Ensure virtual environment is activated
   - Check Docker is running (for executor tests)

2. **Test Output**:
   - Results saved to `test_results_[TIMESTAMP].json`
   - Detailed logs in `tests/outputs/`
   - Session artifacts in `tests/outputs/session_[TIMESTAMP]/`

3. **Debugging Tests**:
   ```bash
   # Run specific test with verbose output
   pytest -vv tests/unit/incremental/test_error_analyzer.py
   
   # Run specific test method
   pytest tests/unit/incremental/test_error_analyzer.py::TestErrorContext::test_method
   
   # Show test coverage
   pytest --cov=agents --cov=workflows --cov-report=html
   ```

4. **CI/CD Integration**:
   ```bash
   # Use CI mode for automated pipelines
   ./test_runner.py --ci
   ```

### Adding New Tests

When adding new tests:
- Unit tests: Add to `tests/unit/` using pytest
- Integration tests: Add to `tests/integration/`
- Agent tests: Create debug script in agent directory
- Update `TEST_CATEGORIES` in `test_runner.py` for new categories

For complete testing documentation, see [TEST_GUIDE.md](TEST_GUIDE.md).