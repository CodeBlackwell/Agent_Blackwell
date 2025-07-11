#!/usr/bin/env python3
"""Flagship TDD Orchestrator Server - Custom server for RED-YELLOW-GREEN workflow"""

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
from configs.flagship_config import get_config
from models.flagship_models import TDDPhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Flagship TDD Orchestrator",
    description="Custom server for RED-YELLOW-GREEN TDD workflow",
    version="1.0.0"
)

# Global workflow storage (in-memory for MVP)
workflows: Dict[str, Dict[str, Any]] = {}


class TDDRequest(BaseModel):
    """Request model for TDD workflow"""
    requirements: str
    config_type: str = "default"  # "quick", "default", "comprehensive"
    session_id: Optional[str] = None
    stream_output: bool = True


class TDDResponse(BaseModel):
    """Response model for TDD workflow"""
    session_id: str
    status: str
    message: str
    phase: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "Flagship TDD Orchestrator Server",
        "version": "1.0.0",
        "description": "RED-YELLOW-GREEN TDD workflow automation",
        "endpoints": {
            "/tdd/start": "Start a new TDD workflow",
            "/tdd/status/{session_id}": "Get workflow status",
            "/tdd/stream/{session_id}": "Stream workflow output",
            "/workflows": "List all workflows",
            "/health": "Health check"
        }
    }


@app.post("/tdd/start", response_model=TDDResponse)
async def start_tdd_workflow(request: TDDRequest, background_tasks: BackgroundTasks):
    """Start a new TDD workflow"""
    # Generate session ID if not provided
    session_id = request.session_id or f"tdd_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Initialize workflow info
    workflows[session_id] = {
        "status": "starting",
        "phase": TDDPhase.RED.value,
        "requirements": request.requirements,
        "config_type": request.config_type,
        "start_time": datetime.now().isoformat(),
        "output": [],
        "results": None,
        "error": None
    }
    
    # Start workflow in background
    background_tasks.add_task(
        run_workflow_async,
        session_id,
        request.requirements,
        request.config_type
    )
    
    return TDDResponse(
        session_id=session_id,
        status="started",
        message=f"TDD workflow started with config: {request.config_type}",
        phase=TDDPhase.RED.value
    )


async def run_workflow_async(session_id: str, requirements: str, config_type: str):
    """Run TDD workflow asynchronously"""
    try:
        # Update status
        workflows[session_id]["status"] = "running"
        
        # Get configuration
        config = get_config(config_type)
        
        # Create custom output handler to capture streaming output
        output_buffer = []
        
        # Save original stdout before redirecting
        original_stdout = sys.stdout
        
        class StreamCapture:
            def __init__(self, original):
                self.original = original
                
            def write(self, text):
                output_buffer.append({
                    "timestamp": datetime.now().isoformat(),
                    "text": text
                })
                workflows[session_id]["output"] = output_buffer
                # Also print to console using original stdout
                self.original.write(text)
                self.original.flush()
            
            def flush(self):
                self.original.flush()
                
            def fileno(self):
                return self.original.fileno()
                
            def isatty(self):
                return self.original.isatty()
        
        # Redirect output
        sys.stdout = StreamCapture(original_stdout)
        
        try:
            # Create and run orchestrator
            orchestrator = FlagshipOrchestrator(config, session_id=session_id)
            state = await orchestrator.run_tdd_workflow(requirements)
            
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
            
            # Save workflow state (uses file manager's session directory)
            orchestrator.save_workflow_state()
            
        finally:
            # Restore stdout
            sys.stdout = original_stdout
            
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Workflow {session_id} failed: {error_msg}")
        workflows[session_id].update({
            "status": "failed",
            "error": str(e),
            "error_traceback": traceback.format_exc(),
            "end_time": datetime.now().isoformat()
        })


