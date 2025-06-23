"""
Agent registry module for the orchestrator.

This module provides a registry for all agents in the system and handles
their initialization and registration with the orchestrator.
"""

import logging
import os
from typing import Any, Dict, Optional

from src.agents.coding_agent import CodingAgent
from src.agents.design_agent import DesignAgent
from src.agents.spec_agent import SpecAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

        # Add more agent initializations here as they are implemented
        # self._initialize_review_agent()
        # self._initialize_test_agent()

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

    def register_agent(self, agent_name: str, agent: Any) -> None:
        """
        Register an agent with the registry.

        Args:
            agent_name: Name of the agent to register
            agent: Agent instance to register
        """
        # Create the appropriate wrapper based on agent type
        if agent_name == "spec":
            # Create a wrapper for the Spec Agent
            class SpecAgentWrapper:
                def __init__(self, agent):
                    self.agent = agent

                async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                    user_request = inputs.get("input", "")
                    tasks = await self.agent.generate_tasks(user_request)

                    # Handle different return types from generate_tasks
                    if isinstance(tasks, list) and tasks and hasattr(tasks[0], "dict"):
                        # If tasks are Pydantic models with dict() method
                        return {
                            "output": [task.dict() for task in tasks],
                            "tasks": tasks,
                        }
                    elif (
                        isinstance(tasks, list) and tasks and isinstance(tasks[0], dict)
                    ):
                        # If tasks are already dictionaries
                        return {"output": tasks, "tasks": tasks}
                    else:
                        # If tasks are strings or other types, convert to simple dict format
                        formatted_tasks = (
                            [
                                {
                                    "description": str(task),
                                    "task_type": "general",
                                    "priority": "medium",
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

            self.agents[agent_name] = SpecAgentWrapper(agent)
            logger.info(f"{agent_name.capitalize()} Agent registered")

        elif agent_name == "design":
            # Create a wrapper for the Design Agent
            class DesignAgentWrapper:
                """Wrapper for the Design Agent to adapt it to the orchestrator interface."""

                def __init__(self, design_agent: DesignAgent):
                    """Initialize the wrapper with a Design Agent instance."""
                    self.design_agent = design_agent

                async def ainvoke(self, task: Dict[str, Any]) -> Dict[str, Any]:
                    """Invoke the Design Agent with the task and return the result."""
                    task_description = task.get("description", "")
                    design_specs = await self.design_agent.generate_design(
                        task_description
                    )
                    return {
                        "task_id": task.get("task_id"),
                        "result": design_specs,
                        "status": "completed",
                    }

            self.agents[agent_name] = DesignAgentWrapper(agent)
            logger.info(f"{agent_name.capitalize()} Agent registered")

        elif agent_name == "coding":
            # Create a wrapper for the Coding Agent
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

            self.agents[agent_name] = CodingAgentWrapper(agent)
            logger.info(f"{agent_name.capitalize()} Agent registered")

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
