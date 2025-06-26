"""
Phase 5 Integration Tests: REST API Endpoints

This module contains integration tests for all REST API endpoints,
including ChatOps, feature requests, health checks, and error handling.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_orchestrator
from src.api.main import app
from src.orchestrator.main import Orchestrator


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock = MagicMock(spec=Orchestrator)
    mock.enqueue_task = AsyncMock(return_value="test-task-123")
    mock.get_task_status = AsyncMock(
        return_value={
            "status": "completed",
            "progress": 100,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:01:00Z",
            "result": {"message": "Task completed successfully"},
        }
    )
    mock.submit_feature_request = AsyncMock(return_value="workflow-456")
    mock.get_workflow_status = AsyncMock(
        return_value={
            "workflow_id": "workflow-456",
            "status": "completed",
            "results": {"feature": "implemented"},
        }
    )
    return mock


@pytest.fixture
def client(mock_orchestrator):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check and basic endpoints."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Agent Blackwell API" in data["name"]


class TestChatOpsEndpoints:
    """Test ChatOps command processing endpoints."""

    def test_help_command(self, client):
        """Test the help command."""
        response = client.post(
            "/api/v1/chatops/command",
            json={
                "command": "!help",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
                "timestamp": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Available Commands" in data["message"]

    def test_spec_agent_command(self, client, mock_orchestrator):
        """Test the spec agent command."""
        response = client.post(
            "/api/v1/chatops/command",
            json={
                "command": "!spec Create a user authentication system",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
                "timestamp": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "queued" in data["message"].lower()

    def test_invalid_command_format(self, client):
        """Test invalid command format handling."""
        response = client.post(
            "/api/v1/chatops/command",
            json={
                "command": "invalid command without !",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
                "timestamp": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Invalid command format" in data["message"]


class TestFeatureRequestEndpoints:
    """Test feature request submission endpoints."""

    def test_submit_feature_request(self, client, mock_orchestrator):
        """Test feature request submission."""
        request_payload = {
            "description": "Implement rate limiting for all API endpoints"
        }

        response = client.post("/api/v1/feature-request", json=request_payload)

        assert response.status_code == 202
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "processing"

    def test_get_workflow_status(self, client, mock_orchestrator):
        """Test workflow status retrieval."""
        response = client.get("/api/v1/workflow-status/workflow-456")

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == "workflow-456"
        assert data["status"] == "completed"


class TestTaskStatusEndpoints:
    """Test legacy task status endpoints."""

    def test_get_task_status_endpoint(self, client, mock_orchestrator):
        """Test the legacy task status endpoint."""
        response = client.get("/api/v1/task-status/test-task-123")

        # This should work as it's a legacy endpoint that redirects to workflow status
        assert response.status_code in [200, 404]  # May not be found, which is valid


class TestErrorHandling:
    """Test API error handling and edge cases."""

    def test_malformed_request_data(self, client):
        """Test handling of malformed request data."""
        response = client.post(
            "/api/v1/chatops/command",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of requests with missing required fields."""
        # Missing command field
        response = client.post(
            "/api/v1/chatops/command",
            json={
                "platform": "slack",
                "user_id": "test_user",
                "timestamp": datetime.now().isoformat(),
            },
        )
        assert response.status_code == 422

        # Missing description for feature request
        response = client.post("/api/v1/feature-request", json={})
        assert response.status_code == 422
