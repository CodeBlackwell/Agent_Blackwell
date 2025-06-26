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

    @pytest.mark.asyncio
    async def test_complete_chatops_workflow(self, client_with_mock_orchestrator):
        """Test complete ChatOps workflow from command to result."""
        async with AsyncClient(base_url="http://test") as ac:
            # Submit a spec command
            response = await ac.post(
                "/api/v1/chatops/command",
                json={
                    "command": "!spec Create a user authentication system",
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "queued" in data["message"].lower()

            # Check task status
            response = await ac.get("/api/v1/task-status/test-task-123")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self, client_with_mock_orchestrator):
        """Test multi-agent workflow coordination."""
        async with AsyncClient(base_url="http://test") as ac:
            # Submit multiple agent commands
            commands = [
                "!spec Create user management system",
                "!design Database schema for users",
                "!code Implement user registration",
            ]

            responses = []
            for command in commands:
                response = await ac.post(
                    "/api/v1/chatops/command",
                    json={
                        "command": command,
                        "platform": "slack",
                        "user_id": "test_user",
                        "channel_id": "test_channel",
                    },
                )
                responses.append(response)

            # All commands should be accepted
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "queued" in data["message"].lower()

    async def test_api_error_handling(self, client_with_mock_orchestrator):
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
    async def test_api_performance_under_load(self, client_with_mock_orchestrator):
        """Test API performance under concurrent load."""
        async with AsyncClient(base_url="http://test") as ac:
            # Create multiple concurrent requests
            tasks = []
            for i in range(20):
                task = ac.post(
                    "/api/v1/chatops/command",
                    json={
                        "command": "!help",
                        "platform": "slack",
                        "user_id": f"load_test_user_{i}",
                        "channel_id": "load_test_channel",
                    },
                )
                tasks.append(task)

            # Execute all requests concurrently
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify all requests succeeded
            for response in responses:
                assert response.status_code == 200

            # Performance should be reasonable (less than 5 seconds for 20 requests)
            total_time = end_time - start_time
            assert total_time < 5.0
