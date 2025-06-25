"""
LangGraph-based orchestrator for agent workflows.

This module implements the main orchestrator using LangGraph's StateGraph
to coordinate agent execution with stateful workflows.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .agent_nodes import (
    coding_agent_node,
    design_agent_node,
    review_agent_node,
    should_continue_to_coding,
    should_continue_to_design,
    should_continue_to_review,
    should_continue_to_test,
    spec_agent_node,
    testing_agent_node,
)
from .workflow_state import (
    AgentWorkflowState,
    WorkflowStatus,
    create_initial_state,
    update_state_timestamp,
)

# Configure logging
logger = logging.getLogger(__name__)


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator for coordinating agent workflows.

    This class replaces the traditional Redis-based orchestrator with
    a LangGraph StateGraph that provides built-in state management,
    checkpointing, and workflow orchestration.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        enable_checkpointing: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize the LangGraph orchestrator.

        Args:
            openai_api_key: API key for OpenAI
            enable_checkpointing: Whether to enable workflow checkpointing
            max_retries: Maximum number of retries for failed workflows
        """
        self.openai_api_key = openai_api_key
        self.max_retries = max_retries

        # Initialize checkpointing if enabled
        self.checkpointer = MemorySaver() if enable_checkpointing else None

        # Build the workflow graph
        self.workflow_graph = self._build_workflow_graph()

        logger.info("LangGraphOrchestrator initialized")

    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for the agent workflow.

        Returns:
            Configured StateGraph for agent orchestration
        """
        # Create the StateGraph
        workflow = StateGraph(AgentWorkflowState)

        # Add agent nodes
        workflow.add_node("spec_agent", spec_agent_node)
        workflow.add_node("design_agent", design_agent_node)
        workflow.add_node("coding_agent", coding_agent_node)
        workflow.add_node("review_agent", review_agent_node)
        workflow.add_node("test_agent", testing_agent_node)

        # Set entry point
        workflow.set_entry_point("spec_agent")

        # Add conditional edges for workflow routing
        workflow.add_conditional_edges(
            "spec_agent",
            should_continue_to_design,
            {"design": "design_agent", "end": END},
        )

        workflow.add_conditional_edges(
            "design_agent",
            should_continue_to_coding,
            {"coding": "coding_agent", "end": END},
        )

        workflow.add_conditional_edges(
            "coding_agent",
            should_continue_to_review,
            {"review": "review_agent", "end": END},
        )

        workflow.add_conditional_edges(
            "review_agent", should_continue_to_test, {"test": "test_agent", "end": END}
        )

        # Test agent goes to END
        workflow.add_edge("test_agent", END)

        # Compile the graph
        return workflow.compile(checkpointer=self.checkpointer)

    async def submit_feature_request(
        self, description: str, task_type: str = "feature_development"
    ) -> str:
        """
        Submit a feature request to the workflow system.

        Args:
            description: Description of the requested feature
            task_type: Type of task to be processed

        Returns:
            workflow_id: ID of the created workflow
        """
        # Generate unique IDs
        workflow_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Create initial state
        initial_state = create_initial_state(
            workflow_id=workflow_id,
            task_id=task_id,
            task_type=task_type,
            user_request=description,
            max_retries=self.max_retries,
        )

        # Add OpenAI API key to metadata
        if self.openai_api_key:
            initial_state["metadata"]["openai_api_key"] = self.openai_api_key

        logger.info(f"Submitted feature request with workflow_id: {workflow_id}")

        return workflow_id

    async def execute_workflow(
        self,
        workflow_id: str,
        user_request: str,
        task_type: str = "feature_development",
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow for a given request.

        Args:
            workflow_id: Unique workflow identifier
            user_request: The user's feature request
            task_type: Type of task to be processed

        Returns:
            Final workflow state and results
        """
        try:
            # Create initial state
            task_id = str(uuid.uuid4())
            initial_state = create_initial_state(
                workflow_id=workflow_id,
                task_id=task_id,
                task_type=task_type,
                user_request=user_request,
                max_retries=self.max_retries,
            )

            # Add OpenAI API key to metadata
            if self.openai_api_key:
                initial_state["metadata"]["openai_api_key"] = self.openai_api_key

            initial_state["status"] = WorkflowStatus.IN_PROGRESS

            logger.info(f"Starting workflow execution for {workflow_id}")

            # Execute the workflow
            config = {"configurable": {"thread_id": workflow_id}}

            # Run the workflow
            final_state: AgentWorkflowState = await self.workflow_graph.ainvoke(
                initial_state, config=config
            )

            # Update final status
            if final_state["status"] == WorkflowStatus.IN_PROGRESS:
                final_state["status"] = WorkflowStatus.COMPLETED

            final_state = update_state_timestamp(final_state)

            logger.info(
                f"Workflow {workflow_id} completed with status: {final_state['status']}"
            )

            return {
                "workflow_id": workflow_id,
                "status": final_state["status"],
                "results": {
                    "spec_tasks": final_state.get("spec_tasks", []),
                    "design_specs": final_state.get("design_specs"),
                    "code_result": final_state.get("code_result"),
                    "review_feedback": final_state.get("review_feedback"),
                    "test_results": final_state.get("test_results"),
                },
                "execution_summary": {
                    "completed_agents": final_state.get("completed_agents", []),
                    "failed_agents": final_state.get("failed_agents", []),
                    "error_messages": final_state.get("error_messages", []),
                    "total_agents": len(final_state.get("agent_results", [])),
                },
                "metadata": final_state.get("metadata", {}),
                "created_at": final_state.get("created_at"),
                "updated_at": final_state.get("updated_at"),
            }

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed with error: {str(e)}")

            return {
                "workflow_id": workflow_id,
                "status": WorkflowStatus.FAILED,
                "error": str(e),
                "results": {},
                "execution_summary": {
                    "completed_agents": [],
                    "failed_agents": [],
                    "error_messages": [str(e)],
                    "total_agents": 0,
                },
            }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow.

        Args:
            workflow_id: ID of the workflow to check

        Returns:
            Dictionary with workflow status information
        """
        try:
            if not self.checkpointer:
                return {
                    "workflow_id": workflow_id,
                    "error": "Checkpointing not enabled, cannot retrieve workflow status",
                }

            # Get workflow state from checkpointer
            config = {"configurable": {"thread_id": workflow_id}}

            # This would require accessing the checkpointer's state
            # For now, return a placeholder response
            return {
                "workflow_id": workflow_id,
                "status": "unknown",
                "message": "Status retrieval not yet implemented",
            }

        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_id}: {str(e)}")
            return {"workflow_id": workflow_id, "error": str(e)}

    async def stream_workflow_execution(
        self,
        workflow_id: str,
        user_request: str,
        task_type: str = "feature_development",
    ):
        """
        Stream workflow execution progress in real-time.

        Args:
            workflow_id: Unique workflow identifier
            user_request: The user's feature request
            task_type: Type of task to be processed

        Yields:
            Workflow state updates as they occur
        """
        try:
            # Create initial state
            task_id = str(uuid.uuid4())
            initial_state = create_initial_state(
                workflow_id=workflow_id,
                task_id=task_id,
                task_type=task_type,
                user_request=user_request,
                max_retries=self.max_retries,
            )

            # Add OpenAI API key to metadata
            if self.openai_api_key:
                initial_state["metadata"]["openai_api_key"] = self.openai_api_key

            initial_state["status"] = WorkflowStatus.IN_PROGRESS

            logger.info(f"Starting streaming workflow execution for {workflow_id}")

            # Execute the workflow with streaming
            config = {"configurable": {"thread_id": workflow_id}}

            async for state_update in self.workflow_graph.astream(
                initial_state, config=config
            ):
                yield {
                    "workflow_id": workflow_id,
                    "state_update": state_update,
                    "timestamp": update_state_timestamp({})["updated_at"],
                }

        except Exception as e:
            logger.error(f"Streaming workflow {workflow_id} failed: {str(e)}")
            yield {
                "workflow_id": workflow_id,
                "error": str(e),
                "status": WorkflowStatus.FAILED,
            }


# Example usage and testing
async def main():
    """Example usage of the LangGraphOrchestrator."""

    import os

    # Initialize orchestrator
    orchestrator = LangGraphOrchestrator(
        openai_api_key=os.getenv("OPENAI_API_KEY"), enable_checkpointing=True
    )

    # Example feature request
    user_request = """
    Create a FastAPI service with PostgreSQL database for a todo app.
    The app should allow users to create, read, update, and delete todos.
    Include proper error handling and API documentation.
    """

    workflow_id = str(uuid.uuid4())

    try:
        # Execute workflow
        result = await orchestrator.execute_workflow(
            workflow_id=workflow_id, user_request=user_request
        )

        print(f"Workflow completed with status: {result['status']}")
        print(f"Completed agents: {result['execution_summary']['completed_agents']}")

        if result.get("results", {}).get("spec_tasks"):
            print(
                f"Generated {len(result['results']['spec_tasks'])} specification tasks"
            )

        if result["status"] == WorkflowStatus.FAILED:
            print(f"Errors: {result['execution_summary']['error_messages']}")

    except Exception as e:
        print(f"Example execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
