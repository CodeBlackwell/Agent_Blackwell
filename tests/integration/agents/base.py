"""
Base classes and utilities for agent integration tests.
"""
import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.fixtures.main import get_fixtures_by_category
from tests.workers.agent_worker import AgentWorker


TIMEOUT_DEFAULT = 30.0  # seconds – complex agent interactions can take time

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

        # Create worker instance with test mode enabled
        worker = AgentWorker(redis_host="redis-test", redis_port=6379, is_test_mode=True)

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
            "spec",
            "design",
            "coding",
            "review",
            "test",
        ]
        stream_types = ["input", "output"]
        
        # Clear both canonical and legacy format streams
        for agent_type in agent_types:
            for stream_type in stream_types:
                # Clear canonical format streams
                canonical_stream = f"agent:{agent_type}:{stream_type}"
                try:
                    await redis_client.delete(canonical_stream)
                except Exception:
                    pass
                    
                # Clear legacy format streams
                legacy_stream = f"agent:{agent_type}_agent:{stream_type}"
                try:
                    await redis_client.delete(legacy_stream)
                except Exception:
                    pass
                    
                # Clear test prefixed streams
                test_stream = f"test_agent:{agent_type}:{stream_type}"
                try:
                    await redis_client.delete(test_stream)
                except Exception:
                    pass
        
        # Also clear generic task streams
        generic_streams = ["agent_tasks", "agent_results", "test_agent_tasks", "test_agent_results"]
        for stream in generic_streams:
            try:
                await redis_client.delete(stream)
            except Exception:
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
        self, redis_client: redis.Redis, agent_type: str, message: Dict[str, Any], is_test_mode: bool = True
    ) -> str:
        """Publish a message to an agent's input stream.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            message: Message data to publish
            is_test_mode: Whether to use test mode stream naming (default: True for tests)

        Returns:
            Message ID in Redis stream
        """
        # Map short agent names to normalized agent types (without _agent suffix)
        agent_type_mapping = {
            "spec": "spec",
            "design": "design",
            "coding": "coding",
            "review": "review",
            "test": "test",
            "spec_agent": "spec",
            "design_agent": "design",
            "coding_agent": "coding",
            "review_agent": "review",
            "test_agent": "test",
        }

        # Normalize the agent type (remove _agent suffix if present)
        normalized_agent_type = agent_type_mapping.get(agent_type, agent_type)
        if normalized_agent_type.endswith("_agent"):
            normalized_agent_type = normalized_agent_type[:-6]  # Remove _agent suffix
            
        # Determine stream name based on environment
        if is_test_mode:
            # In test mode, use test_prefixed streams
            stream_name = f"test_agent:{normalized_agent_type}:input"
            # Also support the generic test task stream
            if "test_agent_tasks" not in message.get("stream_options", []):
                message.setdefault("stream_options", []).append("test_agent_tasks")
        else:
            # In production, use canonical format
            stream_name = f"agent:{normalized_agent_type}:input"
            
        logging.debug(f"Publishing to stream: {stream_name} (test mode: {is_test_mode})")
        logging.debug(f"Message: {message}")


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
    self, redis_client: redis.Redis, agent_type: str, timeout: float = TIMEOUT_DEFAULT, is_test_mode: bool = True
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Wait for output from an agent's output stream.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            timeout: Maximum time to wait in seconds (default: TIMEOUT_DEFAULT, the default timeout for waiting on agent output)
            timeout: Maximum time to wait in seconds (default: TIMEOUT_DEFAULT)
            is_test_mode: Whether to use test mode stream naming (default: True for tests)

        Returns:
            Tuple of (message_id, message_data) or (None, None) if timeout
        """
        # Map short agent names to normalized agent types (without _agent suffix)
        agent_type_mapping = {
            "spec": "spec",
            "design": "design",
            "coding": "coding",
            "review": "review",
            "test": "test",
            "spec_agent": "spec",
            "design_agent": "design",
            "coding_agent": "coding",
            "review_agent": "review",
            "test_agent": "test",
        }

        # Normalize the agent type (remove _agent suffix if present)
        normalized_agent_type = agent_type_mapping.get(agent_type, agent_type)
        if normalized_agent_type.endswith("_agent"):
            normalized_agent_type = normalized_agent_type[:-6]  # Remove _agent suffix
            
        # Determine stream name based on environment
        if is_test_mode:
            # In test mode, use test_prefixed streams
            stream_name = f"test_agent:{normalized_agent_type}:output"
            # Also check the generic test result stream as fallback
            fallback_stream = "test_agent_results"
        else:
            # In production, use canonical format
            stream_name = f"agent:{normalized_agent_type}:output"
            # Also check legacy format as fallback
            fallback_stream = f"agent:{normalized_agent_type}_agent:output"
            
        logging.debug(f"Waiting for output on stream: {stream_name} (test mode: {is_test_mode})")
        
        # We'll check both the primary stream and fallback stream
        streams_to_check = [stream_name, fallback_stream]
        start_time = time.monotonic()
        backoff = 0.1  # seconds

        while time.monotonic() - start_time < timeout:
            # Check each stream for messages
            for current_stream in streams_to_check:
                # Read latest message (if any)
                try:
                    messages = await redis_client.xread(
                        {current_stream: "0-0"}, count=1, block=500
                    )
                    
                    if messages:
                        stream_name, message_list = messages[0]
                        message_id, message_data = message_list[0]
                        logging.debug(f"Found message in stream {current_stream}: {message_id}")
                        
                        # Process message data and return
                        # Deserialize JSON strings back to objects for complex fields
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
                except Exception as e:
                    logging.debug(f"Error reading from stream {current_stream}: {e}")
                    continue
            
            # Small delay before checking again using exponential backoff (capped)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.5, 2.0)

        return None, None

    async def assert_agent_produces_output(
        self,
        redis_client: redis.Redis,
        agent_type: str,
        input_message: Dict[str, Any],
        expected_keys: List[str],
        timeout: float = TIMEOUT_DEFAULT,
        is_test_mode: bool = True,
    ) -> Dict[str, Any]:
        """Assert that an agent produces output with expected keys.

        Args:
            redis_client: Redis client instance
            agent_type: Type of agent (spec, design, coding, review, test)
            input_message: Message to send to agent
            expected_keys: Expected keys in the agent output
            timeout: Maximum time to wait for output
            is_test_mode: Whether to use test mode stream naming (default: True for tests)

        Returns:
            The agent output message data
        """
        # Publish input message
        await self.publish_to_agent_stream(redis_client, agent_type, input_message, is_test_mode=is_test_mode)

        # Wait for output
        message_id, message_data = await self.wait_for_agent_output(
            redis_client, agent_type, timeout, is_test_mode=is_test_mode
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
