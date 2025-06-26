"""
Base classes and utilities for agent integration tests.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.fixtures.main import get_fixtures_by_category
from tests.workers.agent_worker import AgentWorker


class BaseAgentIntegrationTest:
    """Base class for all agent integration tests."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host, port=settings.redis.port, decode_responses=True
        )
        yield client
        await client.close()

    @pytest.fixture
    def mock_openai_response(self):
        """Fixture to provide mock OpenAI API responses."""

        def _create_mock_response(
            content: str, role: str = "assistant"
        ) -> Dict[str, Any]:
            return {
                "id": "mock-completion-id",
                "object": "chat.completion",
                "created": 1677858242,
                "model": "gpt-3.5-turbo-test",
                "usage": {
                    "prompt_tokens": 13,
                    "completion_tokens": len(content) // 4,  # Rough estimate
                    "total_tokens": len(content) // 4 + 13,
                },
                "choices": [
                    {
                        "message": {"role": role, "content": content},
                        "finish_reason": "stop",
                        "index": 0,
                    }
                ],
            }

        return _create_mock_response

    @pytest.fixture
    def mock_vector_db_response(self):
        """Fixture to provide mock vector database responses."""

        def _create_mock_response(
            vectors: List[Dict[str, Any]], scores: Optional[List[float]] = None
        ) -> Dict[str, Any]:
            if scores is None:
                scores = [
                    0.95 - (i * 0.05) for i in range(len(vectors))
                ]  # Descending similarity scores

            return {
                "matches": [
                    {
                        "id": f"vector-{i}",
                        "score": scores[i],
                        "values": vector.get("values", []),
                        "metadata": vector.get("metadata", {}),
                    }
                    for i, vector in enumerate(vectors)
                ],
                "namespace": "test-namespace",
            }

        return _create_mock_response

    @pytest.fixture
    def agent_fixtures(self):
        """Get agent-specific fixtures."""
        return get_fixtures_by_category("agent_io")

    @pytest.fixture
    def user_request_fixtures(self):
        """Get user request fixtures."""
        return get_fixtures_by_category("user_requests")

    @pytest.fixture
    def vector_fixtures(self):
        """Get vector embedding fixtures."""
        return get_fixtures_by_category("vector_embeddings")

    @pytest.fixture
    async def agent_worker(self, redis_client):
        """Start the agent worker in the background during integration tests."""
        # Clear Redis streams before starting worker to ensure clean state
        await self.clear_redis_streams(redis_client)

        # Create worker instance
        worker = AgentWorker(redis_host="redis-test", redis_port=6379)

        # Start worker as a background task
        worker_task = None
        try:
            # Connect to Redis and initialize agents
            await worker.connect_redis()
            await worker.initialize_agents()

            # Start the worker loop as a background task
            worker.running = True
            worker_task = asyncio.create_task(worker.run_worker_loop())

            # Give the worker a moment to start
            await asyncio.sleep(0.5)

            yield worker

        finally:
            # Stop the worker
            worker.running = False
            if worker_task:
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
            await worker.stop()

    async def clear_redis_streams(self, redis_client: redis.Redis) -> None:
        """Clear all agent streams to ensure test isolation."""
        # Define all agent stream names
        agent_types = [
            "spec_agent",
            "design_agent",
            "coding_agent",
            "review_agent",
            "test_agent",
        ]
        stream_types = ["input", "output"]

        for agent_type in agent_types:
            for stream_type in stream_types:
                stream_name = f"agent:{agent_type}:{stream_type}"
                try:
                    # Delete the entire stream (removes all messages)
                    await redis_client.delete(stream_name)
                except Exception as e:
                    # Ignore errors if stream doesn't exist
                    pass

    async def setup_mock_llm_response(
        self, content: str, status_code: int = 200
    ) -> AsyncMock:
        """Setup a mock LLM API response."""
        mock_response = AsyncMock()
        mock_response.status = status_code

        # Create the response data structure
        response_data = {
            "id": "mock-completion-id",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "gpt-3.5-turbo-test",
            "usage": {
                "prompt_tokens": 13,
                "completion_tokens": len(content) // 4,
                "total_tokens": len(content) // 4 + 13,
            },
            "choices": [
                {
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
        }

        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.text = AsyncMock(return_value=json.dumps(response_data))
        return mock_response

    async def publish_to_agent_stream(
        self, redis_client: redis.Redis, agent_type: str, message: Dict[str, Any]
    ) -> str:
        """Publish a message to an agent's input stream.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            message: Message data to publish

        Returns:
            Message ID in Redis stream
        """
        # Map short agent names to full agent worker stream names
        agent_type_mapping = {
            "spec": "spec_agent",
            "design": "design_agent",
            "coding": "coding_agent",
            "review": "review_agent",
            "test": "test_agent",
        }

        # Use the full agent name for stream naming
        full_agent_type = agent_type_mapping.get(agent_type, agent_type)
        stream_name = f"agent:{full_agent_type}:input"

        # Serialize complex fields for Redis stream storage
        # Redis streams can only store string values
        serialized_message = {}
        for key, value in message.items():
            if isinstance(value, (dict, list)):
                # Serialize complex objects as JSON strings
                serialized_message[key] = json.dumps(value)
            else:
                # Keep simple values as strings
                serialized_message[key] = str(value)

        message_id = await redis_client.xadd(stream_name, serialized_message)
        return message_id

    async def wait_for_agent_output(
        self, redis_client: redis.Redis, agent_type: str, timeout: float = 5.0
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Wait for output from an agent's output stream.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            timeout: Maximum time to wait in seconds

        Returns:
            Tuple of (message_id, message_data) or (None, None) if timeout
        """
        # Map short agent names to full agent worker stream names
        agent_type_mapping = {
            "spec": "spec_agent",
            "design": "design_agent",
            "coding": "coding_agent",
            "review": "review_agent",
            "test": "test_agent",
        }

        # Use the full agent name for stream naming
        full_agent_type = agent_type_mapping.get(agent_type, agent_type)
        stream_name = f"agent:{full_agent_type}:output"
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            # Read latest message (if any)
            messages = await redis_client.xread(
                {stream_name: "0-0"}, count=1, block=1000
            )

            if messages:
                stream_name, message_list = messages[0]
                message_id, message_data = message_list[0]

                # Deserialize JSON strings back to objects for complex fields
                # Redis streams store all values as bytes/strings, so we need to decode and parse
                parsed_data = {}
                for field_name, field_value in message_data.items():
                    if isinstance(field_name, bytes):
                        field_name = field_name.decode("utf-8")
                    if isinstance(field_value, bytes):
                        field_value = field_value.decode("utf-8")

                    # Try to parse as JSON for complex fields
                    try:
                        parsed_data[field_name] = json.loads(field_value)
                    except (json.JSONDecodeError, TypeError):
                        # If not valid JSON, keep as string
                        parsed_data[field_name] = field_value

                return message_id, parsed_data

            # Small delay before checking again
            await asyncio.sleep(0.1)

        return None, None

    async def assert_agent_produces_output(
        self,
        redis_client: redis.Redis,
        agent_type: str,
        input_message: Dict[str, Any],
        expected_keys: List[str],
        timeout: float = 5.0,
    ) -> Dict[str, Any]:
        """Assert that an agent produces output with expected keys.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            input_message: Message to send to agent
            expected_keys: Expected keys in the agent output
            timeout: Maximum time to wait for output

        Returns:
            The agent output message data
        """
        # Publish input message
        await self.publish_to_agent_stream(redis_client, agent_type, input_message)

        # Wait for output
        message_id, message_data = await self.wait_for_agent_output(
            redis_client, agent_type, timeout
        )

        # Assert output was received
        assert (
            message_id is not None
        ), f"No output received from {agent_type} agent within {timeout} seconds"
        assert message_data is not None, "Output message data is None"

        # Assert expected keys are in output
        for key in expected_keys:
            assert (
                key in message_data
            ), f"Expected key '{key}' not found in {agent_type} agent output"

        return message_data
