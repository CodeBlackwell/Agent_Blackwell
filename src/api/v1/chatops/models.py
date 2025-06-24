"""
Pydantic models for ChatOps API.

This module contains all the Pydantic models used for request/response validation
in the ChatOps API endpoints.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ChatPlatform(str, Enum):
    """Supported chat platforms."""

    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "microsoft_teams"


class CommandType(str, Enum):
    """Types of commands supported by ChatOps."""

    DEPLOY = "deploy"
    STATUS = "status"
    HELP = "help"
    SPEC = "spec"  # For spec agent
    DESIGN = "design"  # For design agent
    CODE = "code"  # For coding agent
    REVIEW = "review"  # For review agent
    TEST = "test"  # For test agent


class ChatCommandRequest(BaseModel):
    """
    Model for incoming chat commands.

    This is the base structure for all incoming chat messages.
    """

    platform: ChatPlatform
    user_id: str = Field(..., description="ID of the user who sent the command")
    channel_id: str = Field(
        ..., description="ID of the channel where the command was sent"
    )
    command: str = Field(..., description="The full command text")
    timestamp: str = Field(
        ..., description="ISO timestamp of when the command was sent"
    )


class ChatCommandResponse(BaseModel):
    """
    Model for responses to chat commands.

    This is the structure for messages sent back to the chat platform.
    """

    message: str = Field(
        ..., description="The message to send back to the chat platform"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(
        None, description="Optional attachments for rich messages"
    )
    ephemeral: bool = Field(
        False, description="Whether the message should only be visible to the sender"
    )


class TaskCreationResponse(BaseModel):
    """
    Model for task creation responses.

    This is returned when a new task is created via ChatOps.
    """

    task_id: str = Field(..., description="ID of the created task")
    status: str = Field("queued", description="Initial status of the task")
    message: str = Field(..., description="Human-readable description of the task")


class TaskStatusResponse(BaseModel):
    """
    Model for task status responses.

    This is returned when querying the status of a task.
    """

    task_id: str = Field(..., description="ID of the task")
    status: str = Field(..., description="Current status of the task")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(
        None, description="Task result, if completed"
    )
    error: Optional[str] = Field(None, description="Error message, if failed")
    created_at: Optional[str] = Field(
        None, description="ISO timestamp of when the task was created"
    )
    updated_at: Optional[str] = Field(
        None, description="ISO timestamp of when the task was last updated"
    )
