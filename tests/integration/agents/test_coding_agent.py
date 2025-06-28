"""
Integration tests for the CodingAgent.
"""
import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestCodingAgentIntegration(BaseAgentIntegrationTest):
    """Test CodingAgent integration."""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_coding_agent_with_mock_llm(
        self,
        mock_post,
        redis_client,
        agent_fixtures,
        agent_worker,
        user_request_fixtures,
    ):
        """Test CodingAgent with mock LLM."""
        # Setup mock LLM response using the fixture data
        coding_output = agent_fixtures["coding_agent"]["outputs"][0]
        mock_response = await self.setup_mock_llm_response(coding_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Get sample design output as input (design → coding transition)
        design_output = agent_fixtures["design_agent"]["outputs"][0]

        # Prepare input message for the CodingAgent
        input_message = {
            "request_id": "coding-test-123",
            "user_id": "test-user-456",
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
            "timestamp": "2025-06-26T01:25:00Z",
            "request_type": "coding",
            "priority": "high",
        }

        # Test that the agent produces the expected output
        expected_output_keys = [
            "request_id",
            "source_code",
            "file_structure",
            "dependencies",
            "documentation",
        ]

        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "coding",
            input_message,
            expected_output_keys,
            timeout=15.0,  # Coding may take longer
        )

        # Assert specific content in the output
        assert "source_code" in output_data, "source_code missing from output"
        source_code = output_data["source_code"]
        assert isinstance(source_code, dict), "source_code should be a dictionary"
        assert len(source_code) > 0, "source_code is empty"

        # Verify file structure exists and has expected format
        assert "file_structure" in output_data, "file_structure missing from output"
        file_structure = output_data["file_structure"]
        assert isinstance(file_structure, list), "file_structure should be a list"
        if file_structure:
            assert isinstance(
                file_structure[0], dict
            ), "file structure item should be a dictionary"
            assert "path" in file_structure[0], "file structure missing 'path' field"
            assert "type" in file_structure[0], "file structure missing 'type' field"

        # Verify dependencies exist
        assert "dependencies" in output_data, "dependencies missing from output"
        dependencies = output_data["dependencies"]
        assert isinstance(dependencies, dict), "dependencies should be a dictionary"
        assert "requirements" in dependencies, "dependencies missing requirements"

        # Verify documentation exists
        assert "documentation" in output_data, "documentation missing from output"
        documentation = output_data["documentation"]
        assert isinstance(documentation, dict), "documentation should be a dictionary"
        assert (
            "setup_instructions" in documentation
        ), "documentation missing setup_instructions"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_coding_agent_handles_multiple_services(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test CodingAgent with multiple microservices."""
        # Setup mock LLM response for multi-service code generation
        coding_output = agent_fixtures["coding_agent"]["outputs"][0]
        mock_response = await self.setup_mock_llm_response(coding_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Prepare input with multiple services
        input_message = {
            "request_id": "multi-service-789",
            "user_id": "test-user-456",
            "architecture": {
                "components": [
                    "api-gateway",
                    "user-service",
                    "order-service",
                    "payment-service",
                    "notification-service",
                ],
                "patterns": ["microservices", "event-driven", "cqrs"],
                "technologies": ["FastAPI", "Redis", "PostgreSQL", "MongoDB", "Docker"],
            },
            "data_models": [
                {"name": "User", "fields": ["id", "email", "created_at"]},
                {"name": "Order", "fields": ["id", "user_id", "total", "status"]},
                {"name": "Payment", "fields": ["id", "order_id", "amount", "status"]},
            ],
            "api_design": {
                "endpoints": ["/users", "/orders", "/payments", "/notifications"],
                "authentication": "JWT",
                "versioning": "v1",
                "rate_limiting": True,
            },
            "timestamp": "2025-06-26T01:30:00Z",
            "request_type": "coding",
            "priority": "critical",
            "complexity": "high",
        }

        # Expected output keys for multi-service coding
        expected_output_keys = [
            "request_id",
            "source_code",
            "file_structure",
            "dependencies",
            "documentation",
            "deployment_config",
            "docker_config",
        ]

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "coding",
            input_message,
            expected_output_keys,
            timeout=20.0,  # More time for complex code generation
        )

        # Verify multi-service code structure
        source_code = output_data["source_code"]
        assert "user-service" in source_code, "user-service code missing"
        assert "order-service" in source_code, "order-service code missing"
        assert "payment-service" in source_code, "payment-service code missing"

        # Verify deployment configuration
        assert (
            "deployment_config" in output_data
        ), "deployment_config missing for multi-service"
        deployment = output_data["deployment_config"]
        assert isinstance(deployment, dict), "deployment_config should be a dictionary"
        assert "services" in deployment, "services missing from deployment config"

        # Verify Docker configuration
        assert "docker_config" in output_data, "docker_config missing for multi-service"
        docker_config = output_data["docker_config"]
        assert isinstance(docker_config, dict), "docker_config should be a dictionary"
        assert "docker-compose.yml" in docker_config, "docker-compose.yml missing"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_coding_agent_handles_llm_error(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test CodingAgent handles LLM errors gracefully."""
        # Setup mock LLM error response
        mock_response = AsyncMock()
        mock_response.status = 429  # Rate limit error
        mock_response.text = AsyncMock(
            return_value=json.dumps({"error": "Rate limit exceeded"})
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        # Get sample design output as input
        design_output = agent_fixtures["design_agent"]["outputs"][0]

        # Prepare input message with error status
        input_message = {
            "request_id": "error-test-456",
            "user_id": "test-user-789",
            "design": design_output,
            "timestamp": "2025-06-26T01:10:00Z",
            "request_type": "coding",
            "priority": "high",
            "status": "error",
            "error": "LLM service unavailable",
            "error_code": "LLM_SERVICE_ERROR",
        }

        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "coding", input_message)

        # Wait for output - expecting error handling message
        message_id, message_data = await self.wait_for_agent_output(
            redis_client, "coding", timeout=15.0
        )

        # Should get an error response, not a timeout
        assert message_id is not None, "No error response received"
        assert message_data is not None, "Error message data is None"

        # Check for error indicators in response
        assert (
            "error" in message_data or "error_code" in message_data
        ), "Error indicators missing from response"
        assert "request_id" in message_data, "request_id missing in error response"
        assert (
            message_data["request_id"] == input_message["request_id"]
        ), "request_id mismatch in error response"

    @pytest.mark.asyncio
    async def test_coding_agent_persistence(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test that CodingAgent output is persisted correctly."""
        # Create a sample output message
        output_message = {
            "request_id": "persist-coding-123",
            "user_id": "test-user-456",
            "source_code": {
                "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                "models.py": "from sqlalchemy import Column, Integer, String\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)",
                "routes.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users')\ndef get_users():\n    return []",
            },
            "file_structure": [
                {"path": "main.py", "type": "file", "size": 150},
                {"path": "models.py", "type": "file", "size": 200},
                {"path": "routes.py", "type": "file", "size": 120},
            ],
            "dependencies": {
                "requirements": [
                    "fastapi>=0.104.0",
                    "sqlalchemy>=2.0.0",
                    "redis>=4.5.0",
                ],
                "dev_requirements": ["pytest>=7.0.0", "black>=23.0.0"],
            },
            "documentation": {
                "setup_instructions": "1. Install dependencies\n2. Run with uvicorn main:app",
                "api_docs": "Auto-generated at /docs endpoint",
                "deployment_notes": "Use Docker for production deployment",
            },
            "timestamp": "2025-06-26T01:40:00Z",
        }

        # Manually publish to output stream to simulate agent output with test prefix
        output_stream = "test_agent:coding:output"

        # Serialize complex fields for Redis stream storage
        serialized_output = {}
        for key, value in output_message.items():
            if isinstance(value, (dict, list)):
                serialized_output[key] = json.dumps(value)
            else:
                serialized_output[key] = str(value)

        message_id = await redis_client.xadd(output_stream, serialized_output)

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
        assert "source_code" in stored_message, "source_code not persisted correctly"
        assert (
            "file_structure" in stored_message
        ), "file_structure not persisted correctly"
        assert "dependencies" in stored_message, "dependencies not persisted correctly"

        # Cleanup
        await redis_client.xdel(output_stream, message_id)

    @pytest.mark.asyncio
    async def test_coding_agent_design_to_code_transition(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test the transition from DesignAgent output to CodingAgent input."""
        # Simulate design output → coding input transition
        design_output_message = {
            "request_id": "design-to-code-456",
            "user_id": "test-user-789",
            "architecture": {
                "components": ["web-api", "database", "cache"],
                "patterns": ["mvc", "repository"],
                "technologies": ["FastAPI", "PostgreSQL", "Redis"],
            },
            "data_models": [{"name": "Product", "fields": ["id", "name", "price"]}],
            "api_design": {"endpoints": ["/products"], "authentication": "API_KEY"},
            "timestamp": "2025-06-26T01:45:00Z",
        }

        # Publish design output to design output stream with test prefix
        design_output_stream = "test_agent:design:output"

        # Serialize dictionaries to JSON strings before storing in Redis
        serialized_design_output = {}
        for key, value in design_output_message.items():
            if isinstance(value, (dict, list)):
                serialized_design_output[key] = json.dumps(value)
            else:
                serialized_design_output[key] = value

        design_message_id = await redis_client.xadd(
            design_output_stream, serialized_design_output
        )

        # Create coding input based on design output
        coding_input_message = {
            **design_output_message,  # Inherit from design output
            "request_type": "coding",
            "previous_agent": "design",
            "previous_message_id": design_message_id,
        }

        # Publish to coding input stream with test prefix
        coding_input_stream = "test_agent:coding:input"

        # Serialize dictionaries to JSON strings before storing in Redis
        serialized_coding_input = {}
        for key, value in coding_input_message.items():
            if isinstance(value, (dict, list)):
                serialized_coding_input[key] = json.dumps(value)
            else:
                serialized_coding_input[key] = value

        coding_message_id = await redis_client.xadd(
            coding_input_stream, serialized_coding_input
        )

        # Verify both messages exist
        design_messages = await redis_client.xrange(
            design_output_stream, min=design_message_id, max=design_message_id
        )
        coding_messages = await redis_client.xrange(
            coding_input_stream, min=coding_message_id, max=coding_message_id
        )

        assert len(design_messages) == 1, "Design output not persisted"
        assert len(coding_messages) == 1, "Coding input not persisted"

        # Verify content consistency
        _, design_stored = design_messages[0]
        _, coding_stored = coding_messages[0]

        assert (
            design_stored["request_id"] == coding_stored["request_id"]
        ), "request_id not consistent across transition"
        assert (
            coding_stored["previous_agent"] == "design"
        ), "previous_agent not set correctly"
        assert (
            "architecture" in coding_stored
        ), "architecture not passed to coding agent"

        # Cleanup
        await redis_client.xdel(design_output_stream, design_message_id)
        await redis_client.xdel(coding_input_stream, coding_message_id)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_coding_agent_code_quality_features(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test CodingAgent includes code quality features."""
        # Setup mock LLM response with quality-focused output
        quality_coding_output = agent_fixtures["coding_agent"]["outputs"][0]
        mock_response = await self.setup_mock_llm_response(quality_coding_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Input message requesting high code quality
        input_message = {
            "request_id": "quality-code-999",
            "user_id": "test-user-456",
            "architecture": {
                "components": ["api-service"],
                "patterns": ["clean-architecture", "dependency-injection"],
                "technologies": ["FastAPI", "SQLAlchemy"],
            },
            "quality_requirements": {
                "testing": True,
                "linting": True,
                "type_hints": True,
                "documentation": True,
            },
            "timestamp": "2025-06-26T01:50:00Z",
            "request_type": "coding",
            "priority": "high",
        }

        # Expected output keys including quality features
        expected_output_keys = [
            "request_id",
            "source_code",
            "file_structure",
            "dependencies",
            "documentation",
            "test_files",
            "linting_config",
        ]

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client, "coding", input_message, expected_output_keys, timeout=15.0
        )

        # Verify test files are included
        assert "test_files" in output_data, "test_files missing from output"
        test_files = output_data["test_files"]
        assert isinstance(test_files, dict), "test_files should be a dictionary"
        assert len(test_files) > 0, "test_files is empty"

        # Verify linting configuration
        assert "linting_config" in output_data, "linting_config missing from output"
        linting_config = output_data["linting_config"]
        assert isinstance(linting_config, dict), "linting_config should be a dictionary"
        assert (
            "pyproject.toml" in linting_config or ".flake8" in linting_config
        ), "linting config files missing"
