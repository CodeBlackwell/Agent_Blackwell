# Reference Documentation

This section contains detailed technical references for the Multi-Agent Orchestrator System.

## 📋 Contents

### API Documentation
- **[REST API Reference](api-reference.md)** - Complete API endpoint documentation
- **[WebSocket API](websocket-api.md)** - Real-time communication
- **[API Examples](api-examples.md)** - Code samples and use cases

### Command Line Interface
- **[CLI Reference](cli-reference.md)** - Command-line options and usage
- **[Run Script Reference](run-script-reference.md)** - Unified `run.py` commands

### Configuration
- **[Configuration Reference](configuration.md)** - All configuration options
- **[Environment Variables](environment-variables.md)** - Environment settings
- **[Workflow Configuration](workflow-configuration.md)** - Workflow-specific settings

### Component Reference
- **[Component Documentation](components.md)** - Individual component APIs
- **[Agent Interfaces](agent-interfaces.md)** - Agent communication protocols
- **[Data Models](data-models.md)** - Shared data structures

### Code Reference
- **[Python API](python-api.md)** - Internal Python APIs
- **[Error Codes](error-codes.md)** - Error code reference
- **[Event Types](event-types.md)** - System events

## 🔍 Quick Links

### Most Used References
- [REST API Endpoints](api-reference.md#endpoints)
- [CLI Commands](cli-reference.md#commands)
- [Configuration Options](configuration.md#options)
- [Error Codes](error-codes.md#common-errors)

### Integration Points
- [Authentication](api-reference.md#authentication)
- [Webhooks](webhooks.md)
- [Plugins](plugin-api.md)

## 📊 API Overview

### REST Endpoints
```
POST   /execute-workflow      - Submit workflow request
GET    /workflow-status/{id}  - Check workflow status
GET    /workflow-types        - List available workflows
GET    /health               - Health check
```

### Core Objects
- `CodingTeamInput` - Workflow input
- `WorkflowExecutionReport` - Execution results
- `AgentResponse` - Agent output
- `ValidationResult` - Validation status

## 🔧 Configuration Overview

### Key Configuration Files
- `orchestrator_configs.py` - Orchestrator settings
- `workflow_config.py` - Workflow behavior
- `.env` - Environment variables

### Important Settings
- Output display mode
- Retry limits
- Timeout values
- Resource limits

## 💻 CLI Overview

### Common Commands
```bash
# Run examples
python run.py example hello_world

# Execute workflows
python run.py workflow mvp_incremental --task "..."

# Run tests
python run.py test all

# Interactive mode
python run.py
```

## 📚 Related Documentation

- [User Guide](../user-guide/README.md) - Getting started
- [Developer Guide](../developer-guide/README.md) - Development docs
- [Workflows](../workflows/README.md) - Workflow documentation
- [Operations](../operations/README.md) - Operational guides

## 🔍 Finding Information

1. **For API Integration**: Start with [REST API Reference](api-reference.md)
2. **For CLI Usage**: See [CLI Reference](cli-reference.md)
3. **For Configuration**: Check [Configuration Reference](configuration.md)
4. **For Errors**: Look up [Error Codes](error-codes.md)

[← Back to Documentation Hub](../README.md)