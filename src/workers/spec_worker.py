"""
Spec Agent Worker for Redis Stream Consumption.

This module implements a worker that consumes tasks from Redis streams
and processes them using the Spec Agent.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from src.agents.spec_agent import SpecAgent
from src.workers.base_worker import BaseAgentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SpecAgentWorker(BaseAgentWorker):
    """Worker implementation for the Spec Agent."""

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
        Initialize the Spec Agent Worker.
        
        Args:
            redis_url: URL for Redis connection
            input_streams: List of input stream names to consume from
            result_stream: Stream to publish results to
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name
            openai_api_key: OpenAI API key for the Spec Agent
        """
        # Call parent constructor with agent_type="spec"
        super().__init__(
            agent_type="spec",
            redis_url=redis_url,
            input_streams=input_streams,
            result_stream=result_stream,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        
        # Initialize Spec Agent
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agent = None
        
        logger.info("SpecAgentWorker initialized")

    async def initialize(self) -> None:
        """Initialize Redis connections and create the Spec Agent."""
        # Initialize Redis connections from parent class
        await super().initialize()
        
        # Initialize the Spec Agent
        self.agent = SpecAgent(openai_api_key=self.openai_api_key)
        
        logger.info("SpecAgentWorker agent initialized")

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the Spec Agent.
        
        Args:
            task_data: Task data from Redis stream
            
        Returns:
            Task processing result with generated tasks
        """
        try:
            logger.info(f"Processing spec task: {task_data['task_id']}")
            
            # Extract user request from task data
            user_request = task_data.get("input", "")
            if not user_request:
                # Try alternate fields that might contain the user request
                user_request = task_data.get("description", "")
                if not user_request:
                    raise ValueError("No user request found in task data")
            
            # Generate tasks using the Spec Agent
            tasks = await self.agent.generate_tasks(user_request)
            
            # Convert tasks to serializable format
            task_list = [task.dict() for task in tasks]
            
            # Prepare result
            result = {
                "tasks": task_list,
                "count": len(task_list),
                "original_request": user_request,
            }
            
            logger.info(f"Spec agent generated {len(task_list)} tasks")
            return result
            
        except Exception as e:
            logger.error(f"Error processing spec task: {e}")
            # Return error result
            return {
                "error": str(e),
                "status": "failed",
                "original_request": task_data.get("input", ""),
            }


async def main():
    """Run the Spec Agent Worker as a standalone process."""
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Create and start the worker
    worker = SpecAgentWorker(
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
