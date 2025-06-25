"""
Functional tests for ChatOps API endpoints.

This module contains functional tests for the ChatOps API endpoints,
mocking the orchestrator and other dependencies.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.chatops.models import (
    ChatCommandRequest,
    ChatCommandResponse,
    ChatPlatform,
)
from src.api.v1.chatops.router import get_orchestrator, router

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)

# Setup test client
client = TestClient(app)


# Mock orchestrator for testing
@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator for testing."""
    mock = AsyncMock()

    # Mock the enqueue_task method
    async def mock_enqueue_task(task_type, task_data):
        return "test-task-id"

    mock.enqueue_task = mock_enqueue_task

    # Mock the get_task_status method
    async def mock_get_task_status(task_id):
        if task_id == "test-task-id":
            return {
                "status": "completed",
                "progress": 100,
                "result": {"message": "Task completed successfully"},
                "created_at": "2025-06-24T10:00:00Z",
                "updated_at": "2025-06-24T10:05:00Z",
            }
        elif task_id == "error-task-id":
            return {
                "status": "failed",
                "error": "An error occurred",
                "created_at": "2025-06-24T10:00:00Z",
                "updated_at": "2025-06-24T10:01:00Z",
            }
        else:
            return None

    mock.get_task_status = mock_get_task_status

    return mock


@pytest.mark.asyncio
class TestChatOpsEndpoints:
    """Test suite for ChatOps API endpoints."""

    async def test_process_help_command(self, mock_orchestrator):
        """Test processing a help command."""

        # Set up dependency override
        async def override_get_orchestrator():
            return mock_orchestrator

        # Save original dependencies
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Create a test request
            request = {
                "platform": "slack",
                "user_id": "test-user",
                "channel_id": "test-channel",
                "command": "!help",
                "timestamp": "2025-06-24T10:00:00Z",
            }

            # Send the request
            response = client.post("/api/v1/chatops/command", json=request)
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Verify the response contains help text
        assert "Available Commands" in data["message"]
        assert not data["ephemeral"]  # Default is False

    @patch("src.api.v1.chatops.router.handle_status_command")
    async def test_process_status_command(self, mock_handle_status):
        """Test processing a status command."""
        # Create a mock orchestrator instance
        mock_orchestrator_instance = AsyncMock()

        # Create a mock return value for handle_status_command
        mock_handle_status.return_value = ChatCommandResponse(
            message="**Status for Task test-task-id:**\n\n• **Status:** completed\n• **Progress:** 100%\n• **Created:** 2025-06-24T10:00:00Z\n• **Updated:** 2025-06-24T10:05:00Z\n\n**Result Summary:**\nTask completed successfully"
        )

        # Set up dependency override
        async def override_get_orchestrator():
            return mock_orchestrator_instance

        # Save original dependencies
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Create a test request
            request = {
                "platform": "slack",
                "user_id": "test-user",
                "channel_id": "test-channel",
                "command": "!status test-task-id",
                "timestamp": "2025-06-24T10:00:00Z",
            }

            # Send the request
            response = client.post("/api/v1/chatops/command", json=request)
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Verify the response contains status info
        assert "Status for Task" in data["message"]
        assert "completed" in data["message"]

        # Verify the handle_status_command was called (without checking exact parameters)
        assert mock_handle_status.called
        # Check it was called with the task ID we're expecting
        args, _ = mock_handle_status.call_args
        assert args[1] == "test-task-id"
        assert "100%" in data["message"]

    async def test_process_spec_command(self, mock_orchestrator):
        """Test processing a spec command."""

        # Set up dependency override
        async def override_get_orchestrator():
            return mock_orchestrator

        # Save original dependencies
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Create a test request
            request = {
                "platform": "slack",
                "user_id": "test-user",
                "channel_id": "test-channel",
                "command": "!spec Create a user authentication API",
                "timestamp": "2025-06-24T10:00:00Z",
            }

            # Send the request
            response = client.post("/api/v1/chatops/command", json=request)
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Verify the response indicates task was queued
        assert "has been queued" in data["message"]
        assert "spec" in data["message"]

    async def test_process_invalid_command(self, mock_orchestrator):
        """Test processing an invalid command."""

        # Set up dependency override
        async def override_get_orchestrator():
            return mock_orchestrator

        # Save original dependencies
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Create a test request with an invalid command
            request = {
                "platform": "slack",
                "user_id": "test-user",
                "channel_id": "test-channel",
                "command": "!unknown command",
                "timestamp": "2025-06-24T10:00:00Z",
            }

            # Send the request
            response = client.post("/api/v1/chatops/command", json=request)
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Verify the response indicates the command is unknown
        assert "Unknown command" in data["message"]

    async def test_get_task_status_endpoint(self):
        """Test the /status/{task_id} endpoint."""
        # Create a task status dictionary that will be returned by the mock
        task_status = {
            "status": "completed",
            "progress": 100,
            "result": {"message": "Task completed successfully"},
            "created_at": "2025-06-24T10:00:00Z",
            "updated_at": "2025-06-24T10:05:00Z",
        }

        # Create a new mock orchestrator instance
        mock_orchestrator_instance = AsyncMock()
        # Set up the mock to return our task_status
        mock_orchestrator_instance.get_task_status = AsyncMock(return_value=task_status)

        # Use app.dependency_overrides to override the dependency properly
        async def override_get_orchestrator():
            return mock_orchestrator_instance

        # Save the original dependency
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Send the request
            response = client.get("/api/v1/chatops/status/test-task-id")

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Verify the response contains expected status info
            assert data["task_id"] == "test-task-id"
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["result"] == {"message": "Task completed successfully"}
            assert data["created_at"] == "2025-06-24T10:00:00Z"
            assert data["updated_at"] == "2025-06-24T10:05:00Z"
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

    async def test_get_task_status_not_found(self):
        """Test the /status/{task_id} endpoint with a non-existent task."""
        # Create a mock orchestrator that returns None for get_task_status
        mock_orchestrator_instance = AsyncMock()
        # Ensure the mock returns None to trigger the 404 in the router
        mock_orchestrator_instance.get_task_status = AsyncMock(return_value=None)

        # Use app.dependency_overrides to override the dependency properly
        async def override_get_orchestrator():
            return mock_orchestrator_instance

        # Save the original dependency
        original = app.dependency_overrides.copy()
        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        try:
            # Send the request with an unknown task ID
            response = client.get("/api/v1/chatops/status/unknown-task-id")

            # Check response - should be 404 as the endpoint raises HTTPException
            assert response.status_code == 404
            data = response.json()

            # Verify the response indicates the task was not found
            assert "not found" in data["detail"]
        finally:
            # Restore original dependencies
            app.dependency_overrides = original

    @patch("src.api.v1.chatops.router.get_orchestrator")
    async def test_get_command_help_endpoint(
        self, mock_get_orchestrator, mock_orchestrator
    ):
        """Test the /help endpoint."""
        mock_get_orchestrator.return_value = mock_orchestrator

        # Send the request
        response = client.get("/api/v1/chatops/help")

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Verify the response contains help information
        assert "commands" in data
        assert "examples" in data
        assert isinstance(data["commands"], dict)
        assert isinstance(data["examples"], list)

        # Check that key commands are included
        assert "help" in data["commands"]
        assert "status" in data["commands"]
        assert "deploy" in data["commands"]
        assert "spec" in data["commands"]
