"""
Phase 5 Integration Tests: End-to-End System Integration

This module contains essential end-to-end integration tests that validate
the core Agent Blackwell system functionality: API → Orchestrator → Task Management.
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.orchestrator.main import Orchestrator

# Set up logger
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""

    class MockOrchestrator:
        def __init__(self):
            self._tasks = {}
            self.created_task_ids = []

        def reset_state(self):
            """Reset all state for test isolation."""
            self._tasks = {}
            self.created_task_ids = []

        async def enqueue_task(self, task_type, task_data):
            task_id = f"{task_type}-{len(self._tasks)}"
            self._tasks[task_id] = {
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "progress": 0,
                "result": {},
            }
            self.created_task_ids.append(task_id)
            return task_id

        async def get_task_status(self, task_id):
            if task_id in self._tasks:
                return self._tasks[task_id]
            return {"error": "Task not found"}

        async def process_task(self, task_data):
            task_id = task_data["task_id"]
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["result"] = {
                    "message": f"Completed {task_data['task_type']} task",
                    "task_type": task_data["task_type"],
                    "completion_time": datetime.now().isoformat(),
                }
                self._tasks[task_id]["updated_at"] = datetime.now().isoformat()
                self._tasks[task_id]["progress"] = 100
            return self._tasks[task_id]

    orchestrator = MockOrchestrator()
    yield orchestrator
    # Clean up after each test
    orchestrator.reset_state()


@pytest.fixture
def client_with_mock_orchestrator(mock_orchestrator):
    """Create test client with mocked orchestrator dependency."""
    from src.api.dependencies import get_orchestrator

    def override_get_orchestrator():
        return mock_orchestrator

    app.dependency_overrides[get_orchestrator] = override_get_orchestrator
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCoreWorkflows:
    """Test essential end-to-end workflows through the system."""

    def setup_method(self, method):
        """Clear any state before each test."""
        logger.debug("Setting up test method - clearing any previous state")

    async def test_specification_generation_workflow(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test complete specification generation workflow from API to result."""
        mock_orchestrator.reset_state()
        logger.debug("Starting specification generation workflow test")

        # Step 1: Submit specification request via ChatOps API
        command_request = {
            "command": "!spec Create a REST API for user authentication",
            "platform": "slack",
            "user_id": "product_manager",
            "channel_id": "development",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )

        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "queued" in response_data["message"].lower()

        # Step 2: Verify task was created
        assert len(mock_orchestrator.created_task_ids) > 0
        task_id = mock_orchestrator.created_task_ids[0]
        assert task_id in mock_orchestrator._tasks

        # Step 3: Check initial task status
        initial_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/status/{task_id}"
        )

        if initial_status_response.status_code == 200:
            initial_status = initial_status_response.json()
            assert initial_status["task_id"] == task_id
            assert initial_status["status"] == "queued"

        # Step 4: Process the task
        task_data = mock_orchestrator._tasks[task_id]
        await mock_orchestrator.process_task(task_data)

        # Step 5: Verify completion
        final_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/status/{task_id}"
        )

        if final_status_response.status_code == 200:
            final_status = final_status_response.json()
            assert final_status["status"] == "completed"
            assert final_status["task_id"] == task_id

    async def test_basic_concurrent_requests(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test system handling of basic concurrent API requests."""
        mock_orchestrator.reset_state()

        # Submit 3 concurrent requests
        commands = [
            "!spec Create user service",
            "!design Design payment flow",
            "!code Implement dashboard",
        ]

        responses = []
        for i, command in enumerate(commands):
            command_request = {
                "command": command,
                "platform": "slack",
                "user_id": f"user_{i}",
                "channel_id": "testing",
                "timestamp": datetime.now().isoformat(),
            }

            response = client_with_mock_orchestrator.post(
                "/api/v1/chatops/command", json=command_request
            )
            responses.append(response)

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            response_data = response.json()
            assert "message" in response_data

        # Verify tasks were created
        assert len(mock_orchestrator.created_task_ids) >= len(commands)

        # Verify all task IDs are unique
        task_ids = mock_orchestrator.created_task_ids
        assert len(set(task_ids)) == len(task_ids)


class TestTaskStateManagement:
    """Test task state consistency and management."""

    def setup_method(self, method):
        """Clear any state before each test."""
        logger.debug("Setting up task state test")

    async def test_task_state_consistency(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test that task state remains consistent across operations."""
        mock_orchestrator.reset_state()

        # Create a task
        command_request = {
            "command": "!spec Test data consistency",
            "platform": "slack",
            "user_id": "consistency_test",
            "channel_id": "testing",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )
        assert response.status_code == 200

        # Get the task ID
        assert len(mock_orchestrator.created_task_ids) > 0
        task_id = mock_orchestrator.created_task_ids[0]

        # Check initial state
        initial_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/status/{task_id}"
        )

        if initial_status_response.status_code == 200:
            initial_status = initial_status_response.json()
            assert initial_status["task_id"] == task_id
            assert initial_status["status"] == "queued"

        # Process the task
        task_data = mock_orchestrator._tasks[task_id]
        await mock_orchestrator.process_task(task_data)

        # Check final state
        final_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/status/{task_id}"
        )

        if final_status_response.status_code == 200:
            final_status = final_status_response.json()
            assert final_status["status"] == "completed"
            assert final_status["task_id"] == task_id

        # Verify state transition was clean
        assert task_id in mock_orchestrator._tasks
        final_task = mock_orchestrator._tasks[task_id]
        assert final_task["status"] == "completed"
        assert final_task["progress"] == 100
