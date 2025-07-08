# API Development Guide

## Overview

This guide covers the development and extension of the REST API for the Multi-Agent Orchestrator System. The API provides HTTP endpoints for external applications to interact with the orchestrator, submit workflow requests, and monitor execution progress.

## API Architecture

### Core Components

1. **FastAPI Application** (`api/orchestrator_api.py`)
   - RESTful endpoint definitions
   - Request/response models
   - Background task management

2. **Request Handlers**
   - Validate incoming requests
   - Route to appropriate workflows
   - Manage asynchronous execution

3. **Response Models**
   - Standardized response formats
   - Error handling structures
   - Progress tracking schemas

## Current API Endpoints

### Core Endpoints

```python
# Workflow execution
POST   /execute-workflow      # Submit new workflow request
GET    /workflow-status/{id}  # Check workflow progress
GET    /workflow-types        # List available workflows

# System endpoints  
GET    /health               # Health check
GET    /metrics              # System metrics
```

## Adding New Endpoints

### Step 1: Define Request/Response Models

```python
# api/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class CustomWorkflowRequest(BaseModel):
    """Request model for custom workflow"""
    requirements: str = Field(..., description="Task requirements")
    workflow_type: str = Field(..., description="Type of workflow to execute")
    configuration: Optional[Dict[str, any]] = Field(default_factory=dict)
    priority: Optional[str] = Field(default="normal", pattern="^(low|normal|high|critical)$")
    
class CustomWorkflowResponse(BaseModel):
    """Response model for custom workflow"""
    session_id: str
    status: str
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    
class WorkflowProgressResponse(BaseModel):
    """Progress tracking response"""
    session_id: str
    status: str
    progress: float = Field(..., ge=0, le=100)
    current_phase: Optional[str] = None
    phases_completed: List[str] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    partial_results: Optional[Dict[str, any]] = None
```

### Step 2: Implement Endpoint Handler

```python
# api/endpoints/custom_workflow.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
from datetime import datetime

from api.models import CustomWorkflowRequest, CustomWorkflowResponse
from workflows.workflow_manager import execute_workflow

router = APIRouter(prefix="/custom", tags=["custom-workflows"])

# In-memory storage (replace with database for production)
workflow_storage: Dict[str, Dict[str, Any]] = {}

@router.post("/execute", response_model=CustomWorkflowResponse)
async def execute_custom_workflow(
    request: CustomWorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute a custom workflow with advanced options"""
    
    # Validate workflow type
    if request.workflow_type not in get_available_workflows():
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow type: {request.workflow_type}"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Initialize workflow status
    workflow_storage[session_id] = {
        "status": "queued",
        "created_at": datetime.now(),
        "request": request.dict(),
        "progress": 0,
        "results": None,
        "error": None
    }
    
    # Add to background tasks
    background_tasks.add_task(
        run_custom_workflow,
        session_id,
        request
    )
    
    return CustomWorkflowResponse(
        session_id=session_id,
        status="queued",
        message="Workflow queued for execution",
        created_at=datetime.now(),
        estimated_completion=calculate_estimated_completion(request)
    )

async def run_custom_workflow(session_id: str, request: CustomWorkflowRequest):
    """Background task to run workflow"""
    try:
        # Update status
        workflow_storage[session_id]["status"] = "running"
        workflow_storage[session_id]["started_at"] = datetime.now()
        
        # Execute workflow with progress tracking
        async for update in execute_workflow_with_progress(
            requirements=request.requirements,
            workflow_type=request.workflow_type,
            config=request.configuration
        ):
            # Update progress
            if update["type"] == "progress":
                workflow_storage[session_id]["progress"] = update["value"]
                workflow_storage[session_id]["current_phase"] = update.get("phase")
            elif update["type"] == "phase_complete":
                phases = workflow_storage[session_id].get("phases_completed", [])
                phases.append(update["phase"])
                workflow_storage[session_id]["phases_completed"] = phases
            elif update["type"] == "final_result":
                workflow_storage[session_id]["results"] = update["results"]
        
        # Mark as completed
        workflow_storage[session_id]["status"] = "completed"
        workflow_storage[session_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        # Handle errors
        workflow_storage[session_id]["status"] = "failed"
        workflow_storage[session_id]["error"] = str(e)
        workflow_storage[session_id]["failed_at"] = datetime.now()
```

### Step 3: Add Endpoint to Main Application

```python
# api/orchestrator_api.py

from api.endpoints import custom_workflow

# Add to FastAPI app
app.include_router(custom_workflow.router)
```

## Advanced API Features

### 1. WebSocket Support

```python
# api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
    
    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection closed, remove it
                    self.active_connections[session_id].discard(connection)

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
```

### 2. Authentication & Authorization

