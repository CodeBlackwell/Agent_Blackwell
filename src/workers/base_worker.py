"""
Base Agent Worker for Redis Stream Consumption.

This module provides the base worker class that consumes tasks from Redis streams
and processes them using the appropriate agent implementation.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import redis.asyncio as aioredis
from redis import Redis
from src.utils.stream_naming import (
    normalize_agent_type,
    get_input_streams,
    get_result_stream_name,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BaseAgentWorker(ABC):
    """
    Base class for agent workers that consume tasks from Redis streams.
    
    This class handles:
    - Redis stream consumption
    - Task processing dispatch
    - Result publishing
    - Error handling and retries
    """

    def __init__(
        self,
        agent_type: str,
        redis_url: str = "redis://localhost:6379",
        input_streams: List[str] = None,
        result_stream: str = "agent_results",
        consumer_group: str = "agent_workers",
        consumer_name: str = None,
        max_retries: int = 3,
        block_ms: int = 5000,  # 5 seconds
        batch_size: int = 10,
    ):
        """
        Initialize the worker with Redis connection and stream configuration.
        
        Args:
            agent_type: Type of agent this worker processes (spec, design, code, etc.)
            redis_url: URL for Redis connection
            input_streams: List of input stream names to consume from
            result_stream: Stream to publish results to
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name (defaults to {agent_type}_worker_{uuid})
            max_retries: Maximum number of retries for failed tasks
            block_ms: Milliseconds to block waiting for new messages
            batch_size: Number of messages to process in each batch
        """
        self.agent_type = agent_type
        self.redis_url = redis_url
        
        # Initial test-mode detection based on provided streams (if any)
        self.is_test_mode = any(s.startswith("test_") for s in (input_streams or []))

        # Environment indicator emoji for logging
        self.mode_emoji = "🧪" if self.is_test_mode else "🚀"
        logger.info(
            f"{self.mode_emoji} Initializing {agent_type} worker in "
            f"{'TEST' if self.is_test_mode else 'PRODUCTION'} mode"
        )

        # ---------------------------------------------------------------------
        # Stream configuration via shared naming utility
        # ---------------------------------------------------------------------
        canonical_agent_type = normalize_agent_type(agent_type)

        if input_streams is None:
            # Derive standard input streams for this agent type
            self.input_streams = get_input_streams(canonical_agent_type, self.is_test_mode)
        else:
            self.input_streams = input_streams
            # Re-evaluate test mode based on explicit streams
            self.is_test_mode = any(s.startswith("test_") for s in self.input_streams)
            self.mode_emoji = "🧪" if self.is_test_mode else "🚀"

        logger.info(f"{self.mode_emoji} Using input streams: {self.input_streams}")

        # Result stream
        self.result_stream = get_result_stream_name(result_stream, self.is_test_mode)
        logger.info(f"{self.mode_emoji} Using result stream: {self.result_stream}")
            
        self.consumer_group = consumer_group
        
        # Generate a unique consumer name if none provided
        if consumer_name is None:
            import uuid
            self.consumer_name = f"{agent_type}_worker_{uuid.uuid4().hex[:8]}"
        else:
            self.consumer_name = consumer_name
            
        self.max_retries = max_retries
        self.block_ms = block_ms
        self.batch_size = batch_size
        
        # Flags for worker control
        self.running = False
        self.should_stop = False
        
        # Redis clients
        self.redis_client = None  # Synchronous client for setup
        self.async_redis_client = None  # Async client for processing
        
        # Set of processed message IDs to avoid duplicates
        self.processed_ids: Set[str] = set()
        
        logger.info(f"Initialized {self.agent_type} worker: {self.consumer_name}")

    async def initialize(self) -> None:
        """Initialize Redis connections and create consumer groups if needed."""
        try:
            # Initialize Redis clients
            self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            
            # Create consumer groups for each input stream if they don't exist
            for stream in self.input_streams:
                try:
                    # Check if stream exists, create it if not
                    if not self.redis_client.exists(stream):
                        logger.info(f"Creating stream: {stream}")
                        self.redis_client.xadd(stream, {"init": "true"})
                    
                    # Create consumer group if it doesn't exist
                    try:
                        self.redis_client.xgroup_create(stream, self.consumer_group, id="0", mkstream=True)
                        logger.info(f"Created consumer group {self.consumer_group} for stream {stream}")
                    except redis.exceptions.ResponseError as e:
                        if "BUSYGROUP" in str(e):
                            logger.info(f"Consumer group {self.consumer_group} already exists for stream {stream}")
                        else:
                            raise
                            
                except Exception as e:
                    logger.error(f"Error setting up stream {stream}: {e}")
                    raise
                    
            logger.info(f"{self.agent_type} worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing {self.agent_type} worker: {e}")
            raise

    async def start(self) -> None:
        """Start the worker processing loop."""
        if self.running:
            logger.warning(f"{self.agent_type} worker already running")
            return
            
        self.running = True
        self.should_stop = False
        
        # Initialize Redis connections
        await self.initialize()
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()
        
        logger.info(f"Starting {self.agent_type} worker: {self.consumer_name}")
        
        try:
            # Main processing loop
            while not self.should_stop:
                try:
                    # Process pending messages (unacknowledged from previous runs)
                    await self._process_pending_messages()
                    
                    # Process new messages
                    await self._process_new_messages()
                    
                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.1)
                    
                except asyncio.CancelledError:
                    logger.info(f"{self.agent_type} worker processing loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in {self.agent_type} worker processing loop: {e}")
                    logger.error(traceback.format_exc())
                    # Continue the loop after a short delay
                    await asyncio.sleep(1)
                    
        finally:
            self.running = False
            # Clean up resources
            await self._cleanup()
            logger.info(f"{self.agent_type} worker stopped")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info(f"Stopping {self.agent_type} worker: {self.consumer_name}")
        self.should_stop = True
        
        # Wait for the worker to stop (with timeout)
        for _ in range(10):  # Wait up to 10 seconds
            if not self.running:
                break
            await asyncio.sleep(1)
            
        if self.running:
            logger.warning(f"{self.agent_type} worker did not stop gracefully")

    async def _process_pending_messages(self) -> None:
        """Process pending messages (unacknowledged from previous runs)."""
        for stream in self.input_streams:
            try:
                # Get pending messages for this consumer
                pending = await self.async_redis_client.xpending(
                    stream, self.consumer_group, "-", "+", self.batch_size, self.consumer_name
                )
                
                if not pending:
                    continue
                    
                # Claim and process each pending message
                message_ids = [entry[0] for entry in pending]
                if message_ids:
                    claimed = await self.async_redis_client.xclaim(
                        stream,
                        self.consumer_group,
                        self.consumer_name,
                        min_idle_time=0,
                        message_ids=message_ids,
                    )
                    
                    for message_id, message in claimed:
                        await self._process_message(stream, message_id, message)
                        
            except Exception as e:
                logger.error(f"Error processing pending messages from {stream}: {e}")

    async def _process_new_messages(self) -> None:
        """Process new messages from the input streams."""
        try:
            # Prepare streams dict for xreadgroup
            streams = {stream: ">" for stream in self.input_streams}

            logger.debug(
                f"{self.mode_emoji} XREADGROUP blocking for {self.block_ms} ms on "
                f"streams {list(streams.keys())} (batch_size={self.batch_size})"
            )
            # Read new messages
            messages = await self.async_redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                streams,
                count=self.batch_size,
                block=self.block_ms,
            )
            logger.debug(
                f"{self.mode_emoji} XREADGROUP returned {len(messages) if messages else 0} "
                f"stream(s) with {sum(len(m[1]) for m in messages) if messages else 0} message(s)"
            )

            if not messages:
                return
                
            # Process messages from each stream
            for stream_name, stream_messages in messages:
                for message_id, message in stream_messages:
                    await self._process_message(stream_name, message_id, message)
                    
        except asyncio.TimeoutError:
            # This is normal when no messages are available
            pass
        except Exception as e:
            logger.error(f"Error processing new messages: {e}")
            logger.error(traceback.format_exc())

    async def _process_message(self, stream: str, message_id: str, message: Dict[str, str]) -> None:
        """
        Process a single message from a Redis stream.
        
        Args:
            stream: Stream the message came from
            message_id: Redis message ID
            message: Message data
        """

async def start(self) -> None:
    """Start the worker processing loop."""
    if self.running:
        logger.warning(f"{self.agent_type} worker already running")
        return
    # ----------------------------------------
    # Helper utilities
    # ----------------------------------------
    @staticmethod
    def _deep_parse(value: Any) -> Any:
        """Recursively JSON-parse nested stringified structures to dict/list primitives."""
        if isinstance(value, str):
            val = value.strip()
            if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
                try:
                    return BaseAgentWorker._deep_parse(json.loads(val))
                except json.JSONDecodeError:
                    return value
            return value
        if isinstance(value, list):
            return [BaseAgentWorker._deep_parse(v) for v in value]
        if isinstance(value, dict):
            return {k: BaseAgentWorker._deep_parse(v) for k, v in value.items()}
        return value

    def _extract_task_data(self, message: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract task data from a Redis stream message.
        
        Args:
            message: Redis stream message
            
        Returns:
            Task data dictionary or None if invalid
        """
        try:
            raw_task_data = json.loads(message["task"])
            task_data = self._deep_parse(raw_task_data)
            required_fields = ["task_id", "task_type"]
            for field in required_fields:
                if field not in task_data:
                    logger.warning(f"Task missing required field: {field}")
                    return None
            return task_data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in task data: {message.get('task', '')}")
            return None
        except Exception as e:
            logger.error(f"Error extracting task data: {e}")
            return None
            
    async def _publish_result(self, task_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Publish task processing result to the result stream.
        
        Args:
            task_data: Original task data
            result: Processing result
        """
        try:
            # Preserve request_id and job_id from original task if available
            for key in ("request_id", "job_id"):
                if key in task_data and key not in result:
                    result[key] = task_data[key]
                    
            result_json = json.dumps(result)
            logger.debug(f"{self.mode_emoji} Publishing result for task {task_data['task_id']}")
            
            await self.async_redis_client.xadd(
                self.result_stream,
                {"result": result_json},
            )
            logger.debug(
                f"{self.mode_emoji} XADD completed for task {task_data['task_id']}"
            )

            logger.info(f"Published result for task {task_data['task_id']}")
            
        except Exception as e:
            logger.error(f"Error publishing result: {e}")

    async def _publish_error(self, task_data: Dict[str, Any], error: Exception, tb: str) -> None:
        """Publish structured error details to the result stream for observability."""
        try:
            err_payload = {
                "task_id": task_data.get("task_id"),
                "task_type": task_data.get("task_type"),
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": tb,
            }
            # Preserve request_id / job_id if available
            for key in ("request_id", "job_id"):
                if key in task_data:
                    err_payload[key] = task_data[key]

            await self.async_redis_client.xadd(self.result_stream, {"result": json.dumps(err_payload)})
            logger.debug(f"{self.mode_emoji} XADD error record for task {err_payload.get('task_id')}")
        except Exception as publish_err:
            logger.error(f"Failed to publish error details: {publish_err}")

    async def _cleanup(self) -> None:
        """Clean up resources when stopping the worker."""
        try:
            # Close Redis connections
            if self.async_redis_client:
                await self.async_redis_client.close()
            if self.redis_client:
                self.redis_client.close()
                
            logger.info(f"{self.agent_type} worker resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up {self.agent_type} worker resources: {e}")

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown")
            self.should_stop = True
            
        # Register for SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    # ---------------------------------------------------------------------
    # Message processing utilities - exposed at class level for testing
    # ---------------------------------------------------------------------

    async def _process_message(self, stream: str, message_id: str, message: Dict[str, str]) -> None:
        """Process a single message from a Redis stream and publish the outcome."""
        try:
            task_data = self._extract_task_data(message)
            if task_data is None:
                # Acknowledge and drop invalid message so it doesn't block the stream
                await self.async_redis_client.xack(stream, self.consumer_group, message_id)
                logger.warning(f"{self.mode_emoji} Dropped invalid task from stream {stream}: {message_id}")
                return

            # Delegate actual work to the concrete agent implementation
            result = await self.process_task(task_data)

            # Publish the processing result
            await self._publish_result(task_data, result)

            # ACK the message so Redis can remove it from the pending list
            await self.async_redis_client.xack(stream, self.consumer_group, message_id)

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"{self.mode_emoji} Unhandled exception while processing message {message_id}: {e}")
            # Publish structured error so orchestrator / observability tooling can pick it up
            await self._publish_error(task_data if 'task_data' in locals() else {}, e, tb)
            # NOTE: We intentionally do NOT ACK here so the message can be retried later

    # ---------------------------------------------------------------------
    # Helper utilities
    # ---------------------------------------------------------------------

    @staticmethod
    def _deep_parse(value: Any) -> Any:
        """Recursively JSON-parse nested stringified structures to dict/list primitives."""
        if isinstance(value, str):
            val = value.strip()
            if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
                try:
                    return BaseAgentWorker._deep_parse(json.loads(val))
                except json.JSONDecodeError:
                    return value
            return value
        if isinstance(value, list):
            return [BaseAgentWorker._deep_parse(v) for v in value]
        if isinstance(value, dict):
            return {k: BaseAgentWorker._deep_parse(v) for k, v in value.items()}
        return value

    def _extract_task_data(self, message: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract task data from a Redis stream entry, performing deep JSON parsing and validation."""
        try:
            raw_task_data = json.loads(message["task"])
            task_data = self._deep_parse(raw_task_data)
            required_fields = ("task_id", "task_type")
            for field in required_fields:
                if field not in task_data:
                    logger.warning(f"Task missing required field: {field}")
                    return None
            return task_data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in task data: {message.get('task', '')}")
            return None
        except Exception as e:
            logger.error(f"Error extracting task data: {e}")
            return None

    async def _publish_result(self, task_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Publish task processing result to the configured result stream."""
        try:
            # Preserve identifiers for downstream consumers
            for key in ("request_id", "job_id"):
                if key in task_data and key not in result:
                    result[key] = task_data[key]

            await self.async_redis_client.xadd(
                self.result_stream,
                {"result": json.dumps(result)},
            )
            logger.debug(f"{self.mode_emoji} Published result for task {task_data.get('task_id')}")
        except Exception as e:
            logger.error(f"Error publishing result: {e}")

    async def _publish_error(self, task_data: Dict[str, Any], error: Exception, tb: str) -> None:
        """Publish structured error details to the result stream for observability."""
        try:
            err_payload = {
                "task_id": task_data.get("task_id"),
                "task_type": task_data.get("task_type"),
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": tb,
            }
            for key in ("request_id", "job_id"):
                if key in task_data:
                    err_payload[key] = task_data[key]

            await self.async_redis_client.xadd(self.result_stream, {"result": json.dumps(err_payload)})
            logger.debug(f"{self.mode_emoji} Published error for task {err_payload.get('task_id')}")
        except Exception as publish_err:
            logger.error(f"Failed to publish error details: {publish_err}")

    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the appropriate agent.
        
        This method must be implemented by subclasses to handle
        agent-specific task processing logic.
        
        Args:
            task_data: Task data from Redis stream
            
        Returns:
            Task processing result
        """
        pass
