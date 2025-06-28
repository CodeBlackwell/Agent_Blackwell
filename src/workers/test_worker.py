"""
Test Agent Worker for Redis Stream Consumption.

This module implements a worker that consumes tasks from Redis streams
and processes them using the Test Agent.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from src.agents.test_agent import TestAgent
from src.workers.base_worker import BaseAgentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TestAgentWorker(BaseAgentWorker):
    """Worker implementation for the Test Agent."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        input_streams: list = None,
        result_stream: str = "agent_results",
        consumer_group: str = "agent_workers",
        consumer_name: str = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the Test Agent Worker.
        
        Args:
            redis_url: URL for Redis connection
            input_streams: List of input stream names to consume from
            result_stream: Stream to publish results to
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name
            openai_api_key: OpenAI API key for the Test Agent
        """
        # Call parent constructor with agent_type="test"
        super().__init__(
            agent_type="test",
            redis_url=redis_url,
            input_streams=input_streams,
            result_stream=result_stream,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        
        # Initialize Test Agent
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agent = None
        
        logger.info("TestAgentWorker initialized")

    async def initialize(self) -> None:
        """Initialize Redis connections and create the Test Agent."""
        # Initialize Redis connections from parent class
        await super().initialize()
        
        # Initialize the Test Agent
        self.agent = TestAgent(openai_api_key=self.openai_api_key)
        
        logger.info("TestAgentWorker agent initialized")

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the Test Agent.
        
        Args:
            task_data: Task data from Redis stream
            
        Returns:
            Task processing result with test plan and implementation
        """
        try:
            logger.info(f"Processing test task: {task_data['task_id']}")
            
            # Extract source code and requirements from task data
            source_code = task_data.get("source_code", {})
            requirements = task_data.get("requirements", "")
            
            # Handle different source code formats
            if not source_code:
                # Try to get source code from coding_output
                coding_output = task_data.get("coding_output", {})
                if coding_output:
                    # Handle different coding output formats
                    if "code" in coding_output:
                        code_data = coding_output["code"]
                    else:
                        code_data = coding_output
                        
                    # Extract source code based on format
                    if isinstance(code_data.get("source_code"), dict):
                        source_code = code_data["source_code"]
                    elif "files" in code_data:
                        source_code = {}
                        for file_info in code_data["files"]:
                            if isinstance(file_info, dict) and "path" in file_info and "content" in file_info:
                                source_code[file_info["path"]] = file_info["content"]
            
            # If requirements is empty, try to get it from description
            if not requirements:
                requirements = task_data.get("description", "")
                
            # If source code is still empty, return error
            if not source_code:
                raise ValueError("No source code found in task data")
            
            # Generate tests using the Test Agent
            test_result = await self.agent.generate_tests(source_code, requirements)
            
            # Prepare result
            result = {
                "tests": test_result,
                "original_source_code": source_code,
                "original_requirements": requirements,
            }
            
            logger.info(f"Test agent generated tests for task {task_data['task_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing test task: {e}")
            # Return error result
            return {
                "error": str(e),
                "status": "failed",
                "original_source_code": task_data.get("source_code", {}),
                "original_requirements": task_data.get("requirements", ""),
            }


async def main():
    """Run the Test Agent Worker as a standalone process."""
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Create and start the worker
    worker = TestAgentWorker(
        redis_url=redis_url,
        openai_api_key=openai_api_key,
    )
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping worker")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
