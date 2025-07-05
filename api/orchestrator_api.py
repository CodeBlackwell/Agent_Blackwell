"""
Orchestrator API - REST interface for the multi-agent orchestrator system
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput, CodingTeamResult, WorkflowType, StepType, TeamMemberResult
from workflows import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Check what execute_workflow we got
import inspect
logger.info(f"execute_workflow module: {execute_workflow.__module__}")
logger.info(f"execute_workflow signature: {inspect.signature(execute_workflow)}")

# Store workflow executions in memory (for MVP - replace with proper storage later)
workflow_executions: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Orchestrator API started successfully")
    yield
    # Cleanup
    logger.info("Orchestrator API shutting down")

# Create FastAPI app
app = FastAPI(
    title="Orchestrator API",
    description="REST API for the multi-agent orchestrator system",
    version="1.0.0",
    lifespan=lifespan
)

# Request/Response models
class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution"""
    requirements: str = Field(..., description="Project requirements to be implemented")
    workflow_type: WorkflowType = Field(..., description="Type of workflow to execute")
    step_type: Optional[StepType] = Field(None, description="Step type for individual workflows")
    max_retries: int = Field(3, description="Maximum number of retries")
    timeout_seconds: int = Field(300, description="Timeout in seconds")

class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    session_id: str = Field(..., description="Unique session ID for tracking")
    status: str = Field(..., description="Current status of the workflow")
    message: str = Field(..., description="Status message")

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""
    session_id: str
    status: str
    workflow_type: str
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None

class WorkflowTypeInfo(BaseModel):
    """Information about a workflow type"""
    name: str
    description: str
    requires_step_type: bool

# Helper functions
def format_agent_results(results: List[TeamMemberResult]) -> Dict[str, Any]:
    """Format agent results for API response"""
    formatted_results = []
    for result in results:
        formatted_results.append({
            "agent": result.name or result.team_member.value,
            "output_preview": result.output[:500] + "..." if len(result.output) > 500 else result.output,
            "output_length": len(result.output)
        })
    return formatted_results

async def execute_workflow_async(
    session_id: str,
    request: WorkflowExecutionRequest
):
    """Execute workflow asynchronously"""
    # Import execute_workflow locally to avoid potential naming conflicts
    from workflows import execute_workflow as wf_execute_workflow
    
    try:
        # Update status to running
        workflow_executions[session_id]["status"] = "running"
        workflow_executions[session_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        
        # Create input for orchestrator
        coding_input = CodingTeamInput(
            requirements=request.requirements,
            workflow_type=request.workflow_type.value,
            step_type=request.step_type.value if request.step_type else None,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds
        )
        
        # Create workflow execution tracer
        tracer = WorkflowExecutionTracer(
            workflow_type=request.workflow_type.value,
            execution_id=session_id
        )
        
        # Execute workflow
        logger.info(f"Starting workflow execution for session {session_id}")
        
        # Debug: Check execute_workflow before calling
        logger.info(f"About to call wf_execute_workflow: {wf_execute_workflow}")
        logger.info(f"Execute_workflow module: {wf_execute_workflow.__module__}")
        logger.info(f"Execute_workflow signature: {inspect.signature(wf_execute_workflow)}")
        
        # Execute the workflow with monitoring
        agent_results, execution_report = await wf_execute_workflow(coding_input, tracer=tracer)
        
        # Format results for storage
        workflow_executions[session_id]["result"] = {
            "agent_results": format_agent_results(agent_results),
            "agent_count": len(agent_results),
            "total_output_size": sum(len(r.output) for r in agent_results),
            "execution_report": execution_report.to_json() if execution_report else None
        }
        
        # Update progress from execution report
        if execution_report:
            workflow_executions[session_id]["progress"] = {
                "current_step": execution_report.completed_steps,
                "total_steps": execution_report.step_count,
                "status": "completed"
            }
        
        # Update status
        workflow_executions[session_id]["status"] = "completed"
        workflow_executions[session_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Workflow execution completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error executing workflow for session {session_id}: {str(e)}")
        workflow_executions[session_id]["status"] = "failed"
        workflow_executions[session_id]["error"] = str(e)
        workflow_executions[session_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Orchestrator API is running",
        "version": "1.0.0",
        "endpoints": [
            "/docs",
            "/health",
            "/workflow-types",
            "/execute-workflow",
            "/workflow-status/{session_id}"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflows_available": True
    }

@app.get("/workflow-types", response_model=List[WorkflowTypeInfo])
async def get_workflow_types():
    """Get available workflow types"""
    return [
        WorkflowTypeInfo(
            name="tdd",
            description="Test-Driven Development workflow: Planning → Design → Test Writing → Implementation → Execution → Review",
            requires_step_type=False
        ),
        WorkflowTypeInfo(
            name="full",
            description="Full workflow: Planning → Design → Implementation → Review",
            requires_step_type=False
        ),
        WorkflowTypeInfo(
            name="individual",
            description="Execute individual workflow steps",
            requires_step_type=True
        )
    ]

@app.post("/execute-workflow", response_model=WorkflowExecutionResponse)
async def execute_workflow_endpoint(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute a workflow asynchronously"""
    # Validate request
    if request.workflow_type == WorkflowType.INDIVIDUAL and not request.step_type:
        raise HTTPException(
            status_code=400,
            detail="step_type is required for individual workflows"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Initialize execution record
    workflow_executions[session_id] = {
        "session_id": session_id,
        "status": "pending",
        "workflow_type": request.workflow_type.value,
        "requirements": request.requirements,
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
        "progress": None
    }
    
    # Add to background tasks
    background_tasks.add_task(
        execute_workflow_async,
        session_id,
        request
    )
    
    return WorkflowExecutionResponse(
        session_id=session_id,
        status="pending",
        message=f"Workflow execution started. Track progress at /workflow-status/{session_id}"
    )

@app.get("/workflow-status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(session_id: str):
    """Get the status of a workflow execution"""
    if session_id not in workflow_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow execution with session_id {session_id} not found"
        )
    
    execution = workflow_executions[session_id]
    
    return WorkflowStatusResponse(**execution)

@app.delete("/workflow-status/{session_id}")
async def delete_workflow_execution(session_id: str):
    """Delete a workflow execution record"""
    if session_id not in workflow_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow execution with session_id {session_id} not found"
        )
    
    del workflow_executions[session_id]
    
    return {
        "message": f"Workflow execution {session_id} deleted successfully"
    }

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)