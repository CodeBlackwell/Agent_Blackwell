"""
Design Agent Worker for Redis Stream Consumption.

This module implements a worker that consumes tasks from Redis streams
and processes them using the Design Agent.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from src.agents.design_agent import DesignAgent
from src.workers.base_worker import BaseAgentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DesignAgentWorker(BaseAgentWorker):
    """Worker implementation for the Design Agent."""

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
        Initialize the Design Agent Worker.
        
        Args:
            redis_url: URL for Redis connection
            input_streams: List of input stream names to consume from
            result_stream: Stream to publish results to
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name
            openai_api_key: OpenAI API key for the Design Agent
        """
        # Call parent constructor with agent_type="design"
        super().__init__(
            agent_type="design",
            redis_url=redis_url,
            input_streams=input_streams,
            result_stream=result_stream,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        
        # Initialize Design Agent
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agent = None
        
        logger.info("DesignAgentWorker initialized")

    async def initialize(self) -> None:
        """Initialize Redis connections and create the Design Agent."""
        # Initialize Redis connections from parent class
        await super().initialize()
        
        # Initialize the Design Agent
        self.agent = DesignAgent(openai_api_key=self.openai_api_key)
        
        logger.info("DesignAgentWorker agent initialized")

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the Design Agent.
        
        Args:
            task_data: Task data from Redis stream
            
        Returns:
            Task processing result with system design
        """
        try:
            logger.info(f"Processing design task: {task_data['task_id']}")
            
            # Extract requirements from task data
            requirements = task_data.get("requirements", "")
            if not requirements:
                # Try alternate fields that might contain the requirements
                requirements = task_data.get("input", "")
                if not requirements:
                    requirements = task_data.get("description", "")
                    if not requirements:
                        raise ValueError("No requirements found in task data")
            
            # Generate system design using the Design Agent
            design = await self.agent.generate_design(requirements)
            
            # Prepare result
            result = {
                "design": design,
                "original_requirements": requirements,
            }
            
            logger.info(f"Design agent generated system design for task {task_data['task_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing design task: {e}")
            # Return error result
            return {
                "error": str(e),
                "status": "failed",
                "original_requirements": task_data.get("requirements", ""),
            }


async def main():
    """Run the Design Agent Worker as a standalone process."""
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Create and start the worker
    worker = DesignAgentWorker(
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
