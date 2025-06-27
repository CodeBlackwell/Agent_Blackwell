"""
Phase 5 Integration Tests - Global Fixtures

This module provides global test fixtures for all Phase 5 integration tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.orchestrator.main import Orchestrator
import src.api.dependencies


@pytest.fixture(scope="session", autouse=True)
def setup_global_orchestrator_mock():
    """
    Create a global mock orchestrator and patch the dependencies module.
    This ensures that all API endpoints have access to an orchestrator instance.
    
    The autouse=True and session scope means this fixture will run once
    at the beginning of the test session automatically.
    """
    # Create mock orchestrator
    orchestrator = MagicMock(spec=Orchestrator)
    
    # Add necessary mock methods
    orchestrator.enqueue_task = AsyncMock(return_value="mocked-task-id")
    orchestrator.get_task_status = AsyncMock(return_value={"status": "completed"})
    orchestrator.process_task = AsyncMock(return_value={"status": "completed"})
    
    # Store tasks for more complex testing scenarios
    orchestrator._tasks = {}
    
    # Patch the global orchestrator in the dependencies module
    original_orchestrator = src.api.dependencies._orchestrator
    src.api.dependencies._orchestrator = orchestrator
    
    yield orchestrator
    
    # Restore original state after tests
    src.api.dependencies._orchestrator = original_orchestrator


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient for API endpoint testing."""
    with TestClient(app) as client:
        yield client
