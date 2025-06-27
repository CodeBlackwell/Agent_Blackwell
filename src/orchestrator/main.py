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
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

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

from src.api.v1.chatops.models import Job, JobStatus, Task, TaskStatus

# Local imports
from src.orchestrator.agent_registry import AgentRegistry
from .agent_health import AgentHealthMonitor, AgentStatus
from .agent_discovery import AgentDiscoveryService, AgentRegistration
from .agent_router import AgentRouter, RoutingRequest, TaskPriority, RoutingStrategy

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator_instance = None


def get_orchestrator() -> "Orchestrator":
    """
    Get the global orchestrator instance.
    
    Returns:
        Orchestrator instance
        
    Raises:
        RuntimeError: If orchestrator is not initialized
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        raise RuntimeError("Orchestrator not initialized. Call set_orchestrator() first.")
    return _orchestrator_instance


def set_orchestrator(orchestrator: "Orchestrator") -> None:
    """
    Set the global orchestrator instance.
    
    Args:
        orchestrator: Orchestrator instance to set
    """
    global _orchestrator_instance
    _orchestrator_instance = orchestrator


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
            self.async_redis_client = aioredis.from_url(
                redis_url, decode_responses=False
            )

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
                
            # Initialize agent coordination components
            self.health_monitor = AgentHealthMonitor(
                redis_url=redis_url,
                heartbeat_interval=30,
                health_check_interval=60,
                offline_threshold=120
            )
            
            self.discovery_service = AgentDiscoveryService(
                redis_url=redis_url,
                health_monitor=self.health_monitor,
                discovery_interval=30,
                cleanup_interval=300,
                agent_timeout=180
            )
            
            self.agent_router = AgentRouter(
                redis_url=redis_url,
                health_monitor=self.health_monitor,
                discovery_service=self.discovery_service,
                default_strategy=RoutingStrategy.HEALTH_AWARE
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

    async def start_coordination(self) -> None:
        """
        Start all agent coordination services.
        """
        try:
            # Initialize router
            await self.agent_router.initialize()
            
            # Start health monitoring
            await self.health_monitor.start_monitoring()
            
            # Start discovery service
            await self.discovery_service.start_discovery()
            
            # Register existing agents with coordination system
            await self._register_agents_with_coordination()
            
            logger.info("🚀 Agent coordination system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start coordination system: {e}")
            raise

    async def stop_coordination(self) -> None:
        """
        Stop all agent coordination services.
        """
        try:
            await self.discovery_service.stop_discovery()
            await self.health_monitor.stop_monitoring()
            
            logger.info("Agent coordination system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping coordination system: {e}")

    async def _register_agents_with_coordination(self) -> None:
        """
        Register existing agents with the coordination system.
        """
        if not self.agent_registry:
            return
            
        # Register each agent type with discovery service
        agent_types = ["spec", "design", "coding", "review", "test"]
        
        for agent_type in agent_types:
            try:
                agent_id = f"{agent_type}_agent_001"  # Standard agent ID format
                
                # Determine capabilities based on agent type
                capabilities = self._get_agent_capabilities(agent_type)
                
                await self.discovery_service.register_agent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    agent_class=f"{agent_type.capitalize()}Agent",
                    capabilities=capabilities,
                    version="1.0.0",
                    max_concurrent_tasks=5,
                    priority=100,
                    tags=[agent_type, "local", "orchestrator"],
                    metadata={
                        "initialized_at": datetime.utcnow().isoformat(),
                        "orchestrator_managed": True
                    }
                )
                
                logger.info(f"Registered {agent_type} agent with coordination system")
                
            except Exception as e:
                logger.error(f"Failed to register {agent_type} agent: {e}")

    def _get_agent_capabilities(self, agent_type: str) -> List[str]:
        """
        Get capabilities for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of capabilities
        """
        capability_map = {
            "spec": [
                "requirements_analysis",
                "specification_writing",
                "user_story_creation",
                "acceptance_criteria",
                "technical_planning"
            ],
            "design": [
                "system_design",
                "architecture_planning",
                "ui_design",
                "database_design",
                "api_design",
                "scalability_planning"
            ],
            "coding": [
                "code_generation",
                "implementation",
                "refactoring",
                "debugging",
                "optimization",
                "testing_integration"
            ],
            "review": [
                "code_review",
                "quality_assessment",
                "security_analysis",
                "performance_review",
                "best_practices",
                "documentation_review"
            ],
            "test": [
                "test_planning",
                "unit_testing",
                "integration_testing",
                "test_automation",
                "quality_assurance",
                "test_reporting"
            ]
        }
        
        return capability_map.get(agent_type, [agent_type])

    def register_agent(self, agent_name: str, agent_executor) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent_name: Name to register the agent under
            agent_executor: Agent instance with an ainvoke method
        """
        self.agents[agent_name] = agent_executor
        logger.info(f"Registered agent: {agent_name}")

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

    async def enqueue_task(self, task: Task) -> None:
        """
        Enqueue a task for processing using intelligent agent routing.

        Args:
            task: Task to enqueue
        """
        mode_emoji = "🧪" if self.is_test_mode else "🚀"
        logger.info(f"{mode_emoji} Enqueueing task {task.task_id} (type: {task.task_type})")

        try:
            # Create routing request
            routing_request = RoutingRequest(
                task_id=task.task_id,
                task_type=task.task_type,
                priority=self._map_task_priority(task.priority),
                required_capabilities=self._get_required_capabilities(task),
                preferred_tags=self._get_preferred_tags(task),
                max_retries=3,
                timeout_seconds=300,
                metadata={
                    "job_id": task.job_id,
                    "dependencies": task.dependencies,
                    "created_at": task.created_at.isoformat()
                }
            )

            # Route task to best available agent
            routing_result = await self.agent_router.route_with_retry(routing_request)

            if routing_result.success and routing_result.agent_id:
                # Record task start with health monitor
                await self.health_monitor.record_task_start(
                    routing_result.agent_id, 
                    task.task_id
                )

                # Determine target stream based on mode and routing result
                if self.is_test_mode:
                    # In test mode, use generic test stream
                    target_stream = self.task_stream
                else:
                    # In production, use agent-specific stream
                    agent_streams = self.agent_stream_mapping.get(task.task_type, [])
                    target_stream = agent_streams[0] if agent_streams else self.task_stream

                # Prepare task message
                task_message = {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "job_id": task.job_id,
                    "priority": task.priority,
                    "input_data": task.input_data,
                    "dependencies": task.dependencies,
                    "assigned_agent": routing_result.agent_id,
                    "routing_strategy": routing_result.routing_strategy.value if routing_result.routing_strategy else None,
                    "routing_time_ms": routing_result.routing_time_ms,
                    "created_at": task.created_at.isoformat(),
                    "enqueued_at": datetime.utcnow().isoformat(),
                }

                # Add task to Redis stream
                await self.async_redis_client.xadd(target_stream, task_message)

                # Update task status
                task.status = TaskStatus.QUEUED
                task.assigned_agent = routing_result.agent_id
                task.updated_at = datetime.utcnow()
                await self._save_task_to_redis(task)

                logger.info(
                    f"{mode_emoji} Task {task.task_id} routed to agent {routing_result.agent_id} "
                    f"via {routing_result.routing_strategy.value if routing_result.routing_strategy else 'unknown'} "
                    f"strategy (routing time: {routing_result.routing_time_ms:.1f}ms)"
                )

                # Publish task enqueued event
                await self._publish_task_status_update(task, {
                    "assigned_agent": routing_result.agent_id,
                    "routing_strategy": routing_result.routing_strategy.value if routing_result.routing_strategy else None,
                    "target_stream": target_stream
                })

            else:
                # Routing failed - mark task as failed
                task.status = TaskStatus.FAILED
                task.error_message = routing_result.error_message or "Failed to route task to agent"
                task.updated_at = datetime.utcnow()
                await self._save_task_to_redis(task)

                logger.error(
                    f"{mode_emoji} Failed to route task {task.task_id}: {task.error_message}"
                )

                # Publish task failure event
                await self._publish_task_status_update(task, {
                    "routing_error": task.error_message,
                    "retry_count": routing_result.retry_count
                })

                # Check if this affects job completion
                await self._check_job_completion(task.job_id)

        except Exception as e:
            logger.error(f"{mode_emoji} Error enqueueing task {task.task_id}: {e}")
            
            # Mark task as failed
            task.status = TaskStatus.FAILED
            task.error_message = f"Enqueue error: {str(e)}"
            task.updated_at = datetime.utcnow()
            await self._save_task_to_redis(task)

            # Publish error event
            await self._publish_task_status_update(task, {
                "enqueue_error": str(e)
            })

    def _map_task_priority(self, priority: int) -> TaskPriority:
        """
        Map task priority integer to TaskPriority enum.
        
        Args:
            priority: Integer priority (1-4)
            
        Returns:
            TaskPriority enum value
        """
        priority_map = {
            1: TaskPriority.LOW,
            2: TaskPriority.NORMAL,
            3: TaskPriority.HIGH,
            4: TaskPriority.CRITICAL
        }
        return priority_map.get(priority, TaskPriority.NORMAL)

    def _get_required_capabilities(self, task: Task) -> List[str]:
        """
        Get required capabilities for a task based on its type and input data.
        
        Args:
            task: Task to analyze
            
        Returns:
            List of required capabilities
        """
        base_capabilities = self._get_agent_capabilities(task.task_type)
        
        # Add specific capabilities based on task input
        additional_capabilities = []
        
        if task.input_data:
            # Check for specific requirements in task data
            if "security_requirements" in str(task.input_data):
                additional_capabilities.append("security_analysis")
            if "performance_requirements" in str(task.input_data):
                additional_capabilities.append("performance_optimization")
            if "scalability" in str(task.input_data):
                additional_capabilities.append("scalability_planning")
        
        return base_capabilities + additional_capabilities

    def _get_preferred_tags(self, task: Task) -> List[str]:
        """
        Get preferred tags for agent selection based on task characteristics.
        
        Args:
            task: Task to analyze
            
        Returns:
            List of preferred tags
        """
        tags = ["local", "orchestrator"]  # Default tags
        
        # Add priority-based tags
        if task.priority >= 3:
            tags.append("high_priority")
        
        # Add task-type specific tags
        tags.append(task.task_type)
        
        return tags

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task by finding the appropriate agent and executing it.

        Args:
            task: The task to process with task_type and other parameters

        Returns:
            Dictionary with task results or error information
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        task_type = task.get("task_type", "unknown")
        job_id = task.get("job_id")

        logger.info(f"🚀 Processing task {task_id} of type {task_type}")

        try:
            # Handle special planning task type
            if task_type == "planning":
                return await self._handle_planning_task(task)

            # Handle job-oriented tasks
            if job_id:
                return await self._handle_job_task(task)

            # Handle legacy tasks (backward compatibility)
            return await self._handle_legacy_task(task)

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")

            # If this is a job task, update task status to FAILED
            if job_id:
                await self._handle_task_failure(task_id, str(e))

            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _handle_planning_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle planning tasks from spec_agent."""
        job_id = task.get("job_id")
        user_request = task.get("user_request")

        logger.info(f"🧠 Processing planning task for job {job_id}")

        try:
            # Get spec_agent to create task plan
            if "spec_agent" in self.agents and self.agents["spec_agent"]:
                agent = self.agents["spec_agent"]

                # Prepare input for spec_agent
                agent_input = {
                    "input": f"Create a detailed task plan for: {user_request}",
                    "job_id": job_id,
                    "task_type": "planning",
                }

                # Execute spec_agent
                result = await agent.ainvoke(agent_input)

                # Extract task definitions from result
                # This assumes spec_agent returns structured task definitions
                task_definitions = self._extract_task_definitions(result)

                # Process the job plan
                await self.process_job_plan(job_id, task_definitions)

                return {
                    "task_id": task.get("task_id", str(uuid.uuid4())),
                    "status": "completed",
                    "result": {"task_count": len(task_definitions)},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                raise Exception("spec_agent not available for planning")

        except Exception as e:
            logger.error(f"Error in planning task for job {job_id}: {e}")

            # Update job status to FAILED
            job = await self.get_job(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.updated_at = datetime.utcnow()
                await self._save_job_to_redis(job)

            raise

    async def _handle_job_task(self, task_data: Dict[str, Any]) -> None:
        """Handle a job-oriented task with dependency management."""
        job_id = task_data.get("job_id")
        task_id = task_data.get("task_id")

        if not job_id or not task_id:
            logger.error("Job task missing job_id or task_id")
            return

        try:
            # Get job and task from Redis
            job = await self.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Find the specific task
            task = None
            for t in job.tasks:
                if t.task_id == task_id:
                    task = t
                    break

            if not task:
                logger.error(f"Task {task_id} not found in job {job_id}")
                return

            # Update task status to running
            previous_task_status = task.status
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.utcnow()

            # Save updated job
            await self._save_job_to_redis(job)

            # Publish task status change
            await self._publish_task_status_change(job_id, task, previous_task_status)

            logger.info(f"Processing job task {task_id} for job {job_id}")

            # Process the task (simulate work)
            await asyncio.sleep(0.1)  # Simulate processing time

            # For now, simulate successful completion
            # In a real implementation, this would call the appropriate agent
            result = {
                "status": "completed",
                "message": f"Task {task_id} completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Update task with result
            previous_task_status = task.status
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.updated_at = datetime.utcnow()

            # Check if job is complete
            previous_job_status = job.status
            if all(t.status == TaskStatus.COMPLETED for t in job.tasks):
                job.status = JobStatus.COMPLETED
                job.updated_at = datetime.utcnow()
                logger.info(f"Job {job_id} completed successfully")

            # Save updated job
            await self._save_job_to_redis(job)

            # Publish task completion and status change
            await self._publish_task_result(job_id, task_id, result)
            await self._publish_task_status_change(job_id, task, previous_task_status)

            # Publish job status change if it changed
            if job.status != previous_job_status:
                await self._publish_job_status_change(job, previous_job_status)

        except Exception as e:
            logger.error(f"Error processing job task {task_id} for job {job_id}: {e}")

            # Update task status to failed
            try:
                job = await self.get_job(job_id)
                if job:
                    for t in job.tasks:
                        if t.task_id == task_id:
                            previous_status = t.status
                            t.status = TaskStatus.FAILED
                            t.error = str(e)
                            t.updated_at = datetime.utcnow()

                            # Save updated job
                            await self._save_job_to_redis(job)

                            # Publish task failure
                            await self._publish_task_status_change(
                                job_id, t, previous_status
                            )
                            break
            except Exception as save_error:
                logger.error(f"Error saving failed task status: {save_error}")

    async def _handle_legacy_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle legacy tasks for backward compatibility."""
        task_id = task.get("task_id", str(uuid.uuid4()))
        task_type = task.get("task_type", "unknown")

        logger.info(f"🔄 Processing legacy task {task_id} of type {task_type}")

        # Use existing legacy logic
        start_time = datetime.utcnow()

        # Find appropriate agent
        agent = None
        agent_name = None

        # Try exact match first
        if task_type in self.agents:
            agent = self.agents[task_type]
            agent_name = task_type
        else:
            # Try mapping variations
            for mapped_types in self.agent_type_mapping.get(task_type, []):
                if mapped_types in self.agents:
                    agent = self.agents[mapped_types]
                    agent_name = mapped_types
                    break

        if not agent:
            raise Exception(f"No agent found for task type: {task_type}")

        # Execute agent
        if agent_name in ["dummy", "echo"]:
            # Handle test agents
            result = {"message": f"Processed {task_type} task", "input": task}
        else:
            # Execute real agent
            result = await agent.ainvoke(task)

        # Store result in Redis stream
        result_data = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "completed",
            "result": json.dumps(result),
            "processing_time": (datetime.utcnow() - start_time).total_seconds(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.async_redis_client.xadd(self.result_stream, result_data)

        return result_data

    async def _execute_task_with_agent(
        self, task_obj: Task, task_data: Dict[str, Any]
    ) -> Any:
        """Execute a task using the appropriate agent."""
        agent_type = task_obj.agent_type

        # Find appropriate agent
        agent = None
        if agent_type in self.agents:
            agent = self.agents[agent_type]
        else:
            # Try mapping variations
            for mapped_type in self.agent_type_mapping.get(agent_type, []):
                if mapped_type in self.agents:
                    agent = self.agents[mapped_type]
                    break

        if not agent:
            raise Exception(f"No agent found for type: {agent_type}")

        # Prepare agent input
        agent_input = {
            "input": task_obj.description,
            "task_id": task_obj.task_id,
            "job_id": task_obj.job_id,
            "task_type": agent_type,
        }

        # Add any additional task data
        agent_input.update(task_data)

        # Execute agent
        if agent_type in ["dummy", "echo"]:
            # Handle test agents
            return {"message": f"Processed {agent_type} task", "input": agent_input}
        else:
            # Execute real agent
            return await agent.ainvoke(agent_input)

    async def _handle_task_failure(self, task_id: str, error_message: str) -> None:
        """Handle task failure by updating status and checking job impact."""
        try:
            task_obj = await self.get_task(task_id)
            if task_obj:
                task_obj.status = TaskStatus.FAILED
                task_obj.result = {"error": error_message}
                task_obj.updated_at = datetime.utcnow()
                await self._save_task_to_redis(task_obj)

                # Check if job should be marked as failed
                await self._check_job_failure(task_obj.job_id)

        except Exception as e:
            logger.error(f"Error handling task failure for {task_id}: {e}")

    async def _check_and_enqueue_dependent_tasks(self, completed_task_id: str) -> None:
        """Check for tasks that depend on the completed task and enqueue them if ready."""
        try:
            # Get tasks that depend on this completed task
            dependent_task_ids = await self.async_redis_client.smembers(
                f"task:{completed_task_id}:dependents"
            )

            for dep_task_id in dependent_task_ids:
                if isinstance(dep_task_id, bytes):
                    dep_task_id = dep_task_id.decode()

                # Get the dependent task
                dep_task = await self.get_task(dep_task_id)
                if not dep_task or dep_task.status != TaskStatus.PENDING:
                    continue

                # Check if all dependencies are completed
                all_deps_completed = True
                for dependency_id in dep_task.dependencies:
                    dep_obj = await self.get_task(dependency_id)
                    if not dep_obj or dep_obj.status != TaskStatus.COMPLETED:
                        all_deps_completed = False
                        break

                # If all dependencies are completed, enqueue the task
                if all_deps_completed:
                    await self._enqueue_task_for_execution(dep_task)
                    logger.info(
                        f"Enqueued dependent task {dep_task_id} after {completed_task_id} completed"
                    )

        except Exception as e:
            logger.error(f"Error checking dependent tasks for {completed_task_id}: {e}")

    async def _check_job_completion(self, job_id: str) -> None:
        """Check if a job is complete and update its status."""
        try:
            job = await self.get_job(job_id)
            if not job:
                return

            # Count task statuses
            completed_tasks = len(
                [t for t in job.tasks if t.status == TaskStatus.COMPLETED]
            )
            failed_tasks = len([t for t in job.tasks if t.status == TaskStatus.FAILED])
            total_tasks = len(job.tasks)

            # Update job status based on task completion
            if completed_tasks == total_tasks:
                job.status = JobStatus.COMPLETED
                job.updated_at = datetime.utcnow()
                await self._save_job_to_redis(job)
                logger.info(f"Job {job_id} completed successfully")
            elif failed_tasks > 0:
                # If any task failed, mark job as failed
                job.status = JobStatus.FAILED
                job.updated_at = datetime.utcnow()
                await self._save_job_to_redis(job)
                logger.info(f"Job {job_id} failed due to task failures")

        except Exception as e:
            logger.error(f"Error checking job completion for {job_id}: {e}")

    async def _check_job_failure(self, job_id: str) -> None:
        """Check if a job should be marked as failed due to critical task failures."""
        try:
            job = await self.get_job(job_id)
            if not job or job.status == JobStatus.FAILED:
                return

            # Check for failed tasks
            failed_tasks = [t for t in job.tasks if t.status == TaskStatus.FAILED]

            if failed_tasks:
                # For now, any task failure causes job failure
                # In the future, we could implement more sophisticated failure handling
                job.status = JobStatus.FAILED
                job.updated_at = datetime.utcnow()
                await self._save_job_to_redis(job)
                logger.info(f"Job {job_id} marked as failed due to task failures")

        except Exception as e:
            logger.error(f"Error checking job failure for {job_id}: {e}")

    async def _publish_task_result(
        self, job_id: str, task_id: str, result: Any
    ) -> None:
        """Publish task result to job-specific stream for real-time updates."""
        try:
            event_data = {
                "event_type": "task_completed",
                "job_id": job_id,
                "task_id": task_id,
                "result": json.dumps(result),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Publish to job-specific stream
            await self.async_redis_client.xadd(f"job-stream:{job_id}", event_data)

        except Exception as e:
            logger.error(
                f"Error publishing task result for job {job_id}, task {task_id}: {e}"
            )

    async def _publish_job_status_change(
        self, job: Job, previous_status: JobStatus = None
    ) -> None:
        """Publish job status change to job-specific stream for real-time updates."""
        try:
            # Calculate progress metrics
            total_tasks = len(job.tasks)
            completed_tasks = len(
                [t for t in job.tasks if t.status == TaskStatus.COMPLETED]
            )
            failed_tasks = len([t for t in job.tasks if t.status == TaskStatus.FAILED])
            running_tasks = len(
                [t for t in job.tasks if t.status == TaskStatus.RUNNING]
            )
            pending_tasks = len(
                [t for t in job.tasks if t.status == TaskStatus.PENDING]
            )

            progress_percentage = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            event_data = {
                "event_type": "job_status_changed",
                "job_id": job.job_id,
                "status": job.status.value,
                "previous_status": previous_status.value if previous_status else None,
                "progress": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "running_tasks": running_tasks,
                    "pending_tasks": pending_tasks,
                    "percentage": round(progress_percentage, 2),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Publish to job-specific stream
            await self.async_redis_client.xadd(f"job-stream:{job.job_id}", event_data)

        except Exception as e:
            logger.error(
                f"Error publishing job status change for job {job.job_id}: {e}"
            )

    async def _publish_task_status_change(
        self, job_id: str, task: Task, previous_status: TaskStatus = None
    ) -> None:
        """Publish task status change to job-specific stream for real-time updates."""
        try:
            event_data = {
                "event_type": "task_status_changed",
                "job_id": job_id,
                "task_id": task.task_id,
                "status": task.status.value,
                "previous_status": previous_status.value if previous_status else None,
                "agent_type": task.agent_type,
                "description": task.description,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add error information if task failed
            if task.status == TaskStatus.FAILED and hasattr(task, "error"):
                event_data["error"] = str(task.error)

            # Publish to job-specific stream
            await self.async_redis_client.xadd(f"job-stream:{job_id}", event_data)

        except Exception as e:
            logger.error(
                f"Error publishing task status change for job {job_id}, task {task.task_id}: {e}"
            )

    async def _publish_task_status_update(
        self, task: Task, additional_data: Dict[str, Any] = None
    ) -> None:
        """Publish task status update to job-specific stream for real-time updates."""
        try:
            event_data = {
                "event_type": "task_status_update",
                "job_id": task.job_id,
                "task_id": task.task_id,
                "status": task.status.value,
                "agent_type": task.agent_type,
                "description": task.description,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add any additional data
            if additional_data:
                event_data.update(additional_data)

            # Publish to job-specific stream
            await self.async_redis_client.xadd(f"job-stream:{task.job_id}", event_data)

        except Exception as e:
            logger.error(
                f"Error publishing task status update for job {task.job_id}, task {task.task_id}: {e}"
            )

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

        # Start the coordination system
        await self.start_coordination()

        # Start the processing loop
        await self.run_loop()

    # --- Job Lifecycle Management Methods ---

    async def create_job(
        self, user_request: str, priority: str = "medium", tags: List[str] = None
    ) -> Job:
        """Create a new job with tasks based on user request."""
        job_id = str(uuid.uuid4())

        # Create initial job
        job = Job(
            job_id=job_id,
            user_request=user_request,
            status=JobStatus.PENDING,
            tasks=[],
            priority=priority,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save job to Redis
        await self._save_job_to_redis(job)

        # Publish job creation event
        await self._publish_job_status_change(job)

        logger.info(f"Created job {job_id} with request: {user_request}")

        # Generate job plan (tasks) asynchronously
        try:
            await self._generate_job_plan(job)
        except Exception as e:
            logger.error(f"Error generating job plan for {job_id}: {e}")
            job.status = JobStatus.FAILED
            await self._save_job_to_redis(job)
            await self._publish_job_status_change(job, JobStatus.PENDING)
            raise

        return job

    async def process_job_plan(self, job_id: str, task_definitions: List[Dict]) -> None:
        """
        Process the output from spec_agent and create tasks for the job.

        Args:
            job_id: The job ID to create tasks for
            task_definitions: List of task definitions from spec_agent
        """
        try:
            # Get the job
            job = await self.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found for plan processing")
                return

            # Create Task objects from definitions
            tasks = []
            for task_def in task_definitions:
                task_id = str(uuid.uuid4())
                task = Task(
                    task_id=task_id,
                    job_id=job_id,
                    agent_type=task_def.get("agent_type", "spec"),
                    status=TaskStatus.PENDING,
                    description=task_def.get("description", ""),
                    dependencies=task_def.get("dependencies", []),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                tasks.append(task)

            # Save tasks to Redis
            for task in tasks:
                await self._save_task_to_redis(task)

            # Update job with tasks and change status to RUNNING
            job.tasks = tasks
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.utcnow()

            await self._save_job_to_redis(job)

            # Enqueue initial tasks (those with no dependencies)
            initial_tasks = [task for task in tasks if not task.dependencies]
            for task in initial_tasks:
                await self._enqueue_task_for_execution(task)

            logger.info(
                f"Processed plan for job {job_id}: created {len(tasks)} tasks, enqueued {len(initial_tasks)} initial tasks"
            )

        except Exception as e:
            logger.error(f"Error processing job plan for {job_id}: {e}")
            # Update job status to FAILED
            job = await self.get_job(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.updated_at = datetime.utcnow()
                await self._save_job_to_redis(job)

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job from Redis.

        Args:
            job_id: The job ID to retrieve

        Returns:
            Job object or None if not found
        """
        try:
            # Get job data from Redis hash
            job_data = await self.async_redis_client.hgetall(f"job:{job_id}")
            if not job_data:
                return None

            # Decode bytes to strings
            job_data = {
                k.decode()
                if isinstance(k, bytes)
                else k: v.decode()
                if isinstance(v, bytes)
                else v
                for k, v in job_data.items()
            }

            # Get associated tasks
            task_ids = await self.async_redis_client.smembers(
                f"job:{job_id}:tasks"
            )

            tasks = []
            for task_id in task_ids:
                if isinstance(task_id, bytes):
                    task_id = task_id.decode()
                task = await self.get_task(task_id)
                if task:
                    tasks.append(task)

            # Create Job object
            job = Job(
                job_id=job_data["job_id"],
                user_request=job_data["user_request"],
                status=JobStatus(job_data["status"]),
                tasks=tasks,
                created_at=datetime.fromisoformat(job_data["created_at"]),
                updated_at=datetime.fromisoformat(job_data["updated_at"]),
            )

            return job

        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {e}")
            return None

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task from Redis.

        Args:
            task_id: The task ID to retrieve

        Returns:
            Task object or None if not found
        """
        try:
            # Get task data from Redis hash
            task_data = await self.async_redis_client.hgetall(f"task:{task_id}")
            if not task_data:
                return None

            # Decode bytes to strings
            task_data = {
                k.decode()
                if isinstance(k, bytes)
                else k: v.decode()
                if isinstance(v, bytes)
                else v
                for k, v in task_data.items()
            }

            # Parse dependencies and result
            dependencies = json.loads(task_data.get("dependencies", "[]"))
            result = None
            if task_data.get("result"):
                result = json.loads(task_data["result"])

            # Create Task object
            task = Task(
                task_id=task_data["task_id"],
                job_id=task_data["job_id"],
                agent_type=task_data["agent_type"],
                status=TaskStatus(task_data["status"]),
                description=task_data["description"],
                dependencies=dependencies,
                result=result,
                created_at=datetime.fromisoformat(task_data["created_at"]),
                updated_at=datetime.fromisoformat(task_data["updated_at"]),
            )

            return task

        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            return None

    async def _save_job_to_redis(self, job: Job) -> None:
        """Save a job to Redis with proper indexing."""
        try:
            # Prepare job data for Redis hash
            job_data = {
                "job_id": job.job_id,
                "user_request": job.user_request,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "task_count": len(job.tasks),
                "completed_tasks": len(
                    [t for t in job.tasks if t.status == TaskStatus.COMPLETED]
                ),
            }

            # Save to Redis hash
            await self.async_redis_client.hset(f"job:{job.job_id}", mapping=job_data)

            # Update status index
            await self.async_redis_client.sadd(
                f"jobs:status:{job.status.value}", job.job_id
            )

            # Remove from other status indexes if status changed
            for status in JobStatus:
                if status != job.status:
                    await self.async_redis_client.srem(
                        f"jobs:status:{status.value}", job.job_id
                    )

        except Exception as e:
            logger.error(f"Error saving job {job.job_id} to Redis: {e}")
            raise

    async def _save_task_to_redis(self, task: Task) -> None:
        """Save a task to Redis with proper indexing."""
        try:
            # Prepare task data for Redis hash
            task_data = {
                "task_id": task.task_id,
                "job_id": task.job_id,
                "agent_type": task.agent_type,
                "status": task.status.value,
                "description": task.description,
                "dependencies": json.dumps(task.dependencies),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

            if task.result is not None:
                task_data["result"] = json.dumps(task.result)

            # Save to Redis hash
            await self.async_redis_client.hset(
                f"task:{task.task_id}", mapping=task_data
            )

            # Update job-task relationship
            await self.async_redis_client.sadd(f"job:{task.job_id}:tasks", task.task_id)

            # Update status index
            await self.async_redis_client.sadd(
                f"tasks:status:{task.status.value}", task.task_id
            )

            # Update agent type index
            await self.async_redis_client.sadd(
                f"tasks:agent:{task.agent_type}", task.task_id
            )

            # Remove from other status indexes if status changed
            for status in TaskStatus:
                if status != task.status:
                    await self.async_redis_client.srem(
                        f"tasks:status:{status.value}", task.task_id
                    )

            # Handle dependencies
            for dep_task_id in task.dependencies:
                await self.async_redis_client.sadd(
                    f"task:{task.task_id}:dependencies", dep_task_id
                )
                await self.async_redis_client.sadd(
                    f"task:{dep_task_id}:dependents", task.task_id
                )

        except Exception as e:
            logger.error(f"Error saving task {task.task_id} to Redis: {e}")
            raise

    async def _enqueue_task_for_execution(self, task: Task) -> None:
        """Enqueue a task for execution by the appropriate agent."""
        try:
            # Update task status to QUEUED
            task.status = TaskStatus.QUEUED
            task.updated_at = datetime.utcnow()
            await self._save_task_to_redis(task)

            # Prepare task data for agent execution
            task_data = {
                "task_id": task.task_id,
                "job_id": task.job_id,
                "task_type": task.agent_type,
                "description": task.description,
                "dependencies": task.dependencies,
            }

            # Enqueue to appropriate agent stream
            await self.enqueue_task(task.agent_type, task_data)

            logger.info(f"Enqueued task {task.task_id} for agent {task.agent_type}")

        except Exception as e:
            logger.error(f"Error enqueuing task {task.task_id}: {e}")
            # Update task status to FAILED
            task.status = TaskStatus.FAILED
            task.updated_at = datetime.utcnow()
            await self._save_task_to_redis(task)


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
