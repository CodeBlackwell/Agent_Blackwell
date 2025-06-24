"""
Tests for the task status API endpoint.

These tests verify the functionality of the task status endpoint,
which allows users to check the status of submitted tasks.
"""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.v1.feature_request.router import get_orchestrator


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock = AsyncMock()

    # Mock the response data for different task statuses
    task_status_responses = {
        "pending-task": {
            "status": "pending",
            "task": {"task_id": "pending-task", "task_type": "spec_agent"},
        },
        "completed-task": {
            "status": "completed",
            "result": {"task_id": "completed-task", "output": "Task completed"},
        },
        # Default response for any other task ID
        "default": {"status": "not_found"},
    }

    # Use AsyncMock's side_effect to implement different return values based on input
    async def side_effect(task_id):
        return task_status_responses.get(task_id, task_status_responses["default"])

    # Create a dedicated mock for get_task_status with the side_effect
    mock.get_task_status = AsyncMock(side_effect=side_effect)
    return mock


@pytest.fixture
def client(mock_orchestrator):
    """Create a test client for the FastAPI application.

    Override the get_orchestrator dependency to return our mock.
    """
    # Store the original dependency overrides
    original_overrides = app.dependency_overrides.copy()

    # Set up our dependency override
    async def get_mock_orchestrator():
        return mock_orchestrator

    app.dependency_overrides[get_orchestrator] = get_mock_orchestrator

    # Create and yield the test client
    test_client = TestClient(app)
    yield test_client

    # Restore the original dependency overrides
    app.dependency_overrides = original_overrides


def test_task_status_endpoint_exists(client):
    """Test that the task status endpoint exists and returns proper error for non-existent task."""
    response = client.get("/api/v1/task-status/test-task")

    # The endpoint exists but returns 404 for a non-existent task
    # Let's make sure the error message is a "Task not found" error
    # rather than a "Route not found" error
    assert (
        "Task with ID" in response.json()["detail"]
    ), "Endpoint exists but returns wrong error message"

    # The status code should be 404 for a non-existent task
    assert response.status_code == 404, "Should return 404 for non-existent task"


def test_task_status_not_found(client):
    """Test task status for a non-existent task."""
    response = client.get("/api/v1/task-status/non-existent-task")

    assert response.status_code == 404, "Should return 404 Not Found"
    assert "detail" in response.json(), "Response should contain error detail"
    assert (
        "not found" in response.json()["detail"].lower()
    ), "Error should indicate task not found"


def test_task_status_pending(client, mock_orchestrator):
    """Test task status for a pending task."""
    response = client.get("/api/v1/task-status/pending-task")

    assert response.status_code == 200, "Should return 200 OK"
    assert response.json()["status"] == "pending", "Status should be pending"
    assert "task_id" in response.json(), "Response should contain task_id"
    assert (
        response.json()["task_id"] == "pending-task"
    ), "Should return the correct task ID"

    # Verify orchestrator was called correctly
    mock_orchestrator.get_task_status.assert_called_with("pending-task")


def test_task_status_completed(client, mock_orchestrator):
    """Test task status for a completed task."""
    response = client.get("/api/v1/task-status/completed-task")

    assert response.status_code == 200, "Should return 200 OK"
    assert response.json()["status"] == "completed", "Status should be completed"
    assert "task_id" in response.json(), "Response should contain task_id"
    assert (
        response.json()["task_id"] == "completed-task"
    ), "Should return the correct task ID"
    assert "result" in response.json(), "Response should contain result"

    # Verify orchestrator was called correctly
    mock_orchestrator.get_task_status.assert_called_with("completed-task")
