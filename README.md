# Modular Agent System

A modular multi-agent system built on the Agent Communication Protocol (ACP) that orchestrates specialized AI agents to collaborate on software development tasks. Features a highly modular workflow architecture with advanced visualization capabilities.

## 🌟 Overview

This system implements a team of specialized AI agents that work together to complete software development tasks. Each agent has a specific role in the development process, from planning to review, and communicates through a standardized protocol. The system features a modular workflow architecture that visualizes data flows between agents for better understanding and debugging.

## 🤖 Architecture

The system is built on a modular, single-server architecture that coordinates a team of specialized AI agents. The core components are:

- **Orchestrator Agent**: The central coordinator that manages the entire workflow. It uses an `EnhancedCodingTeamTool` to dynamically execute workflows and track progress.
- **Specialized Agents**: A team of agents, each responsible for a specific task:
    - **Planner**: Creates detailed project plans and task breakdowns.
    - **Designer**: Develops technical designs, architecture, and database schemas.
    - **Coder**: Implements the code based on the provided plans and designs.
    - **Test Writer**: Creates comprehensive test suites for the implemented code.
    - **Reviewer**: Provides code reviews, feedback, and suggestions for improvement.

## Workflow Execution

The system's workflow execution is managed by a sophisticated, multi-layered process:

1.  **`EnhancedCodingTeamTool`**: The orchestrator receives a task and uses this tool to initiate a workflow. The tool is responsible for setting up progress tracking, managing the session, and generating final reports.
2.  **`workflow_manager.py`**: This module acts as a dispatcher. It receives the workflow request from the `EnhancedCodingTeamTool` and calls the appropriate workflow function based on the user's selection (`TDD`, `Full Development`, or `Individual Step`).
3.  **Workflow Modules**: Each workflow is implemented in its own dedicated module (e.g., `tdd_workflow.py`), ensuring a clean separation of concerns and making it easy to add new workflows in the future.

This architecture allows for a flexible and extensible system where workflows can be easily modified or added without changing the core orchestration logic.

## ✨ Features

- **Modular Agent System**: Each agent is a self-contained module, making it easy to update, test, and replace individual components.
- **Dynamic Workflows**: Supports multiple development workflows, including Test-Driven Development (TDD), Full Development, and individual step execution.
- **Advanced Progress Tracking**: A comprehensive progress tracking system that monitors each step of the workflow, records performance metrics, and generates detailed reports.
- **Workflow Visualization**: Includes tools to generate visual diagrams of the workflows, providing a clear overview of the data flow between agents.
- **Centralized Configuration**: All LLM configurations, including prompts and model parameters, are managed in a central location for consistency and easy maintenance.
- **Comprehensive Testing**: The system includes a full suite of tests for each agent and workflow, ensuring reliability and stability.

## 🌐 REST API

The system exposes a REST API for submitting code generation requests and tracking their progress. This allows external applications to leverage the multi-agent system's capabilities.

### API Endpoints

#### POST /execute-workflow
Submit a new workflow execution request.

**Request Body:**
```json
{
  "requirements": "Create a Python function that adds two numbers",
  "workflow_type": "full",
  "max_retries": 3,
  "timeout_seconds": 300
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "status": "pending",
  "message": "Workflow execution started. Track progress at /workflow-status/{session_id}"
}
```

#### GET /workflow-status/{session_id}
Track the progress and retrieve results of a workflow execution.

**Response:**
```json
{
  "session_id": "uuid-here",
  "status": "completed",
  "workflow_type": "full",
  "started_at": "2025-07-05T16:41:46.524476+00:00",
  "completed_at": "2025-07-05T16:42:19.984355+00:00",
  "result": {
    "agent_results": [
      {
        "agent": "planner",
        "output_preview": "Project plan...",
        "output_length": 2509
      }
    ],
    "agent_count": 4,
    "total_output_size": 11113
  }
}
```

#### GET /workflow-types
List available workflow types.

**Response:**
```json
[
  {
    "name": "tdd",
    "description": "Test-Driven Development workflow",
    "requires_step_type": false
  },
  {
    "name": "full",
    "description": "Full workflow: Planning → Design → Implementation → Review",
    "requires_step_type": false
  }
]
```

#### GET /health
Health check endpoint.

### API Usage Example

```python
import httpx
import asyncio

async def generate_code():
    async with httpx.AsyncClient() as client:
        # Submit workflow
        response = await client.post(
            "http://localhost:8000/execute-workflow",
            json={
                "requirements": "Create a Calculator class with add, subtract, multiply, divide",
                "workflow_type": "full"
            }
        )
        
        session_id = response.json()["session_id"]
        
        # Poll for completion
        while True:
            status = await client.get(f"http://localhost:8000/workflow-status/{session_id}")
            data = status.json()
            
            if data["status"] in ["completed", "failed"]:
                print(f"Workflow {data['status']}")
                break
                
            await asyncio.sleep(2)

asyncio.run(generate_code())
```

Generated code is saved in the `generated/` directory.

## 🧪 Testing

The system includes a comprehensive testing suite for both individual agents and workflows.

### Agent Testing

To run the agent tests, use the `run_agent_tests.py` script:

