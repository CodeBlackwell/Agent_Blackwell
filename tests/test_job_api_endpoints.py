"""
Integration tests for Job Management API endpoints.

This module tests the REST API endpoints for job and task management,
ensuring proper integration with the orchestrator and correct response formats.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.v1.jobs.router import router as jobs_router
from src.api.v1.chatops.models import (
    Job,
    Task,
    JobStatus,
    TaskStatus,
    JobCreationRequest,
)
from src.orchestrator.main import Orchestrator


class MockOrchestrator:
    """Mock orchestrator for testing API endpoints."""
    
    def __init__(self):
        self.jobs = {}
        self.tasks = {}
    
    async def create_job(self, user_request: str) -> Job:
        """Mock job creation."""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            user_request=user_request,
            status=JobStatus.PLANNING,
            tasks=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.jobs[job_id] = job
        return job
    
    async def get_job(self, job_id: str) -> Job:
        """Mock job retrieval."""
        return self.jobs.get(job_id)
    
    def reset_state(self):
        """Reset mock state for test isolation."""
        self.jobs.clear()
        self.tasks.clear()


@pytest.fixture
def mock_orchestrator():
    """Fixture providing a mock orchestrator."""
    return MockOrchestrator()


@pytest.fixture
def test_app(mock_orchestrator):
    """Fixture providing a test FastAPI app with job router."""
    app = FastAPI()
    app.include_router(jobs_router)
    
    # Override the orchestrator dependency
    from src.api.dependencies import get_orchestrator
    
    def get_test_orchestrator():
        return mock_orchestrator
    
    app.dependency_overrides[get_orchestrator] = get_test_orchestrator
    
    return app


@pytest.fixture
def client(test_app):
    """Fixture providing a test client."""
    return TestClient(test_app)


class TestJobCreationEndpoint:
    """Test cases for job creation endpoint."""
    
    def test_create_job_success(self, client, mock_orchestrator):
        """Test successful job creation."""
        request_data = {
            "user_request": "Create a new feature for user authentication",
            "priority": "high",
            "tags": ["auth", "security"],
            "context": {"team": "backend"}
        }
        
        response = client.post("/api/v1/jobs/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "job_id" in data
        assert data["status"] == "planning"
        assert data["message"] == "Job created successfully and planning has started"
        assert "created_at" in data
        assert "status_endpoint" in data
        assert data["status_endpoint"].startswith("/api/v1/jobs/")
        
        # Verify job was created in mock orchestrator
        job_id = data["job_id"]
        assert job_id in mock_orchestrator.jobs
        created_job = mock_orchestrator.jobs[job_id]
        assert created_job.user_request == request_data["user_request"]
        assert created_job.status == JobStatus.PLANNING
    
    def test_create_job_minimal_request(self, client, mock_orchestrator):
        """Test job creation with minimal required fields."""
        request_data = {
            "user_request": "Simple test request"
        }
        
        response = client.post("/api/v1/jobs/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "planning"
    
    def test_create_job_missing_user_request(self, client):
        """Test job creation with missing required field."""
        request_data = {
            "priority": "high"
        }
        
        response = client.post("/api/v1/jobs/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_job_orchestrator_error(self, client, mock_orchestrator):
        """Test job creation when orchestrator raises an error."""
        # Mock orchestrator to raise an exception
        async def failing_create_job(user_request):
            raise Exception("Orchestrator error")
        
        mock_orchestrator.create_job = failing_create_job
        
        request_data = {
            "user_request": "Test request"
        }
        
        response = client.post("/api/v1/jobs/", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create job" in data["detail"]


class TestJobStatusEndpoint:
    """Test cases for job status endpoint."""
    
    def test_get_job_status_success(self, client, mock_orchestrator):
        """Test successful job status retrieval."""
        # Create a job with tasks
        job_id = str(uuid.uuid4())
        task1 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="spec",
            status=TaskStatus.COMPLETED,
            description="Spec task",
            dependencies=[],
            result={"spec": "completed"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        task2 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="design",
            status=TaskStatus.RUNNING,
            description="Design task",
            dependencies=[task1.task_id],
            result=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        job = Job(
            job_id=job_id,
            user_request="Test job with tasks",
            status=JobStatus.RUNNING,
            tasks=[task1, task2],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_orchestrator.jobs[job_id] = job
        
        response = client.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["job_id"] == job_id
        assert data["user_request"] == "Test job with tasks"
        assert data["status"] == "running"
        assert len(data["tasks"]) == 2
        assert "created_at" in data
        assert "updated_at" in data
        assert "progress" in data
        
        # Verify progress calculation
        progress = data["progress"]
        assert progress["total_tasks"] == 2
        assert progress["completed_tasks"] == 1
        assert progress["failed_tasks"] == 0
        assert progress["running_tasks"] == 1
        assert progress["completion_percentage"] == 50.0
    
    def test_get_job_status_not_found(self, client, mock_orchestrator):
        """Test job status retrieval for non-existent job."""
        non_existent_job_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/jobs/{non_existent_job_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert f"Job {non_existent_job_id} not found" in data["detail"]
    
    def test_get_job_status_orchestrator_error(self, client, mock_orchestrator):
        """Test job status retrieval when orchestrator raises an error."""
        job_id = str(uuid.uuid4())
        
        # Mock orchestrator to raise an exception
        async def failing_get_job(job_id):
            raise Exception("Database error")
        
        mock_orchestrator.get_job = failing_get_job
        
        response = client.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get job status" in data["detail"]


class TestTaskStatusEndpoint:
    """Test cases for task status endpoint."""
    
    def test_get_task_status_success(self, client, mock_orchestrator):
        """Test successful task status retrieval."""
        job_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            job_id=job_id,
            agent_type="code",
            status=TaskStatus.COMPLETED,
            description="Code generation task",
            dependencies=[],
            result={"code": "generated successfully"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        job = Job(
            job_id=job_id,
            user_request="Test job",
            status=JobStatus.RUNNING,
            tasks=[task],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_orchestrator.jobs[job_id] = job
        
        response = client.get(f"/api/v1/jobs/{job_id}/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["task_id"] == task_id
        assert data["job_id"] == job_id
        assert data["agent_type"] == "code"
        assert data["status"] == "completed"
        assert data["description"] == "Code generation task"
        assert data["dependencies"] == []
        assert data["result"] == {"code": "generated successfully"}
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_task_status_job_not_found(self, client, mock_orchestrator):
        """Test task status retrieval for non-existent job."""
        non_existent_job_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/jobs/{non_existent_job_id}/tasks/{task_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert f"Job {non_existent_job_id} not found" in data["detail"]
    
    def test_get_task_status_task_not_found(self, client, mock_orchestrator):
        """Test task status retrieval for non-existent task."""
        job_id = str(uuid.uuid4())
        non_existent_task_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            user_request="Test job",
            status=JobStatus.RUNNING,
            tasks=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_orchestrator.jobs[job_id] = job
        
        response = client.get(f"/api/v1/jobs/{job_id}/tasks/{non_existent_task_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert f"Task {non_existent_task_id} not found in job {job_id}" in data["detail"]


class TestJobCancellationEndpoint:
    """Test cases for job cancellation endpoint."""
    
    def test_cancel_job_success(self, client, mock_orchestrator):
        """Test successful job cancellation request."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            user_request="Test job",
            status=JobStatus.RUNNING,
            tasks=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_orchestrator.jobs[job_id] = job
        
        response = client.post(f"/api/v1/jobs/{job_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job_id
        assert "cancellation_requested" in data["status"]
        assert "Job cancellation requested" in data["message"]
    
    def test_cancel_job_already_completed(self, client, mock_orchestrator):
        """Test cancellation of already completed job."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            user_request="Test job",
            status=JobStatus.COMPLETED,
            tasks=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_orchestrator.jobs[job_id] = job
        
        response = client.post(f"/api/v1/jobs/{job_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job_id
        assert data["status"] == "completed"
        assert "already in final state" in data["message"]
    
    def test_cancel_job_not_found(self, client, mock_orchestrator):
        """Test cancellation of non-existent job."""
        non_existent_job_id = str(uuid.uuid4())
        
        response = client.post(f"/api/v1/jobs/{non_existent_job_id}/cancel")
        
        assert response.status_code == 404
        data = response.json()
        assert f"Job {non_existent_job_id} not found" in data["detail"]


class TestJobListEndpoint:
    """Test cases for job listing endpoint."""
    
    def test_list_jobs_placeholder(self, client, mock_orchestrator):
        """Test job listing endpoint (placeholder implementation)."""
        response = client.get("/api/v1/jobs/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure for placeholder implementation
        assert "jobs" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["jobs"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_list_jobs_with_pagination(self, client, mock_orchestrator):
        """Test job listing with pagination parameters."""
        response = client.get("/api/v1/jobs/?page=2&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 5


@pytest.mark.asyncio
class TestEndToEndJobWorkflow:
    """End-to-end tests for job workflow through API."""
    
    async def test_create_and_retrieve_job_workflow(self, client, mock_orchestrator):
        """Test complete workflow: create job, check status, get task details."""
        # Step 1: Create a job
        create_request = {
            "user_request": "Build a user authentication system",
            "priority": "high",
            "tags": ["auth", "backend"]
        }
        
        create_response = client.post("/api/v1/jobs/", json=create_request)
        assert create_response.status_code == 200
        
        job_data = create_response.json()
        job_id = job_data["job_id"]
        
        # Step 2: Add some tasks to the job (simulate orchestrator processing)
        task1 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="spec",
            status=TaskStatus.COMPLETED,
            description="Create authentication specification",
            dependencies=[],
            result={"spec": "Authentication spec completed"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        task2 = Task(
            task_id=str(uuid.uuid4()),
            job_id=job_id,
            agent_type="design",
            status=TaskStatus.RUNNING,
            description="Design authentication system",
            dependencies=[task1.task_id],
            result=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Update the job with tasks
        job = mock_orchestrator.jobs[job_id]
        job.tasks = [task1, task2]
        job.status = JobStatus.RUNNING
        
        # Step 3: Check job status
        status_response = client.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["status"] == "running"
        assert len(status_data["tasks"]) == 2
        assert status_data["progress"]["completion_percentage"] == 50.0
        
        # Step 4: Get individual task status
        task_response = client.get(f"/api/v1/jobs/{job_id}/tasks/{task1.task_id}")
        assert task_response.status_code == 200
        
        task_data = task_response.json()
        assert task_data["status"] == "completed"
        assert task_data["agent_type"] == "spec"
        assert task_data["result"]["spec"] == "Authentication spec completed"
