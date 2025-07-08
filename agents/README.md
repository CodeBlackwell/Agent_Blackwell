# Agents Directory

This directory contains all specialized AI agents that work together to complete software development tasks.

## Agent Overview

Each agent is a self-contained module with a specific role in the development process:

### Core Development Agents

#### 📋 Planner Agent (`planner/`)
- **Role**: Requirements analysis and project planning
- **Input**: User requirements
- **Output**: Structured project plan with tasks and milestones
- **Key Skills**: Breaking down complex requirements, identifying dependencies

#### 🏗️ Designer Agent (`designer/`)
- **Role**: Technical architecture and system design
- **Input**: Project plan from Planner
- **Output**: Technical specifications, architecture diagrams, database schemas
- **Key Skills**: System design, database modeling, API design

#### 💻 Coder Agent (`coder/`)
- **Role**: Code implementation
- **Input**: Technical design from Designer
- **Output**: Working source code
- **Key Skills**: Multiple programming languages, best practices, clean code

#### 🧪 Test Writer Agent (`test_writer/`)
- **Role**: Test generation
- **Input**: Code implementation and specifications
- **Output**: Comprehensive test suites
- **Key Skills**: Unit testing, integration testing, test coverage

#### 🔍 Reviewer Agent (`reviewer/`)
- **Role**: Code review and quality assurance
- **Input**: Code and tests from other agents
- **Output**: Review feedback, approval/rejection with reasons
- **Key Skills**: Code quality assessment, best practices, security review

### Specialized Agents

#### ✅ Executor Agent (`executor/`)
- **Role**: Code execution in sandboxed environment
- **Technology**: Docker containers
- **Input**: Code and tests to execute
- **Output**: Execution results, test outcomes
- **Key Skills**: Environment setup, dependency management, error reporting

#### 👁️ Feature Reviewer Agent (`feature_reviewer/`)
- **Role**: Feature-specific validation (used in MVP Incremental workflow)
- **Input**: Individual feature implementation
- **Output**: Feature-level review and approval
- **Key Skills**: Feature completeness validation, incremental review

#### 🔬 Validator Agent (`validator/`)
- **Role**: Code validation and verification
- **Input**: Generated code
- **Output**: Validation results, error reports
- **Key Skills**: Syntax checking, logic validation, requirement matching

## Agent Structure

Each agent directory typically contains:
```
agent_name/
├── __init__.py          # Agent initialization
├── agent_name.py        # Main agent implementation
├── prompts.py           # Agent-specific prompts
├── utils.py             # Helper functions
└── test_agent_name.py   # Agent tests
```

## Agent Communication

All agents communicate through the Agent Communication Protocol (ACP):
- Standardized request/response format
- Streaming support for incremental output
- Error handling and retry mechanisms

## Creating New Agents

To add a new agent:
1. Create a directory under `agents/`
2. Implement the agent following the existing pattern
3. Add appropriate prompts and utilities
4. Include comprehensive tests
5. Update workflow configurations to use the new agent

## Testing Agents

Each agent has individual test files:
```bash
# Test individual agent
python agents/planner/test_planner_debug.py

# Run all agent tests
python run.py test agent
```

## Related Documentation

- [Architecture Overview](../docs/developer-guide/architecture/README.md)
- [ACP Protocol](../docs/developer-guide/architecture/acp-insights.md)
- [Agent Development Guide](../docs/developer-guide/agent-development.md)
- [Workflow Integration](../workflows/README.md)