"""Messages endpoint module for accessing agent communication and workflow data."""

import json
import os
from typing import Any, List, Optional, Dict

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Query, Depends

from src.api.dependencies import get_orchestrator
from src.orchestrator.langgraph_orchestrator import LangGraphOrchestrator

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_NAME = os.getenv("AGENT_MESSAGE_STREAM", "orchestrator_tasks")
WORKFLOW_METRICS_STREAM = os.getenv("WORKFLOW_METRICS_STREAM", "langgraph_workflows")


async def get_redis():
    """Create and return a Redis client connection."""
    return redis.from_url(REDIS_URL, decode_responses=True)


async def log_workflow_event(workflow_id: str, event_type: str, data: Dict[str, Any]):
    """
    Log workflow events to Redis for external monitoring and metrics.
    
    Args:
        workflow_id: ID of the workflow
        event_type: Type of event (started, completed, failed, etc.)
        data: Event data to log
    """
    try:
        redis_client = await get_redis()
        
        # Create event record
        event_record = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "timestamp": data.get("timestamp", ""),
            "data": json.dumps(data)
        }
        
        # Add to workflow metrics stream
        await redis_client.xadd(WORKFLOW_METRICS_STREAM, event_record)
        
        await redis_client.close()
    except Exception as e:
        # Don't fail the main workflow if logging fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to log workflow event: {str(e)}")


@router.get("/messages", summary="Get agent messages from Redis stream")
async def get_messages(
    number_of_messages: Optional[int] = Query(None, gt=0),
    task_id: Optional[str] = Query(None, description="Filter messages by task ID"),
    workflow_id: Optional[str] = Query(None, description="Filter messages by workflow ID"),
):
    """
    Returns agent messages from the Redis stream and workflow metrics.

    Parameters:
    - number_of_messages: If provided, limits the number of returned messages
    - task_id: If provided, filters messages to only include those related to the specified task ID
    - workflow_id: If provided, filters messages to only include those related to the specified workflow ID
    """
    redis_client = await get_redis()
    try:
        messages = []
        
        # Get legacy messages from the original stream
        if number_of_messages:
            entries = await redis_client.xrevrange(STREAM_NAME, count=number_of_messages)
            entries = list(reversed(entries))
        else:
            entries = await redis_client.xrange(STREAM_NAME)
        
        # Process legacy messages
        for entry in entries:
            msg_id = entry[0]
            msg_data = entry[1]
            message = {"id": msg_id, "source": "legacy", **msg_data}
            
            # Apply filters
            if task_id and not _message_matches_task_id(msg_data, task_id):
                continue
            if workflow_id and not _message_matches_workflow_id(msg_data, workflow_id):
                continue
                
            messages.append(message)
        
        # Get workflow metrics from the new stream
        try:
            workflow_entries = await redis_client.xrange(WORKFLOW_METRICS_STREAM)
            for entry in workflow_entries:
                msg_id = entry[0]
                msg_data = entry[1]
                message = {"id": msg_id, "source": "workflow", **msg_data}
                
                # Apply filters
                if workflow_id and msg_data.get("workflow_id") != workflow_id:
                    continue
                if task_id and not _workflow_message_matches_task_id(msg_data, task_id):
                    continue
                    
                messages.append(message)
        except Exception:
            # Workflow stream might not exist yet, continue with legacy messages only
            pass
        
        # Sort by timestamp if possible
        messages.sort(key=lambda x: x.get("id", ""), reverse=False)
        
        # Limit results if requested
        if number_of_messages:
            messages = messages[-number_of_messages:]
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching messages: {str(e)}"
        )
    finally:
        await redis_client.close()


def _message_matches_task_id(msg_data: Dict[str, Any], task_id: str) -> bool:
    """Check if a legacy message matches the given task ID."""
    # Check in task field
    if "task" in msg_data:
        try:
            task_json = json.loads(msg_data["task"])
            if task_json.get("task_id") == task_id:
                return True
        except (json.JSONDecodeError, TypeError):
            pass

    # Check in result field
    if "result" in msg_data:
        try:
            result_json = json.loads(msg_data["result"])
            if result_json.get("task_id") == task_id:
                return True
        except (json.JSONDecodeError, TypeError):
            pass
            
    return False


