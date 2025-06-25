"""Messages endpoint module for accessing agent communication from Redis streams."""

import json
import os
from typing import Any, List, Optional

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_NAME = os.getenv(
    "AGENT_MESSAGE_STREAM", "orchestrator_tasks"
)  # Adjust as needed


async def get_redis():
    """Create and return a Redis client connection."""
    return redis.from_url(REDIS_URL, decode_responses=True)


@router.get("/messages", summary="Get agent messages from Redis stream")
async def get_messages(
    number_of_messages: Optional[int] = Query(None, gt=0),
    task_id: Optional[str] = Query(None, description="Filter messages by task ID"),
):
    """
    Returns agent messages from the Redis stream.

    Parameters:
    - number_of_messages: If provided, limits the number of returned messages
    - task_id: If provided, filters messages to only include those related to the specified task ID
    """
    redis = await get_redis()
    try:
        if number_of_messages:
            # Get the most recent N messages
            entries = await redis.xrevrange(STREAM_NAME, count=number_of_messages)
            entries = list(reversed(entries))  # Return in chronological order
        else:
            # Get all messages
            entries = await redis.xrange(STREAM_NAME)
        # Format and potentially filter messages
        messages = []
        for entry in entries:
            msg_id = entry[0]
            msg_data = entry[1]

            # Create base message with ID and raw fields
            message = {"id": msg_id, **msg_data}

            # If task_id filter is applied, check if this message contains the specified task
            if task_id:
                # Check if task or result fields exist and contain the task_id
                is_match = False

                # Check in task field
                if "task" in msg_data:
                    try:
                        task_json = json.loads(msg_data["task"])
                        if task_json.get("task_id") == task_id:
                            is_match = True
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Check in result field
                if not is_match and "result" in msg_data:
                    try:
                        result_json = json.loads(msg_data["result"])
                        if result_json.get("task_id") == task_id:
                            is_match = True
                    except (json.JSONDecodeError, TypeError):
                        pass

                if is_match:
                    messages.append(message)
            else:
                # No filter applied, include all messages
                messages.append(message)

        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching messages: {str(e)}"
        )
    finally:
        await redis.close()
