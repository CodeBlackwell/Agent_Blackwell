# Agent Blackwell Frontend Integration Plan

## 🔍 Critical Context & Project Overview

Agent Blackwell is a modular LLM-powered agent orchestration system that consists of five specialized agents working together through Redis streams and Pinecone vector DB:

1. **Spec Agent**: Converts high-level requirements into detailed tasks
2. **Design Agent**: Creates architecture diagrams and API contracts
3. **Coding Agent**: Generates code based on specifications and designs
4. **Review Agent**: Performs code reviews and security analyses
5. **Test Agent**: Creates comprehensive test suites

The system is built on:
- **Python 3.11+** with FastAPI
- **LangChain** for agent framework
- **Redis Streams** for inter-agent communication
- **Pinecone** for vector storage
- **Kubernetes/Helm** for deployment

## 📝 Backend Changes Required for Frontend Integration

### Phase 1: Core API Endpoints (Priority)

#### 1. Authentication System
- **Implementation Needed**: Create JWT-based authentication with refresh tokens
- **Files to Create**:
  - `src/api/v1/auth/router.py`: Login, register, and token refresh endpoints
  - `src/api/v1/auth/models.py`: User and token schemas
  - `src/api/v1/auth/dependencies.py`: Authentication dependencies
- **Changes to Existing Files**:
  - `src/api/main.py`: Add auth router
  - Create database models for user storage

```python
# Example auth router to implement
@router.post("/auth/login")
async def login(credentials: UserLogin) -> TokenResponse:
    # Validate credentials and return JWT tokens
    pass

@router.post("/auth/register")
async def register(user_data: UserRegister) -> UserResponse:
    # Create new user and return details
    pass
```

#### 2. Extended Task Management API
- **Implementation Needed**: Additional endpoints for task listing, filtering, and actions
- **New Endpoints**:
  - `GET /api/v1/tasks`: List all tasks with pagination and filters
  - `GET /api/v1/tasks/{task_id}/details`: Detailed task information
  - `POST /api/v1/tasks/{task_id}/cancel`: Cancel a running task
  - `GET /api/v1/tasks/summary`: Task statistics and summary
- **Files to Create/Modify**:
  - `src/api/v1/tasks/router.py`: Task management endpoints
  - `src/api/v1/tasks/models.py`: Task-related schemas
  - `src/orchestrator/main.py`: Add task cancellation functionality

```python
# Example tasks listing endpoint to implement
@router.get("/tasks", response_model=PaginatedTasks)
async def list_tasks(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    orchestrator: Orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    # Get tasks with pagination and optional filtering
    pass
```

#### 3. Agent Management API
- **Implementation Needed**: Endpoints to list and configure agents
- **New Endpoints**:
  - `GET /api/v1/agents`: List all registered agents
  - `GET /api/v1/agents/{agent_id}`: Get agent details
  - `GET /api/v1/agents/{agent_id}/stats`: Get agent performance stats
  - `PATCH /api/v1/agents/{agent_id}/config`: Update agent configuration
- **Files to Create/Modify**:
  - `src/api/v1/agents/router.py`: Agent management endpoints
  - `src/api/v1/agents/models.py`: Agent-related schemas
  - `src/orchestrator/agent_registry.py`: Add methods to get agent details

#### 4. WebSocket Implementation for Real-time Updates
- **Implementation Needed**: WebSocket endpoints for live updates
- **New Endpoints**:
  - `WebSocket /api/v1/ws/tasks`: Stream task status updates
  - `WebSocket /api/v1/ws/agents`: Stream agent activity
- **Files to Create/Modify**:
  - `src/api/v1/ws/router.py`: WebSocket connection handler
  - `src/api/v1/ws/manager.py`: Connection management
  - `src/orchestrator/main.py`: Add event emitting on status changes

