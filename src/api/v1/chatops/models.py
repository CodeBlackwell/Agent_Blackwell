"""
Pydantic models for ChatOps API.

This module contains all the Pydantic models used for request/response validation
in the ChatOps API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


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
    # New command for job submission
    JOB = "job"


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


# --- Legacy Task Models (to be phased out) ---


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


# --- Job & Task Models (New Architecture) ---


class JobStatus(str, Enum):
    """Represents the lifecycle status of a job."""

    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskStatus(str, Enum):
    """Represents the lifecycle status of a task within a job."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """Represents a single, executable task within a job."""

    task_id: str = Field(..., description="Unique identifier for the task.")
    job_id: str = Field(..., description="The parent job ID.")
    agent_type: str = Field(
        ..., description="The type of agent required to execute this task (e.g., 'design', 'code')."
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="The current status of the task."
    )
    description: str = Field(
        ..., description="A description of what the task needs to accomplish."
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="A list of other task_ids that must be completed before this task can start.",
    )
    result: Optional[Any] = Field(
        None, description="The output or result of the task upon completion."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of when the task was created."
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the last update."
    )

    @field_validator("updated_at", "created_at", mode="before")
    def dt_to_iso(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class Job(BaseModel):
    """Represents a high-level job that consists of multiple tasks."""

    job_id: str = Field(..., description="Unique identifier for the job.")
    user_request: str = Field(
        ..., description="The original high-level request from the user."
    )
    status: JobStatus = Field(
        default=JobStatus.PLANNING, description="The current status of the job."
    )
    tasks: List[Task] = Field(
        default_factory=list, description="The list of tasks that make up this job."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of when the job was created."
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the last update."
    )

    @field_validator("updated_at", "created_at", mode="before")
    def dt_to_iso(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


# API Response Models for Job Management

class JobCreationRequest(BaseModel):
    """Request model for creating a new job."""
    user_request: str = Field(..., description="The user's request that will be processed as a job")
    priority: Optional[str] = Field(None, description="Priority level (high, medium, low)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the job")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class JobCreationResponse(BaseModel):
    """Response model for job creation."""
    job_id: str = Field(..., description="Unique identifier for the created job")
    status: JobStatus = Field(..., description="Current status of the job")
    message: str = Field(..., description="Success message")
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    status_endpoint: str = Field(..., description="Endpoint to check job status")


class JobStatusResponse(BaseModel):
    """Response model for job status queries."""
    job_id: str = Field(..., description="Unique identifier for the job")
    user_request: str = Field(..., description="Original user request")
    status: JobStatus = Field(..., description="Current status of the job")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks in the job")
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    updated_at: datetime = Field(..., description="Timestamp of the last update")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Progress information")


class TaskStatusResponse(BaseModel):
    """Response model for task status queries."""
    task_id: str = Field(..., description="Unique identifier for the task")
    job_id: str = Field(..., description="Job ID this task belongs to")
    agent_type: str = Field(..., description="Type of agent handling this task")
    status: TaskStatus = Field(..., description="Current status of the task")
    description: str = Field(..., description="Task description")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    result: Optional[Any] = Field(None, description="Task result if completed")
    created_at: datetime = Field(..., description="Timestamp when the task was created")
    updated_at: datetime = Field(..., description="Timestamp of the last update")


class JobListResponse(BaseModel):
    """Response model for listing jobs."""
    jobs: List[JobStatusResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Number of jobs per page")