```python
# api/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

security = HTTPBearer()

SECRET_KEY = "your-secret-key"  # Use environment variable in production
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# Protected endpoint example
@app.post("/protected/execute-workflow")
async def protected_execute(
    request: WorkflowRequest,
    current_user: str = Depends(get_current_user)
):
    # User is authenticated
    return await execute_workflow_endpoint(request)
```

### 3. Rate Limiting

```python
# api/rate_limit.py

from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, calls: int = 10, period: int = 60):
        self.calls = calls
        self.period = timedelta(seconds=period)
        self.clients = defaultdict(list)
        
    async def __call__(self, request: Request):
        client_id = request.client.host
        now = datetime.now()
        
        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if now - timestamp < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_id]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.clients[client_id].append(now)

# Apply rate limiting
rate_limiter = RateLimiter(calls=10, period=60)

@app.post("/execute-workflow", dependencies=[Depends(rate_limiter)])
async def rate_limited_execute(request: WorkflowRequest):
    return await execute_workflow_endpoint(request)
```

### 4. API Versioning

```python
# api/v1/endpoints.py
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

@v1_router.post("/execute-workflow")
async def execute_workflow_v1(request: WorkflowRequest):
    # V1 implementation
    pass

# api/v2/endpoints.py  
v2_router = APIRouter(prefix="/api/v2")

@v2_router.post("/execute-workflow")
async def execute_workflow_v2(request: WorkflowRequestV2):
    # V2 implementation with new features
    pass

# Main app
app.include_router(v1_router)
app.include_router(v2_router)
```

## Error Handling

### Standard Error Response

```python
# api/errors.py

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None

class APIError(HTTPException):
    def __init__(
        self, 
        status_code: int, 
        error: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.error = error
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)

# Custom exception handler
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            message=exc.message,
            details=exc.details,
            timestamp=datetime.now(),
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )

# Usage
if not validate_input(request):
    raise APIError(
        status_code=400,
        error="INVALID_INPUT",
        message="The provided input is invalid",
        details={"field": "requirements", "issue": "too short"}
    )
```

## Testing API Endpoints

### 1. Unit Tests

```python
# tests/unit/api/test_endpoints.py

from fastapi.testclient import TestClient
from api.orchestrator_api import app

client = TestClient(app)

def test_execute_workflow():
    response = client.post(
        "/execute-workflow",
        json={
            "requirements": "Create a calculator",
            "workflow_type": "full"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "accepted"

def test_invalid_workflow_type():
    response = client.post(
        "/execute-workflow",
        json={
            "requirements": "Test",
            "workflow_type": "invalid"
        }
    )
    assert response.status_code == 400
    assert "Unknown workflow type" in response.json()["detail"]
```

### 2. Integration Tests

```python
# tests/integration/api/test_full_flow.py

import asyncio
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_full_workflow_execution():
    with TestClient(app) as client:
        # Submit workflow
        response = client.post(
            "/execute-workflow",
            json={
                "requirements": "Create a simple API",
                "workflow_type": "full"
            }
        )
        session_id = response.json()["session_id"]
        
        # Poll for completion
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = client.get(f"/workflow-status/{session_id}")
            status = status_response.json()["status"]
            
            if status in ["completed", "failed"]:
                break
                
            await asyncio.sleep(2)
        
        # Verify completion
        assert status == "completed"
        assert "generated_code" in status_response.json()
```

## API Documentation

### 1. OpenAPI/Swagger

FastAPI automatically generates OpenAPI documentation:

```python
# Customize OpenAPI schema
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="Multi-Agent Orchestrator API",
        version="1.0.0",
        description="API for orchestrating AI agents in software development workflows",
        routes=app.routes,
    )
    
    # Add custom documentation
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 2. ReDoc Documentation

```python
# Enable ReDoc
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Multi-Agent Orchestrator API",
    description="Complete API documentation",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)
```

## Performance Optimization

### 1. Response Caching

```python
# api/cache.py

from functools import lru_cache
from typing import Optional
import hashlib
import json

class APICache:
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
        
    def get_key(self, endpoint: str, params: dict) -> str:
        content = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
        return None
    
    async def set(self, key: str, data: dict):
        self.cache[key] = (data, datetime.now())

cache = APICache()

# Use in endpoint
@app.get("/workflow-types")
async def get_workflow_types_cached():
    cache_key = cache.get_key("workflow-types", {})
    
    # Check cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Generate fresh data
    data = {"workflow_types": get_available_workflows()}
    await cache.set(cache_key, data)
    
    return data
```

### 2. Database Connection Pooling

```python
# api/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine with connection pooling
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/db",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Create session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency for endpoints
async def get_db():
    async with async_session() as session:
        yield session
```

## Deployment Considerations

### 1. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Related Documentation

- [Architecture Overview](architecture/README.md)
- [API Reference](../reference/api-reference.md)
- [Testing Guide](testing-guide.md)
- [Deployment Guide](../operations/deployment.md)