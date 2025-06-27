"""
Phase 5 Integration Test Configuration

This module contains configuration settings and utilities for Phase 5 integration tests,
including test markers, fixtures, and environment setup.
"""

import pytest
import os
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock


# Test markers for selective test execution
pytest_plugins = ["pytest_asyncio"]

# Test markers
SLOW_TEST_MARKER = pytest.mark.slow
PERFORMANCE_TEST_MARKER = pytest.mark.performance
API_TEST_MARKER = pytest.mark.api
ORCHESTRATION_TEST_MARKER = pytest.mark.orchestration
MONITORING_TEST_MARKER = pytest.mark.monitoring
E2E_TEST_MARKER = pytest.mark.e2e


# Test environment configuration
class Phase5TestConfig:
    """Configuration class for Phase 5 integration tests."""
    
    # Default test settings
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_CONCURRENT_TASKS = 10
    
    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_TEST_DB = 15  # Use separate DB for tests
    
    # API configuration
    API_BASE_URL = "http://localhost:8000"
    API_TIMEOUT = 10
    
    # Orchestrator configuration
    ORCHESTRATOR_QUEUE_TIMEOUT = 5
    ORCHESTRATOR_TASK_TIMEOUT = 30
    
    # Monitoring configuration
    METRICS_ENDPOINT = "/metrics"
    HEALTH_CHECK_ENDPOINT = "/health"
    
    # Test data configuration
    TEST_USER_ID = "phase5_test_user"
    TEST_CHANNEL_ID = "phase5_test_channel"
    TEST_PLATFORM = "slack"
    
    @classmethod
    def get_test_environment_vars(cls) -> Dict[str, str]:
        """Get environment variables for test execution."""
        return {
            "REDIS_URL": cls.REDIS_URL,
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG",
            "TESTING": "true"
        }
    
    @classmethod
    def get_mock_task_data(cls, task_type: str = "spec", **kwargs) -> Dict[str, Any]:
        """Generate mock task data for testing."""
        base_data = {
            "task_type": task_type,
            "description": f"Test {task_type} task description",
            "user_id": cls.TEST_USER_ID,
            "channel_id": cls.TEST_CHANNEL_ID,
            "platform": cls.TEST_PLATFORM,
            "priority": "normal",
            "metadata": {
                "test_mode": True,
                "created_by": "phase5_tests"
            }
        }
        base_data.update(kwargs)
        return base_data
    
    @classmethod
    def get_mock_chatops_command(cls, command: str = "!help", **kwargs) -> Dict[str, Any]:
        """Generate mock ChatOps command data for testing."""
        base_data = {
            "command": command,
            "platform": cls.TEST_PLATFORM,
            "user_id": cls.TEST_USER_ID,
            "channel_id": cls.TEST_CHANNEL_ID,
            "timestamp": "2025-06-26T12:00:00Z"
        }
        base_data.update(kwargs)
        return base_data


# Common test fixtures
@pytest.fixture
def phase5_config():
    """Provide Phase 5 test configuration."""
    return Phase5TestConfig()


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    mock_client = AsyncMock()
    
    # Mock basic Redis operations
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()
    mock_client.xadd = AsyncMock(return_value="test-message-id")
    mock_client.xread = AsyncMock(return_value=[])
    mock_client.exists = AsyncMock(return_value=1)
    mock_client.delete = AsyncMock(return_value=1)
    
    return mock_client


@pytest.fixture
def mock_orchestrator_full():
    """Create a comprehensive mock orchestrator for testing."""
    mock_orchestrator = MagicMock()
    
    # Task storage for state management
    mock_orchestrator._tasks = {}
    mock_orchestrator._task_counter = 0
    
    async def mock_enqueue_task(task_type: str, task_data: Dict[str, Any]) -> str:
        mock_orchestrator._task_counter += 1
        task_id = f"mock-{task_type}-{mock_orchestrator._task_counter}"
        
        mock_orchestrator._tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "status": "queued",
            "created_at": "2025-06-26T12:00:00Z",
            "updated_at": "2025-06-26T12:00:00Z"
        }
        
        return task_id
    
    async def mock_get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        return mock_orchestrator._tasks.get(task_id)
    
    async def mock_process_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task_data.get("task_id")
        if task_id and task_id in mock_orchestrator._tasks:
            mock_orchestrator._tasks[task_id]["status"] = "completed"
            mock_orchestrator._tasks[task_id]["result"] = f"Mock result for {task_data.get('task_type', 'unknown')} task"
            mock_orchestrator._tasks[task_id]["updated_at"] = "2025-06-26T12:05:00Z"
            return mock_orchestrator._tasks[task_id]
        
        return {"status": "error", "error": "Task not found"}
    
    async def mock_list_tasks(status: Optional[str] = None) -> list:
        if status:
            return [task for task in mock_orchestrator._tasks.values() if task["status"] == status]
        return list(mock_orchestrator._tasks.values())
    
    # Assign mock methods
    mock_orchestrator.enqueue_task = mock_enqueue_task
    mock_orchestrator.get_task_status = mock_get_task_status
    mock_orchestrator.process_task = mock_process_task
    mock_orchestrator.list_tasks = mock_list_tasks
    
    # Mock agent management
    mock_orchestrator.agents = {
        "spec": AsyncMock(),
        "design": AsyncMock(), 
        "coding": AsyncMock(),
        "review": AsyncMock()
    }
    
    return mock_orchestrator


