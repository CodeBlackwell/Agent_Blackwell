"""
Unit tests for the BaseAgentWorker message processing pipeline hardening.

Tests focus on:
1. Robust JSON parsing for nested/optional fields
2. Request ID preservation throughout the message lifecycle
3. Structured error reporting on worker failures
"""
import asyncio
import json
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure a stable legacy alias to prevent import collisions when pytest loads
# similarly named test modules from different package paths.
import sys as _sys
# Provide a distinct alias for this *unit* variant so other code can import it if needed.
_sys.modules.setdefault("test_base_worker_pipeline_unit", _sys.modules[__name__])
import redis.asyncio as redis

from src.workers.base_worker import BaseAgentWorker
from tests.unit.workers.test_worker_implementation import TestWorkerImplementation


class TestBaseWorkerPipeline:
    """Test the BaseAgentWorker message processing pipeline hardening features."""

    @pytest.mark.asyncio
    async def test_deep_parse_nested_json(self):
        """Test the deep_parse method with nested JSON strings."""
        worker = TestWorkerImplementation()
        
        # Test with simple values
        assert worker.deep_parse("test") == "test"
        assert worker.deep_parse(123) == 123
        assert worker.deep_parse(True) == True
        
        # Test with JSON strings
        json_str = '{"key": "value"}'
        expected = {"key": "value"}
        assert worker.deep_parse(json_str) == expected
        
        # Test with nested JSON strings
        nested_json_str = '{"outer": "{\\"inner\\": \\"value\\"}"}'
        expected = {"outer": {"inner": "value"}}
        assert worker.deep_parse(nested_json_str) == expected
        
        # Test with array of JSON strings
        array_json_str = '[{"item1": "value1"}, "{\\"item2\\": \\"value2\\"}"]'
        expected = [{"item1": "value1"}, {"item2": "value2"}]
        assert worker.deep_parse(array_json_str) == expected
        
        # Test with deeply nested JSON
        deep_nested = '{"level1": "{\\"level2\\": \\"{\\\\\\"level3\\\\\\": \\\\\\"value\\\\\\"}\\"}"}'
        expected = {"level1": {"level2": {"level3": "value"}}}
        assert worker.deep_parse(deep_nested) == expected

    @pytest.mark.asyncio
    async def test_extract_task_data(self):
        """Test the extract_task_data method with various message formats."""
        worker = TestWorkerImplementation()
        
        # Test with valid simple task data
        valid_message = {"task": json.dumps({"task_id": "123", "task_type": "test"})}
        task_data = worker.extract_task_data(valid_message)
        assert task_data == {"task_id": "123", "task_type": "test"}
        
        # Test with nested JSON in task data
        nested_task = {
            "task": json.dumps({
                "task_id": "123", 
                "task_type": "test",
                "nested_data": json.dumps({"key": "value"})
            })
        }
        task_data = worker.extract_task_data(nested_task)
        assert task_data["nested_data"] == {"key": "value"}
        
        # Test with missing required fields
        invalid_message = {"task": json.dumps({"some_field": "value"})}
        task_data = worker.extract_task_data(invalid_message)
        assert task_data is None
        
        # Test with invalid JSON
        invalid_json = {"task": "not a json string"}
        task_data = worker.extract_task_data(invalid_json)
        assert task_data is None

    @pytest.mark.asyncio
    async def test_request_id_preservation(self):
        """Test that request_id is preserved when publishing results."""
        # Create a worker with a mock Redis client
        worker = TestWorkerImplementation()
        worker.async_redis_client = AsyncMock()
        
        # Create task data with request_id
        task_data = {
            "task_id": "123",
            "task_type": "test",
            "request_id": "req-456"
        }
        
        # Create result without request_id
        result = {
            "status": "success",
            "result": "test_result"
        }
        
        # Publish result
        await worker.publish_result(task_data, result)
        
        # Verify that xadd was called with the correct parameters
        worker.async_redis_client.xadd.assert_called_once()
        args = worker.async_redis_client.xadd.call_args[0]
        kwargs = worker.async_redis_client.xadd.call_args[1]
        
        # Extract the result JSON that was published
        published_data = kwargs.get("fields", args[1])
        published_result = json.loads(published_data["result"])
        
        # Verify request_id was preserved
        assert published_result["request_id"] == "req-456"
        assert published_result["status"] == "success"
        assert published_result["result"] == "test_result"

    @pytest.mark.asyncio
    async def test_structured_error_reporting(self):
        """Test structured error reporting on worker failures."""
        # Create a worker with a mock Redis client
        worker = TestWorkerImplementation()
        worker.async_redis_client = AsyncMock()
        
        # Create task data
        task_data = {
            "task_id": "123",
            "task_type": "test",
            "request_id": "req-456"
        }
        
        # Create an error and traceback
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error = e
            tb_str = traceback.format_exc()
        
        # Publish error
        await worker.publish_error(task_data, error, tb_str)
        
        # Verify that xadd was called with the correct parameters
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
        assert published_error["error_message"] == "Test error"
        assert "traceback" in published_error

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """Test error handling in process_message method."""
        # Create a worker with mock Redis client
        worker = TestWorkerImplementation()
        worker.async_redis_client = AsyncMock()
        worker.async_redis_client.xack = AsyncMock()
        worker.async_redis_client.xadd = AsyncMock()
        
        # Mock the process_task method to raise an exception
        error = ValueError("Test process error")
        worker.process_task_mock = AsyncMock(side_effect=error)
        
        # Create a test message
        stream = "test_stream"
        message_id = "1234567890-0"
        message = {"task": json.dumps({"task_id": "123", "task_type": "test", "request_id": "req-456"})}
        
        # Process the message
        await worker.process_message(stream, message_id, message)
        
        # Verify that xack was not called (message not acknowledged due to error)
        worker.async_redis_client.xack.assert_not_called()
        
        # Verify that publish_error was called with structured error
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
