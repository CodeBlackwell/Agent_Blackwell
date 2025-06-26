"""
Phase 5 Integration Tests: REST API Endpoints

This module contains integration tests for all REST API endpoints,
including ChatOps, feature requests, health checks, and error handling.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app
from src.orchestrator.main import Orchestrator


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = MagicMock(spec=Orchestrator)
    orchestrator.enqueue_task = AsyncMock()
    orchestrator.get_task_status = AsyncMock()
    orchestrator.submit_feature_request = AsyncMock()
    return orchestrator


@pytest.fixture(autouse=True)
def mock_orchestrator_dependency(mock_orchestrator):
    """Override the orchestrator dependency with mock."""
    from src.api.dependencies import get_orchestrator
    
    def override_get_orchestrator():
        return mock_orchestrator
    
    app.dependency_overrides[get_orchestrator] = override_get_orchestrator
    yield
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check and status endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Agent Blackwell API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"
    
    @patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"})
    @patch("redis.asyncio.from_url")
    def test_health_check_endpoint_with_redis(self, mock_redis_from_url, client):
        """Test health check endpoint with Redis connectivity."""
        # Mock Redis client and ping
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock()
        mock_redis_client.close = AsyncMock()
        mock_redis_from_url.return_value = mock_redis_client
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "services" in data
        assert "redis" in data["services"]
    
    def test_health_check_endpoint_minimal(self, client):
        """Test health check endpoint without external dependencies."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "services" in data
        assert data["services"]["api"] == "up"


