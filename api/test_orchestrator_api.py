"""
Tests for the Orchestrator API
"""

import asyncio
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.orchestrator_api import app, workflow_executions
from shared.data_models import CodingTeamResult, WorkflowType, StepType

# Create test client
client = TestClient(app)

class TestOrchestratorAPI:
    """Test suite for Orchestrator API"""
    
    def setup_method(self):
        """Setup before each test"""
        # Clear workflow executions
        workflow_executions.clear()
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert len(data["endpoints"]) > 0
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "orchestrator_initialized" in data
    
    def test_workflow_types_endpoint(self):
        """Test workflow types endpoint"""
        response = client.get("/workflow-types")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check workflow types
        workflow_names = [w["name"] for w in data]
        assert "tdd" in workflow_names
        assert "full" in workflow_names
        assert "individual" in workflow_names
        
        # Check individual workflow requires step_type
        individual = next(w for w in data if w["name"] == "individual")
        assert individual["requires_step_type"] is True
    
    def test_execute_workflow_success(self):
        """Test successful workflow execution"""
        request_data = {
            "requirements": "Create a simple hello world function",
            "workflow_type": "full",
            "max_retries": 3,
            "timeout_seconds": 60
        }
        
        response = client.post("/execute-workflow", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        # Check execution was recorded
        session_id = data["session_id"]
        assert session_id in workflow_executions
        assert workflow_executions[session_id]["status"] == "pending"
    
    def test_execute_workflow_individual_without_step_type(self):
        """Test individual workflow without step_type should fail"""
        request_data = {
            "requirements": "Create a simple hello world function",
            "workflow_type": "individual",
            "max_retries": 3,
            "timeout_seconds": 60
        }
        
        response = client.post("/execute-workflow", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "step_type is required" in data["detail"]
    
    def test_execute_workflow_individual_with_step_type(self):
        """Test individual workflow with step_type"""
        request_data = {
            "requirements": "Create a simple hello world function",
            "workflow_type": "individual",
            "step_type": "planning",
            "max_retries": 3,
            "timeout_seconds": 60
        }
        
        response = client.post("/execute-workflow", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "pending"
    
    def test_workflow_status_exists(self):
        """Test getting workflow status for existing execution"""
        # Create a mock execution
        session_id = "test-session-123"
        workflow_executions[session_id] = {
            "session_id": session_id,
            "status": "running",
            "workflow_type": "full",
            "requirements": "Test requirements",
            "started_at": "2024-01-01T00:00:00",
            "completed_at": None,
            "result": None,
            "error": None,
            "progress": {
                "current_step": 2,
                "total_steps": 4,
                "status": "Processing"
            }
        }
        
        response = client.get(f"/workflow-status/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert data["status"] == "running"
        assert data["workflow_type"] == "full"
        assert data["progress"]["current_step"] == 2
    
    def test_workflow_status_not_found(self):
        """Test getting workflow status for non-existent execution"""
        response = client.get("/workflow-status/non-existent-id")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_delete_workflow_execution(self):
        """Test deleting workflow execution"""
        # Create a mock execution
        session_id = "test-session-456"
        workflow_executions[session_id] = {
            "session_id": session_id,
            "status": "completed"
        }
        
        # Delete it
        response = client.delete(f"/workflow-status/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify it's gone
        assert session_id not in workflow_executions
    
    def test_delete_workflow_execution_not_found(self):
        """Test deleting non-existent workflow execution"""
        response = client.delete("/workflow-status/non-existent-id")
        assert response.status_code == 404

@pytest.mark.asyncio
class TestAsyncWorkflowExecution:
    """Test async workflow execution"""
    
    @patch('api.orchestrator_api.orchestrator_tool')
    async def test_execute_workflow_async_success(self, mock_tool):
        """Test successful async workflow execution"""
        from api.orchestrator_api import execute_workflow_async, WorkflowExecutionRequest
        
        # Setup mock
        mock_result = Mock()
        mock_result.dict.return_value = {"success": True, "code": "print('hello')"}
        mock_result.progress_report = Mock(
            current_step=4,
            total_steps=4,
            status="Completed"
        )
        
        async def mock_run(*args, **kwargs):
            yield mock_result
        
        mock_tool.run = mock_run
        
        # Create request
        session_id = "test-async-123"
        workflow_executions[session_id] = {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "progress": None
        }
        
        request = WorkflowExecutionRequest(
            requirements="Create hello world",
            workflow_type=WorkflowType.FULL,
            max_retries=3,
            timeout_seconds=60
        )
        
        # Execute
        await execute_workflow_async(session_id, request)
        
        # Check results
        assert workflow_executions[session_id]["status"] == "completed"
        assert workflow_executions[session_id]["started_at"] is not None
        assert workflow_executions[session_id]["completed_at"] is not None
        assert workflow_executions[session_id]["result"] is not None
        assert workflow_executions[session_id]["error"] is None
    
    @patch('api.orchestrator_api.orchestrator_tool')
    async def test_execute_workflow_async_failure(self, mock_tool):
        """Test failed async workflow execution"""
        from api.orchestrator_api import execute_workflow_async, WorkflowExecutionRequest
        
        # Setup mock to raise exception
        async def mock_run(*args, **kwargs):
            raise Exception("Workflow failed")
            yield  # This won't be reached
        
        mock_tool.run = mock_run
        
        # Create request
        session_id = "test-async-456"
        workflow_executions[session_id] = {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "progress": None
        }
        
        request = WorkflowExecutionRequest(
            requirements="Create hello world",
            workflow_type=WorkflowType.FULL,
            max_retries=3,
            timeout_seconds=60
        )
        
        # Execute
        await execute_workflow_async(session_id, request)
        
        # Check results
        assert workflow_executions[session_id]["status"] == "failed"
        assert workflow_executions[session_id]["error"] == "Workflow failed"
        assert workflow_executions[session_id]["completed_at"] is not None

def test_api_validation():
    """Test API request validation"""
    # Test invalid workflow type
    request_data = {
        "requirements": "Create a function",
        "workflow_type": "invalid_type",
        "max_retries": 3,
        "timeout_seconds": 60
    }
    
    response = client.post("/execute-workflow", json=request_data)
    assert response.status_code == 422  # Validation error
    
    # Test missing required field
    request_data = {
        "workflow_type": "full",
        "max_retries": 3,
        "timeout_seconds": 60
    }
    
    response = client.post("/execute-workflow", json=request_data)
    assert response.status_code == 422  # Validation error

def test_concurrent_workflow_executions():
    """Test handling multiple concurrent workflow executions"""
    # Start multiple workflows
    session_ids = []
    for i in range(5):
        request_data = {
            "requirements": f"Create function {i}",
            "workflow_type": "full",
            "max_retries": 3,
            "timeout_seconds": 60
        }
        
        response = client.post("/execute-workflow", json=request_data)
        assert response.status_code == 200
        session_ids.append(response.json()["session_id"])
    
    # Check all executions were recorded
    assert len(workflow_executions) == 5
    for session_id in session_ids:
        assert session_id in workflow_executions

if __name__ == "__main__":
    pytest.main([__file__, "-v"])