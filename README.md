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

### Running the Server

To start the orchestrator server, run the following command:

```bash
python orchestrator/orchestrator_agent.py
```

The server will be available at `http://localhost:8080`.

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
python tests/test_workflows.py
```

This script allows you to test the TDD, Full Development, and individual step workflows with custom inputs.

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