@pytest.fixture
def sample_test_data():
    """Provide sample test data for various test scenarios."""
    return {
        "valid_commands": [
            "!help",
            "!spec Create a REST API for user management",
            "!design Design microservices architecture",
            "!code Implement authentication service",
            "!review Review security implementation",
            "!status",
            "!deploy"
        ],
        "invalid_commands": [
            "help",  # Missing !
            "!unknown_command",
            "!spec",  # Missing description
            "",  # Empty command
            "! spaces in command name"
        ],
        "task_types": ["spec", "design", "coding", "review", "deployment"],
        "agent_responses": {
            "spec": {
                "specification": "Detailed API specification",
                "endpoints": ["/api/users", "/api/auth"],
                "requirements": ["FastAPI", "PostgreSQL", "JWT"]
            },
            "design": {
                "architecture": "Microservices with API Gateway",
                "components": ["Auth Service", "User Service", "Gateway"],
                "scalability_plan": {"load_balancing": "nginx", "caching": "redis"}
            },
            "coding": {
                "files": [
                    {"path": "main.py", "content": "# FastAPI application"},
                    {"path": "auth.py", "content": "# Authentication module"}
                ],
                "dependencies": ["fastapi", "pydantic", "sqlalchemy"]
            },
            "review": {
                "overall_score": 8.5,
                "issues": [
                    {"severity": "low", "description": "Add more comments"}
                ],
                "recommendations": ["Use environment variables for config"]
            }
        }
    }


# Test utilities
class TestResultTracker:
    """Utility class to track test results across multiple test runs."""
    
    def __init__(self):
        self.results = {
            "orchestration": {"passed": 0, "failed": 0, "skipped": 0},
            "api": {"passed": 0, "failed": 0, "skipped": 0},
            "monitoring": {"passed": 0, "failed": 0, "skipped": 0},
            "system": {"passed": 0, "failed": 0, "skipped": 0}
        }
        self.execution_times = {}
    
    def record_result(self, category: str, test_name: str, status: str, execution_time: float = 0):
        """Record a test result."""
        if category in self.results:
            if status in self.results[category]:
                self.results[category][status] += 1
            self.execution_times[f"{category}::{test_name}"] = execution_time
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        total_passed = sum(cat["passed"] for cat in self.results.values())
        total_failed = sum(cat["failed"] for cat in self.results.values())
        total_skipped = sum(cat["skipped"] for cat in self.results.values())
        total_tests = total_passed + total_failed + total_skipped
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "by_category": self.results,
            "execution_times": self.execution_times
        }


# Global test result tracker
test_tracker = TestResultTracker()


# Pytest hooks for Phase 5
def pytest_configure(config):
    """Configure pytest for Phase 5 tests."""
    # Register custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "api: marks tests as API integration tests")
    config.addinivalue_line("markers", "orchestration: marks tests as orchestration tests")
    config.addinivalue_line("markers", "monitoring: marks tests as monitoring tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


def pytest_runtest_setup(item):
    """Setup hook for each test."""
    # Set environment variables for test
    test_env = Phase5TestConfig.get_test_environment_vars()
    for key, value in test_env.items():
        os.environ[key] = value


def pytest_runtest_teardown(item, nextitem):
    """Teardown hook for each test."""
    # Clean up any test-specific environment changes if needed
    pass


def pytest_collection_modifyitems(config, items):
    """Modify collected test items."""
    # Add default markers based on test file location
    for item in items:
        if "orchestration" in str(item.fspath):
            item.add_marker(ORCHESTRATION_TEST_MARKER)
        elif "api" in str(item.fspath):
            item.add_marker(API_TEST_MARKER)
        elif "monitoring" in str(item.fspath):
            item.add_marker(MONITORING_TEST_MARKER)
        
        # Mark performance tests
        if "performance" in item.name or "concurrent" in item.name or "load" in item.name:
            item.add_marker(PERFORMANCE_TEST_MARKER)
        
        # Mark slow tests
        if "slow" in item.name or item.get_closest_marker("slow"):
            item.add_marker(SLOW_TEST_MARKER)
