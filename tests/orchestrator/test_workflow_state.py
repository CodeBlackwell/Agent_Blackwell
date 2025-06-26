"""
Tests for the AgentWorkflowState schema and workflow state management.

These tests verify the workflow state TypedDict behaves correctly,
validates required fields, handles optional fields, and maintains
state consistency throughout workflow execution.
"""

from datetime import datetime
from typing import Any, Dict

import pytest

from src.orchestrator.workflow_state import (
    AgentWorkflowState,
    WorkflowStatus,
    create_initial_state,
    update_state_timestamp,
)


class TestAgentWorkflowStateCreation:
    """Test creation and initialization of AgentWorkflowState."""

    def test_create_initial_state_basic(self):
        """Test creating initial workflow state with basic parameters."""
        workflow_id = "test-wf-123"
        task_id = "test-task-456"
        task_type = "feature_development"
        user_request = "Create a REST API"

        state = create_initial_state(
            workflow_id=workflow_id,
            task_id=task_id,
            task_type=task_type,
            user_request=user_request,
        )

        # Verify core fields
        assert state["workflow_id"] == workflow_id
        assert state["task_id"] == task_id
        assert state["task_type"] == task_type
        assert state["user_request"] == user_request
        assert state["current_step"] == "spec"
        assert state["status"] == WorkflowStatus.PENDING

        # Verify agent results are empty initially
        assert state["spec_tasks"] == []
        assert state["design_specs"] is None
        assert state["code_result"] is None
        assert state["review_feedback"] is None
        assert state["test_results"] is None

        # Verify execution tracking
        assert state["completed_agents"] == []
        assert state["failed_agents"] == []
        assert state["agent_results"] == []

        # Verify error handling
        assert state["error_messages"] == []
        assert state["retry_count"] == 0
        assert state["max_retries"] == 3

        # Verify metadata and timestamps
        assert state["metadata"] == {}
        assert "created_at" in state
        assert "updated_at" in state

    def test_create_initial_state_with_custom_retries(self):
        """Test creating initial state with custom max_retries."""
        max_retries = 5

        state = create_initial_state(
            workflow_id="test-wf",
            task_id="test-task",
            task_type="test_type",
            user_request="test request",
            max_retries=max_retries,
        )

        assert state["max_retries"] == max_retries
        assert state["retry_count"] == 0

    def test_full_workflow_state(self):
        """Test that initial workflow state has all required fields."""
        state = create_initial_state(
            workflow_id="full-test",
            task_id="full-task",
            task_type="comprehensive_test",
            user_request="Full test request",
        )

        # Required TypedDict fields
        required_fields = [
            "workflow_id",
            "task_id",
            "task_type",
            "user_request",
            "current_step",
            "status",
            "spec_tasks",
            "design_specs",
            "code_result",
            "review_feedback",
            "test_results",
            "completed_agents",
            "failed_agents",
            "agent_results",
            "error_messages",
            "retry_count",
            "max_retries",
            "metadata",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in state, f"Required field '{field}' missing from state"

        # Verify the state status is PENDING (not COMPLETED as expected in old test)
        assert state["status"] == WorkflowStatus.PENDING


class TestWorkflowStateModification:
    """Test modification and updating of workflow state."""

    def test_state_update_with_agent_results(self):
        """Test updating state with agent results."""
        state = create_initial_state(
            workflow_id="update-test",
            task_id="update-task",
            task_type="test",
            user_request="test request",
        )

        # Update with spec tasks
        state["spec_tasks"] = [
            {"id": "task1", "description": "Task 1"},
            {"id": "task2", "description": "Task 2"},
        ]
        state["completed_agents"].append("spec")
        state["current_step"] = "design"

        assert len(state["spec_tasks"]) == 2
        assert "spec" in state["completed_agents"]
        assert state["current_step"] == "design"

    def test_state_update_with_additional_tasks(self):
        """Test adding additional tasks to existing state."""
        state = create_initial_state(
            workflow_id="task-test",
            task_id="task-id",
            task_type="test",
            user_request="test",
        )

        # Initially empty
        assert len(state["spec_tasks"]) == 0

        # Add tasks
        state["spec_tasks"].extend(
            [
                {"id": "task1", "description": "First task"},
                {"id": "task2", "description": "Second task"},
            ]
        )

        assert len(state["spec_tasks"]) == 2
        assert state["spec_tasks"][0]["id"] == "task1"
        assert state["spec_tasks"][1]["id"] == "task2"

    def test_state_error_update(self):
        """Test updating state with error information."""
        state = create_initial_state(
            workflow_id="error-test",
            task_id="error-task",
            task_type="test",
            user_request="test",
        )

        # Add error information
        state["error_messages"].append("Test error occurred")
        state["failed_agents"].append("spec")
        state["status"] = WorkflowStatus.FAILED
        state["retry_count"] = 1

        assert len(state["error_messages"]) == 1
        assert "spec" in state["failed_agents"]
        assert state["status"] == WorkflowStatus.FAILED
        assert state["retry_count"] == 1


class TestWorkflowStateTransitions:
    """Test state transitions and workflow progression."""

    def test_linear_workflow_progression(self):
        """Test progressing through workflow steps."""
        state = create_initial_state(
            workflow_id="progression-test",
            task_id="prog-task",
            task_type="test",
            user_request="test progression",
        )

        # Initial state
        assert state["current_step"] == "spec"
        assert state["status"] == WorkflowStatus.PENDING

        # Progress to design
        state["current_step"] = "design"
        state["status"] = WorkflowStatus.IN_PROGRESS
        state["completed_agents"].append("spec")

        assert state["current_step"] == "design"
        assert state["status"] == WorkflowStatus.IN_PROGRESS
        assert "spec" in state["completed_agents"]

    def test_workflow_error_recovery(self):
        """Test error handling and recovery in workflow."""
        state = create_initial_state(
            workflow_id="recovery-test",
            task_id="rec-task",
            task_type="test",
            user_request="test recovery",
        )

        # Simulate error
        state["status"] = WorkflowStatus.FAILED
        state["failed_agents"].append("design")
        state["error_messages"].append("Design failed")
        state["retry_count"] = 1

        # Simulate recovery
        state["status"] = WorkflowStatus.IN_PROGRESS
        state["failed_agents"].remove("design")
        state["error_messages"].clear()

        assert state["status"] == WorkflowStatus.IN_PROGRESS
        assert len(state["failed_agents"]) == 0
        assert len(state["error_messages"]) == 0
        assert state["retry_count"] == 1  # Retry count persists


class TestWorkflowStateUtilities:
    """Test utility functions for workflow state."""

    def test_update_state_timestamp(self):
        """Test updating workflow state timestamp."""
        state = create_initial_state(
            workflow_id="timestamp-test",
            task_id="ts-task",
            task_type="test",
            user_request="test timestamp",
        )

        original_updated_at = state["updated_at"]

        # Update timestamp
        updated_state = update_state_timestamp(state)

        # Should be the same object (state is modified in place)
        assert updated_state is state
        assert state["updated_at"] != original_updated_at
        assert (
            state["created_at"] == updated_state["created_at"]
        )  # Created time unchanged

    def test_workflow_state_comparison(self):
        """Test comparing workflow states."""
        state1 = create_initial_state(
            workflow_id="comp-test-1",
            task_id="comp-task-1",
            task_type="test",
            user_request="test comparison",
        )

        state2 = create_initial_state(
            workflow_id="comp-test-2",
            task_id="comp-task-2",
            task_type="test",
            user_request="test comparison",
        )

        # States should be different due to different IDs and timestamps
        assert state1["workflow_id"] != state2["workflow_id"]
        assert state1["task_id"] != state2["task_id"]
        # Timestamps will likely be different due to creation time
        # but we can't rely on exact equality due to timing

    def test_state_metadata_manipulation(self):
        """Test manipulating metadata in workflow state."""
        state = create_initial_state(
            workflow_id="meta-test",
            task_id="meta-task",
            task_type="test",
            user_request="test metadata",
        )

        # Add metadata
        state["metadata"]["api_key"] = "test-key"
        state["metadata"]["environment"] = "test"
        state["metadata"]["custom_config"] = {"setting": "value"}

        assert state["metadata"]["api_key"] == "test-key"
        assert state["metadata"]["environment"] == "test"
        assert state["metadata"]["custom_config"]["setting"] == "value"

    def test_agent_results_tracking(self):
        """Test tracking detailed agent results."""
        state = create_initial_state(
            workflow_id="results-test",
            task_id="res-task",
            task_type="test",
            user_request="test results",
        )

        # Add agent results
        spec_result = {
            "agent": "spec",
            "status": "completed",
            "output": {"tasks": ["Task 1", "Task 2"]},
            "timestamp": datetime.now().isoformat(),
        }

        state["agent_results"].append(spec_result)
        state["completed_agents"].append("spec")

        assert len(state["agent_results"]) == 1
        assert state["agent_results"][0]["agent"] == "spec"
        assert state["agent_results"][0]["status"] == "completed"
        assert "spec" in state["completed_agents"]
