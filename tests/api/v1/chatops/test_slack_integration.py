"""
Tests for Slack integration endpoints.

This module tests the Slack events and commands endpoints in the ChatOps API.
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.v1.chatops.models import ChatCommandResponse
from src.api.v1.chatops.platforms.slack import (
    get_slack_signing_secret,
    get_slack_token,
    verify_slack_signature,
)
from src.orchestrator.main import Orchestrator


class TestSlackIntegration:
    """Test suite for Slack integration endpoints."""

    @pytest.fixture
    def client(self):
        """Return a test client for the FastAPI application."""
        return TestClient(app)

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock the Orchestrator dependency."""
        mock_orch = AsyncMock(spec=Orchestrator)
        mock_orch.get_task_status = AsyncMock(
            return_value={
                "status": "completed",
                "progress": 100,
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:05:00Z",
                "result": "Task completed successfully",
            }
        )
        mock_orch.enqueue_task = AsyncMock(return_value="test-task-id")
        return mock_orch

    @pytest.fixture
    def setup_app_dependencies(self, mock_orchestrator):
        """Configure the app dependencies."""
        # Store original dependency override to restore later
        original_dependency_overrides = app.dependency_overrides.copy()

        # Override Slack token and signing secret dependencies
        async def mock_get_slack_token():
            return "test-slack-token"

        async def mock_get_slack_signing_secret():
            return "test-signing-secret"

        # Set up dependency overrides
        app.dependency_overrides[get_slack_token] = mock_get_slack_token
        app.dependency_overrides[
            get_slack_signing_secret
        ] = mock_get_slack_signing_secret

        # In the router module used by process_command
        from src.api.v1.chatops.router import get_orchestrator

        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

        yield

        # Restore original dependencies after the test
        app.dependency_overrides = original_dependency_overrides

    def test_verify_slack_signature(self):
        """Test the verify_slack_signature function."""
        # Test data
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))
        signing_secret = "test-secret"

        # Create signature
        base_string = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = (
            "v0="
            + hmac.new(
                signing_secret.encode("utf-8"),
                base_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        )

        # Test with valid signature
        assert (
            verify_slack_signature(body, signature, timestamp, signing_secret) is True
        )

        # Test with invalid signature
        assert (
            verify_slack_signature(body, "v0=invalid", timestamp, signing_secret)
            is False
        )

        # Test with old timestamp
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
        assert (
            verify_slack_signature(body, signature, old_timestamp, signing_secret)
            is False
        )

        # Test with missing parameters
        assert verify_slack_signature(body, None, timestamp, signing_secret) is False
        assert verify_slack_signature(body, signature, None, signing_secret) is False

    @pytest.mark.asyncio
    async def test_slack_events_url_verification(self, client, setup_app_dependencies):
        """Test the URL verification challenge for Slack events API."""
        # Mock the signature verification
        with patch(
            "src.api.v1.chatops.platforms.slack.verify_slack_signature",
            return_value=True,
        ):
            # Send a URL verification challenge
            response = client.post(
                "/api/v1/chatops/slack/events",
                json={"type": "url_verification", "challenge": "test-challenge"},
                headers={
                    "X-Slack-Signature": "v0=test",
                    "X-Slack-Request-Timestamp": str(int(time.time())),
                },
            )

            # Assert response
            assert response.status_code == 200
            assert response.json() == {"challenge": "test-challenge"}

    @pytest.mark.asyncio
    async def test_slack_events_message(
        self, client, setup_app_dependencies, mock_orchestrator
    ):
        """Test handling a message event from Slack."""
        # Mock the signature verification and message handler
        with patch(
            "src.api.v1.chatops.platforms.slack.verify_slack_signature",
            return_value=True,
        ), patch(
            "src.api.v1.chatops.platforms.slack.handle_slack_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            # Send a message event
            response = client.post(
                "/api/v1/chatops/slack/events",
                json={
                    "event": {
                        "type": "message",
                        "user": "U123456",
                        "text": "!help",
                        "channel": "C123456",
                        "ts": "1602264707.000100",
                    }
                },
                headers={
                    "X-Slack-Signature": "v0=test",
                    "X-Slack-Request-Timestamp": str(int(time.time())),
                },
            )

            # Assert response
            assert response.status_code == 200
            assert response.json() == {"ok": True}
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_commands(
        self, client, setup_app_dependencies, mock_orchestrator
    ):
        """Test handling a slash command from Slack."""
        # Mock the process_command function to return a known response
        # Note: Need to patch where it's actually imported in the slack.py file
        with patch(
            "src.api.v1.chatops.platforms.slack.process_command", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = ChatCommandResponse(
                message="Command processed!"
            )

            # Send a slash command
            response = client.post(
                "/api/v1/chatops/slack/commands",
                data={
                    "token": "test-token",
                    "command": "/agent",
                    "text": "help",
                    "user_id": "U123456",
                    "channel_id": "C123456",
                    "response_url": "https://slack.com/response",
                    "trigger_id": "trigger123",
                    "team_id": "team123",
                },
            )

            # Assert response
            assert response.status_code == 200
            response_data = response.json()
            assert "response_type" in response_data
            assert "text" in response_data
            assert "Processing command" in response_data["text"]
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_commands_unknown(self, client, setup_app_dependencies):
        """Test handling an unknown slash command from Slack."""
        # Send an unknown slash command
        response = client.post(
            "/api/v1/chatops/slack/commands",
            data={
                "token": "test-token",
                "command": "/unknown",
                "text": "help",
                "user_id": "U123456",
                "channel_id": "C123456",
                "response_url": "https://slack.com/response",
                "trigger_id": "trigger123",
                "team_id": "team123",
            },
        )

        # Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["response_type"] == "ephemeral"
        assert "Unknown command" in response_data["text"]

    @pytest.mark.asyncio
    async def test_send_slack_message(self, setup_app_dependencies):
        """Test the send_slack_message function."""
        from src.api.v1.chatops.platforms.slack import send_slack_message

        # We need to directly mock the get_slack_token function here
        # since we're calling the function directly, not through an endpoint
        with patch(
            "src.api.v1.chatops.platforms.slack.get_slack_token",
            new_callable=AsyncMock,
            return_value="test-token",
        ), patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"ok": True}
            mock_post.return_value = mock_response

            # Call the function
            result = await send_slack_message(
                "C123456", "Test message", thread_ts="1602264707.000100"
            )

            # Assert result
            assert result == {"ok": True}
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "json" in call_args.kwargs
            assert call_args.kwargs["json"]["channel"] == "C123456"
            assert call_args.kwargs["json"]["text"] == "Test message"
            assert call_args.kwargs["json"]["thread_ts"] == "1602264707.000100"
