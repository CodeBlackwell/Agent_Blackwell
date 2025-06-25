"""
LangGraph node functions for agent execution.

This module contains the node functions that integrate individual agents
into the LangGraph StateGraph workflow system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from src.agents.coding_agent import CodingAgent
from src.agents.design_agent import DesignAgent
from src.agents.review_agent import ReviewAgent
from src.agents.spec_agent import SpecAgent
from src.agents.test_agent import TestGeneratorAgent

from .workflow_state import (
    AgentType,
    AgentWorkflowState,
    WorkflowStatus,
    add_agent_result,
    update_state_timestamp,
)

# Configure logging
logger = logging.getLogger(__name__)


async def spec_agent_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """
    LangGraph node for the Specification Agent.

    This node processes user requests and generates structured tasks
    using the SpecAgent.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with spec tasks
    """
    logger.info(f"Executing spec_agent_node for task {state['task_id']}")

    start_time = datetime.now()

    try:
        # Initialize the SpecAgent
        spec_agent = SpecAgent(
            openai_api_key=state.get("metadata", {}).get("openai_api_key")
        )

        # Extract user request from state
        user_request = state["user_request"]

        # Generate tasks using the SpecAgent
        tasks = await spec_agent.generate_tasks(user_request)

        # Convert tasks to dictionaries for state storage
        spec_tasks = [task.model_dump() for task in tasks]

        # Update state with results
        state["spec_tasks"] = spec_tasks
        state["current_step"] = "design"

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add successful result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.SPEC,
            success=True,
            result=spec_tasks,
            execution_time=execution_time,
            metadata={"tasks_generated": len(spec_tasks)},
        )

        logger.info(f"SpecAgent completed successfully, generated {len(tasks)} tasks")

    except Exception as e:
        logger.error(f"SpecAgent failed: {str(e)}")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add failed result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.SPEC,
            success=False,
            error_message=str(e),
            execution_time=execution_time,
        )

        # Update state to reflect failure
        state["status"] = WorkflowStatus.FAILED

    return update_state_timestamp(state)


async def design_agent_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """
    LangGraph node for the Design Agent.

    This node generates design specifications based on the tasks
    created by the SpecAgent.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with design specifications
    """
    logger.info(f"Executing design_agent_node for task {state['task_id']}")

    start_time = datetime.now()

    try:
        # Initialize the DesignAgent
        design_agent = DesignAgent(
            openai_api_key=state.get("metadata", {}).get("openai_api_key")
        )

        # Extract task description from spec tasks
        if not state.get("spec_tasks"):
            raise ValueError("No spec tasks available for design generation")

        # Use the first task or combine multiple tasks for design input
        task_descriptions = [
            task.get("description", "") for task in state["spec_tasks"]
        ]
        combined_description = "\n".join(task_descriptions)

        # Generate design specifications
        design_specs = await design_agent.generate_design(combined_description)

        # Update state with results
        state["design_specs"] = design_specs
        state["current_step"] = "coding"

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add successful result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.DESIGN,
            success=True,
            result=design_specs,
            execution_time=execution_time,
            metadata={"tasks_processed": len(state["spec_tasks"])},
        )

        logger.info("DesignAgent completed successfully")

    except Exception as e:
        logger.error(f"DesignAgent failed: {str(e)}")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add failed result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.DESIGN,
            success=False,
            error_message=str(e),
            execution_time=execution_time,
        )

        # Update state to reflect failure
        state["status"] = WorkflowStatus.FAILED

    return update_state_timestamp(state)


async def coding_agent_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """
    LangGraph node for the Coding Agent.

    This node generates code based on the design specifications
    and task requirements.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with generated code
    """
    logger.info(f"Executing coding_agent_node for task {state['task_id']}")

    start_time = datetime.now()

    try:
        # Initialize the CodingAgent
        coding_agent = CodingAgent(
            openai_api_key=state.get("metadata", {}).get("openai_api_key")
        )

        # Extract required inputs
        if not state.get("spec_tasks"):
            raise ValueError("No spec tasks available for code generation")

        task_descriptions = [
            task.get("description", "") for task in state["spec_tasks"]
        ]
        combined_description = "\n".join(task_descriptions)
        design_specs = state.get("design_specs", "")

        # Generate code
        code_result = await coding_agent.generate_code(
            task_description=combined_description,
            design_specs=design_specs,
            architecture_diagram="",  # Could be enhanced to include architecture diagrams
        )

        # Update state with results
        state["code_result"] = code_result
        state["current_step"] = "review"

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add successful result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.CODING,
            success=True,
            result=code_result,
            execution_time=execution_time,
            metadata={"tasks_processed": len(state["spec_tasks"])},
        )

        logger.info("CodingAgent completed successfully")

    except Exception as e:
        logger.error(f"CodingAgent failed: {str(e)}")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add failed result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.CODING,
            success=False,
            error_message=str(e),
            execution_time=execution_time,
        )

        # Update state to reflect failure
        state["status"] = WorkflowStatus.FAILED

    return update_state_timestamp(state)


async def review_agent_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """
    LangGraph node for the Review Agent.

    This node reviews the generated code against requirements
    and provides feedback.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with review feedback
    """
    logger.info(f"Executing review_agent_node for task {state['task_id']}")

    start_time = datetime.now()

    try:
        # Initialize the ReviewAgent
        review_agent = ReviewAgent(
            openai_api_key=state.get("metadata", {}).get("openai_api_key")
        )

        # Extract required inputs
        code_to_review = state.get("code_result", "")
        if not code_to_review:
            raise ValueError("No code available for review")

        task_descriptions = [
            task.get("description", "") for task in state.get("spec_tasks", [])
        ]
        requirements = "\n".join(task_descriptions)

        # Review code
        review_result = await review_agent.review_code(
            code=code_to_review, requirements=requirements
        )

        # Update state with results
        state["review_feedback"] = review_result
        state["current_step"] = "test"

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add successful result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.REVIEW,
            success=True,
            result=review_result,
            execution_time=execution_time,
        )

        logger.info("ReviewAgent completed successfully")

    except Exception as e:
        logger.error(f"ReviewAgent failed: {str(e)}")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add failed result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.REVIEW,
            success=False,
            error_message=str(e),
            execution_time=execution_time,
        )

        # Update state to reflect failure
        state["status"] = WorkflowStatus.FAILED

    return update_state_timestamp(state)


async def testing_agent_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """
    LangGraph node for the Test Agent.

    This node generates tests for the created code.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with test results
    """
    logger.info(f"Executing test_agent_node for task {state['task_id']}")

    start_time = datetime.now()

    try:
        # Initialize the TestAgent
        test_agent = TestGeneratorAgent(
            openai_api_key=state.get("metadata", {}).get("openai_api_key")
        )

        # Extract required inputs
        code_to_test = state.get("code_result", "")
        if not code_to_test:
            raise ValueError("No code available for test generation")

        task_descriptions = [
            task.get("description", "") for task in state.get("spec_tasks", [])
        ]
        requirements = "\n".join(task_descriptions)

        # Generate tests
        test_result = await test_agent.generate_tests(
            code=code_to_test, requirements=requirements
        )

        # Update state with results
        state["test_results"] = test_result
        state["current_step"] = "completed"
        state["status"] = WorkflowStatus.COMPLETED

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add successful result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.TEST,
            success=True,
            result=test_result,
            execution_time=execution_time,
        )

        logger.info("TestAgent completed successfully - workflow finished")

    except Exception as e:
        logger.error(f"TestAgent failed: {str(e)}")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add failed result
        state = add_agent_result(
            state=state,
            agent_type=AgentType.TEST,
            success=False,
            error_message=str(e),
            execution_time=execution_time,
        )

        # Update state to reflect failure
        state["status"] = WorkflowStatus.FAILED

    return update_state_timestamp(state)


def should_continue_to_design(state: AgentWorkflowState) -> str:
    """
    Decision function to determine if workflow should continue to design phase.

    Args:
        state: Current workflow state

    Returns:
        "design" if should continue, "end" if should stop
    """
    if "spec" in state.get("failed_agents", []):
        return "end"

    if state.get("spec_tasks") and len(state["spec_tasks"]) > 0:
        return "design"

    return "end"


def should_continue_to_coding(state: AgentWorkflowState) -> str:
    """
    Decision function to determine if workflow should continue to coding phase.

    Args:
        state: Current workflow state

    Returns:
        "coding" if should continue, "end" if should stop
    """
    if "design" in state.get("failed_agents", []):
        return "end"

    if state.get("design_specs"):
        return "coding"

    return "end"


def should_continue_to_review(state: AgentWorkflowState) -> str:
    """
    Decision function to determine if workflow should continue to review phase.

    Args:
        state: Current workflow state

    Returns:
        "review" if should continue, "end" if should stop
    """
    if "coding" in state.get("failed_agents", []):
        return "end"

    if state.get("code_result"):
        return "review"

    return "end"


def should_continue_to_test(state: AgentWorkflowState) -> str:
    """
    Decision function to determine if workflow should continue to test phase.

    Args:
        state: Current workflow state

    Returns:
        "test" if should continue, "end" if should stop
    """
    if "review" in state.get("failed_agents", []):
        return "end"

    if state.get("review_feedback"):
        return "test"

    return "end"
