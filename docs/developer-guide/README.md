# Developer Guide

This guide is for developers who want to understand the system architecture, contribute to the project, or extend its capabilities.

## 📋 Contents

### Architecture & Design
- **[Architecture Overview](architecture/README.md)** - System design and principles
  - [ACP Architecture Insights](architecture/acp-insights.md) - Agent Communication Protocol
  - [Implementation Guide](architecture/implementation-guide.md) - Building components
  - [Architectural Lessons](architecture/lessons-learned.md) - Design decisions
  - [Job Pipeline](architecture/job-pipeline.md) - Request processing pipeline

### Development
- **[Testing Guide](testing-guide.md)** - Comprehensive testing documentation
- **[Migration Guide](migration-guide.md)** - Upgrading between versions
- **[Contributing](contributing.md)** - How to contribute
- **[Development Setup](development-setup.md)** - Setting up dev environment

### Technical References
- **[Agent Development](agent-development.md)** - Creating new agents
- **[Workflow Development](workflow-development.md)** - Building workflows
- **[API Development](api-development.md)** - Extending the REST API
- **[Plugin System](plugin-system.md)** - Extension points

## 🚀 Getting Started

### For New Contributors
1. Read [Architecture Overview](architecture/README.md)
2. Set up [Development Environment](development-setup.md)
3. Review [Contributing Guidelines](contributing.md)
4. Run [Tests](testing-guide.md)

### For Agent Developers
1. Understand [ACP Architecture](architecture/acp-insights.md)
2. Read [Agent Development Guide](agent-development.md)
3. Study existing agents in `/agents/`

### For Workflow Developers
1. Review [Workflow Development](workflow-development.md)
2. Understand [Data Flow](../workflows/data-flow.md)
3. Study existing workflows in `/workflows/`

## 🏗️ System Architecture

### Core Components
- **Orchestrator** - Central coordination server
- **Agents** - Specialized task processors
- **Workflows** - Task execution patterns
- **API Server** - REST interface
- **Data Models** - Shared data structures

### Key Concepts
- Agent Communication Protocol (ACP)
- Streaming responses
- Error handling and retries
- Progress tracking
- Review integration

## 🧪 Testing

The project uses multiple testing approaches:
- **Unit Tests** - Component-level testing
- **Integration Tests** - System interaction testing
- **Workflow Tests** - End-to-end validation
- **Agent Tests** - Individual agent testing

See [Testing Guide](testing-guide.md) for details.

## 📊 Development Tools

### Recommended Setup
- Python 3.8+
- Virtual environment (uv recommended)
- Docker (for containerized testing)
- VS Code or PyCharm

### Useful Commands
```bash
# Run tests
python run.py test all

# Run specific workflow
python run.py workflow mvp_incremental --task "..."

# Generate visualizations
python workflows/workflow_visualizer.py

# Start development servers
python orchestrator/orchestrator_agent.py
python api/orchestrator_api.py
```

## 📚 Related Documentation

- [User Guide](../user-guide/README.md) - Usage documentation
- [Workflows](../workflows/README.md) - Workflow documentation
- [API Reference](../reference/api-reference.md) - REST API docs
- [Component READMEs](/agents/README.md) - Individual component docs

## 🤝 Contributing

We welcome contributions! Please:
1. Read [Contributing Guidelines](contributing.md)
2. Check existing issues and PRs
3. Follow code style guidelines
4. Add tests for new features
5. Update documentation

[← Back to Documentation Hub](../README.md)