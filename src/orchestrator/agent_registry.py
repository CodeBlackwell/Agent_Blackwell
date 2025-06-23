"""
Agent registry module for the orchestrator.

This module provides a registry for all agents in the system and handles
their initialization and registration with the orchestrator.
"""

import logging
import os
from typing import Dict, Any, Optional

from langchain.agents import AgentExecutor
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

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
        self._initialize_spec_agent()
        
        # Add more agent initializations here as they are implemented
        # self._initialize_design_agent()
        # self._initialize_coding_agent()
        # self._initialize_review_agent()
        # self._initialize_test_agent()
    
    def _initialize_spec_agent(self) -> None:
        """Initialize the Spec Agent."""
        try:
            # Create the Spec Agent
            spec_agent = SpecAgent(openai_api_key=self.openai_api_key)
            
            # Create a simple wrapper to adapt the SpecAgent to the AgentExecutor interface
            class SpecAgentWrapper:
                async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                    user_request = inputs.get("input", "")
                    tasks = await spec_agent.generate_tasks(user_request)
                    
                    # Handle different return types from generate_tasks
                    if isinstance(tasks, list) and tasks and hasattr(tasks[0], 'dict'):
                        # If tasks are Pydantic models with dict() method
                        return {
                            "output": [task.dict() for task in tasks],
                            "tasks": tasks
                        }
                    elif isinstance(tasks, list) and tasks and isinstance(tasks[0], dict):
                        # If tasks are already dictionaries
                        return {
                            "output": tasks,
                            "tasks": tasks
                        }
                    else:
                        # If tasks are strings or other types, convert to simple dict format
                        formatted_tasks = [{
                            "description": str(task),
                            "task_type": "general",
                            "priority": "medium"
                        } for task in tasks] if isinstance(tasks, list) else [{
                            "description": str(tasks),
                            "task_type": "general",
                            "priority": "medium"
                        }]
                        
                        return {
                            "output": formatted_tasks,
                            "tasks": formatted_tasks
                        }
            
            # Register the agent
            self.agents["spec_agent"] = SpecAgentWrapper()
            logger.info("Spec Agent initialized and registered")
            
        except Exception as e:
            logger.error(f"Error initializing Spec Agent: {e}")
    
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
