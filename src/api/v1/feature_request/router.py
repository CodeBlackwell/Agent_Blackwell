"""
Router for feature request API endpoints.

This module provides endpoints for submitting and managing feature requests
using the LangGraph orchestrator system.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.dependencies import get_orchestrator
from src.orchestrator.langgraph_orchestrator import LangGraphOrchestrator

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

    workflow_id: str = Field(..., description="ID of the created workflow")
    status: str = Field(
        default="processing", description="Status of the feature request"
    )


class WorkflowStatusResponse(BaseModel):
    """Schema for workflow status response."""

    workflow_id: str = Field(..., description="ID of the workflow")
    status: str = Field(..., description="Current status of the workflow")
    results: Optional[Dict[str, Any]] = Field(
        None, description="Workflow results if completed"
    )
    execution_summary: Optional[Dict[str, Any]] = Field(
        None, description="Summary of workflow execution"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post(
    "/feature-request",
    response_model=FeatureRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_feature_request(
    request: FeatureRequestInput, 
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Submit a new feature request to the LangGraph workflow system.

    Args:
        request: Feature request details
        orchestrator: LangGraph Orchestrator instance for workflow submission

    Returns:
        Dict with workflow ID and status
    """
    logger.info(f"Received feature request: {request.description[:50]}...")
    logger.info(f"Using LangGraph orchestrator instance: {id(orchestrator)}")

    try:
        # Submit the feature request to the LangGraph orchestrator
        workflow_id = await orchestrator.submit_feature_request(request.description)

        # Log the workflow ID to help with debugging
        logger.info(f"Generated workflow_id: {workflow_id}")

        # Return the response
        return {"workflow_id": workflow_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Error submitting feature request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feature request",
        )


@router.get(
    "/workflow-status/{workflow_id}",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_workflow_status(
    workflow_id: str, 
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get the status of a workflow by its ID.

    Args:
        workflow_id: ID of the workflow to check
        orchestrator: LangGraph Orchestrator instance for status retrieval

    Returns:
        Dict with workflow status information
    """
    logger.info(f"Checking status for workflow: {workflow_id}")

    try:
        # Get workflow status from LangGraph orchestrator
        status_info = await orchestrator.get_workflow_status(workflow_id)

        if status_info.get("error"):
            if "not found" in status_info["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow with ID {workflow_id} not found",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=status_info["error"]
                )

        return status_info
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking workflow status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking workflow status",
        )


@router.post(
    "/execute-workflow",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_workflow(
    request: FeatureRequestInput,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Execute a complete workflow synchronously and return the final results.

    Args:
        request: Feature request details
        orchestrator: LangGraph Orchestrator instance for workflow execution

    Returns:
        Dict with complete workflow results
    """
    logger.info(f"Executing workflow synchronously: {request.description[:50]}...")

    try:
        # Generate a unique workflow ID
        workflow_id = str(uuid.uuid4())

        # Execute the complete workflow
        result = await orchestrator.execute_workflow(
            workflow_id=workflow_id,
            user_request=request.description
        )

        logger.info(f"Workflow {workflow_id} completed with status: {result['status']}")

        return result
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing workflow",
        )


@router.get(
    "/stream-workflow/{workflow_id}",
    status_code=status.HTTP_200_OK,
)
async def stream_workflow_execution(
    workflow_id: str,
    description: str,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
):
    """
    Stream workflow execution progress in real-time.

    Args:
        workflow_id: ID of the workflow to execute
        description: Feature request description
        orchestrator: LangGraph Orchestrator instance for streaming execution

    Returns:
        StreamingResponse with real-time workflow updates
    """
    logger.info(f"Starting streaming execution for workflow: {workflow_id}")

    async def generate():
        try:
            async for update in orchestrator.stream_workflow_execution(
                workflow_id=workflow_id,
                user_request=description
            ):
                import json
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming workflow: {str(e)}")
            import json
            error_update = {
                "workflow_id": workflow_id,
                "error": str(e),
                "status": "failed"
            }
            yield f"data: {json.dumps(error_update)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Legacy endpoint for backward compatibility
@router.get(
    "/task-status/{task_id}",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
)
async def get_task_status(
    task_id: str, 
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get the status of a task by its ID (legacy endpoint - redirects to workflow status).

    Args:
        task_id: ID of the task/workflow to check
        orchestrator: LangGraph Orchestrator instance for status retrieval

    Returns:
        Dict with workflow status information
    """
    logger.warning(f"Using deprecated task-status endpoint for ID: {task_id}")
    
    # Redirect to the new workflow status endpoint
    return await get_workflow_status(task_id, orchestrator)
