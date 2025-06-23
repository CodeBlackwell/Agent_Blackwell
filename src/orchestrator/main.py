"""
Main orchestrator module for agent coordination.

This module implements a task orchestration system using LangChain for agent coordination,
Redis Streams for task queuing, and Pinecone for vector storage.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

# LangChain imports
from pinecone import Pinecone, ServerlessSpec
from redis import Redis

# Local imports
from src.orchestrator.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator class that coordinates agent tasks using LangChain.

    This class handles:
    - Task queue management via Redis Streams
    - Context storage via Pinecone vector store
    - Agent dispatch and execution
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        pinecone_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        task_stream: str = "agent_tasks",
        result_stream: str = "agent_results",
    ):
        """
        Initialize the orchestrator with Redis and Pinecone connections.

        Args:
            redis_url: URL for Redis connection
            pinecone_api_key: API key for Pinecone (optional for local dev)
            openai_api_key: API key for OpenAI (optional, will use env var if not provided)
            task_stream: Name of the Redis stream for tasks
            result_stream: Name of the Redis stream for results
        """
        # Initialize Redis client
        self.redis_client = Redis.from_url(redis_url)
        self.task_stream = task_stream
        self.result_stream = result_stream

        # Initialize Pinecone client (if API key provided)
        self.pinecone_client = None
        self.vector_index = None
        if pinecone_api_key:
            self.pinecone_client = Pinecone(api_key=pinecone_api_key)
            # Create or get index
            if "agent-memory" not in self.pinecone_client.list_indexes().names():
                self.pinecone_client.create_index(
                    name="agent-memory",
                    dimension=1536,  # OpenAI embeddings dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-west-2"),
                )
            self.vector_index = self.pinecone_client.Index("agent-memory")

        # Initialize agent registry
        self.agents = {}
        self.agent_registry = None
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        logger.info("Orchestrator initialized")

    def register_agent(self, agent_name: str, agent_executor) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent_name: Name to register the agent under
            agent_executor: Agent instance with an ainvoke method
        """
        self.agents[agent_name] = agent_executor
        logger.info(f"Registered agent: {agent_name}")

    def initialize_agents(self) -> None:
        """
        Initialize all agents using the AgentRegistry.
        """
        try:
            # Create agent registry
            self.agent_registry = AgentRegistry(openai_api_key=self.openai_api_key)

            # Register all agents with the orchestrator
            self.agent_registry.register_agents_with_orchestrator(self)

            logger.info("All agents initialized and registered")
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")

    async def enqueue_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        Add a task to the task queue.

        Args:
            task_type: Type of task (corresponds to agent name)
            task_data: Dictionary containing task parameters

        Returns:
            task_id: Unique ID for the enqueued task
        """
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            **task_data,
        }

        # Add to Redis stream
        self.redis_client.xadd(self.task_stream, {"task": json.dumps(task)})

        logger.info(f"Enqueued task {task_id} of type {task_type}")
        return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task to check

        Returns:
            Dictionary with task status information
        """
        # Check result stream first
        results = self.redis_client.xrevrange(
            self.result_stream, count=100  # Limit to recent results
        )

        for _, result in results:
            result_data = json.loads(result[b"result"].decode("utf-8"))
            if result_data.get("task_id") == task_id:
                return result_data

        # Check task stream if not found in results
        tasks = self.redis_client.xrevrange(
            self.task_stream, count=100  # Limit to recent tasks
        )

        for _, task in tasks:
            task_data = json.loads(task[b"task"].decode("utf-8"))
            if task_data.get("task_id") == task_id:
                return task_data

        return {"task_id": task_id, "status": "not_found"}

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single task using the appropriate agent.

        Args:
            task: Task dictionary with task_type and parameters

        Returns:
            Result dictionary
        """
        task_id = task.get("task_id")
        task_type = task.get("task_type")

        try:
            # Check if agent exists
            if task_type not in self.agents:
                logger.error(f"No agent registered for task type: {task_type}")
                error_result = {
                    "task_id": task_id,
                    "status": "error",
                    "error": f"No agent registered for task type: {task_type}",
                }

                # Store error in Redis
                self.redis_client.xadd(
                    self.result_stream, {"result": json.dumps(error_result)}
                )

                return error_result

            # For now, implement special handling for dummy and echo agents
            if task_type == "dummy":
                result = {
                    "task_id": task_id,
                    "status": "completed",
                    "result": (
                        "pong"
                        if task.get("input") == "ping"
                        else "echo: " + str(task.get("input", ""))
                    ),
                }
            elif task_type == "echo":
                # Echo agent just returns the input
                result = {
                    "task_id": task_id,
                    "status": "completed",
                    "result": "echo: " + str(task.get("input", "")),
                }
            else:
                # Execute the agent
                agent = self.agents[task_type]
                agent_result = await agent.ainvoke(task)

                result = {
                    "task_id": task_id,
                    "status": "completed",
                    "result": agent_result,
                }

                # Handle sub-tasks if this was a spec_agent task
                if task_type == "spec_agent" and isinstance(agent_result, dict):
                    # Check if there are tasks in the result
                    if "output" in agent_result and isinstance(
                        agent_result["output"], list
                    ):
                        sub_tasks = agent_result["output"]
                        logger.info(f"Found {len(sub_tasks)} sub-tasks from spec_agent")

                        # Enqueue each sub-task
                        for i, sub_task in enumerate(sub_tasks):
                            # Extract task information
                            task_type = sub_task.get("task_type", "general")
                            task_description = sub_task.get("description", "")

                            # Create a new task with the extracted information
                            new_task_data = {
                                "input": task_description,
                                "parent_task_id": task_id,
                                "priority": sub_task.get("priority", "medium"),
                                "metadata": {
                                    "source": "spec_agent",
                                    "original_request": task.get("input", ""),
                                    "sub_task_index": i,
                                },
                            }

                            # Enqueue the new task if we have an agent for it
                            if task_type in self.agents or task_type == "general":
                                sub_task_id = await self.enqueue_task(
                                    task_type, new_task_data
                                )
                                logger.info(
                                    f"Enqueued sub-task {sub_task_id} of type {task_type}"
                                )
                            else:
                                logger.warning(
                                    f"No agent registered for sub-task type: {task_type}"
                                )

            # Store result in Redis
            self.redis_client.xadd(self.result_stream, {"result": json.dumps(result)})

            logger.info(f"Completed task {task_id}")
            return result

        except Exception as e:
            error_result = {"task_id": task_id, "status": "error", "error": str(e)}

            # Store error in Redis
            self.redis_client.xadd(
                self.result_stream, {"result": json.dumps(error_result)}
            )

            logger.error(f"Error processing task {task_id}: {e}")
            return error_result

    async def run_loop(self) -> None:
        """Main processing loop that dequeues and processes tasks."""
        logger.info("Starting orchestrator processing loop")

        last_id = "0"  # Start from the beginning of the stream

        while True:
            try:
                # Read new messages from the stream
                response = self.redis_client.xread(
                    {self.task_stream: last_id},
                    count=1,
                    block=1000,  # Block for 1 second
                )

                if not response:
                    await asyncio.sleep(0.1)  # Small delay if no messages
                    continue

                # Process each message
                for stream_name, messages in response:
                    for message_id, message in messages:
                        last_id = message_id  # Update last seen ID

                        # Parse task
                        task_data = json.loads(message[b"task"].decode("utf-8"))

                        # Process task
                        await self.process_task(task_data)

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)  # Delay before retry

    async def start(self) -> None:
        """
        Start the orchestrator.
        """
        # Initialize agents using the registry
        self.initialize_agents()

        # For testing purposes, also register dummy and echo agents
        if "dummy" not in self.agents:
            self.register_agent("dummy", None)
        if "echo" not in self.agents:
            self.register_agent("echo", None)

        # Start the processing loop
        await self.run_loop()


# Example usage
async def main():
    """Example usage of the Orchestrator with Spec Agent integration."""
    # Create orchestrator with OpenAI API key from environment
    # Make sure OPENAI_API_KEY is set in your environment
    orchestrator = Orchestrator()

    # Create agent registry and register agents with orchestrator
    try:
        # Initialize agents
        orchestrator.initialize_agents()

        # Register dummy agent explicitly for testing
        orchestrator.register_agent("dummy", None)

        # Print registered agents
        print(f"Registered agents: {list(orchestrator.agents.keys())}")

        # Check if spec_agent is registered
        if "spec_agent" in orchestrator.agents:
            # Enqueue a test task for the spec agent
            user_request = (
                "Create a FastAPI service with PostgreSQL database for a todo app"
            )
            task_id = await orchestrator.enqueue_task(
                "spec_agent", {"input": user_request}
            )
            print(f"Enqueued spec_agent task: {task_id}")
        else:
            print("Warning: spec_agent not registered, skipping spec agent test")

        # Enqueue a dummy task for testing
        dummy_task_id = await orchestrator.enqueue_task("dummy", {"input": "ping"})
        print(f"Enqueued dummy task: {dummy_task_id}")

        # Process tasks manually for testing
        print("\nProcessing tasks...")

        # Get tasks from the stream
        tasks = orchestrator.redis_client.xread(
            {orchestrator.task_stream: "0"}, count=10
        )

        for stream_name, messages in tasks:
            for message_id, message in messages:
                # Parse task
                task_data = json.loads(message[b"task"].decode("utf-8"))
                print(
                    f"Processing task: {task_data['task_id']} of type {task_data['task_type']}"
                )

                # Process task
                result = await orchestrator.process_task(task_data)
                print(f"Task result: {result}")

        print("\nAll tasks processed. Check the result stream for outputs.")

        # For a real application, you would start the continuous processing loop:
        # await orchestrator.start()
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
