"""
Integration tests for the BaseAgentWorker message processing pipeline hardening.

Tests focus on:
1. Robust JSON parsing for nested/optional fields
2. Request ID preservation throughout the message lifecycle
3. Structured error reporting on worker failures
"""
import asyncio
import json
import traceback
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure stable aliases so pytest can import both unit and integration variants
import sys as _sys
# Provide only an *integration*-specific alias; do *not* register the generic
# name to avoid import collisions with the unit test variant.
_sys.modules.setdefault("test_base_worker_pipeline_integration", _sys.modules[__name__])
import redis.asyncio as redis

from src.workers.base_worker import BaseAgentWorker
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestWorkerImplementation(BaseAgentWorker):
    """Test implementation of BaseAgentWorker for testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__("test_worker", *args, **kwargs)
        self.process_task_mock = AsyncMock()
        self.process_task_mock.return_value = {"status": "success", "result": "test_result"}
        
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for testing."""
        return await self.process_task_mock(task_data)


class TestBaseWorkerPipeline(BaseAgentIntegrationTest):
    """Test the BaseAgentWorker message processing pipeline hardening features."""

    @pytest.mark.asyncio
    async def test_deep_parse_nested_json(self):
        """Test the _deep_parse method with nested JSON strings."""
        worker = TestWorkerImplementation()
        
        # Test with simple values
        assert worker._deep_parse("test") == "test"
        assert worker._deep_parse(123) == 123
        assert worker._deep_parse(True) == True
        
        # Test with JSON strings
        json_str = '{"key": "value"}'
        expected = {"key": "value"}
        assert worker._deep_parse(json_str) == expected
        
        # Test with nested JSON strings
        nested_json_str = '{"outer": "{\\"inner\\": \\"value\\"}"}'
        expected = {"outer": {"inner": "value"}}
        assert worker._deep_parse(nested_json_str) == expected
        
        # Test with array of JSON strings
        array_json_str = '[{"item1": "value1"}, "{\\"item2\\": \\"value2\\"}"]'
        expected = [{"item1": "value1"}, {"item2": "value2"}]
        assert worker._deep_parse(array_json_str) == expected
        
        # Test with deeply nested JSON
        deep_nested = '{"level1": "{\\"level2\\": \\"{\\\\\\"level3\\\\\\": \\\\\\"value\\\\\\"}\\"}"}'
        expected = {"level1": {"level2": {"level3": "value"}}}
        assert worker._deep_parse(deep_nested) == expected

    @pytest.mark.asyncio
    async def test_extract_task_data(self):
        """Test the _extract_task_data method with various message formats."""
        worker = TestWorkerImplementation()
        
        # Test with valid simple task data
        valid_message = {"task": json.dumps({"task_id": "123", "task_type": "test"})}
        task_data = worker._extract_task_data(valid_message)
        assert task_data == {"task_id": "123", "task_type": "test"}
        
        # Test with nested JSON in task data
        nested_task = {
            "task": json.dumps({
                "task_id": "123", 
                "task_type": "test",
                "nested_data": json.dumps({"key": "value"})
            })
        }
        task_data = worker._extract_task_data(nested_task)
        assert task_data["nested_data"] == {"key": "value"}
        
        # Test with missing required fields
        invalid_message = {"task": json.dumps({"some_field": "value"})}
        task_data = worker._extract_task_data(invalid_message)
        assert task_data is None
        
        # Test with invalid JSON
        invalid_json = {"task": "not a json string"}
        task_data = worker._extract_task_data(invalid_json)
        assert task_data is None

    @pytest.mark.asyncio
    async def test_request_id_preservation(self, redis_client):
        """Test that request_id is preserved when publishing results."""
        # Create a worker with a mock Redis client
        worker = TestWorkerImplementation(redis_url="redis://localhost:6379")
        worker.async_redis_client = AsyncMock()
        worker.async_redis_client.xadd = AsyncMock()
        
        # Test task data with request_id
        task_data = {
            "task_id": "123",
            "task_type": "test",
            "request_id": "req-456",
            "job_id": "job-789"
        }
        
        # Result without request_id
        result = {"status": "success", "result": "test_result"}
        
        # Publish result
        await worker._publish_result(task_data, result)
        
        # Check that xadd was called with the correct arguments
        worker.async_redis_client.xadd.assert_called_once()
        args = worker.async_redis_client.xadd.call_args[0]
        kwargs = worker.async_redis_client.xadd.call_args[1]
        
        # Extract the result JSON that was published
        published_data = kwargs.get("fields", args[1])
        published_result = json.loads(published_data["result"])
        
        # Verify request_id and job_id were preserved
        assert published_result["request_id"] == "req-456"
        assert published_result["job_id"] == "job-789"
        assert published_result["status"] == "success"
        assert published_result["result"] == "test_result"

    @pytest.mark.asyncio
    async def test_structured_error_reporting(self):
        """Test structured error reporting on worker failures."""
        # Create a worker with a mock Redis client
        worker = TestWorkerImplementation(redis_url="redis://localhost:6379")
        worker.async_redis_client = AsyncMock()
        worker.async_redis_client.xadd = AsyncMock()
        
        # Test task data with request_id
        task_data = {
            "task_id": "123",
            "task_type": "test",
            "request_id": "req-456"
        }
        
        # Create an error and traceback
        error = ValueError("Test error")
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Publish error
        await worker._publish_error(task_data, error, tb)
        
        # Check that xadd was called with the correct arguments
        worker.async_redis_client.xadd.assert_called_once()
        args = worker.async_redis_client.xadd.call_args[0]
        kwargs = worker.async_redis_client.xadd.call_args[1]
        
        # Extract the error JSON that was published
        published_data = kwargs.get("fields", args[1])
        published_error = json.loads(published_data["result"])
        
        # Verify error structure
        assert published_error["task_id"] == "123"
        assert published_error["task_type"] == "test"
        assert published_error["agent_type"] == "test_worker"
        assert published_error["request_id"] == "req-456"
        assert published_error["status"] == "failed"
        assert published_error["error_type"] == "ValueError"
        assert published_error["error_message"] == "Test error"
        assert "traceback" in published_error
        assert isinstance(published_error["timestamp"], str)

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """Test error handling in _process_message method."""
        # Create a worker with mock Redis client
        worker = TestWorkerImplementation(redis_url="redis://localhost:6379")
        worker.async_redis_client = AsyncMock()
        worker.async_redis_client.xack = AsyncMock()
        worker.async_redis_client.xadd = AsyncMock()
        
        # Mock the process_task method to raise an exception
        error = ValueError("Test process error")
        worker.process_task_mock.side_effect = error
        
        # Create a test message
        stream = "test_stream"
        message_id = "1234567890-0"
        message = {"task": json.dumps({"task_id": "123", "task_type": "test", "request_id": "req-456"})}
        
        # Process the message
        await worker._process_message(stream, message_id, message)
        
        # Verify that xack was not called (message not acknowledged due to error)
        worker.async_redis_client.xack.assert_not_called()
        
        # Verify that _publish_error was called with structured error
        worker.async_redis_client.xadd.assert_called_once()
        args = worker.async_redis_client.xadd.call_args[0]
        kwargs = worker.async_redis_client.xadd.call_args[1]
        
        # Extract the error JSON that was published
        published_data = kwargs.get("fields", args[1])
        published_error = json.loads(published_data["result"])
        
        # Verify error structure
        assert published_error["task_id"] == "123"
        assert published_error["task_type"] == "test"
        assert published_error["request_id"] == "req-456"
        assert published_error["status"] == "failed"
        assert published_error["error_type"] == "ValueError"
        assert published_error["error_message"] == "Test process error"
        assert "traceback" in published_error

    @pytest.mark.asyncio
    async def test_end_to_end_message_processing(self, redis_client):
        """Test end-to-end message processing with real Redis."""
        # Clear Redis streams before test
        await self.clear_redis_streams(redis_client)
        
        # Create worker with real Redis client
        worker = TestWorkerImplementation(redis_url=f"redis://{redis_client.connection_pool.connection_kwargs['host']}:{redis_client.connection_pool.connection_kwargs['port']}")
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
        
        # Process one message
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