```python
# Example WebSocket implementation
@router.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Handle incoming messages or just keep connection open
            data = await websocket.receive_text()
            # Process if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Phase 2: Advanced Features

#### 5. System Configuration API
- **Implementation Needed**: API for retrieving and updating system configs
- **New Endpoints**:
  - `GET /api/v1/config`: Get system configuration
  - `PATCH /api/v1/config`: Update configuration settings
- **Files to Create**:
  - `src/api/v1/config/router.py`: Configuration endpoints
  - `src/config/`: Configuration management system

#### 6. Results & Artifacts API
- **Implementation Needed**: APIs for retrieving agent-generated artifacts
- **New Endpoints**:
  - `GET /api/v1/artifacts/{task_id}`: List artifacts for a task
  - `GET /api/v1/artifacts/{task_id}/{artifact_id}`: Get specific artifact
- **Files to Create**:
  - `src/api/v1/artifacts/router.py`: Artifact endpoints
  - `src/storage/`: Artifact storage system

## 🔑 Critical Notes on System Architecture

### Agent Orchestration
- **Orchestrator**: Central component managing task flow between agents
- **Redis Streams**: Used as message broker between orchestrator and agents
  - Consumer groups ensure each task is processed once
  - Stream keys follow pattern: `agent-blackwell:tasks:{task_type}`
- **Agent Registry**: Maintains references to all agent instances
  - Each agent is wrapped in a class that provides standard `ainvoke` method
  - Wrappers handle input/output formatting for the orchestrator

```python
# Example of how agent wrappers work
class SpecAgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    async def ainvoke(self, task):
        # Pre-process task for spec agent
        result = await self.agent.run(task["prompt"])
        # Post-process result for orchestrator
        return {"subtasks": parse_subtasks(result)}
```

### Data Flow
1. User input → API → Orchestrator → Spec Agent
2. Spec Agent output → Orchestrator → Design Agent
3. Design Agent output → Orchestrator → Coding Agent
4. Coding Agent output → Orchestrator → Review Agent
5. Review Agent output → Orchestrator → Test Agent
6. Test Agent output → Orchestrator → API → User

### Authentication & Security
- All API endpoints except health checks should require authentication
- Use JWT with short expiry + refresh token pattern
- Store user credentials securely with proper hashing (Argon2id recommended)
- API keys for service-to-service communication
- CORS configuration in main.py needs updating for frontend domains

### Performance Considerations
- Agent operations are CPU and memory intensive
- Long-running tasks should be processed asynchronously
- WebSockets can cause memory leaks if not managed properly
- Consider connection pooling for Redis and database connections

## 🛠 Development Environment Setup

### Required Environment Variables
```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_environment
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=complex_random_string_min_32_chars
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:3000
```

### Local Development Commands
```bash
# Start backend services with Docker Compose
docker-compose up -d

# Run API server in development mode
python -m src.api.main

# Run tests
pytest

# Check code style
pre-commit run --all-files
```

## 📊 Database Schema for User Management

For user authentication, we need to add a database. Suggested schema:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE
);
```

## 🔄 API Response Formats

For consistent frontend integration, standardize on these response formats:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid credentials provided"
  }
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 2,
    "limit": 20,
    "pages": 5
  }
}
```

## 📈 Testing Strategy

- Unit tests for all new API endpoints
- Integration tests for authentication flow
- WebSocket connection tests
- Mock Redis streams for testing real-time updates
- Test frontend-backend integration with end-to-end tests

## 🚀 Implementation Roadmap

1. **Week 1**: Authentication system and core API extensions
2. **Week 2**: WebSocket implementation and agent management API
3. **Week 3**: Extended task management and artifact APIs
4. **Week 4**: System configuration API and frontend integration testing

## 🧪 Testing the API with Frontend

Test the API endpoints with a simple React app before full implementation:

```bash
# Using create-react-app with TypeScript
npx create-react-app agent-blackwell-ui --template typescript

# Install dependencies
cd agent-blackwell-ui
npm install axios @mui/material @emotion/react @emotion/styled react-router-dom
```

## 🔗 Links to Key Documentation

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [JWT Authentication with FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [React Query for API Data Fetching](https://tanstack.com/query/latest)
- [Material-UI Components](https://mui.com/components/)

---

This plan will evolve as implementation progresses. Regular reviews will adjust priorities and incorporate new requirements.
