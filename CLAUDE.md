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

## Key Commands

### Running the System

```bash
# Set up virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the orchestrator server
python orchestrator/orchestrator_agent.py
```

### Testing Commands

```bash
# Run all agent tests
python tests/run_agent_tests.py

# Run specific agent test
python tests/run_agent_tests.py planner

# Run workflow tests (minimal complexity)
python tests/test_workflows.py

# Run specific workflow with specific complexity
python tests/test_workflows.py --workflow tdd --complexity minimal

# List available tests
python tests/test_workflows.py --list

# Run executor integration tests
python tests/test_executor_direct.py
```

### Visualization Commands

```bash
# Generate workflow visualizations
python workflows/workflow_visualizer.py

# Generate enhanced visualizations with schema details
python workflows/enhanced_workflow_visualizer.py
```

## Workflow Types

- **TDD Workflow**: Planning → Design → Test Writing → Implementation → Execution → Review
- **Full Workflow**: Planning → Design → Implementation → Review  
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
   - Test individual agents with `test_[agent]_debug.py` files
   - Use workflow tests to validate end-to-end flows
   - All test artifacts saved in `tests/outputs/`

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