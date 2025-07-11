#!/usr/bin/env python3
"""Flagship TDD Orchestrator Server with Proper Streaming"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os
import signal
import subprocess
import platform

# FastAPI for the server
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flagship_orchestrator import FlagshipOrchestrator
from flagship_streaming import StreamingOrchestrator, StreamBuffer, create_streaming_generator
from configs.flagship_config import get_config
from models.flagship_models import TDDPhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Flagship TDD Orchestrator", version="1.0.0")

# Store active workflows
workflows: Dict[str, Dict[str, Any]] = {}
stream_buffers: Dict[str, StreamBuffer] = {}


class TDDRequest(BaseModel):
    """Request model for TDD workflow"""
    requirements: str
    config_name: Optional[str] = "default"


class TDDResponse(BaseModel):
    """Response model for TDD workflow"""
    session_id: str
    status: str
    phase: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Flagship TDD Orchestrator",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/tdd/start", response_model=TDDResponse)
async def start_tdd_workflow(request: TDDRequest, background_tasks: BackgroundTasks):
    """Start a new TDD workflow"""
    # Generate session ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    session_id = f"tdd_{timestamp}"
    
    # Create workflow entry
    workflows[session_id] = {
        "session_id": session_id,
        "status": "running",
        "phase": "INIT",
        "requirements": request.requirements,
        "config_name": request.config_name,
        "start_time": datetime.now().isoformat(),
        "output": [],
        "results": None,
        "error": None
    }
    
    # Create stream buffer
    stream_buffers[session_id] = StreamBuffer()
    
    # Start workflow in background
    background_tasks.add_task(run_workflow, session_id, request.requirements, request.config_name)
    
    return TDDResponse(
        session_id=session_id,
        status="running",
        phase="INIT"
    )


async def run_workflow(session_id: str, requirements: str, config_name: str):
    """Run a TDD workflow with streaming support"""
    print(f"\n{'='*80}")
    print(f"🚀 Starting TDD Workflow")
    print(f"{'='*80}\n")
    print(f"Requirements: {requirements}\n")
    
    try:
        # Get config
        config = get_config(config_name)
        
        # Create base orchestrator
        base_orchestrator = FlagshipOrchestrator(config, session_id=session_id)
        
        # Wrap with streaming orchestrator
        streaming_orchestrator = StreamingOrchestrator(base_orchestrator)
        streaming_orchestrator.buffer = stream_buffers[session_id]
        
        # Run workflow
        state = await streaming_orchestrator.run_tdd_workflow(requirements)
        
        # Update workflow info with results
        workflows[session_id].update({
            "status": "completed",
            "phase": state.current_phase.value,
            "results": {
                "all_tests_passing": state.all_tests_passing,
                "iterations": state.iteration_count,
                "test_summary": state.get_test_summary(),
                "duration": (state.end_time - state.start_time).total_seconds() if state.end_time else 0,
                "generated_tests": len(state.generated_tests),
                "generated_code": len(state.generated_code)
            },
            "end_time": datetime.now().isoformat()
        })
        
        # Save workflow state
        base_orchestrator.save_workflow_state()
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Workflow {session_id} failed: {error_msg}")
        
        # Update workflow with error
        workflows[session_id].update({
            "status": "failed",
            "error": str(e),
            "error_traceback": traceback.format_exc(),
            "end_time": datetime.now().isoformat()
        })
        
        # Add error to stream
        if session_id in stream_buffers:
            await stream_buffers[session_id].add_text(
                f"\n❌ ERROR: {str(e)}\n",
                "error"
            )


@app.get("/tdd/status/{session_id}", response_model=TDDResponse)
async def get_workflow_status(session_id: str):
    """Get the status of a TDD workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[session_id]
    return TDDResponse(
        session_id=session_id,
        status=workflow["status"],
        phase=workflow.get("phase"),
        results=workflow.get("results"),
        error=workflow.get("error")
    )


@app.get("/tdd/stream/{session_id}")
async def stream_workflow_output(session_id: str):
    """Stream the output of a running workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if session_id not in stream_buffers:
        raise HTTPException(status_code=400, detail="Streaming not available for this workflow")
    
    buffer = stream_buffers[session_id]
    
    async def generate():
        async for chunk in create_streaming_generator(buffer, session_id, workflows):
            yield chunk
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


def cleanup():
    """Cleanup function to kill any orphaned processes"""
    if platform.system() == "Darwin":  # macOS
        # Find and kill any Python processes running flagship_server
        try:
            result = subprocess.run(
                ["pgrep", "-f", "flagship_server"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid and pid != str(os.getpid()):
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                        except ProcessLookupError:
                            pass
        except Exception:
            pass


def main():
    """Run the server"""
    print("\n🚀 Starting Flagship TDD Orchestrator Server (Streaming Mode)")
    print("="*80)
    print(f"Server running at: http://localhost:8100")
    print(f"API docs at: http://localhost:8100/docs")
    print("="*80 + "\n")
    
    # Cleanup any orphaned processes
    cleanup()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8100)


if __name__ == "__main__":
    main()