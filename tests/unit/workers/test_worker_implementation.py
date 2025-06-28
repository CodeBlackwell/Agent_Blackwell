"""
Test implementation of BaseAgentWorker for testing.

This module provides a test implementation of BaseAgentWorker
that exposes protected methods for testing.
"""

import json
from typing import Any, Dict

from src.workers.base_worker import BaseAgentWorker


class TestWorkerImplementation(BaseAgentWorker):
    """Test implementation of BaseAgentWorker that exposes protected methods."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the test worker."""
        super().__init__("test_worker", *args, **kwargs)
        self.process_task_mock = None
        
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for testing."""
        if self.process_task_mock:
            return await self.process_task_mock(task_data)
        return {"status": "success", "result": "test_result"}
    
    # Expose protected methods for testing
    
    def deep_parse(self, value: Any) -> Any:
        """Expose _deep_parse for testing."""
        return self._deep_parse(value)
    
    def extract_task_data(self, message: Dict[str, str]) -> Dict[str, Any]:
        """Expose _extract_task_data for testing."""
        return self._extract_task_data(message)
    
    async def publish_result(self, task_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Expose _publish_result for testing."""
        await self._publish_result(task_data, result)
    
    async def publish_error(self, task_data: Dict[str, Any], error: Exception, tb: str) -> None:
        """Expose _publish_error for testing."""
        await self._publish_error(task_data, error, tb)
    
    async def process_message(self, stream: str, message_id: str, message: Dict[str, str]) -> None:
        """Expose _process_message for testing."""
        await self._process_message(stream, message_id, message)
