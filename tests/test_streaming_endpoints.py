"""
Integration tests for real-time streaming endpoints.

This module tests WebSocket endpoints for real-time job and task status streaming,
ensuring proper connection management, event broadcasting, and error handling.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import redis.asyncio as redis

from src.api.v1.streaming.router import router as streaming_router, ConnectionManager, StreamingService
from src.api.v1.chatops.models import Job, Task, JobStatus, TaskStatus


class MockRedisClient:
    """Mock Redis client for testing streaming functionality."""
    
    def __init__(self):
        self.streams = {}
        self.scan_keys = []
    
    async def xadd(self, stream_name: str, fields: Dict[str, Any]) -> str:
        """Mock xadd operation."""
        if stream_name not in self.streams:
            self.streams[stream_name] = []
        
        message_id = f"{int(datetime.utcnow().timestamp() * 1000)}-0"
        self.streams[stream_name].append((message_id, fields))
        return message_id
    
    async def xread(self, streams: Dict[str, str], count: int = None, block: int = None) -> list:
        """Mock xread operation."""
        result = []
        for stream_name, last_id in streams.items():
            if stream_name in self.streams:
                messages = []
                for msg_id, fields in self.streams[stream_name]:
                    if msg_id > last_id:
                        messages.append((msg_id, fields))
                
                if messages:
                    result.append((stream_name, messages))
        
        return result
    
    async def scan_iter(self, match: str = None):
        """Mock scan_iter operation."""
        for key in self.scan_keys:
            if not match or key.startswith(match.replace("*", "")):
                yield key


class MockOrchestrator:
    """Mock orchestrator for testing streaming endpoints."""
    
    def __init__(self):
        self.jobs = {}
        self.async_redis_client = MockRedisClient()
    
    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID."""
        if job_id in self.jobs:
            return self.jobs[job_id]
        return None
    
    async def create_job(self, user_request: str, priority: str = "medium", tags: list = None) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            user_request=user_request,
            status=JobStatus.PLANNING,
            tasks=[],
            priority=priority,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.jobs[job_id] = job
        return job


@pytest.fixture
def mock_orchestrator():
    """Fixture providing a mock orchestrator."""
    return MockOrchestrator()


@pytest.fixture
def test_app(mock_orchestrator):
    """Fixture providing a test FastAPI app with streaming router."""
    app = FastAPI()
    app.include_router(streaming_router)
    
    # Override the orchestrator dependency
    from src.api.dependencies import get_orchestrator
    
    def get_test_orchestrator():
        return mock_orchestrator
    
    app.dependency_overrides[get_orchestrator] = get_test_orchestrator
    
    return app


@pytest.fixture
def client(test_app):
    """Fixture providing a test client."""
    return TestClient(test_app)


class TestConnectionManager:
    """Test cases for the ConnectionManager class."""
    
    @pytest.fixture
    def manager(self):
        """Fixture providing a connection manager."""
        return ConnectionManager()
    
    def test_connection_manager_initialization(self, manager):
        """Test connection manager initializes correctly."""
        assert isinstance(manager.active_connections, dict)
        assert isinstance(manager.global_connections, set)
        assert len(manager.active_connections) == 0
        assert len(manager.global_connections) == 0
    
    @pytest.mark.asyncio
    async def test_job_specific_connection(self, manager):
        """Test job-specific connection management."""
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        
        job_id = "test-job-123"
        
        # Test connection
        await manager.connect(mock_websocket, job_id)
        
        assert job_id in manager.active_connections
        assert mock_websocket in manager.active_connections[job_id]
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_global_connection(self, manager):
        """Test global connection management."""
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        
        # Test connection
        await manager.connect(mock_websocket)
        
        assert mock_websocket in manager.global_connections
        mock_websocket.accept.assert_called_once()
    
    def test_disconnect_job_specific(self, manager):
        """Test disconnecting job-specific connections."""
        mock_websocket = MagicMock()
        job_id = "test-job-123"
        
        # Setup connection
        manager.active_connections[job_id] = {mock_websocket}
        
        # Test disconnection
        manager.disconnect(mock_websocket, job_id)
        
        assert job_id not in manager.active_connections
    
    def test_disconnect_global(self, manager):
        """Test disconnecting global connections."""
        mock_websocket = MagicMock()
        
        # Setup connection
        manager.global_connections.add(mock_websocket)
        
        # Test disconnection
        manager.disconnect(mock_websocket)
        
        assert mock_websocket not in manager.global_connections
    
    @pytest.mark.asyncio
    async def test_send_to_job(self, manager):
        """Test sending messages to job-specific connections."""
        mock_websocket = MagicMock()
        mock_websocket.send_json = AsyncMock()
        
        job_id = "test-job-123"
        manager.active_connections[job_id] = {mock_websocket}
        
        message = {"event_type": "test", "data": "test_data"}
        
        await manager.send_to_job(job_id, message)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_to_all(self, manager):
        """Test sending messages to all global connections."""
        mock_websocket = MagicMock()
        mock_websocket.send_json = AsyncMock()
        
        manager.global_connections.add(mock_websocket)
        
        message = {"event_type": "test", "data": "test_data"}
        
        await manager.send_to_all(message)
        
        mock_websocket.send_json.assert_called_once_with(message)


