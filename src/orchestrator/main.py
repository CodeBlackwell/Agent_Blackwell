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
from typing import Any, Dict, List, Optional

# LangChain imports
from redis import Redis

# Optional imports for vector storage
try:
    from pinecone import Pinecone, ServerlessSpec

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Pinecone not available - vector storage features disabled")

# Local imports
from src.orchestrator.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
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
        task_stream: str = "agent_tasks",
        result_stream: str = "agent_results",
        is_test_mode: bool = False,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        skip_pinecone_init: bool = False,
    ) -> None:
        """
        Initialize the orchestrator with Redis and stream configuration.

        Args:
            redis_url: URL for Redis connection
            task_stream: Name of the main task stream
            result_stream: Name of the result stream
            is_test_mode: Whether running in test mode (affects stream naming)
            openai_api_key: OpenAI API key for agent initialization
            pinecone_api_key: Pinecone API key for vector storage
            skip_pinecone_init: Skip Pinecone initialization for testing
        """
        try:
            # Store configuration
            self.redis_url = redis_url
            self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

            # For synchronous operations (used in some diagnostic methods)
            self.redis_client = Redis.from_url(redis_url, decode_responses=False)
            # For async operations (used in main processing loop)
            self.async_redis_client = Redis.from_url(redis_url, decode_responses=False)

            # Define Redis streams
            self.task_stream = task_stream
            self.result_stream = result_stream
            self.is_test_mode = is_test_mode

            # If we're in test mode, prepend "test_" to stream names if not already prefixed
            if is_test_mode and not task_stream.startswith("test_"):
                self.task_stream = f"test_{task_stream}"
                logger.debug(
                    f"Test mode enabled, using task stream: {self.task_stream}"
                )
            if is_test_mode and not result_stream.startswith("test_"):
                self.result_stream = f"test_{result_stream}"
                logger.debug(
                    f"Test mode enabled, using result stream: {self.result_stream}"
                )
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

        # Agent type mapping to handle both naming formats (with/without _agent suffix)
        self.agent_type_mapping = {
            # Standard agent type format
            "spec": ["spec", "spec_agent"],
            "design": ["design", "design_agent"],
            "coding": ["coding", "coding_agent"],
            "review": ["review", "review_agent"],
            "test": ["test", "test_agent"],
            # Support for agent type with suffix
            "spec_agent": ["spec", "spec_agent"],
            "design_agent": ["design", "design_agent"],
            "coding_agent": ["coding", "coding_agent"],
            "review_agent": ["review", "review_agent"],
            "test_agent": ["test", "test_agent"],
        }

        # Agent-specific stream name mapping
        self.agent_stream_mapping = {
            # Map task type to potential agent stream names
            "spec": ["agent:spec:input", "agent:spec_agent:input"],
            "design": ["agent:design:input", "agent:design_agent:input"],
            "coding": ["agent:coding:input", "agent:coding_agent:input"],
            "review": ["agent:review:input", "agent:review_agent:input"],
            "test": ["agent:test:input", "agent:test_agent:input"],
            # Support for agent type with suffix
            "spec_agent": ["agent:spec:input", "agent:spec_agent:input"],
            "design_agent": ["agent:design:input", "agent:design_agent:input"],
            "coding_agent": ["agent:coding:input", "agent:coding_agent:input"],
            "review_agent": ["agent:review:input", "agent:review_agent:input"],
            "test_agent": ["agent:test:input", "agent:test_agent:input"],
        }

        # Initialize Pinecone if configured
        self.pinecone_client = None
        self.vector_index = None
        if PINECONE_AVAILABLE and pinecone_api_key and not skip_pinecone_init:
            try:
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
                logger.info("Pinecone vector store initialized")
            except Exception as e:
                logger.warning(f"Pinecone initialization failed: {e}")

        # Initialize agent registry
        self.agents = {}
        self.agent_registry = None

        logger.info("Orchestrator initialized successfully")

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

    async def diagnose_task_routing(self, task_type: str):
        """Run diagnostic tests on task routing configuration."""
        mode_emoji = "🧪" if self.is_test_mode else "🚀"
        logger.debug(f"{mode_emoji} ===== TASK ROUTING DIAGNOSTIC =====")
        logger.debug(f"Mode: {'TEST' if self.is_test_mode else 'PRODUCTION'}")
        logger.debug(f"Task Type: {task_type}")
        logger.debug(
            f"Redis URL: {self.redis_url if hasattr(self, 'redis_url') else 'Not set'}"
        )
        logger.debug(f"Task Stream: {self.task_stream}")
        logger.debug(f"Result Stream: {self.result_stream}")

        # Check agent type mapping for this task type
        if task_type in self.agent_type_mapping:
            logger.debug(
                f"Agent type mapping for '{task_type}': {self.agent_type_mapping[task_type]}"
            )
        else:
            logger.warning(f"No agent type mapping found for '{task_type}'")

        # Check stream mapping for this task type
        if task_type in self.agent_stream_mapping:
            logger.debug(
                f"Stream mapping for '{task_type}': {self.agent_stream_mapping[task_type]}"
            )
        else:
            logger.warning(f"No stream mapping found for '{task_type}'")

        # Check Redis connectivity
        try:
            ping_result = self.redis_client.ping()
            logger.debug(f"Redis ping result: {ping_result}")
            logger.debug("✅ Redis connection: OK")
        except Exception as e:
            logger.error(f"❌ Redis connection FAILED: {e}")

        # List registered agents
        logger.debug("Registered agents:")
        for agent_type, agent in self.agents.items():
            logger.debug(
                f"  - {agent_type}: {type(agent).__name__ if agent else 'None'}"
            )

        # Redis client details
        logger.debug(f"Redis client type: {type(self.redis_client).__name__}")
        logger.debug(
            f"Redis client connection pool: {self.redis_client.connection_pool}"
        )

        logger.debug(f"{mode_emoji} =====================================")

    async def enqueue_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """Enqueue a task to the Redis stream for processing.

        Args:
            task_type: Type of task
            task_data: Dictionary containing task data

        Returns:
            Task ID
        """
        # Create a unique task ID
        task_id = str(uuid.uuid4())

        # Call diagnostics before enqueueing
        await self.diagnose_task_routing(task_type)

        # Build task dictionary
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            **task_data,
        }

        # Convert task to JSON string
        task_json = json.dumps(task)

        # Add to main task queue
        try:
            # Add to the main task queue first
            msg_id = self.redis_client.xadd(self.task_stream, {"task": task_json})
            msg_id_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
            logger.info(
                f"✅ Successfully enqueued task {task_id} of type {task_type} with message ID {msg_id_str}"
            )

            # In test mode, we only use the main test_agent_tasks stream
            # In production mode, we also publish to agent-specific streams for compatibility
            if not self.is_test_mode:
                # Only publish to agent-specific streams in production mode
                for stream_name in self.agent_stream_mapping.get(task_type, []):
                    try:
                        agent_msg_id = self.redis_client.xadd(
                            stream_name, {"task": task_json}
                        )
                        agent_msg_id_str = (
                            agent_msg_id.decode()
                            if isinstance(agent_msg_id, bytes)
                            else str(agent_msg_id)
                        )
                        logger.info(
                            f"✅ Task {task_id} also published to agent stream {stream_name} with ID {agent_msg_id_str}"
                        )
                    except Exception as e:
                        logger.error(
                            f"❌ Failed to publish task {task_id} to agent stream {stream_name}: {e}"
                        )

            return task_id
        except Exception as e:
            logger.error(f"❌ Failed to enqueue task: {e}")
            # Add Redis info for debugging
            try:
                info = self.redis_client.info()
                logger.debug(f"Redis info: {info}")
            except Exception as info_error:
                logger.error(f"❌ Could not get Redis info: {info_error}")

            # Re-raise the exception
            raise

    async def submit_feature_request(self, description: str) -> str:
        """
        Submit a feature request to the system.

        Args:
            description: Description of the requested feature

        Returns:
            task_id: ID of the created task
        """
        logger.info(f"Submitting feature request: {description[:50]}...")

        # First, initialize agents if they haven't been initialized yet
        if not self.agents or "spec_agent" not in self.agents:
            self.initialize_agents()

        # Check if spec_agent is registered, if not, register a dummy one for testing
        if "spec_agent" not in self.agents:
            logger.warning("Spec agent not registered, using dummy agent for testing")
            self.register_agent("spec_agent", None)

        # Submit the feature request as a task to the spec agent
        task_id = await self.enqueue_task("spec_agent", {"input": description})
        logger.info(f"Feature request submitted as task: {task_id}")

        return task_id

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task by finding the appropriate agent and executing it.

        Args:
            task: The task to process with task_type and other parameters

        Returns:
            Dictionary with task results or error information
        """
        logger.debug(f"Processing task: {json.dumps(task, indent=2)}")

        task_id = task.get("task_id")
        task_type = task.get("task_type")
        agent = None

        # Use our mapping to find the right agent
        agent_types_to_try = [task_type]
        if task_type in self.agent_type_mapping:
            agent_types_to_try = self.agent_type_mapping[task_type]
            logger.debug(f"Will try these agent types: {agent_types_to_try}")

        # Try each possible agent type
        for agent_type in agent_types_to_try:
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                logger.info(f"Found registered agent for type {agent_type}")
                break

        try:
            # Check if any agent was found
            if not agent:
                logger.error(
                    f"No agent registered for task type: {task_type} or its alternatives"
                )
                error_result = {
                    "task_id": task_id,
                    "status": "error",
                    "error": f"No agent registered for task type: {task_type} or its alternatives",
                }
                logger.debug(f"Available agents: {list(self.agents.keys())}")

                # Store error in Redis
                self.redis_client.xadd(
                    self.result_stream, {"result": json.dumps(error_result)}
                )
                return error_result

            # Invoke the agent
            result = await agent.ainvoke(task)
            logger.debug(f"Agent {task_type} returned result: {result}")

            # Create and store the result
            full_result = {
                "task_id": task_id,
                "status": "completed",
            }

            # Merge in the agent result if it's a dict
            if isinstance(result, dict):
                full_result.update(result)
            else:
                full_result["result"] = result

            # Add the result to Redis
            logger.debug(
                f"Adding result to stream: {json.dumps(full_result, indent=2)}"
            )
            self.redis_client.xadd(
                self.result_stream, {"result": json.dumps(full_result)}
            )

            # Handle sub-tasks if this was a spec_agent task
            if task_type == "spec_agent" and isinstance(result, dict):
                # Check if there are tasks in the result
                if "output" in result and isinstance(result["output"], list):
                    sub_tasks = result["output"]
                    logger.info(f"Found {len(sub_tasks)} sub-tasks from spec_agent")

                    # Enqueue each sub-task
                    for i, sub_task in enumerate(sub_tasks):
                        # Extract task information
                        subtask_type = sub_task.get("task_type", "general")
                        task_description = sub_task.get("description", "")

                        # Create a new task with the extracted information
                        new_task_data = {
                            "description": task_description,
                            "priority": sub_task.get("priority", "medium"),
                            "parent_task": task_id,
                            "source": "subtask",
                        }

                        # Check if we have an agent for this subtask type
                        valid_agent_found = False
                        for st_type in self.agent_type_mapping.get(
                            subtask_type, [subtask_type]
                        ):
                            if st_type in self.agents:
                                valid_agent_found = True
                                break

                        if valid_agent_found:
                            # Add the subtask to the queue
                            sub_task_id = await self.enqueue_task(
                                subtask_type, new_task_data
                            )
                            logger.info(
                                f"Enqueued sub-task {i+1}/{len(sub_tasks)}: {sub_task_id} ({subtask_type})"
                            )
                        else:
                            logger.warning(
                                f"No agent registered for sub-task type: {subtask_type}"
                            )

            logger.info(f"Completed task {task_id}")
            return full_result

        except Exception as e:
            # Handle any errors
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            error_result = {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
            }
            # Store error in Redis
            self.redis_client.xadd(
                self.result_stream, {"result": json.dumps(error_result)}
            )

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
