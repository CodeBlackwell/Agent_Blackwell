"""
Tests for the feature request API endpoint.

These tests verify the functionality of the feature request endpoint,
which allows users to submit new feature requests to the system.
"""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_orchestrator
from src.api.main import app


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock = AsyncMock()
    # Set the return value for submit_feature_request
    mock.submit_feature_request.return_value = "workflow-123"
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


def test_feature_request_endpoint_exists(client):
    """Test that the feature request endpoint exists."""
    response = client.post(
        "/api/v1/feature-request", json={"description": "Test feature"}
    )
    assert response.status_code != 404, "Feature request endpoint not found"


def test_feature_request_validation(client):
    """Test input validation for the feature request endpoint."""
    # Test with missing required field
    response = client.post("/api/v1/feature-request", json={})
    assert (
        response.status_code == 422
    ), "Should reject requests with missing description"

    # Test with empty description
    response = client.post("/api/v1/feature-request", json={"description": ""})
    assert response.status_code == 422, "Should reject requests with empty description"


def test_feature_request_success(client, mock_orchestrator):
    """Test successful feature request submission."""
    # Make the request
    response = client.post(
        "/api/v1/feature-request", json={"description": "Add a new dashboard feature"}
    )

    # Verify response
    assert response.status_code == 202, "Should return 202 Accepted"
    response_data = response.json()
    assert "workflow_id" in response_data, "Response should contain workflow_id"
    assert (
        response_data["workflow_id"] == "workflow-123"
    ), "Should return the workflow ID from the orchestrator"

    # Verify orchestrator was called correctly
    mock_orchestrator.submit_feature_request.assert_called_once_with(
        "Add a new dashboard feature"
    )