def _message_matches_workflow_id(msg_data: Dict[str, Any], workflow_id: str) -> bool:
    """Check if a legacy message matches the given workflow ID."""
    # Legacy messages might not have workflow IDs
    return False


def _workflow_message_matches_task_id(msg_data: Dict[str, Any], task_id: str) -> bool:
    """Check if a workflow message matches the given task ID."""
    try:
        if "data" in msg_data:
            data_json = json.loads(msg_data["data"])
            return data_json.get("task_id") == task_id
    except (json.JSONDecodeError, TypeError):
        pass
    return False


@router.get("/workflow-events/{workflow_id}", summary="Get workflow events")
async def get_workflow_events(
    workflow_id: str,
    number_of_events: Optional[int] = Query(None, gt=0),
):
    """
    Get events for a specific workflow from Redis metrics stream.

    Parameters:
    - workflow_id: ID of the workflow to get events for
    - number_of_events: If provided, limits the number of returned events
    """
    redis_client = await get_redis()
    try:
        # Get workflow events from metrics stream
        entries = await redis_client.xrange(WORKFLOW_METRICS_STREAM)
        
        # Filter events for the specific workflow
        workflow_events = []
        for entry in entries:
            msg_id = entry[0]
            msg_data = entry[1]
            
            if msg_data.get("workflow_id") == workflow_id:
                event = {"id": msg_id, **msg_data}
                
                # Parse the data field if it exists
                if "data" in event:
                    try:
                        event["parsed_data"] = json.loads(event["data"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                workflow_events.append(event)
        
        # Sort by timestamp
        workflow_events.sort(key=lambda x: x.get("id", ""))
        
        # Limit results if requested
        if number_of_events:
            workflow_events = workflow_events[-number_of_events:]
        
        return {"workflow_id": workflow_id, "events": workflow_events}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching workflow events: {str(e)}"
        )
    finally:
        await redis_client.close()


@router.post("/workflow-events", summary="Log workflow event")
async def log_workflow_event_endpoint(
    workflow_id: str,
    event_type: str,
    event_data: Dict[str, Any],
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
):
    """
    Log a workflow event to Redis metrics stream.
    
    This endpoint allows external systems to log workflow events for monitoring.
    
    Parameters:
    - workflow_id: ID of the workflow
    - event_type: Type of event to log
    - event_data: Event data to store
    """
    try:
        await log_workflow_event(workflow_id, event_type, event_data)
        return {"status": "success", "message": "Event logged successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error logging workflow event: {str(e)}"
        )


@router.get("/metrics/workflows", summary="Get workflow metrics summary")
async def get_workflow_metrics():
    """
    Get aggregated metrics for all workflows.
    
    Returns summary statistics about workflow performance and status.
    """
    redis_client = await get_redis()
    try:
        # Get all workflow events
        entries = await redis_client.xrange(WORKFLOW_METRICS_STREAM)
        
        # Aggregate metrics
        metrics = {
            "total_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "in_progress_workflows": 0,
            "event_types": {},
            "recent_activity": []
        }
        
        workflow_statuses = {}
        
        for entry in entries:
            msg_data = entry[1]
            workflow_id = msg_data.get("workflow_id")
            event_type = msg_data.get("event_type")
            
            # Count event types
            if event_type:
                metrics["event_types"][event_type] = metrics["event_types"].get(event_type, 0) + 1
            
            # Track workflow statuses
            if workflow_id:
                if event_type == "started":
                    workflow_statuses[workflow_id] = "in_progress"
                elif event_type == "completed":
                    workflow_statuses[workflow_id] = "completed"
                elif event_type == "failed":
                    workflow_statuses[workflow_id] = "failed"
            
            # Add to recent activity (last 10 events)
            if len(metrics["recent_activity"]) < 10:
                metrics["recent_activity"].append({
                    "workflow_id": workflow_id,
                    "event_type": event_type,
                    "timestamp": msg_data.get("timestamp")
                })
        
        # Count workflow statuses
        metrics["total_workflows"] = len(workflow_statuses)
        for status in workflow_statuses.values():
            if status == "completed":
                metrics["completed_workflows"] += 1
            elif status == "failed":
                metrics["failed_workflows"] += 1
            elif status == "in_progress":
                metrics["in_progress_workflows"] += 1
        
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching workflow metrics: {str(e)}"
        )
    finally:
        await redis_client.close()
