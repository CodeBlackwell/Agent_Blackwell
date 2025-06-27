"""
Real-time streaming API router.

This module implements WebSocket endpoints for real-time job and task status streaming,
allowing clients to receive live updates about job progress and task completion.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from src.api.dependencies import get_orchestrator
from src.orchestrator.main import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/streaming", tags=["Streaming"])


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""

    def __init__(self):
        """Initialize the connection manager with empty connection sets."""
        # Active connections: job_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global connections (listening to all jobs)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, job_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if job_id:
            # Job-specific connection
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()
            self.active_connections[job_id].add(websocket)
            logger.info(f"WebSocket connected for job {job_id}")
        else:
            # Global connection
            self.global_connections.add(websocket)
            logger.info("Global WebSocket connection established")

    def disconnect(self, websocket: WebSocket, job_id: str = None):
        """Remove a WebSocket connection."""
        if job_id and job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")
        else:
            self.global_connections.discard(websocket)
            logger.info("Global WebSocket connection closed")

    async def send_to_job(self, job_id: str, message: dict):
        """Send a message to all connections listening to a specific job."""
        if job_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[job_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.add(websocket)

            # Clean up disconnected websockets
            for websocket in disconnected:
                self.active_connections[job_id].discard(websocket)

    async def send_to_all(self, message: dict):
        """Send a message to all global connections."""
        disconnected = set()
        for websocket in self.global_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to global WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.global_connections.discard(websocket)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/jobs/{job_id}")
async def websocket_job_status(
    websocket: WebSocket,
    job_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """
    WebSocket endpoint for real-time job status updates.

    Clients can connect to this endpoint to receive live updates about a specific job,
    including task completions, status changes, and progress updates.
    """
    await manager.connect(websocket, job_id)

    try:
        # Send initial job status
        job = await orchestrator.get_job(job_id)
        if job:
            initial_status = {
                "event_type": "job_status",
                "job_id": job.job_id,
                "status": job.status.value,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "agent_type": task.agent_type,
                        "status": task.status.value,
                        "description": task.description,
                    }
                    for task in job.tasks
                ],
                "progress": {
                    "total_tasks": len(job.tasks),
                    "completed_tasks": len(
                        [t for t in job.tasks if t.status.value == "completed"]
                    ),
                    "failed_tasks": len(
                        [t for t in job.tasks if t.status.value == "failed"]
                    ),
                    "running_tasks": len(
                        [t for t in job.tasks if t.status.value == "running"]
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
            await websocket.send_json(initial_status)
        else:
            await websocket.send_json(
                {
                    "event_type": "error",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "event_type": "error",
                        "message": "Invalid JSON message",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, job_id)


@router.websocket("/jobs")
async def websocket_all_jobs(
    websocket: WebSocket, orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    WebSocket endpoint for real-time updates on all jobs.

    Clients can connect to this endpoint to receive live updates about all jobs
    in the system, useful for dashboard and monitoring applications.
    """
    await manager.connect(websocket)

    try:
        # Send initial status message
        await websocket.send_json(
            {
                "event_type": "connected",
                "message": "Connected to global job stream",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "event_type": "error",
                        "message": "Invalid JSON message",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Error in global WebSocket connection: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


class StreamingService:
    """Service for managing real-time streaming of job/task updates."""

    def __init__(self, redis_client, connection_manager: ConnectionManager):
        """Initialize the streaming service with Redis client and connection manager."""
        self.redis_client = redis_client
        self.manager = connection_manager
        self.running = False
        self.stream_task = None

    async def start_streaming(self):
        """Start the Redis stream consumer for real-time updates."""
        if self.running:
            return

        self.running = True
        self.stream_task = asyncio.create_task(self._consume_streams())
        logger.info("Started real-time streaming service")

    async def stop_streaming(self):
        """Stop the Redis stream consumer."""
        self.running = False
        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped real-time streaming service")

    async def _consume_streams(self):
        """Consume Redis streams and broadcast updates to WebSocket clients."""
        last_ids = {}

        while self.running:
            try:
                # Get all job stream names
                job_streams = []
                async for key in self.redis_client.scan_iter(match="job-stream:*"):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    job_streams.append(key_str)
                    if key_str not in last_ids:
                        last_ids[key_str] = "0"

                if not job_streams:
                    await asyncio.sleep(1)
                    continue

                # Read from all job streams
                streams_dict = {stream: last_ids[stream] for stream in job_streams}

                try:
                    response = await self.redis_client.xread(
                        streams_dict, count=10, block=1000  # Block for 1 second
                    )

                    for stream_name, messages in response:
                        stream_name_str = (
                            stream_name.decode()
                            if isinstance(stream_name, bytes)
                            else stream_name
                        )
                        job_id = stream_name_str.replace("job-stream:", "")

                        for message_id, fields in messages:
                            message_id_str = (
                                message_id.decode()
                                if isinstance(message_id, bytes)
                                else message_id
                            )
                            last_ids[stream_name_str] = message_id_str

                            # Decode fields
                            decoded_fields = {}
                            for key, value in fields.items():
                                key_str = (
                                    key.decode() if isinstance(key, bytes) else key
                                )
                                value_str = (
                                    value.decode()
                                    if isinstance(value, bytes)
                                    else value
                                )
                                decoded_fields[key_str] = value_str

                            # Broadcast to WebSocket clients
                            await self._broadcast_update(job_id, decoded_fields)

                except Exception as e:
                    if "NOGROUP" not in str(e):  # Ignore consumer group errors
                        logger.error(f"Error reading from Redis streams: {e}")
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in stream consumer: {e}")
                await asyncio.sleep(5)

    async def _broadcast_update(self, job_id: str, event_data: dict):
        """Broadcast an update to relevant WebSocket connections."""
        try:
            # Parse result if it's JSON
            if "result" in event_data:
                try:
                    event_data["result"] = json.loads(event_data["result"])
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON

            # Send to job-specific connections
            await self.manager.send_to_job(job_id, event_data)

            # Send to global connections
            await self.manager.send_to_all(event_data)

        except Exception as e:
            logger.error(f"Error broadcasting update: {e}")


# Global streaming service instance
streaming_service = None


@router.get("/health")
async def streaming_health():
    """Health check endpoint for streaming service."""
    global streaming_service

    return {
        "status": "healthy",
        "streaming_active": streaming_service.running if streaming_service else False,
        "active_connections": {
            "job_specific": len(manager.active_connections),
            "global": len(manager.global_connections),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


async def initialize_streaming_service(redis_client):
    """Initialize the streaming service with Redis client."""
    global streaming_service
    streaming_service = StreamingService(redis_client, manager)
    await streaming_service.start_streaming()


async def shutdown_streaming_service():
    """Shutdown the streaming service."""
    global streaming_service
    if streaming_service:
        await streaming_service.stop_streaming()