@app.get("/tdd/status/{session_id}", response_model=TDDResponse)
async def get_workflow_status(session_id: str):
    """Get the status of a TDD workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[session_id]
    return TDDResponse(
        session_id=session_id,
        status=workflow["status"],
        message=f"Workflow is {workflow['status']}",
        phase=workflow.get("phase"),
        results=workflow.get("results")
    )


@app.get("/tdd/stream/{session_id}")
async def stream_workflow_output(session_id: str):
    """Stream the output of a running workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    async def generate():
        last_index = 0
        while True:
            workflow = workflows.get(session_id)
            if not workflow:
                break
            
            # Send new output lines
            output = workflow.get("output", [])
            for i in range(last_index, len(output)):
                yield json.dumps(output[i]) + "\n"
            last_index = len(output)
            
            # Check if completed
            if workflow["status"] in ["completed", "failed"]:
                # Send final status
                yield json.dumps({
                    "type": "status",
                    "status": workflow["status"],
                    "results": workflow.get("results")
                }) + "\n"
                break
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/workflows")
async def list_workflows():
    """List all workflows"""
    return {
        "total": len(workflows),
        "workflows": [
            {
                "session_id": sid,
                "status": w["status"],
                "phase": w.get("phase"),
                "requirements": w["requirements"][:100] + "..." if len(w["requirements"]) > 100 else w["requirements"],
                "start_time": w["start_time"],
                "config_type": w["config_type"]
            }
            for sid, w in workflows.items()
        ]
    }


@app.delete("/workflows/{session_id}")
async def delete_workflow(session_id: str):
    """Delete a workflow from memory"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows[session_id]
    return {"message": f"Workflow {session_id} deleted"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_workflows": len([w for w in workflows.values() if w["status"] == "running"])
    }


@app.get("/phases")
async def get_tdd_phases():
    """Get information about TDD phases"""
    return {
        "phases": [
            {
                "name": "RED",
                "description": "Write failing tests based on requirements",
                "emoji": "🔴"
            },
            {
                "name": "YELLOW", 
                "description": "Write minimal code to make tests pass",
                "emoji": "🟡"
            },
            {
                "name": "GREEN",
                "description": "Run tests and verify they all pass",
                "emoji": "🟢"
            }
        ],
        "flow": "RED → YELLOW → GREEN → (repeat if needed)"
    }


@app.get("/debug/{session_id}")
async def get_debug_info(session_id: str):
    """Get debug information for a workflow"""
    if session_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows[session_id]


def kill_process_on_port(port: int):
    """Kill any process using the specified port"""
    try:
        if platform.system() == "Windows":
            # Windows command to find and kill process
            cmd = f"netstat -ano | findstr :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        try:
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=False)
                            print(f"✅ Killed process {pid} using port {port}")
                        except:
                            pass
        else:
            # Unix-like systems (Linux, macOS)
            # First try lsof
            try:
                cmd = f"lsof -ti:{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            try:
                                os.kill(int(pid), signal.SIGTERM)
                                print(f"✅ Killed process {pid} using port {port}")
                                # Give it a moment to terminate
                                time.sleep(0.5)
                                # Force kill if still running
                                try:
                                    os.kill(int(pid), signal.SIGKILL)
                                except ProcessLookupError:
                                    pass  # Already dead
                            except Exception as e:
                                print(f"⚠️  Could not kill process {pid}: {e}")
            except subprocess.CalledProcessError:
                # If lsof fails, try netstat
                cmd = f"netstat -tlnp 2>/dev/null | grep :{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    # Extract PID from netstat output
                    import re
                    match = re.search(r'(\d+)/', result.stdout)
                    if match:
                        pid = match.group(1)
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"✅ Killed process {pid} using port {port}")
                        except:
                            pass
                            
    except Exception as e:
        print(f"⚠️  Error checking/killing process on port {port}: {e}")


def check_port_availability(port: int) -> bool:
    """Check if a port is available"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False


def main():
    """Main entry point"""
    import time
    
    PORT = 8100
    
    print("🚀 Starting Flagship TDD Orchestrator Server")
    print("=" * 80)
    
    # Check if port is in use
    if not check_port_availability(PORT):
        print(f"⚠️  Port {PORT} is already in use. Attempting to free it...")
        kill_process_on_port(PORT)
        time.sleep(1)  # Give the OS time to release the port
        
        # Check again
        if not check_port_availability(PORT):
            print(f"❌ Failed to free port {PORT}. Please manually stop the process.")
            sys.exit(1)
    
    print(f"✅ Port {PORT} is available")
    print(f"Server running at: http://localhost:{PORT}")
    print(f"API docs at: http://localhost:{PORT}/docs")
    print("=" * 80)
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()