class TestStreamingService:
    """Test cases for the StreamingService class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Fixture providing a mock Redis client."""
        return MockRedisClient()
    
    @pytest.fixture
    def mock_manager(self):
        """Fixture providing a mock connection manager."""
        manager = MagicMock()
        manager.send_to_job = AsyncMock()
        manager.send_to_all = AsyncMock()
        return manager
    
    @pytest.fixture
    def streaming_service(self, mock_redis, mock_manager):
        """Fixture providing a streaming service."""
        return StreamingService(mock_redis, mock_manager)
    
    @pytest.mark.asyncio
    async def test_streaming_service_initialization(self, streaming_service):
        """Test streaming service initializes correctly."""
        assert not streaming_service.running
        assert streaming_service.stream_task is None
    
    @pytest.mark.asyncio
    async def test_start_streaming(self, streaming_service):
        """Test starting the streaming service."""
        await streaming_service.start_streaming()
        
        assert streaming_service.running
        assert streaming_service.stream_task is not None
        
        # Cleanup
        await streaming_service.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_stop_streaming(self, streaming_service):
        """Test stopping the streaming service."""
        await streaming_service.start_streaming()
        await streaming_service.stop_streaming()
        
        assert not streaming_service.running
    
    @pytest.mark.asyncio
    async def test_broadcast_update(self, streaming_service):
        """Test broadcasting updates to WebSocket connections."""
        job_id = "test-job-123"
        event_data = {
            "event_type": "task_completed",
            "job_id": job_id,
            "task_id": "task-456",
            "result": '{"status": "success"}'
        }
        
        await streaming_service._broadcast_update(job_id, event_data)
        
        # Verify calls to connection manager
        streaming_service.manager.send_to_job.assert_called_once()
        streaming_service.manager.send_to_all.assert_called_once()
        
        # Verify result parsing
        call_args = streaming_service.manager.send_to_job.call_args[0]
        assert call_args[0] == job_id
        assert call_args[1]["result"] == {"status": "success"}


