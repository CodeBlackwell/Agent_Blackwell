"""
Job Management API router.

This module implements the FastAPI router for job-oriented functionality, providing
REST endpoints for creating, querying, and managing jobs and tasks in the Agent Blackwell system.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from src.api.dependencies import get_orchestrator
from src.api.v1.chatops.models import (
    JobCreationRequest,
    JobCreationResponse,
    JobListResponse,
    JobStatus,
    JobStatusResponse,
    TaskStatus,
    TaskStatusResponse,
)
from src.orchestrator.main import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("/", response_model=JobCreationResponse)
async def create_job(
    request: JobCreationRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> JobCreationResponse:
    """
    Create a new job from a user request.

    This endpoint creates a new job that will be processed through the orchestrator's
    job-oriented workflow. The job will start in PLANNING status and progress through
    the various stages automatically.
    """
    logger.info(f"Creating new job for request: {request.user_request[:100]}...")

    try:
        # Create the job using the orchestrator
        job = await orchestrator.create_job(request.user_request)

        logger.info(f"Successfully created job {job.job_id} with status {job.status}")

        return JobCreationResponse(
            job_id=job.job_id,
            status=job.status,
            message="Job created successfully and planning has started",
            created_at=job.created_at,
            status_endpoint=f"/api/v1/jobs/{job.job_id}",
        )

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> JobStatusResponse:
    """
    Get the status and details of a specific job.

    This endpoint returns comprehensive information about a job including its current
    status, associated tasks, progress, and timestamps.
    """
    logger.info(f"Getting status for job {job_id}")

    try:
        # Retrieve the job from the orchestrator
        job = await orchestrator.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        # Calculate progress information
        total_tasks = len(job.tasks)
        completed_tasks = len(
            [t for t in job.tasks if t.status == TaskStatus.COMPLETED]
        )
        failed_tasks = len([t for t in job.tasks if t.status == TaskStatus.FAILED])
        running_tasks = len([t for t in job.tasks if t.status == TaskStatus.RUNNING])

        progress = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
        }

        return JobStatusResponse(
            job_id=job.job_id,
            user_request=job.user_request,
            status=job.status,
            tasks=job.tasks,
            created_at=job.created_at,
            updated_at=job.updated_at,
            progress=progress,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter jobs by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of jobs per page"),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> JobListResponse:
    """
    List jobs with optional filtering and pagination.

    This endpoint returns a paginated list of jobs, optionally filtered by status.
    """
    logger.info(
        f"Listing jobs - status: {status}, page: {page}, page_size: {page_size}"
    )

    try:
        # Get jobs from orchestrator (this would need to be implemented in orchestrator)
        # For now, we'll implement a basic version
        jobs = []
        total = 0

        # Note: This is a placeholder implementation
        # The orchestrator would need a list_jobs method to be fully functional
        logger.warning(
            "list_jobs endpoint is not fully implemented - orchestrator needs list_jobs method"
        )

        return JobListResponse(jobs=jobs, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        )


@router.get("/{job_id}/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    job_id: str,
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TaskStatusResponse:
    """
    Get the status and details of a specific task within a job.

    This endpoint returns detailed information about a task including its status,
    dependencies, results, and timestamps.
    """
    logger.info(f"Getting status for task {task_id} in job {job_id}")

    try:
        # First verify the job exists
        job = await orchestrator.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        # Find the specific task
        task = None
        for t in job.tasks:
            if t.task_id == task_id:
                task = t
                break

        if not task:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found in job {job_id}",
            )

        return TaskStatusResponse(
            task_id=task.task_id,
            job_id=task.job_id,
            agent_type=task.agent_type,
            status=task.status,
            description=task.description,
            dependencies=task.dependencies,
            result=task.result,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> dict:
    """
    Cancel a job and all its pending/running tasks.

    This endpoint attempts to cancel a job by stopping all pending and running tasks.
    Already completed tasks will remain completed.
    """
    logger.info(f"Canceling job {job_id}")

    try:
        # Get the job first
        job = await orchestrator.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        # Check if job can be canceled
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]:
            return {
                "message": f"Job {job_id} is already in final state ({job.status}) and cannot be canceled",
                "job_id": job_id,
                "status": job.status,
            }

        # Note: This would need to be implemented in the orchestrator
        # For now, we'll return a placeholder response
        logger.warning(
            "cancel_job endpoint is not fully implemented - orchestrator needs cancel_job method"
        )

        return {
            "message": f"Job cancellation requested for {job_id}",
            "job_id": job_id,
            "status": "cancellation_requested",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling job: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        )
