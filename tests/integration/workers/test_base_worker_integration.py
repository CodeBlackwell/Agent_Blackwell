"""
Integration tests for the BaseAgentWorker message processing pipeline.

These tests require a real Redis instance and test the end-to-end functionality
of the BaseAgentWorker with actual Redis streams.
"""
import asyncio
import json
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List

import pytest
import redis.asyncio as redis

from src.workers.base_worker import BaseAgentWorker
from tests.integration.agents.base import BaseAgentIntegrationTest
from tests.unit.workers.test_worker_implementation import TestWorkerImplementation


class TestBaseWorkerIntegration(BaseAgentIntegrationTest):
    """Integration tests for the BaseAgentWorker message processing pipeline."""

    @pytest.fixture
    async def redis_client(self):
        """Create a Redis client for testing."""
        # Use environment variable for Redis URL if available, otherwise use default
        redis_url = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_end_to_end_message_processing(self, redis_client):
        """Test end-to-end message processing with real Redis."""
        # Clear Redis streams before test
        await self.clear_redis_streams(redis_client)
        
        # Get Redis connection details from the client
        host = redis_client.connection_pool.connection_kwargs.get('host', 'localhost')
        port = redis_client.connection_pool.connection_kwargs.get('port', 6379)
        redis_url = f"redis://{host}:{port}"
        
        # Create worker with real Redis client
        worker = TestWorkerImplementation(redis_url=redis_url)
        await worker.initialize()
        
        # Create test streams
        input_stream = "test_worker_input"
        worker.input_streams = [input_stream]
        worker.result_stream = "test_worker_output"
        
        # Create consumer group
        try:
            await worker.async_redis_client.xgroup_create(
                input_stream, worker.consumer_group, "0", mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        
        # Publish test message with nested JSON and request_id
        message_data = {
            "task_id": "e2e-123",
            "task_type": "test",
            "request_id": "req-e2e-456",
            "nested_data": json.dumps({"key": "value"})
        }
        
        await redis_client.xadd(input_stream, {"task": json.dumps(message_data)})
        
        # Process messages
        # We need to access protected methods here for integration testing
        # pylint: disable=protected-access
        await worker._process_pending_messages()
        await worker._process_new_messages()
        
        # Wait for result
        messages = await redis_client.xread({worker.result_stream: "0"}, count=1)
        
        # Verify result
        assert len(messages) == 1
        stream_name, message_list = messages[0]
        assert stream_name == worker.result_stream
        assert len(message_list) == 1
        
        # Extract and parse result
        _, message_data = message_list[0]
        result = json.loads(message_data["result"])
        
        # Verify request_id preservation
        assert result["request_id"] == "req-e2e-456"
        assert result["status"] == "success"
        assert result["result"] == "test_result"
        
        # Clean up
        await worker._cleanup()
        
    @pytest.mark.asyncio
    async def test_request_id_preservation_integration(self, redis_client):
        """Test that request_id is preserved in an integration setting."""
        # Clear Redis streams before test
        await self.clear_redis_streams(redis_client)
        
        # Get Redis connection details from the client
        host = redis_client.connection_pool.connection_kwargs.get('host', 'localhost')
        port = redis_client.connection_pool.connection_kwargs.get('port', 6379)
        redis_url = f"redis://{host}:{port}"
        
        # Create worker with real Redis client
        worker = TestWorkerImplementation(redis_url=redis_url)
        await worker.initialize()
        
        # Create task data with request_id
        task_data = {
            "task_id": "int-123",
            "task_type": "test",
            "request_id": "req-int-456"
        }
        
        # Create result without request_id
        result = {
            "status": "success",
            "result": "integration_test_result"
        }
        
        # Publish result
        await worker.publish_result(task_data, result)
        
        # Read from result stream
        messages = await redis_client.xread({worker.result_stream: "0"}, count=1)
        
        # Verify result
        assert len(messages) == 1
        stream_name, message_list = messages[0]
        assert stream_name == worker.result_stream
        assert len(message_list) == 1
        
        # Extract and parse result
        _, message_data = message_list[0]
        published_result = json.loads(message_data["result"])
        
        # Verify request_id preservation
        assert published_result["request_id"] == "req-int-456"
        assert published_result["status"] == "success"
        assert published_result["result"] == "integration_test_result"
        
        # Clean up
        await worker._cleanup()
