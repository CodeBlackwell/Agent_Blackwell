"""
Run all agent workers for end-to-end task processing.

This script starts all agent workers to consume tasks from Redis streams
and process them using the appropriate agents.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, List

from src.workers.spec_worker import SpecAgentWorker
from src.workers.design_worker import DesignAgentWorker
from src.workers.coding_worker import CodingAgentWorker
from src.workers.review_worker import ReviewAgentWorker
from src.workers.test_worker import TestAgentWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages multiple agent workers."""

    def __init__(self, redis_url: str = None, openai_api_key: str = None):
        """
        Initialize the worker manager.
        
        Args:
            redis_url: URL for Redis connection
            openai_api_key: OpenAI API key for the agents
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.workers = {}
        self.running = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("WorkerManager initialized")

    def _signal_handler(self, sig, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {sig}, shutting down workers")
        self.running = False
        # Let the async loop handle the shutdown
    
    async def initialize_workers(self):
        """Initialize all agent workers."""
        # Create worker instances
        self.workers = {
            "spec": SpecAgentWorker(
                redis_url=self.redis_url,
                openai_api_key=self.openai_api_key,
            ),
            "design": DesignAgentWorker(
                redis_url=self.redis_url,
                openai_api_key=self.openai_api_key,
            ),
            "coding": CodingAgentWorker(
                redis_url=self.redis_url,
                openai_api_key=self.openai_api_key,
            ),
            "review": ReviewAgentWorker(
                redis_url=self.redis_url,
                openai_api_key=self.openai_api_key,
            ),
            "test": TestAgentWorker(
                redis_url=self.redis_url,
                openai_api_key=self.openai_api_key,
            ),
        }
        
        # Initialize each worker
        for worker_type, worker in self.workers.items():
            logger.info(f"Initializing {worker_type} worker")
            await worker.initialize()
        
        logger.info("All workers initialized")
    
    async def start_workers(self):
        """Start all agent workers to process tasks."""
        self.running = True
        
        # Start worker tasks
        worker_tasks = []
        for worker_type, worker in self.workers.items():
            logger.info(f"Starting {worker_type} worker")
            # Create a task for each worker's process_messages method
            task = asyncio.create_task(worker.process_messages())
            worker_tasks.append(task)
        
        logger.info("All workers started")
        
        # Wait for workers to complete or for shutdown signal
        try:
            # Use asyncio.gather to wait for all tasks
            await asyncio.gather(*worker_tasks)
        except asyncio.CancelledError:
            logger.info("Worker tasks cancelled")
        finally:
            await self.stop_workers()
    
    async def stop_workers(self):
        """Stop all agent workers."""
        logger.info("Stopping all workers")
        
        # Stop each worker
        for worker_type, worker in self.workers.items():
            logger.info(f"Stopping {worker_type} worker")
            await worker.stop()
        
        logger.info("All workers stopped")


async def main():
    """Run all agent workers."""
    # Get Redis URL and OpenAI API key from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Check if OpenAI API key is available
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY environment variable not set")
    
    # Create and start the worker manager
    manager = WorkerManager(
        redis_url=redis_url,
        openai_api_key=openai_api_key,
    )
    
    try:
        # Initialize and start all workers
        await manager.initialize_workers()
        await manager.start_workers()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping workers")
    except Exception as e:
        logger.error(f"Error running workers: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
