"""
Test fixtures for workflow testing.
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime

from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return {
        "simple": "Build a hello world API",
        "calculator": "Build a calculator API with basic math operations",
        "todo": "Create a TODO list application with CRUD operations",
        "complex": """
        Build a comprehensive task management system with:
        - User authentication
        - Task CRUD operations
        - Task assignment and tracking
        - Due date management
        - Priority levels
        - Email notifications
        """
    }


@pytest.fixture
def mock_agent_responses():
    """Mock responses for different agent types."""
    return {
        "planner": {
            "simple": "1. Create Flask app\n2. Add hello endpoint\n3. Return JSON response",
            "complex": "1. Design database schema\n2. Implement auth\n3. Build API endpoints\n4. Add notifications"
        },
        "designer": {
            "simple": "GET /hello -> {\"message\": \"Hello, World!\"}",
            "complex": "RESTful API with /auth, /tasks, /users endpoints"
        },
        "coder": {
            "simple": 'from flask import Flask\napp = Flask(__name__)\n@app.route("/hello")\ndef hello(): return {"message": "Hello, World!"}',
            "complex": "# Complex implementation with multiple files and modules"
        },
        "test_writer": {
            "simple": "def test_hello():\n    assert client.get('/hello').json['message'] == 'Hello, World!'",
            "complex": "# Comprehensive test suite with unit and integration tests"
        },
        "reviewer": {
            "approved": "Code looks good. All requirements met.",
            "revision": "REVISION NEEDED: Missing error handling for edge cases"
        },
        "executor": {
            "success": "All tests passed. Application running successfully.",
            "failure": "Test failed: ConnectionError"
        }
    }


@pytest.fixture
def workflow_configs():
    """Sample workflow configurations."""
    return {
        "default": {
            "timeout": 600,
            "max_retries": 3,
            "steps": {
                "planning": {"timeout": 300, "retries": 2},
                "design": {"timeout": 300, "retries": 2},
                "implementation": {"timeout": 360, "retries": 3},
                "test_writing": {"timeout": 240, "retries": 2},
                "review": {"timeout": 180, "retries": 1},
                "execution": {"timeout": 300, "retries": 1}
            }
        },
        "fast": {
            "timeout": 300,
            "max_retries": 1,
            "steps": {
                "planning": {"timeout": 60, "retries": 1},
                "design": {"timeout": 60, "retries": 1},
                "implementation": {"timeout": 120, "retries": 1}
            }
        },
        "robust": {
            "timeout": 1200,
            "max_retries": 5,
            "steps": {
                "planning": {"timeout": 600, "retries": 5},
                "design": {"timeout": 600, "retries": 5},
                "implementation": {"timeout": 600, "retries": 5}
            }
        }
    }


@pytest.fixture
def create_mock_tracer():
    """Factory for creating mock tracers."""
    def _create_tracer(workflow_type="Individual", execution_id=None):
        if execution_id is None:
            execution_id = f"test_{int(datetime.now().timestamp())}"
        
        tracer = WorkflowExecutionTracer(
            workflow_type=workflow_type,
            execution_id=execution_id
        )
        return tracer
    
    return _create_tracer


@pytest.fixture
def create_input_data():
    """Factory for creating input data objects."""
    def _create_input(
        requirements: str = "Test requirement",
        workflow_type: str = "individual",
        step_type: str = None,
        max_retries: int = 3
    ) -> CodingTeamInput:
        return CodingTeamInput(
            requirements=requirements,
            workflow_type=workflow_type,
            step_type=step_type,
            max_retries=max_retries
        )
    
    return _create_input


@pytest.fixture
def create_team_member_result():
    """Factory for creating team member results."""
    def _create_result(
        team_member: TeamMember,
        output: str,
        name: str = None
    ) -> TeamMemberResult:
        if name is None:
            name = team_member.value
        
        return TeamMemberResult(
            team_member=team_member,
            output=output,
            name=name
        )
    
    return _create_result


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        "network_error": Exception("Connection timeout"),
        "api_error": Exception("API rate limit exceeded"),
        "validation_error": ValueError("Invalid input format"),
        "timeout_error": TimeoutError("Operation timed out"),
        "auth_error": Exception("Authentication failed"),
        "resource_error": Exception("Insufficient resources")
    }


@pytest.fixture
def performance_metrics():
    """Expected performance metrics for different operations."""
    return {
        "agent_response_times": {
            "planner_agent": {"avg": 2.5, "max": 5.0},
            "designer_agent": {"avg": 3.0, "max": 6.0},
            "coder_agent": {"avg": 4.0, "max": 8.0},
            "test_writer_agent": {"avg": 2.0, "max": 4.0},
            "reviewer_agent": {"avg": 1.5, "max": 3.0},
            "executor_agent": {"avg": 3.0, "max": 6.0}
        },
        "workflow_times": {
            "planning": {"avg": 3.0, "max": 10.0},
            "full": {"avg": 15.0, "max": 30.0},
            "individual": {"avg": 5.0, "max": 15.0}
        }
    }


class MockAgentRunner:
    """Mock agent runner for testing."""
    
    def __init__(self, responses: Dict[str, Any] = None):
        """Initialize with mock responses."""
        self.responses = responses or {}
        self.call_history = []
    
    async def run_team_member_with_tracking(
        self,
        agent_name: str,
        requirements: str,
        context: str
    ) -> Dict[str, Any]:
        """Mock implementation of run_team_member_with_tracking."""
        self.call_history.append({
            "agent_name": agent_name,
            "requirements": requirements,
            "context": context,
            "timestamp": datetime.now()
        })
        
        # Return mock response or default
        if agent_name in self.responses:
            return self.responses[agent_name]
        
        return {
            "content": f"Mock response from {agent_name}",
            "success": True,
            "messages": []
        }
    
    def get_call_count(self, agent_name: str = None) -> int:
        """Get number of calls for a specific agent or all agents."""
        if agent_name:
            return len([c for c in self.call_history if c["agent_name"] == agent_name])
        return len(self.call_history)
    
    def reset(self):
        """Reset call history."""
        self.call_history = []