class TestStreamingEndpoints:
    """Test cases for streaming WebSocket endpoints."""
    
    def test_streaming_health_endpoint(self, client):
        """Test the streaming health check endpoint."""
        response = client.get("/api/v1/streaming/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "streaming_active" in data
        assert "active_connections" in data
        assert "timestamp" in data
        
        assert data["status"] == "healthy"
        assert isinstance(data["streaming_active"], bool)
        assert "job_specific" in data["active_connections"]
        assert "global" in data["active_connections"]


class TestWebSocketConnections:
    """Test cases for WebSocket connection handling."""
    
    @pytest.mark.asyncio
    async def test_websocket_job_connection_with_existing_job(self, client, mock_orchestrator):
        """Test WebSocket connection for existing job."""
        # Create a test job
        job = await mock_orchestrator.create_job("Test job request")
        job_id = job.job_id
        
        # Add some tasks to the job
        task = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="code",
            status=TaskStatus.PENDING,
            description="Test task",
            dependencies=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        job.tasks.append(task)
        mock_orchestrator.jobs[job_id] = job
        
        # Test WebSocket connection
        with client.websocket_connect(f"/api/v1/streaming/jobs/{job_id}") as websocket:
            # Should receive initial job status
            data = websocket.receive_json()
            
            assert data["event_type"] == "job_status"
            assert data["job_id"] == job_id
            assert data["status"] == "planning"
            assert len(data["tasks"]) == 1
            assert "progress" in data
            assert data["progress"]["total_tasks"] == 1
            assert data["progress"]["completed_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_websocket_job_connection_with_nonexistent_job(self, client, mock_orchestrator):
        """Test WebSocket connection for non-existent job."""
        non_existent_job_id = str(uuid.uuid4())
        
        # Test WebSocket connection
        with client.websocket_connect(f"/api/v1/streaming/jobs/{non_existent_job_id}") as websocket:
            # Should receive error message
            data = websocket.receive_json()
            
            assert data["event_type"] == "error"
            assert f"Job {non_existent_job_id} not found" in data["message"]
    
    @pytest.mark.asyncio
    async def test_websocket_global_connection(self, client):
        """Test global WebSocket connection."""
        # Test WebSocket connection
        with client.websocket_connect("/api/v1/streaming/jobs") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            
            assert data["event_type"] == "connected"
            assert "Connected to global job stream" in data["message"]
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, client, mock_orchestrator):
        """Test WebSocket ping/pong functionality."""
        # Create a test job
        job = await mock_orchestrator.create_job("Test job request")
        job_id = job.job_id
        
        # Test WebSocket connection
        with client.websocket_connect(f"/api/v1/streaming/jobs/{job_id}") as websocket:
            # Receive initial status
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_json(self, client, mock_orchestrator):
        """Test WebSocket handling of invalid JSON."""
        # Create a test job
        job = await mock_orchestrator.create_job("Test job request")
        job_id = job.job_id
        
        # Test WebSocket connection
        with client.websocket_connect(f"/api/v1/streaming/jobs/{job_id}") as websocket:
            # Receive initial status
            websocket.receive_json()
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error message
            data = websocket.receive_json()
            assert data["event_type"] == "error"
            assert "Invalid JSON message" in data["message"]


class TestRealTimeEventFlow:
    """Test cases for end-to-end real-time event flow."""
    
    @pytest.mark.asyncio
    async def test_job_creation_to_completion_flow(self, mock_orchestrator):
        """Test complete job lifecycle with real-time events."""
        # Setup streaming service
        manager = ConnectionManager()
        streaming_service = StreamingService(mock_orchestrator.async_redis_client, manager)
        
        # Create a job
        job = await mock_orchestrator.create_job("Build authentication system")
        job_id = job.job_id
        
        # Add tasks to the job
        task1 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="design",
            status=TaskStatus.PENDING,
            description="Design authentication system",
            dependencies=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        task2 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="code",
            status=TaskStatus.PENDING,
            description="Implement authentication system",
            dependencies=[task1.task_id],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        job.tasks = [task1, task2]
        mock_orchestrator.jobs[job_id] = job
        
        # Simulate task completion events
        await mock_orchestrator.async_redis_client.xadd(
            f"job-stream:{job_id}",
            {
                "event_type": "task_status_changed",
                "job_id": job_id,
                "task_id": task1.task_id,
                "status": "running",
                "previous_status": "pending"
            }
        )
        
        await mock_orchestrator.async_redis_client.xadd(
            f"job-stream:{job_id}",
            {
                "event_type": "task_completed",
                "job_id": job_id,
                "task_id": task1.task_id,
                "result": '{"status": "success", "output": "Design completed"}'
            }
        )
        
        # Verify events were stored in Redis streams
        assert f"job-stream:{job_id}" in mock_orchestrator.async_redis_client.streams
        events = mock_orchestrator.async_redis_client.streams[f"job-stream:{job_id}"]
        assert len(events) == 2
        
        # Verify event content
        assert events[0][1]["event_type"] == "task_status_changed"
        assert events[1][1]["event_type"] == "task_completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
