# Component Documentation

Reference documentation for individual system components.

## 🚧 Under Construction

This documentation is currently being developed. For component information, please refer to:
- [Architecture Overview](../developer-guide/architecture/README.md) for system design
- Component-specific READMEs in their directories

## Core Components

### Orchestrator Agent
- **Location**: `/orchestrator/orchestrator_agent.py`
- **Purpose**: Central coordination server
- **Port**: 8080
- **Protocol**: Agent Communication Protocol (ACP)

### REST API Server
- **Location**: `/api/orchestrator_api.py`
- **Purpose**: HTTP interface for external access
- **Port**: 8000
- **Framework**: FastAPI

### Workflow Manager
- **Location**: `/workflows/workflow_manager.py`
- **Purpose**: Routes and executes workflow requests
- **Key Function**: `execute_workflow()`

## Specialized Agents

### Planner Agent
- **Location**: `/agents/planner/`
- **Purpose**: Requirements analysis and project planning
- **Output**: Structured project plan

### Designer Agent
- **Location**: `/agents/designer/`
- **Purpose**: Technical architecture and database design
- **Output**: Technical specifications

### Coder Agent
- **Location**: `/agents/coder/`
- **Purpose**: Code implementation
- **Output**: Source code files

### Test Writer Agent
- **Location**: `/agents/test_writer/`
- **Purpose**: Test generation
- **Output**: Test files

### Reviewer Agent
- **Location**: `/agents/reviewer/`
- **Purpose**: Code review and quality assurance
- **Output**: Review feedback

### Executor Agent
- **Location**: `/agents/executor/`
- **Purpose**: Code execution in sandboxed environment
- **Technology**: Docker containers

### Feature Reviewer Agent
- **Location**: `/agents/feature_reviewer/`
- **Purpose**: Feature-specific validation
- **Used In**: MVP Incremental workflow

## Shared Components

### Data Models
- **Location**: `/shared/data_models.py`
- **Purpose**: Common data structures
- **Key Classes**: `CodingTeamInput`, `AgentResponse`

### Types
- **Location**: `/shared/types.py`
- **Purpose**: Type definitions and enums
- **Key Types**: `TeamMember`, `WorkflowType`

---

[← Back to Reference](README.md) | [← Back to Docs](../README.md)