"""Simplified Flagship TDD Orchestrator Server - No stdout redirection"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from flagship_orchestrator import FlagshipOrchestrator
from models.flagship_models import TDDWorkflowConfig, TDDPhase
from configs.flagship_config import get_config


# Request/Response Models
class TDDRequest(BaseModel):
    requirements: str
    config_type: str = "default"
    stream_output: bool = True


class TDDResponse(BaseModel):
    session_id: str
    status: str
    message: str
    phase: str = TDDPhase.RED.value


# Global workflow storage (in production, use Redis/database)
workflows: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n🚀 Starting Flagship TDD Orchestrator Server (Simple Mode)")
    print("=" * 80)
    print("Server running at: http://localhost:8100")
    print("API docs at: http://localhost:8100/docs")
    print("=" * 80 + "\n")
    yield
    # Shutdown
    print("\nShutting down Flagship TDD Orchestrator Server")


# Create FastAPI app
app = FastAPI(
    title="Flagship TDD Orchestrator",
    description="Simple TDD workflow orchestrator without stdout redirection",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "service": "Flagship TDD Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "start_workflow": "/tdd/start",
            "get_status": "/tdd/status/{session_id}",
            "stream_output": "/tdd/stream/{session_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/tdd/start", response_model=TDDResponse)
async def start_tdd_workflow(request: TDDRequest):
    """Start a new TDD workflow"""
    # Generate session ID
    session_id = f"tdd_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Store workflow info
    workflows[session_id] = {
        "status": "starting",
        "requirements": request.requirements,
        "config_type": request.config_type,
        "start_time": datetime.now().isoformat(),
        "output": [],
        "results": None
    }
    
    # Start async workflow
    asyncio.create_task(
        run_workflow_simple(session_id, request.requirements, request.config_type)
    )
    
    return TDDResponse(
        session_id=session_id,
        status="started",
        message=f"TDD workflow started with config: {request.config_type}",
        phase=TDDPhase.RED.value
    )


async def run_workflow_simple(session_id: str, requirements: str, config_type: str):
    """Run TDD workflow without stdout redirection"""
    try:
        # Update status
        workflows[session_id]["status"] = "running"
        
        # Get configuration
        config = get_config(config_type)
        
        # Create and run orchestrator
        orchestrator = FlagshipOrchestrator(config, session_id=session_id)
        
        # Capture output by collecting from workflow
        output_buffer = []
        workflows[session_id]["output"] = output_buffer
        
        # Note: In simple mode, we don't capture print statements
        # The workflow will print to console directly
        state = await orchestrator.run_tdd_workflow(requirements)
        
        # Save generated files
        orchestrator.save_workflow_state()
        
        # Update workflow info with results
        workflows[session_id].update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "results": {
                "all_tests_passing": state.all_tests_passing,
                "iterations": state.iteration_count,
                "test_summary": state.get_test_summary(),
                "duration": (state.end_time - state.start_time).total_seconds() if state.end_time else 0,
                "generated_tests": len(state.generated_tests),
                "generated_code": len(state.generated_code)
            }
        })
        
        # Add completion message to output
        output_buffer.append({
            "timestamp": datetime.now().isoformat(),
            "text": f"\n✅ Workflow completed. All tests passing: {state.all_tests_passing}\n"
        })
        
    except Exception as e:
        import traceback
        error_msg = f"Workflow {session_id} failed: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_msg}")
        
        workflows[session_id].update({
            "status": "failed",
            "end_time": datetime.now().isoformat(),
            "error": str(e),
            "results": None
        })
        
        workflows[session_id]["output"].append({
            "timestamp": datetime.now().isoformat(),
            "text": f"\n❌ ERROR: {str(e)}\n"
        })


@app.get("/tdd/status/{session_id}")
async def get_workflow_status(session_id: str):
    """Get the status of a workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[session_id]
    return {
        "session_id": session_id,
        "status": workflow["status"],
        "requirements": workflow["requirements"],
        "start_time": workflow["start_time"],
        "end_time": workflow.get("end_time"),
        "results": workflow.get("results"),
        "error": workflow.get("error")
    }


@app.get("/tdd/stream/{session_id}")
async def stream_workflow_output(session_id: str):
    """Stream the output of a running workflow (simplified)"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    async def generate():
        # In simple mode, just send a status update
        workflow = workflows.get(session_id)
        
        # Send initial message
        yield json.dumps({
            "timestamp": datetime.now().isoformat(),
            "text": f"Workflow {session_id} is running in simple mode.\n"
        }) + "\n"
        
        # Wait for completion
        while workflow and workflow["status"] == "running":
            await asyncio.sleep(1)
            workflow = workflows.get(session_id)
        
        # Send final status
        if workflow:
            yield json.dumps({
                "type": "status",
                "status": workflow["status"],
                "results": workflow.get("results")
            }) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


def main():
    """Run the server"""
    uvicorn.run(app, host="0.0.0.0", port=8100)


if __name__ == "__main__":
    main()