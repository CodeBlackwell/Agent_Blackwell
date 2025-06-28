"""
Coding Agent Worker for Redis Stream Consumption.

This module implements a worker that consumes tasks from Redis streams
and processes them using the Coding Agent.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from src.agents.coding_agent import CodingAgent
from src.workers.base_worker import BaseAgentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CodingAgentWorker(BaseAgentWorker):
    """Worker implementation for the Coding Agent."""

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
        Initialize the Coding Agent Worker.
        
        Args:
            redis_url: URL for Redis connection
            input_streams: List of input stream names to consume from
            result_stream: Stream to publish results to
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name
            openai_api_key: OpenAI API key for the Coding Agent
        """
        # Call parent constructor with agent_type="coding"
        super().__init__(
            agent_type="coding",
            redis_url=redis_url,
            input_streams=input_streams,
            result_stream=result_stream,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        
        # Initialize Coding Agent
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agent = None
        
        logger.info("CodingAgentWorker initialized")

    async def initialize(self) -> None:
        """Initialize Redis connections and create the Coding Agent."""
        # Initialize Redis connections from parent class
        await super().initialize()
        
        # Initialize the Coding Agent
        self.agent = CodingAgent(openai_api_key=self.openai_api_key)
        
        logger.info("CodingAgentWorker agent initialized")

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the Coding Agent.
        
        Args:
            task_data: Task data from Redis stream
            
        Returns:
            Task processing result with generated code
        """
        try:
            logger.info(f"Processing coding task: {task_data['task_id']}")
            
            # Extract design and requirements from task data
            design = task_data.get("design", {})
            requirements = task_data.get("requirements", "")
            
            # If design is empty, try to get it from other fields
            if not design:
                design = task_data.get("input", {})
                if isinstance(design, str):
                    # Convert string to dict if possible
                    try:
                        design = json.loads(design)
                    except json.JSONDecodeError:
                        # Use as requirements if not JSON
                        if not requirements:
                            requirements = design
                        design = {}
            
            # If requirements is empty, try to get it from description
            if not requirements:
                requirements = task_data.get("description", "")
            
            # Generate code using the Coding Agent
            code_result = await self.agent.generate_code(design, requirements)
            
            # Prepare result
            result = {
                "code": code_result,
                "original_design": design,
                "original_requirements": requirements,
            }
            
            logger.info(f"Coding agent generated code for task {task_data['task_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing coding task: {e}")
            # Return error result
            return {
                "error": str(e),
                "status": "failed",
                "original_design": task_data.get("design", {}),
                "original_requirements": task_data.get("requirements", ""),
            }


async def main():
    """Run the Coding Agent Worker as a standalone process."""
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Create and start the worker
    worker = CodingAgentWorker(
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
