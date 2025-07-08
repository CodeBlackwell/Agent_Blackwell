# Reference Documentation

This section contains detailed technical references for the Multi-Agent Orchestrator System.

## 📋 Contents

### API Documentation
- **[REST API Reference](api-reference.md)** - Complete API endpoint documentation

### Command Line Interface
- **[CLI Reference](cli-reference.md)** - Command-line options and usage

### Configuration
- **[Configuration Reference](configuration.md)** - All configuration options

### Component Reference
- **[Component Documentation](components.md)** - Individual component APIs

### Code Reference

## 🔍 Quick Links

### Most Used References
- [REST API Endpoints](api-reference.md#endpoints)
- [CLI Commands](cli-reference.md#commands)
- [Configuration Options](configuration.md#options)

### Integration Points
- [Authentication](api-reference.md#authentication)

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

[← Back to Documentation Hub](../README.md)