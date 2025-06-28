"""
Unit tests for the BaseAgentWorker message processing pipeline hardening.

Tests focus on:
1. Robust JSON parsing for nested/optional fields
2. Request ID preservation throughout the message lifecycle
3. Structured error reporting on worker failures
"""
import json
import traceback
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.base_worker import BaseAgentWorker


class TestBaseWorkerMethods:
    """Unit tests for BaseAgentWorker methods."""
    
    @pytest.fixture
    def worker(self):
        """Create a BaseAgentWorker instance with mocked Redis client."""
        # Create a concrete implementation of the abstract class for testing
        class ConcreteWorker(BaseAgentWorker):
            async def process_task(self, task_data):
                return {"status": "success", "result": "test_result"}
            
            # Expose protected methods for testing
            def deep_parse(self, value):
                return self._deep_parse(value)
                
            def extract_task_data(self, message):
                return self._extract_task_data(message)
                
            async def publish_result(self, task_data, result):
                return await self._publish_result(task_data, result)
                
            async def publish_error(self, task_data, error, tb):
                return await self._publish_error(task_data, error, tb)
                
            async def process_message(self, stream, message_id, message):
                return await self._process_message(stream, message_id, message)
        
        # Create worker with mocked Redis client
        worker = ConcreteWorker("test_worker")
        worker.async_redis_client = AsyncMock()
        worker.processed_ids = set()
        return worker
    
    def test_deep_parse_simple_values(self, worker):
        """Test deep_parse with simple values."""
        assert worker.deep_parse("test") == "test"
        assert worker.deep_parse(123) == 123
        assert worker.deep_parse(True) is True
        assert worker.deep_parse(None) is None
        assert worker.deep_parse([1, 2, 3]) == [1, 2, 3]
        assert worker.deep_parse({"a": 1}) == {"a": 1}
    
    def test_deep_parse_json_strings(self, worker):
        """Test deep_parse with JSON strings."""
        # Simple JSON string
        json_str = '{"key": "value"}'
        expected = {"key": "value"}
        assert worker.deep_parse(json_str) == expected
        
        # JSON array string
        array_str = '[1, 2, 3]'
        expected = [1, 2, 3]
        assert worker.deep_parse(array_str) == expected
    
    def test_deep_parse_nested_json(self, worker):
        """Test deep_parse with nested JSON strings."""
        # Nested JSON string
        nested_json_str = '{"outer": "{\\"inner\\": \\"value\\"}"}'
        expected = {"outer": {"inner": "value"}}
        assert worker._deep_parse(nested_json_str) == expected
        
        # Array with nested JSON
        array_json_str = '[{"item1": "value1"}, "{\\"item2\\": \\"value2\\"}"]'
        expected = [{"item1": "value1"}, {"item2": "value2"}]
        assert worker._deep_parse(array_json_str) == expected
    
    def test_deep_parse_invalid_json(self, worker):
        """Test _deep_parse with invalid JSON strings."""
        # Invalid JSON should be returned as-is
        invalid_json = "not a json string"
        assert worker._deep_parse(invalid_json) == invalid_json
    
    def test_extract_task_data_valid(self, worker):
        """Test _extract_task_data with valid message."""
        # Valid message with required fields
        valid_message = {"task": json.dumps({"task_id": "123", "task_type": "test"})}
        task_data = worker._extract_task_data(valid_message)
        assert task_data == {"task_id": "123", "task_type": "test"}
    
    def test_extract_task_data_nested(self, worker):
        """Test _extract_task_data with nested JSON fields."""
        # Message with nested JSON fields
        nested_message = {
            "task": json.dumps({
                "task_id": "123", 
                "task_type": "test",
                "nested_data": json.dumps({"key": "value"})
            })
        }
        task_data = worker._extract_task_data(nested_message)
        assert task_data["task_id"] == "123"
        assert task_data["task_type"] == "test"
        assert task_data["nested_data"] == {"key": "value"}
    
    def test_extract_task_data_missing_fields(self, worker):
        """Test _extract_task_data with missing required fields."""
        # Missing required fields
        invalid_message = {"task": json.dumps({"some_field": "value"})}
        task_data = worker._extract_task_data(invalid_message)
        assert task_data is None
    
    def test_extract_task_data_invalid_json(self, worker):
        """Test _extract_task_data with invalid JSON."""
        # Invalid JSON
        invalid_json = {"task": "not a json string"}
        task_data = worker._extract_task_data(invalid_json)
        assert task_data is None
    
    @pytest.mark.asyncio
    async def test_publish_result_with_request_id(self, worker):
        """Test _publish_result preserves request_id and job_id."""
        # Task data with request_id and job_id
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
    async def test_publish_error_structure(self, worker):
        """Test _publish_error creates structured error reports."""
        # Task data with request_id
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
    async def test_process_message_success_path(self, worker):
        """Test the happy path of _process_message."""
        # Mock process_task to return success
        worker.process_task = AsyncMock()
        worker.process_task.return_value = {"status": "success", "result": "test_result"}
        
        # Create a test message
        stream = "test_stream"
        message_id = "1234567890-0"
        message = {"task": json.dumps({"task_id": "123", "task_type": "test", "request_id": "req-456"})}
        
        # Process the message
        await worker._process_message(stream, message_id, message)
        
        # Verify message was acknowledged
        worker.async_redis_client.xack.assert_called_once_with(stream, worker.consumer_group, message_id)
        
        # Verify result was published
        worker.async_redis_client.xadd.assert_called_once()
        
        # Verify message was added to processed_ids
        assert message_id in worker.processed_ids
    
    @pytest.mark.asyncio
    async def test_process_message_error_path(self, worker):
        """Test the error path of _process_message."""
        # Mock process_task to raise an exception
        error = ValueError("Test process error")
        worker.process_task = AsyncMock(side_effect=error)
        
        # Create a test message
        stream = "test_stream"
        message_id = "1234567890-0"
        message = {"task": json.dumps({"task_id": "123", "task_type": "test", "request_id": "req-456"})}
        
        # Process the message
        await worker._process_message(stream, message_id, message)
        
        # Verify message was NOT acknowledged (to allow retry)
        worker.async_redis_client.xack.assert_not_called()
        
        # Verify error was published
        worker.async_redis_client.xadd.assert_called_once()
        
        # Verify message was NOT added to processed_ids
        assert message_id not in worker.processed_ids
        
        # Extract the error JSON that was published
        args = worker.async_redis_client.xadd.call_args[0]
        kwargs = worker.async_redis_client.xadd.call_args[1]
        published_data = kwargs.get("fields", args[1])
        published_error = json.loads(published_data["result"])
        
        # Verify error structure
        assert published_error["status"] == "failed"
        assert published_error["error_type"] == "ValueError"
        assert published_error["error_message"] == "Test process error"
