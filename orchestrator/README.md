# Orchestrator Component

The Orchestrator is the central coordination server for the Multi-Agent System, implementing the Agent Communication Protocol (ACP) server.

## Overview

The orchestrator manages the entire workflow execution process, coordinating communication between specialized agents and tracking progress throughout the development lifecycle.

## Key Files

### orchestrator_agent.py
The main orchestrator server that:
- Runs on port 8080
- Implements the ACP protocol
- Manages the `EnhancedCodingTeamTool`
- Handles workflow execution requests

### orchestrator_configs.py
Configuration settings including:
- Output display modes (detailed/summary)
- Character limits for truncation
- Interaction export settings
- Logging configuration

### enhanced_coding_team_tool.py
The primary tool that:
- Accepts coding team requests
- Manages session tracking
- Coordinates workflow execution
- Generates completion reports

## Architecture

```
Client Request → Orchestrator (8080) → EnhancedCodingTeamTool → Workflow Manager → Agents
                                                                         ↓
                                                                   Generated Code
```

## Running the Orchestrator

```bash
# Start the orchestrator server
python orchestrator/orchestrator_agent.py

# The server will start on http://localhost:8080
```

## Configuration

Edit `orchestrator_configs.py` to customize:
- Output verbosity
- Display limits
- Export settings
- Logging levels

## Integration Points

- **REST API**: The API server connects to the orchestrator
- **Workflows**: Workflow manager is invoked by the orchestrator
- **Agents**: All agents communicate through the orchestrator

## Generated Output

The orchestrator saves generated code in:
```
orchestrator/generated/app_generated_[timestamp]/
```

## Related Documentation

- [Architecture Overview](../docs/developer-guide/architecture/README.md)
- [ACP Protocol](../docs/developer-guide/architecture/acp-insights.md)
- [API Integration](../api/README.md)