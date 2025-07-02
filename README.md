# Modular Agent System

A modular multi-agent system built on the Agent Communication Protocol (ACP) that orchestrates specialized AI agents to collaborate on software development tasks. Features a highly modular workflow architecture with advanced visualization capabilities.

## 🌟 Overview

This system implements a team of specialized AI agents that work together to complete software development tasks. Each agent has a specific role in the development process, from planning to review, and communicates through a standardized protocol. The system features a modular workflow architecture that visualizes data flows between agents for better understanding and debugging.

## 🤖 Agent Architecture

The system follows a modular single-server architecture with the following specialized agents:

- **Orchestrator**: Coordinates the workflow and manages communication between agents
- **Planner**: Creates detailed project plans and task breakdowns
- **Designer**: Develops technical designs, architecture, and schemas
- **Coder**: Implements code based on plans and designs
- **Test Writer**: Creates comprehensive test suites
- **Reviewer**: Provides code reviews and improvement suggestions

## 📋 Workflows

The system supports multiple workflows through a modular architecture:

1. **Full Development**: End-to-end software development (planning → design → implementation → testing → review)
2. **TDD Workflow**: Test-driven development approach (planning → design → test writing → implementation → review)
3. **Individual Steps**: Run any specific step of the development process in isolation

All workflows are implemented as modular, reusable components in the `workflows/` directory with clear separation of concerns and standardized interfaces.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- UV package manager

### Installation

1. Clone this repository
2. Set up a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
uv pip install -r requirements.txt
```

4. Create a `.env` file with your API keys (see `.env.example`)

### Running the Server

```bash
python orchestrator/orchestrator_agent.py
```

The server will start on http://localhost:8080

## 🧪 Testing

### Agent Testing

The system includes comprehensive test suites for each agent:

```bash
# Run all agent tests
python tests/run_agent_tests.py

# Run specific agent tests
python tests/run_agent_tests.py planner
```

Each agent has both automated test cases and an interactive testing mode. The test runner will automatically start the orchestrator server if one is not already running.

### Workflow Testing

Workflows can be tested independently using the workflow test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run workflow tests
python tests/test_workflows.py
```

Test options include:

- TDD workflow testing
- Full development workflow testing
- Individual workflow step testing
- Custom input testing

Test results are saved to the `tests/outputs/` directory with timestamped filenames.

## 📁 Project Structure

```
├── orchestrator/
│   └── orchestrator_agent.py     # Main server and orchestrator agent
├── agents/
│   ├── planner/                  # Planner agent module
│   │   ├── planner_agent.py
│   │   └── test_planner.py
│   ├── designer/                 # Designer agent module
│   ├── coder/                    # Coder agent module
│   ├── test_writer/              # Test writer agent module
│   ├── reviewer/                 # Reviewer agent module
│   └── run_agent_tests.py        # Master agent test runner script
├── workflows/
│   ├── tdd/                      # TDD workflow implementation
│   │   └── tdd_workflow.py
│   ├── full/                     # Full workflow implementation
│   │   └── full_workflow.py
│   ├── individual/               # Individual step workflow
│   │   └── individual_workflow.py
│   ├── workflow_manager.py       # Workflow dispatch system
│   ├── workflow_visualizer.py    # Basic workflow visualization tool
│   └── enhanced_workflow_visualizer.py # Advanced workflow visualization
├── docs/
│   ├── WORKFLOW_DATA_FLOW.md     # Workflow data flow documentation
│   └── workflow_visualizations/  # Generated workflow diagrams
├── tests/
│   └── outputs/                  # Test output directory
│   └── run_agent_tests.py        # Master agent test runner script
│   └── test_workflows.py         # Workflow testing utilities
├── generated/                    # Output directory for generated code
└── requirements.txt              # Project dependencies
```

## 📊 Development Workflow

1. The orchestrator receives a project request
2. The planner creates a detailed project plan
3. The designer develops the technical architecture
4. The test writer creates test specifications (in TDD workflow)
5. The coder implements the required functionality
6. The test writer creates tests (in traditional workflow)
7. The reviewer evaluates the implementation

All workflows are visualized and documented in the `docs/workflow_visualizations/` directory.

## 🛠 Configuration

All LLM configurations (prompts, model parameters, etc.) are centralized in the configuration files to ensure consistency and maintainability.

## 📊 Workflow Visualization

The system includes powerful tools for visualizing the data flow between agents in workflows:

### Basic Visualization

```bash
# Activate virtual environment
source venv/bin/activate

# Generate basic workflow visualizations
python workflows/workflow_visualizer.py
```

### Enhanced Visualization

```bash
# Generate enhanced workflow visualizations with detailed schema information
python workflows/enhanced_workflow_visualizer.py
```

### Visualization Outputs

The visualization tools generate multiple output formats in `docs/workflow_visualizations/`:

- **DOT files**: Raw GraphViz format for custom rendering
- **PDF files**: High-quality vector diagrams
- **PNG files**: Bitmap images for easy viewing and sharing
- **JSON files**: Structured data flow information

### Visualization Documentation

Comprehensive documentation of the workflow data flows is generated at `docs/WORKFLOW_DATA_FLOW.md`, including:

- Detailed schema information for data passed between agents
- Visual diagrams for each workflow type
- Data transformation descriptions
- Complete workflow system overview diagram

## 🔗 Integration Examples

The system can integrate with frameworks like LangGraph, CrewAI, and more. See the examples directory for integration patterns.

## 📦 Dependencies

The system requires the following dependencies:

- Python 3.8+
- Virtual environment (created with `uv venv`)
- Graphviz (system package, install with `brew install graphviz` on macOS)
- Python packages listed in requirements.txt

Environment variables are managed through dotenv, with all sensitive credentials stored in a .env file (not versioned in git).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