```bash
# Run all agent tests
python tests/run_agent_tests.py

# Run a specific agent test
python tests/run_agent_tests.py planner
```

### Workflow Testing

To test the different workflows, use the `test_workflows.py` script:

```bash
# Run all workflow tests with minimal complexity
python tests/test_workflows.py

# Run a specific workflow with a specific complexity
python tests/test_workflows.py --workflow tdd --complexity minimal

# List all available tests without running them
python tests/test_workflows.py --list

# Run full workflow tests with standard complexity
python tests/test_workflows.py --workflow full --complexity standard
```

#### Workflow Test Options

- **Workflow Types**:
  - `tdd`: Test-Driven Development workflow (Planning → Design → Test Writing → Implementation → Execution → Review)
  - `full`: Full Development workflow (Planning → Design → Implementation → Review)
  - `planning`: Execute only the planning phase
  - `design`: Execute only the design phase
  - `implementation`: Execute only the implementation phase
  - `all`: Run all workflow types (default)

- **Complexity Levels**:
  - `minimal`: Simple "Hello World" API (fastest)
  - `standard`: TODO List API with CRUD operations
  - `complex`: E-Commerce platform with multiple features
  - `stress`: Microservices architecture (most comprehensive)
  - `all`: Run all complexity levels

#### Test Monitoring and Reports

The workflow testing framework includes comprehensive monitoring capabilities:
- **Progress Tracking**: Monitors each step of the workflow execution
- **Performance Metrics**: Captures timing data for each agent and step
- **Agent Interactions**: Records the sequence and patterns of agent communications
- **Review Process Analysis**: Tracks approval rates, retry patterns, and feedback loops
- **Test Artifacts**: Saves all agent outputs, generated code, and execution reports

#### Test Results and Artifacts

All test results are stored in the `tests/outputs/session_[TIMESTAMP]` directory, with:
- Agent outputs saved as individual text files
- Execution reports in JSON format
- Generated code in separate directories
- Comprehensive session report with metrics and observations

#### Working with the Executor Agent

The Executor Agent can be included in workflows to test and run the generated code:

1. Ensure `TeamMember.executor` is included in the `team_members` list of the `CodingTeamInput`
2. The Executor will:
   - Create project files in `orchestrator/generated/app_generated_[timestamp]/`
   - Set up the development environment 
   - Attempt to run the tests against the code
   - Return execution results for the reviewer to evaluate

```bash
# To view generated project files from the most recent test
cd orchestrator/generated/
ls -lt | head -5
```

### Integration Testing

For more detailed integration testing focused on executor functionality:

```bash
# Run executor direct tests
python tests/test_executor_direct.py

# Run full TDD workflow with executor integration
python tests/test_workflows.py --workflow tdd --complexity standard
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- UV package manager
- Graphviz (`brew install graphviz` on macOS)

### Installation

1.  Clone this repository.
2.  Set up a virtual environment:
    ```bash
    uv venv
    source .venv/bin/activate
    ```
3.  Install the dependencies:
    ```bash
    uv pip install -r requirements.txt
    ```
4.  Create a `.env` file with your API keys (you can use `.env.example` as a template).

### Running the System

The system provides two ways to interact with the orchestrator:

#### 1. ACP Server (Port 8080)

To start the orchestrator server for agent communication:

```bash
python orchestrator/orchestrator_agent.py
```

The ACP server will be available at `http://localhost:8080`.

#### 2. REST API (Port 8000)

To start the REST API server for external applications:

```bash
python api/orchestrator_api.py
```

The API server will be available at `http://localhost:8000`.

## 📁 Project Structure

```
├── orchestrator/
│   ├── orchestrator_agent.py     # Main server and orchestrator agent
│   └── orchestrator_configs.py   # Configuration for the orchestrator
├── agents/
│   ├── planner/                  # Planner agent module
│   ├── designer/                 # Designer agent module
│   ├── coder/                    # Coder agent module
│   ├── test_writer/              # Test writer agent module
│   └── reviewer/                 # Reviewer agent module
├── api/
│   ├── orchestrator_api.py       # REST API server
│   ├── test_orchestrator_api.py  # API tests
│   └── test_api_client.py        # Demo API client
├── workflows/
│   ├── tdd/                      # TDD workflow implementation
│   ├── full/                     # Full workflow implementation
│   ├── individual/               # Individual step workflow implementation
│   └── workflow_manager.py       # Workflow dispatch system
├── tests/
│   ├── run_agent_tests.py        # Master agent test runner
│   └── test_workflows.py         # Workflow testing script
├── docs/
│   └── workflow_visualizations/  # Generated workflow diagrams
├── generated/                    # Output directory for generated code
└── requirements.txt              # Project dependencies
```

## 📊 Workflow Visualization

The system includes powerful tools for visualizing the data flow between agents. To generate the visualizations, run the following scripts:

```bash
# Generate basic workflow visualizations
python workflows/workflow_visualizer.py

# Generate enhanced visualizations with detailed schema information
python workflows/enhanced_workflow_visualizer.py
```

The generated diagrams will be saved in the `docs/workflow_visualizations/` directory.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
