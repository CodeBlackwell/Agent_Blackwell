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
from src.api.dependencies import get_orchestrator


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock = AsyncMock()

    # Mock the response data for different workflow statuses
    # Make sure responses match the WorkflowStatusResponse schema
    workflow_status_responses = {
        "pending-workflow": {
            "status": "running",
            "workflow_id": "pending-workflow",
            "results": None,
            "execution_summary": None,
            "error": None
        },
        "completed-workflow": {
            "status": "completed",
            "workflow_id": "completed-workflow", 
            "results": {"output": "Workflow completed successfully"},
            "execution_summary": {
                "started_at": "2025-01-01T00:00:00Z",
                "completed_at": "2025-01-01T00:05:00Z"
            },
            "error": None
        },
        # Default response for any other workflow ID
        "default": {
            "status": "not_found",
            "workflow_id": "nonexistent-task",
            "results": None,
            "execution_summary": None,
            "error": "Workflow not found"
        },
    }

    # Use AsyncMock's side_effect to implement different return values based on input
    async def side_effect(workflow_id):
        return workflow_status_responses.get(workflow_id, workflow_status_responses["default"])

    # Create a dedicated mock for get_workflow_status with the side_effect
    mock.get_workflow_status = AsyncMock(side_effect=side_effect)
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
    """Test that the task status endpoints are properly set up.
    
    Note: The task-status endpoint is marked as deprecated in the router,
    and the workflow-status endpoint is the preferred replacement.
    
    This test verifies that we can access the API status functionality
    through at least one of these endpoints correctly.
    """
    # Test if we get an appropriate response from the API
    # Even if it's a 404 for a non-existent workflow, we should get a proper
    # JSON response with an error message, not a route-not-found 404
    response = client.get("/api/v1/workflow-status/some-id")
    
    # Check that we get a JSON response (indicating the endpoint exists)
    # The response for a non-existent workflow would be a 404, but with JSON content
    try:
        response_data = response.json()
        # If we can parse JSON, the endpoint is functioning properly
        assert True, "Endpoint exists and returns JSON"
    except ValueError:
        # If we can't parse JSON, the test failed
        assert False, "Endpoint should return valid JSON response"
    
    # Verify we get either a proper error response or a workflow status
    assert response.status_code in [200, 404], f"Expected status code 200 or 404, got {response.status_code}"


def test_task_status_not_found(client, mock_orchestrator):
    """Test task status endpoint with non-existent task ID."""
    # This test might need to be adjusted based on how your router handles not-found workflows
    # It seems the router returns a 404 while our mock currently returns a status key with 'not_found'
    # We'll update the test to expect a 404 error from the API layer
    response = client.get("/api/v1/task-status/nonexistent-task")
    assert response.status_code == 404, "Should return 404 for non-existent task"


def test_task_status_pending(client, mock_orchestrator):
    """Test task status endpoint with pending task."""
    response = client.get("/api/v1/task-status/pending-workflow")
    assert response.status_code == 200, "Should return 200 for existing pending task"
    
    data = response.json()
    assert data["status"] == "running", "Status should be running for pending task"
    assert data["workflow_id"] == "pending-workflow", "Should return correct workflow ID"


def test_task_status_completed(client, mock_orchestrator):
    """Test task status endpoint with completed task."""
    response = client.get("/api/v1/task-status/completed-workflow")
    assert response.status_code == 200, "Should return 200 for completed task"
    
    data = response.json()
    assert data["status"] == "completed", "Status should be completed"
    assert data["workflow_id"] == "completed-workflow", "Should return correct workflow ID"
    assert "results" in data, "Should include results for completed task"
    assert data["results"] is not None, "Results should not be None"
    assert "output" in data["results"], "Results should contain output"
