"""
Router for feature request API endpoints.

This module provides endpoints for submitting and managing feature requests.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_orchestrator
from src.orchestrator.main import Orchestrator

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["feature-requests"],
)


class FeatureRequestInput(BaseModel):
    """Schema for feature request input."""

    description: str = Field(
        ...,
        description="Detailed description of the requested feature",
        min_length=1,
    )


class FeatureRequestResponse(BaseModel):
    """Schema for feature request response."""

    task_id: str = Field(..., description="ID of the created task")
    status: str = Field(
        default="processing", description="Status of the feature request"
    )


class TaskStatusResponse(BaseModel):
    """Schema for task status response."""

    task_id: str = Field(..., description="ID of the task")
    status: str = Field(..., description="Current status of the task")
    result: Optional[Dict[str, Any]] = Field(
        None, description="Task result if completed"
    )


# We now use the centralized dependency instead of creating a new instance


@router.post(
    "/feature-request",
    response_model=FeatureRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_feature_request(
    request: FeatureRequestInput, orchestrator: Orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Submit a new feature request to the system.

    Args:
        request: Feature request details
        orchestrator: Orchestrator instance for task submission

    Returns:
        Dict with task ID and status
    """
    logger.info(f"Received feature request: {request.description[:50]}...")
    logger.info(f"Using orchestrator instance: {id(orchestrator)}")

    try:
        # Submit the feature request to the orchestrator
        task_id = await orchestrator.submit_feature_request(request.description)

        # Log the task ID to help with debugging
        logger.info(f"Generated task_id: {task_id}")

        # Return the response
        return {"task_id": task_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Error submitting feature request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feature request",
        )


@router.get(
    "/task-status/{task_id}",
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_task_status(
    task_id: str, orchestrator: Orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get the status of a task by its ID.

    Args:
        task_id: ID of the task to check
        orchestrator: Orchestrator instance for task status retrieval

    Returns:
        Dict with task status information
    """
    logger.info(f"Checking status for task: {task_id}")

    try:
        # Get task status from orchestrator
        status_info = await orchestrator.get_task_status(task_id)

        if status_info.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        # Prepare response
        response = {"task_id": task_id, "status": status_info.get("status")}

        # Add result if available
        if status_info.get("status") == "completed" and "result" in status_info:
            response["result"] = status_info["result"]
        elif "task" in status_info:
            response["task"] = status_info["task"]

        return response
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking task status",
        )
