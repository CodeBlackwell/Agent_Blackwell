"""
Slack integration for ChatOps.

This module provides functionality to integrate with Slack for ChatOps,
including sending messages to Slack and handling Slack slash commands.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    Header,
    HTTPException,
    Request,
)
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from src.api.v1.chatops.models import ChatCommandRequest, ChatPlatform
from src.api.v1.chatops.router import process_command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create router
router = APIRouter(prefix="/api/v1/chatops/slack", tags=["Slack"])


class SlackMessageBlock(BaseModel):
    """Model for a Slack message block."""

    type: str
    text: Optional[Dict[str, str]] = None
    elements: Optional[List[Dict[str, Any]]] = None
    accessory: Optional[Dict[str, Any]] = None


class SlackMessage(BaseModel):
    """Model for a Slack message."""

    channel: str
    text: str
    blocks: Optional[List[SlackMessageBlock]] = None
    thread_ts: Optional[str] = None
    mrkdwn: bool = True


async def get_slack_token() -> str:
    """
    Get the Slack API token from environment variables.

    Returns:
        str: The Slack API token
    """
    token = os.getenv("SLACK_API_TOKEN")
    if not token:
        raise ValueError("SLACK_API_TOKEN environment variable not set")
    return token


async def get_slack_signing_secret() -> str:
    """
    Get the Slack signing secret from environment variables.

    Returns:
        str: The Slack signing secret
    """
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret:
        raise ValueError("SLACK_SIGNING_SECRET environment variable not set")
    return secret


@router.post("/events")
async def slack_events(
    request: Request,
    x_slack_signature: Optional[str] = Header(None, alias="X-Slack-Signature"),
    x_slack_request_timestamp: Optional[str] = Header(
        None, alias="X-Slack-Request-Timestamp"
    ),
    signing_secret: str = Depends(get_slack_signing_secret),
) -> Dict[str, Any]:
    """
    Handle Slack events.

    This endpoint receives events from Slack, such as message events,
    and processes them accordingly.
    """
    # Get the request body
    body = await request.body()

    # Verify the request signature to ensure the request is coming from Slack
    is_valid = verify_slack_signature(
        body, x_slack_signature, x_slack_request_timestamp, signing_secret
    )
    if not is_valid:
        logger.warning("Invalid Slack signature")
        return {"ok": False, "error": "Invalid signature"}

    # Parse the request body
    try:
        data = json.loads(body)

        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge")}

        # Handle events
        if data.get("event"):
            event = data.get("event")
            # Process different event types
            if event.get("type") == "message" and not event.get("bot_id"):
                # Handle a user message (not from a bot)
                await handle_slack_message(event)

        return {"ok": True}
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return {"ok": False, "error": str(e)}


@router.post("/commands")
async def slack_commands(
    token: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    user_id: str = Form(...),
    channel_id: str = Form(...),
    response_url: str = Form(...),
    trigger_id: str = Form(...),
    team_id: str = Form(...),
) -> Dict[str, Any]:
    """
    Handle Slack slash commands.

    This endpoint receives slash commands from Slack and processes them.
    """
    try:
        logger.info(
            f"Received Slack command: {command} {text} from user {user_id} in channel {channel_id}"
        )

        # Process the command
        if command == "/agent":
            # Convert to our standard ChatCommandRequest format
            # Format the command with the expected syntax for our router
            formatted_command = f"!{text}"

            command_request = ChatCommandRequest(
                platform=ChatPlatform.SLACK,
                user_id=user_id,
                channel_id=channel_id,
                command=formatted_command,
                timestamp=str(time.time()),
            )

            # Process the command using our router
            # For slash commands, we need to return immediately and then
            # send the response to the response_url
            response = await process_command(command_request, BackgroundTasks())

            # Send an initial acknowledgment
            initial_response = {
                "response_type": "in_channel",
                "text": f"Processing command: `/agent {text}`...",
            }

            # Send the actual response to the response_url asynchronously
            async def send_delayed_response():
                await asyncio.sleep(0.5)  # Small delay before sending response
                async with httpx.AsyncClient() as client:
                    await client.post(
                        response_url,
                        json={
                            "response_type": "in_channel",
                            "text": response.message,
                        },
                    )

            # Kick off the async task to send the delayed response
            asyncio.create_task(send_delayed_response())

            return initial_response

        # Unknown command
        return {"response_type": "ephemeral", "text": f"Unknown command: {command}"}
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        return {
            "response_type": "ephemeral",
            "text": f"An error occurred while processing your command: {str(e)}",
        }


async def handle_slack_message(event: Dict[str, Any]) -> None:
    """
    Handle a Slack message event.

    This function processes a Slack message event, potentially looking for
    command-like patterns in the text.
    """
    text = event.get("text", "")
    user = event.get("user")
    channel = event.get("channel")
    ts = event.get("ts")

    logger.info(f"Received Slack message: {text} from user {user} in channel {channel}")

    # Check if the message looks like a command (starts with !)
    from src.api.v1.chatops.router import COMMAND_PATTERN

    if COMMAND_PATTERN.match(text):
        # Convert to our standard ChatCommandRequest format
        command_request = ChatCommandRequest(
            platform=ChatPlatform.SLACK,
            user_id=user,
            channel_id=channel,
            command=text,
            timestamp=ts or "",
        )

        # Process the command using our existing router logic
        from src.api.v1.chatops.router import process_command

        response = await process_command(command_request)

        # Send the response back to Slack
        await send_slack_message(channel, response.message, thread_ts=ts)


async def send_slack_message(
    channel: str,
    text: str,
    thread_ts: Optional[str] = None,
    blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Send a message to a Slack channel.

    Args:
        channel: The channel ID to send the message to
        text: The message text
        thread_ts: Optional thread timestamp to reply in a thread
        blocks: Optional blocks for rich formatting

    Returns:
        The Slack API response
    """
    # Get the Slack token
    token = await get_slack_token()

    # Prepare the message
    message = {
        "channel": channel,
        "text": text,
    }

    if thread_ts:
        message["thread_ts"] = thread_ts

    if blocks:
        message["blocks"] = blocks

    # Send the message
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            json=message,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        data = response.json()
        if not data.get("ok"):
            logger.error(f"Error sending Slack message: {data.get('error')}")

        return data


def verify_slack_signature(
    body: bytes, signature: Optional[str], timestamp: Optional[str], signing_secret: str
) -> bool:
    """
    Verify that a request came from Slack.

    Args:
        body: The request body
        signature: The X-Slack-Signature header value
        timestamp: The X-Slack-Request-Timestamp header value
        signing_secret: The Slack signing secret

    Returns:
        True if the signature is valid, False otherwise
    """
    import hashlib
    import hmac
    import time

    if not signature or not timestamp:
        return False

    # Check timestamp to prevent replay attacks
    # Slack recommends rejecting requests older than 5 minutes
    current_timestamp = int(time.time())
    request_timestamp = int(timestamp)

    if abs(current_timestamp - request_timestamp) > 300:
        return False

    # Compute the signature
    base_string = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    # Compare signatures using constant time comparison
    return hmac.compare_digest(my_signature, signature)
