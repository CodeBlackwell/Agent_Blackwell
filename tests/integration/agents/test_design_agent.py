"""
Integration tests for the DesignAgent.
"""
import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestDesignAgentIntegration(BaseAgentIntegrationTest):
    """Test DesignAgent integration."""

    @pytest.mark.asyncio
    async def test_design_agent_with_mock_llm(
        self, redis_client, agent_fixtures, user_request_fixtures, agent_worker
    ):
        """Test DesignAgent with mock data processing."""
        # Get sample design request (spec output as input)
        spec_output = agent_fixtures["spec_agent"]["outputs"][0]

        # Prepare input message for the DesignAgent
        input_message = {
            "request_id": "design-test-123",
            "user_id": "test-user-456",
            "spec_details": spec_output,
            "user_stories": [
                {
                    "role": "user",
                    "action": "submit request",
                    "benefit": "track progress",
                },
                {
                    "role": "admin",
                    "action": "review requests",
                    "benefit": "ensure quality",
                },
            ],
            "acceptance_criteria": [
                "System must respond within 2 seconds",
                "All inputs must be validated",
            ],
            "timestamp": "2025-06-26T01:00:00Z",
            "request_type": "design",
            "priority": "high",
        }

        # Test that the agent produces the expected output
        expected_output_keys = [
            "request_id",
            "architecture",
            "data_models",
            "api_design",
            "ui_wireframes",
        ]

        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client, "design", input_message, expected_output_keys, timeout=10.0
        )

        # Assert specific content in the output
        assert "architecture" in output_data, "architecture missing from output"
        architecture = output_data["architecture"]
        assert isinstance(architecture, dict), "architecture should be a dictionary"
        assert "components" in architecture, "architecture missing components"

        # Verify data models exist and have expected format
        assert "data_models" in output_data, "data_models missing from output"
        data_models = output_data["data_models"]
        assert isinstance(data_models, list), "data_models should be a list"
        if data_models:
            assert isinstance(data_models[0], dict), "data model should be a dictionary"
            assert "name" in data_models[0], "data model missing 'name' field"
            assert "fields" in data_models[0], "data model missing 'fields' field"

        # Verify API design exists
        assert "api_design" in output_data, "api_design missing from output"
        api_design = output_data["api_design"]
        assert isinstance(api_design, dict), "api_design should be a dictionary"
        assert "endpoints" in api_design, "api_design missing endpoints"

    @pytest.mark.asyncio
    async def test_design_agent_handles_complex_architecture(
        self, redis_client, agent_fixtures, user_request_fixtures, agent_worker
    ):
        """Test DesignAgent with complex architectural requirements."""
        # Get complex spec input
        complex_spec = (
            agent_fixtures["spec_agent"]["outputs"][1]
            if len(agent_fixtures["spec_agent"]["outputs"]) > 1
            else agent_fixtures["spec_agent"]["outputs"][0]
        )

        # Prepare input message with microservices requirements
        input_message = {
            "request_id": "complex-design-789",
            "user_id": "test-user-456",
            "spec_details": complex_spec,
            "user_stories": [
                {
                    "role": "customer",
                    "action": "place order",
                    "benefit": "buy products",
                },
                {
                    "role": "admin",
                    "action": "manage inventory",
                    "benefit": "track stock",
                },
            ],
            "acceptance_criteria": [
                "System must scale to 1M users",
                "99.9% uptime required",
                "Support multiple payment methods",
            ],
            "timestamp": "2025-06-26T01:05:00Z",
            "request_type": "design",
            "priority": "critical",
            "complexity": "high",
            "scale_requirements": "enterprise",
        }

        # Expected output keys for complex design
        expected_output_keys = [
            "request_id",
            "architecture",
            "data_models",
            "api_design",
            "ui_wireframes",
            "scalability_plan",
            "security_design",
        ]

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "design",
            input_message,
            expected_output_keys,
            timeout=15.0,  # More time for complex processing
        )

        # Verify scalability considerations
        assert (
            "scalability_plan" in output_data
        ), "scalability_plan missing for complex design"
        scalability = output_data["scalability_plan"]
        assert isinstance(scalability, dict), "scalability_plan should be a dictionary"
        assert (
            "load_balancing" in scalability
        ), "load_balancing missing from scalability plan"

        # Verify security design
        assert (
            "security_design" in output_data
        ), "security_design missing for complex design"
        security = output_data["security_design"]
        assert isinstance(security, dict), "security_design should be a dictionary"
        assert (
            "authentication" in security
        ), "authentication missing from security design"

    @pytest.mark.asyncio
    async def test_design_agent_handles_llm_error(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test DesignAgent handles missing or invalid input gracefully."""
        # Test with missing required spec_details
        input_message = {
            "request_id": "error-design-123",
            "user_id": "test-user-456",
            # Missing spec_details intentionally
            "timestamp": "2025-06-26T01:10:00Z",
            "request_type": "design",
            "priority": "normal",
        }

        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "design", input_message)

        # Wait for output - should still get a response (graceful handling)
        message_id, message_data = await self.wait_for_agent_output(
            redis_client, "design", timeout=10.0
        )

        # Should get a response even with missing data (graceful degradation)
        assert message_id is not None, "No response received for invalid input"
        assert message_data is not None, "Response message data is None"

        # Should still have request_id for traceability
        assert "request_id" in message_data, "request_id missing from response"
        assert (
            message_data["request_id"] == input_message["request_id"]
        ), "request_id mismatch"

        # Should have basic required fields even with missing input
        assert "status" in message_data, "status missing from response"

    @pytest.mark.asyncio
    async def test_design_agent_persistence(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test that DesignAgent output is persisted correctly."""
        # Get sample design output
        design_output = agent_fixtures["design_agent"]["outputs"][0]

        # Create a sample output message
        output_message = {
            "request_id": "persist-test-123",
            "user_id": "test-user-456",
            "design": design_output["design"],
            "architecture": {
                "components": ["api-gateway", "user-service", "notification-service"],
                "patterns": ["microservices", "event-driven"],
                "technologies": ["FastAPI", "Redis", "PostgreSQL"],
            },
            "data_models": [
                {
                    "name": "User",
                    "fields": ["id", "email", "created_at"],
                    "relationships": ["has_many_requests"],
                }
            ],
            "api_design": {
                "endpoints": ["/users", "/requests", "/notifications"],
                "authentication": "JWT",
                "versioning": "v1",
            },
            "ui_wireframes": {
                "pages": ["dashboard", "profile", "settings"],
                "components": ["header", "sidebar", "main-content"],
            },
            "timestamp": "2025-06-26T01:15:00Z",
        }

        # Manually publish to output stream to simulate agent output
        # Use test-prefixed stream name since we're in a test environment
        output_stream = "test_agent:design:output"

        # Serialize complex fields for Redis stream storage
        # Redis streams can only store string values
        serialized_message = {}
        for key, value in output_message.items():
            if isinstance(value, (dict, list)):
                # Serialize complex objects as JSON strings
                serialized_message[key] = json.dumps(value)
            else:
                # Keep simple values as strings
                serialized_message[key] = str(value)

        message_id = await redis_client.xadd(output_stream, serialized_message)

        # Verify message was added to stream
        messages = await redis_client.xrange(
            output_stream, min=message_id, max=message_id
        )
        assert len(messages) == 1, "Output message not found in stream"

        # Check if message content is correct
        _, stored_message = messages[0]
        assert (
            stored_message["request_id"] == output_message["request_id"]
        ), "request_id not persisted correctly"
        assert "architecture" in stored_message, "architecture not persisted correctly"
        assert "data_models" in stored_message, "data_models not persisted correctly"

        # Verify that complex objects can be deserialized back
        stored_architecture = json.loads(stored_message["architecture"])
        assert (
            stored_architecture == output_message["architecture"]
        ), "architecture not serialized/deserialized correctly"

        stored_data_models = json.loads(stored_message["data_models"])
        assert (
            stored_data_models == output_message["data_models"]
        ), "data_models not serialized/deserialized correctly"

        # Cleanup
        await redis_client.xdel(output_stream, message_id)

    @pytest.mark.asyncio
    async def test_design_agent_spec_to_design_transition(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test the transition from SpecAgent output to DesignAgent input."""
        # Simulate the complete workflow: spec output → design input
        spec_output_message = {
            "request_id": "transition-test-456",
            "user_id": "test-user-789",
            "spec_details": agent_fixtures["spec_agent"]["outputs"][0],
            "user_stories": [
                {
                    "role": "user",
                    "action": "create account",
                    "benefit": "access services",
                }
            ],
            "acceptance_criteria": [
                "Email validation required",
                "Password strength minimum 8 chars",
            ],
            "timestamp": "2025-06-26T01:20:00Z",
        }

        # Publish spec output to spec output stream
        # Use test-prefixed stream name since we're in a test environment
        spec_output_stream = "test_agent:spec:output"

        # Serialize complex fields for Redis stream storage
        serialized_spec_message = {}
        for key, value in spec_output_message.items():
            if isinstance(value, (dict, list)):
                serialized_spec_message[key] = json.dumps(value)
            else:
                serialized_spec_message[key] = str(value)

        spec_message_id = await redis_client.xadd(
            spec_output_stream, serialized_spec_message
        )

        # Create design input based on spec output
        design_input_message = {
            **spec_output_message,  # Inherit from spec output
            "request_type": "design",
            "previous_agent": "spec",
            "previous_message_id": spec_message_id,
        }

        # Publish to design input stream
        # Use test-prefixed stream name since we're in a test environment
        design_input_stream = "test_agent:design:input"

        # Serialize design input message
        serialized_design_message = {}
        for key, value in design_input_message.items():
            if isinstance(value, (dict, list)):
                serialized_design_message[key] = json.dumps(value)
            else:
                serialized_design_message[key] = str(value)

        design_message_id = await redis_client.xadd(
            design_input_stream, serialized_design_message
        )

        # Verify both messages exist
        spec_messages = await redis_client.xrange(
            spec_output_stream, min=spec_message_id, max=spec_message_id
        )
        design_messages = await redis_client.xrange(
            design_input_stream, min=design_message_id, max=design_message_id
        )

        assert len(spec_messages) == 1, "Spec output not persisted"
        assert len(design_messages) == 1, "Design input not persisted"

        # Verify content consistency
        _, spec_stored = spec_messages[0]
        _, design_stored = design_messages[0]

        assert (
            spec_stored["request_id"] == design_stored["request_id"]
        ), "request_id not consistent across transition"
        assert (
            design_stored["previous_agent"] == "spec"
        ), "previous_agent not set correctly"

        # Cleanup
        await redis_client.xdel(spec_output_stream, spec_message_id)
        await redis_client.xdel(design_input_stream, design_message_id)
