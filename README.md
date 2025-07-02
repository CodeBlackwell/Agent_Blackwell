# Modular Agent System

A modular multi-agent system built on the Agent Communication Protocol (ACP) that orchestrates specialized AI agents to collaborate on software development tasks.

## 🌟 Overview

This system implements a team of specialized AI agents that work together to complete software development tasks. Each agent has a specific role in the development process, from planning to review, and communicates through a standardized protocol.

## 🤖 Agent Architecture

The system follows a modular single-server architecture with the following specialized agents:

- **Orchestrator**: Coordinates the workflow and manages communication between agents
- **Planner**: Creates detailed project plans and task breakdowns
- **Designer**: Develops technical designs, architecture, and schemas
- **Coder**: Implements code based on plans and designs
- **Test Writer**: Creates comprehensive test suites
- **Reviewer**: Provides code reviews and improvement suggestions

## 📋 Workflows

The system supports multiple workflows:

1. **Full Development**: End-to-end software development (planning → design → implementation → testing → review)
2. **TDD Workflow**: Test-driven development approach (planning → test writing → implementation → review)
3. **Individual Steps**: Run any specific step of the development process in isolation

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

The system includes comprehensive test suites for each agent:

```bash
# Run all tests
python orchestrator/run_agent_tests.py

# Run specific agent tests
python orchestrator/agents/{agent_name}/test_{agent_name}.py
```

Each agent has both automated test cases and an interactive testing mode.

## 📁 Project Structure

```
├── orchestrator/
│   ├── orchestrator_agent.py     # Main server and orchestrator agent
│   ├── run_agent_tests.py        # Master test runner script
│   ├── agents/
│   │   ├── planner/              # Planner agent module
│   │   │   ├── planner_agent.py
│   │   │   └── test_planner.py
│   │   ├── designer/             # Designer agent module
│   │   ├── coder/                # Coder agent module
│   │   ├── test_writer/          # Test writer agent module
│   │   ├── reviewer/             # Reviewer agent module
│   │   └── orchestrator/         # Orchestrator agent module
│   └── generated/                # Output directory for generated code
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

## 🛠 Configuration

All LLM configurations (prompts, model parameters, etc.) are centralized in the configuration files to ensure consistency and maintainability.

## 🔗 Integration Examples

The system can integrate with frameworks like LangGraph, CrewAI, and more. See the examples directory for integration patterns.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
