"""
System Integration Tests for Agent Blackwell

These tests validate the complete system integration across all components:
- API Layer
- Orchestration Layer
- Agent Workers
- External Services
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.dependencies import get_orchestrator
from src.api.main import app
from tests.integration.phase5_config import Phase5TestConfig


class TestEndToEndWorkflow:
    """Tests that validate full system workflow execution from API to result."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with realistic task tracking."""
        mock_orch = MagicMock()
        mock_orch.enqueue_task = AsyncMock()
        mock_orch.get_task_status = AsyncMock()
        mock_orch.process_task = AsyncMock()

        # Task storage for realistic workflow simulation
        mock_orch._tasks = {}

        # Task creation with proper tracking
        async def mock_enqueue(task_type, payload):
            task_id = str(uuid.uuid4())
            mock_orch._tasks[task_id] = {
                "type": task_type,
                "payload": payload,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            return task_id

        # Task status retrieval
        async def mock_get_status(task_id):
            if task_id not in mock_orch._tasks:
                return {"status": "not_found"}
            return mock_orch._tasks[task_id]

        # Task processing simulation
        async def mock_process(task_id):
            if task_id not in mock_orch._tasks:
                return {"status": "not_found"}

            # Simulate processing time
            mock_orch._tasks[task_id]["status"] = "processing"
            await asyncio.sleep(0.1)

            # Complete the task with results
            task_type = mock_orch._tasks[task_id]["type"]
            mock_orch._tasks[task_id]["status"] = "completed"
            mock_orch._tasks[task_id]["completed_at"] = datetime.now().isoformat()

            if task_type == "spec":
                mock_orch._tasks[task_id]["result"] = {
                    "spec_details": "Test specification details",
                    "user_stories": [
                        "As a user, I want to test",
                        "As a dev, I need stability",
                    ],
                    "acceptance_criteria": ["System passes all tests"],
                }
            elif task_type == "design":
                mock_orch._tasks[task_id]["result"] = {
                    "design_docs": "Test design documents",
                    "architecture": "Component diagram here",
                    "data_flow": "Request/response pattern",
                }
            else:
                mock_orch._tasks[task_id]["result"] = {
                    "message": f"Completed {task_type} task",
                    "details": "Generic result",
                }

            return mock_orch._tasks[task_id]

        # Assign mocks
        mock_orch.enqueue_task.side_effect = mock_enqueue
        mock_orch.get_task_status.side_effect = mock_get_status
        mock_orch.process_task.side_effect = mock_process

        return mock_orch

    @pytest.fixture
    def client_with_mock_orchestrator(self, mock_orchestrator):
        """Create a test client with mock orchestrator."""
        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()

    async def test_complete_chatops_workflow(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test a complete workflow from ChatOps command to task completion."""
        # Submit a chatops command
        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command",
            json={
                "command": "!spec Create a test system",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
            },
        )

        assert response.status_code == 202
        data = response.json()
        task_id = data["task_id"]

        # Verify task was created in orchestrator
        assert task_id in mock_orchestrator._tasks
        assert mock_orchestrator._tasks[task_id]["type"] == "spec"

        # Process the task
        result = await mock_orchestrator.process_task(task_id)
        assert result["status"] == "completed"

        # Check task status via API
        status_response = client_with_mock_orchestrator.get(
            f"/api/v1/tasks/{task_id}/status"
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert "spec_details" in status_data["result"]

    async def test_multi_agent_workflow(self, mock_orchestrator):
        """Test a multi-agent workflow with chained task dependencies."""
        # Create a spec task
        spec_task_id = await mock_orchestrator.enqueue_task(
            "spec", {"prompt": "Create a test system", "user_id": "test_user"}
        )

        # Complete the spec task
        await mock_orchestrator.process_task(spec_task_id)
        spec_result = await mock_orchestrator.get_task_status(spec_task_id)
        assert spec_result["status"] == "completed"

        # Create a design task based on spec results
        design_task_id = await mock_orchestrator.enqueue_task(
            "design", {"spec_task_id": spec_task_id, "user_id": "test_user"}
        )

        # Complete the design task
        await mock_orchestrator.process_task(design_task_id)
        design_result = await mock_orchestrator.get_task_status(design_task_id)
        assert design_result["status"] == "completed"
        assert "architecture" in design_result["result"]

        # Verify task relationships
        assert design_task_id != spec_task_id
        assert "spec_task_id" in mock_orchestrator._tasks[design_task_id]["payload"]
        assert (
            mock_orchestrator._tasks[design_task_id]["payload"]["spec_task_id"]
            == spec_task_id
        )

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

        # Test invalid command
        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command",
            json={
                "command": "!invalid command",
                "platform": "slack",
                "user_id": "test_user",
                "channel_id": "test_channel",
            },
        )
        assert response.status_code == 400


class TestSystemHealthChecks:
    """Tests that validate system health and availability."""

    def test_system_health_endpoints(self, client_with_mock_orchestrator):
        """Test system health check endpoints."""
        response = client_with_mock_orchestrator.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        response = client_with_mock_orchestrator.get("/metrics")
        assert response.status_code == 200
        assert "agent_blackwell" in response.text

    @pytest.mark.asyncio
    async def test_api_performance(self, mock_orchestrator):
        """Test API performance with multiple concurrent requests."""
        # Create a FastAPI test client for async requests
        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create multiple concurrent requests
            start_time = time.time()
            tasks = []
            for i in range(5):
                tasks.append(
                    client.post(
                        "/api/v1/chatops/command",
                        json={
                            "command": f"!spec Test system {i}",
                            "platform": "slack",
                            "user_id": f"user_{i}",
                            "channel_id": "test_channel",
                        },
                    )
                )

            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            # All responses should be successful
            for response in responses:
                assert response.status_code == 202

            # Performance check - all requests should complete in under 1 second total
            assert end_time - start_time < 1.0

        app.dependency_overrides.clear()
