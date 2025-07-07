# Architecture Overview

The Multi-Agent Orchestrator System implements a modular, event-driven architecture based on the Agent Communication Protocol (ACP). This document provides an overview of the system design and key architectural decisions.

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   REST API      │────▶│   Orchestrator   │────▶│     Agents      │
│  (Port 8000)    │     │   (Port 8080)    │     │  (Specialized)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Workflows     │     │  Workflow Mgr    │     │   Data Models   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Core Components

1. **Orchestrator Agent** (`orchestrator/orchestrator_agent.py`)
   - Central coordination server
   - Implements ACP server on port 8080
   - Routes requests to appropriate workflows
   - Manages agent communication

2. **REST API Server** (`api/orchestrator_api.py`)
   - HTTP interface on port 8000
   - Async request handling
   - Session-based tracking
   - External integration point

3. **Specialized Agents** (`agents/` directory)
   - Planner Agent - Requirements analysis
   - Designer Agent - Technical design
   - Coder Agent - Implementation
   - Test Writer Agent - Test generation
   - Reviewer Agent - Code review
   - Executor Agent - Code execution

4. **Workflow Manager** (`workflows/workflow_manager.py`)
   - Workflow type routing
   - Execution coordination
   - Progress tracking
   - Error handling

## 📋 Detailed Documentation

### Architecture Documents
- **[ACP Architecture Insights](acp-insights.md)** - Agent Communication Protocol details
- **[Implementation Guide](implementation-guide.md)** - Building system components
- **[Architectural Lessons](lessons-learned.md)** - Design decisions and rationale
- **[Job Pipeline Implementation](job-pipeline.md)** - Request processing pipeline

### Design Principles

1. **Modularity**
   - Each agent is self-contained
   - Workflows are pluggable
   - Clear separation of concerns

2. **Scalability**
   - Async/await throughout
   - Streaming responses
   - Stateless agent design

3. **Reliability**
   - Comprehensive error handling
   - Retry mechanisms
   - Progress tracking
   - Validation at each step

4. **Flexibility**
   - Multiple workflow types
   - Configurable behavior
   - Extension points

## 🔄 Data Flow

1. **Request Flow**
   ```
   Client → REST API → Orchestrator → Workflow Manager → Agents
   ```

2. **Response Flow**
   ```
   Agents → Workflow Manager → Orchestrator → REST API → Client
   ```

3. **Streaming Updates**
   - Real-time progress updates
   - Incremental output delivery
   - Error propagation

See [Workflow Data Flow](../../workflows/data-flow.md) for detailed information.

## 🧩 Key Patterns

### Agent Communication Protocol (ACP)
- Standardized message format
- Request/response pattern
- Streaming support
- Error handling

### Workflow Orchestration
- Phase-based execution
- Dependency management
- Progress tracking
- Result aggregation

### Error Handling
- Graceful degradation
- Retry strategies
- Error context preservation
- User-friendly messages

## 🔧 Technology Stack

- **Language**: Python 3.8+
- **Async Framework**: asyncio
- **HTTP Framework**: FastAPI
- **Testing**: pytest, unittest
- **Containerization**: Docker
- **Code Execution**: Docker containers

## 📊 Performance Considerations

- Async I/O for concurrent operations
- Streaming to reduce memory usage
- Efficient serialization
- Connection pooling
- Resource cleanup

## 🔒 Security

- Input validation
- Sandboxed code execution
- API authentication (extensible)
- Rate limiting (configurable)
- Audit logging

## 📚 Related Documentation

- [Developer Guide](../README.md) - Main developer documentation
- [Testing Guide](../testing-guide.md) - Testing strategies
- [Workflow Documentation](../../workflows/README.md) - Workflow details
- [API Reference](../../reference/api-reference.md) - REST API docs

[← Back to Developer Guide](../README.md)