class TestChatOpsEndpoints:
    """Test ChatOps command processing endpoints."""
    
    def test_help_command(self, client, mock_orchestrator):
        """Test the !help command processing."""
        command_request = {
            "command": "!help",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "Available Commands" in data["message"]
        assert "!spec" in data["message"]
        assert "!design" in data["message"]
        assert "!code" in data["message"]
    
    def test_spec_agent_command(self, client, mock_orchestrator):
        """Test the !spec command for specification generation."""
        mock_orchestrator.enqueue_task.return_value = "task-spec-123"
        
        command_request = {
            "command": "!spec Create a REST API for user management",
            "platform": "slack", 
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "task has been queued" in data["message"]
        assert "task-spec-123" in data["message"]
        
        # Verify orchestrator was called correctly
        mock_orchestrator.enqueue_task.assert_called_once_with(
            "spec", 
            {"description": "Create a REST API for user management"}
        )
    
    def test_design_agent_command(self, client, mock_orchestrator):
        """Test the !design command for system design."""
        mock_orchestrator.enqueue_task.return_value = "task-design-456"
        
        command_request = {
            "command": "!design Microservices architecture with API gateway",
            "platform": "teams",
            "user_id": "designer_user", 
            "channel_id": "design_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "task-design-456" in data["message"]
        
        mock_orchestrator.enqueue_task.assert_called_once_with(
            "design",
            {"description": "Microservices architecture with API gateway"}
        )
    
    def test_status_command(self, client, mock_orchestrator):
        """Test the !status command for task status inquiry."""
        mock_orchestrator.get_task_status.return_value = {
            "status": "completed",
            "progress": 100,
            "created_at": "2025-06-26T12:00:00Z",
            "updated_at": "2025-06-26T12:05:00Z",
            "result": "Specification generated successfully"
        }
        
        command_request = {
            "command": "!status task-123",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "Status for Task task-123" in data["message"]
        assert "completed" in data["message"]
        assert "100%" in data["message"]
        
        mock_orchestrator.get_task_status.assert_called_once_with("task-123")
    
    def test_status_command_with_parameter(self, client, mock_orchestrator):
        """Test the !status command with --id parameter."""
        mock_orchestrator.get_task_status.return_value = {
            "status": "in_progress", 
            "progress": 75,
            "created_at": "2025-06-26T12:00:00Z",
            "updated_at": "2025-06-26T12:03:00Z"
        }
        
        command_request = {
            "command": "!status --id=task-456",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Status for Task task-456" in data["message"]
        assert "in_progress" in data["message"]
        assert "75%" in data["message"]
    
    def test_deploy_command(self, client, mock_orchestrator):
        """Test the !deploy command functionality."""
        mock_orchestrator.enqueue_task.return_value = "deploy-task-789"
        
        command_request = {
            "command": "!deploy my-app --env=staging",
            "platform": "slack",
            "user_id": "deploy_user",
            "channel_id": "ops_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "🚀 Deployment of my-app to staging" in data["message"]
        assert "deploy-task-789" in data["message"]
        
        mock_orchestrator.enqueue_task.assert_called_once_with(
            "deploy",
            {"app_name": "my-app", "environment": "staging"}
        )
    
    def test_invalid_command_format(self, client, mock_orchestrator):
        """Test handling of invalid command formats."""
        command_request = {
            "command": "invalid command without exclamation",
            "platform": "slack",
            "user_id": "test_user", 
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Invalid command format" in data["message"]
        assert "Commands should start with '!'" in data["message"]
    
    def test_missing_task_description(self, client, mock_orchestrator):
        """Test handling of agent commands without descriptions."""
        command_request = {
            "command": "!spec",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "requires a description" in data["message"]
        assert "Usage: !spec <description>" in data["message"]


class TestTaskStatusEndpoints:
    """Test task status inquiry endpoints."""
    
    def test_get_task_status_endpoint(self, client, mock_orchestrator):
        """Test the dedicated task status endpoint."""
        mock_orchestrator.get_task_status.return_value = {
            "task_id": "test-task-123",
            "status": "completed",
            "progress": 100,
            "created_at": "2025-06-26T12:00:00Z",
            "updated_at": "2025-06-26T12:05:00Z",
            "result": {"output": "Task completed successfully"}
        }
        
        response = client.get("/api/v1/chatops/tasks/test-task-123/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "result" in data
        
        mock_orchestrator.get_task_status.assert_called_once_with("test-task-123")
    
    def test_get_task_status_not_found(self, client, mock_orchestrator):
        """Test handling of non-existent task status requests."""
        mock_orchestrator.get_task_status.return_value = None
        
        response = client.get("/api/v1/chatops/tasks/nonexistent-task/status")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "not found" in data["detail"].lower()


class TestFeatureRequestEndpoints:
    """Test feature request submission endpoints."""
    
    def test_submit_feature_request(self, client, mock_orchestrator):
        """Test feature request submission."""
        mock_orchestrator.submit_feature_request.return_value = "feature-req-456"
        
        request_payload = {
            "title": "Add API Rate Limiting",
            "description": "Implement rate limiting for all API endpoints",
            "priority": "high",
            "requester": "product_team"
        }
        
        response = client.post("/api/v1/feature_request", json=request_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "task_id" in data
        assert data["task_id"] == "feature-req-456"
        assert data["status"] == "queued"
        
        mock_orchestrator.submit_feature_request.assert_called_once()


class TestErrorHandling:
    """Test API error handling and edge cases."""
    
    def test_global_exception_handler(self, client, mock_orchestrator):
        """Test global exception handling."""
        # Mock orchestrator to raise an exception
        mock_orchestrator.enqueue_task.side_effect = Exception("Database connection failed")
        
        command_request = {
            "command": "!spec Test exception handling",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = client.post("/api/v1/chatops/command", json=command_request)
        
        # The global exception handler should catch this and return 500
        assert response.status_code == 500
        data = response.json()
        
        assert "An unexpected error occurred" in data["detail"]
    
    def test_malformed_request_data(self, client):
        """Test handling of malformed request data."""
        # Send invalid JSON
        response = client.post(
            "/api/v1/chatops/command",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test handling of requests with missing required fields."""
        incomplete_request = {
            "command": "!help"
            # Missing platform, user_id, channel_id
        }
        
        response = client.post("/api/v1/chatops/command", json=incomplete_request)
        
        assert response.status_code == 422
        data = response.json()
        
        assert "detail" in data
        # Should indicate missing fields
        assert any("required" in str(error).lower() for error in data["detail"])


class TestAPIPerformance:
    """Test API performance and response times."""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, mock_orchestrator):
        """Test handling of concurrent API requests."""
        mock_orchestrator.enqueue_task.return_value = "concurrent-task"
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                request_data = {
                    "command": f"!spec Concurrent test {i}",
                    "platform": "slack",
                    "user_id": f"user_{i}",
                    "channel_id": "test_channel"
                }
                tasks.append(ac.post("/api/v1/chatops/command", json=request_data))
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            assert all(r.status_code == 200 for r in responses)
            assert len(responses) == 10
    
    def test_request_timing_header(self, client):
        """Test that response includes processing time header."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        # Verify the header contains a valid time value
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 10  # Should complete within 10 seconds
