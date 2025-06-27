"""
System Integration Tests for Agent Blackwell

These tests validate the complete system integration across all components:
- API Layer
- Orchestration Layer
- Agent Workers
- External Services
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_orchestrator
from src.api.main import app
from tests.integration.phase5_config import Phase5TestConfig


class TestEndToEndWorkflow:
    """Tests that validate essential system workflow execution."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with realistic task tracking."""
        mock_orch = MagicMock()
        mock_orch.enqueue_task = AsyncMock()
        mock_orch.get_task_status = AsyncMock()
        
        # Simple task tracking for basic functionality
        mock_orch._tasks = {}

        async def mock_enqueue(task_type, payload):
            task_id = str(uuid.uuid4())
            mock_orch._tasks[task_id] = {
                "type": task_type,
                "payload": payload,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            return task_id

        async def mock_get_status(task_id):
            if task_id not in mock_orch._tasks:
                return {"status": "not_found"}
            return mock_orch._tasks[task_id]

        mock_orch.enqueue_task.side_effect = mock_enqueue
        mock_orch.get_task_status.side_effect = mock_get_status

        return mock_orch

    @pytest.fixture
    def client_with_mock_orchestrator(self, mock_orchestrator):
        """Create a test client with mock orchestrator."""
        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()

    def test_api_error_handling(self, client_with_mock_orchestrator):
        """Test API error handling for system integration."""
        # Test missing task
        response = client_with_mock_orchestrator.get(
            "/api/v1/tasks/nonexistent-task/status"
        )
        assert response.status_code == 404

        # Test invalid request format
        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command",
            json={
                # Missing required fields
                "platform": "slack"
            },
        )
        assert response.status_code == 422

        # Test invalid command format - should return 422 for validation errors
        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command",
            json={
                "command": "!invalid command",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
            },
        )
        # 422 is correct for validation errors, not 400
        assert response.status_code == 422


class TestSystemHealthChecks:
    """Tests that validate system health and availability."""

    @pytest.fixture
    def client_with_mock_orchestrator(self):
        """Create a test client with mock orchestrator for health checks."""
        mock_orch = MagicMock()
        mock_orch.enqueue_task = AsyncMock(return_value="test-task-123")
        mock_orch.get_task_status = AsyncMock(return_value={"status": "completed"})
        
        app.dependency_overrides[get_orchestrator] = lambda: mock_orch
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()

    def test_system_health_endpoints(self, client_with_mock_orchestrator):
        """Test system health check endpoints."""
        response = client_with_mock_orchestrator.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Health status can be "healthy" or "degraded" depending on service configuration
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data

        response = client_with_mock_orchestrator.get("/metrics")
        assert response.status_code == 200
        assert "agent_blackwell" in response.text
