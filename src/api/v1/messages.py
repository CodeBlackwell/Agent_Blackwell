"""Messages endpoint module for accessing agent communication from Redis streams."""

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
async def get_messages(number_of_messages: Optional[int] = Query(None, gt=0)):
    """
    Returns the most recent agent messages from the Redis stream. If number_of_messages is not provided, returns all messages.
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
        # Format messages
        messages = [{"id": entry[0], **entry[1]} for entry in entries]
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching messages: {str(e)}"
        )
    finally:
        await redis.close()
