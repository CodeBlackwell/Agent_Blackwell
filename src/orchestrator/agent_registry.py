"""
Agent registry module for the orchestrator.

This module provides a registry for all agents in the system and handles
their initialization and registration with the orchestrator.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from src.agents.coding_agent import CodingAgent
from src.agents.design_agent import DesignAgent
from src.agents.review_agent import ReviewAgent
from src.agents.spec_agent import SpecAgent
from src.agents.test_agent import TestGeneratorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SpecAgentWrapper:
    """Wrapper for the Spec Agent to adapt it to the orchestrator interface."""

    def __init__(self, agent):
        """Initialize the wrapper with a Spec Agent instance."""
        self.agent = agent

    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Spec Agent with the prompt and return formatted tasks."""
        prompt = inputs.get("prompt", "")
        tasks = await self.agent.generate_tasks(prompt)

        # Format the tasks for the orchestrator
        formatted_tasks = (
            [
                {
                    "description": str(task),
                    "task_type": "development",  # Default task type
                    "priority": "medium",  # Default priority
                }
                for task in tasks
            ]
            if isinstance(tasks, list)
            else [
                {
                    "description": str(tasks),
                    "task_type": "general",
                    "priority": "medium",
                }
            ]
        )

        return {"output": formatted_tasks, "tasks": formatted_tasks}


class DesignAgentWrapper:
    """Wrapper for the Design Agent to adapt it to the orchestrator interface."""

    def __init__(self, design_agent: DesignAgent):
        """Initialize the wrapper with a Design Agent instance."""
        self.design_agent = design_agent

    async def ainvoke(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Design Agent with the task and return the result."""
        task_description = task.get("description", "")
        design_specs = await self.design_agent.generate_design(task_description)
        return {
            "task_id": task.get("task_id"),
            "result": design_specs,
            "status": "completed",
        }


class CodingAgentWrapper:
    """Wrapper for the Coding Agent to adapt it to the orchestrator interface."""

    def __init__(self, coding_agent: CodingAgent):
        """Initialize the wrapper with a Coding Agent instance."""
        self.coding_agent = coding_agent

    async def ainvoke(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Coding Agent with the task and return the result."""
        task_description = task.get("description", "")
        design_specs = task.get("design_specs", "")
        architecture_diagram = task.get("architecture_diagram", "")

        code_result = await self.coding_agent.generate_code(
            task_description=task_description,
            design_specs=design_specs,
            architecture_diagram=architecture_diagram,
        )

        return {
            "task_id": task.get("task_id"),
            "result": code_result,
            "status": "completed",
        }


class ReviewAgentWrapper:
    """Wrapper for the Review Agent to adapt it to the orchestrator interface."""

    def __init__(self, review_agent: ReviewAgent):
        """Initialize the wrapper with a Review Agent instance."""
        self.review_agent = review_agent

    async def ainvoke(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Review Agent with the task and return the result."""
        code_to_review = task.get("code", "")
        requirements = task.get("requirements", "")

        review_result = await self.review_agent.review_code(
            code=code_to_review, requirements=requirements
        )

        return {
            "task_id": task.get("task_id"),
            "result": review_result,
            "status": "completed",
        }


class TestAgentWrapper:
    """Wrapper for the Test Agent to adapt it to the orchestrator interface."""

    def __init__(self, test_agent: TestGeneratorAgent):
        """Initialize the wrapper with a Test Agent instance."""
        self.test_agent = test_agent

    async def ainvoke(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Test Agent with the task and return the result."""
        code_to_test = task.get("code", "")
        requirements = task.get("requirements", "")

        test_result = await self.test_agent.generate_tests(
            code=code_to_test, requirements=requirements
        )

        return {
            "task_id": task.get("task_id"),
            "result": test_result,
            "status": "completed",
        }


class AgentRegistry:
    """
    Registry for all agents in the system.

    This class handles the initialization and registration of agents with the orchestrator.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the agent registry.

        Args:
            openai_api_key: API key for OpenAI (required for production)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agents = {}

        # Initialize agents
        self._initialize_agents()

        logger.info("AgentRegistry initialized")

    def _initialize_agents(self) -> None:
        """Initialize all agents in the system."""
        # Initialize the Spec Agent
        spec_agent = SpecAgent(openai_api_key=self.openai_api_key)
        self.register_agent("spec", spec_agent)

        # Initialize the Design Agent
        self.register_design_agent()

        # Initialize the Coding Agent
        self.register_coding_agent()

        # Initialize the Review Agent
        self.register_review_agent()

        # Initialize the Test Agent
        self.register_test_agent()

        # Add more agent initializations here as they are implemented

    def register_design_agent(self) -> None:
        """Register the Design Agent with the registry."""
        try:
            design_agent = DesignAgent(openai_api_key=self.openai_api_key)
            self.register_agent("design", design_agent)
            logger.info("Design Agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register Design Agent: {e}")
            raise

    def register_coding_agent(self) -> None:
        """Register the Coding Agent with the registry."""
        try:
            coding_agent = CodingAgent(openai_api_key=self.openai_api_key)
            self.register_agent("coding", coding_agent)
            logger.info("Coding Agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register Coding Agent: {e}")
            raise

    def register_review_agent(self) -> None:
        """Register the Review Agent with the registry."""
        try:
            review_agent = ReviewAgent(openai_api_key=self.openai_api_key)
            self.register_agent("review", review_agent)
            logger.info("Review Agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register Review Agent: {e}")
            raise

    def register_test_agent(self) -> None:
        """Register the Test Agent with the registry."""
        try:
            test_agent = TestGeneratorAgent(openai_api_key=self.openai_api_key)
            self.register_agent("test", test_agent)
            logger.info("Test Agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register Test Agent: {e}")
            raise

    def register_agent(self, agent_name: str, agent: Any) -> None:
        """
        Register an agent with the registry.

        Args:
            agent_name: Name of the agent to register
            agent: Agent instance to register
        """
        # Create the appropriate wrapper based on agent type
        if agent_name == "spec":
            self.agents[agent_name] = SpecAgentWrapper(agent)
        elif agent_name == "design":
            self.agents[agent_name] = DesignAgentWrapper(agent)
        elif agent_name == "coding":
            self.agents[agent_name] = CodingAgentWrapper(agent)
        elif agent_name == "review":
            self.agents[agent_name] = ReviewAgentWrapper(agent)
        elif agent_name == "test":
            self.agents[agent_name] = TestAgentWrapper(agent)
        else:
            # Generic registration for other agent types
            self.agents[agent_name] = agent

        logger.info(f"{agent_name.capitalize()} Agent registered")

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get an agent by name.

        Args:
            agent_name: Name of the agent to get

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_name)

    def register_agents_with_orchestrator(self, orchestrator) -> None:
        """
        Register all agents with the orchestrator.

        Args:
            orchestrator: Orchestrator instance to register agents with
        """
        for agent_name, agent in self.agents.items():
            orchestrator.register_agent(agent_name, agent)
            logger.info(f"Registered agent {agent_name} with orchestrator")
