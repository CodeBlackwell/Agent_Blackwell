"""
Planning Agent that analyzes user requests and creates structured job plans.

Based on reference pattern from beeai-orchestrator agent implementation.
"""

from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server

import sys
import os
# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from config.config import LLM_CONFIG, AGENT_PORTS, PROMPT_TEMPLATES


class PlanningAgent(BaseAgent):
    """
    Agent responsible for parsing user requests and creating structured job plans.
    
    This agent is the entry point for new development tasks, breaking them down
    into clear objectives and potential feature sets for implementation.
    """
    
    def initialize_agent(self):
        """
        Initialize the planning agent with its endpoint and tools.
        
        Sets up the agent's server endpoint and configures planning tools.
        """
        # PSEUDOCODE: Initialize ACP server following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/servers/echo.py
        # - Create Server() instance
        # - Register @server.agent() decorated methods
        # - Load LLM configuration from centralized config
        
        # PSEUDOCODE: Setup session management following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/acp-agent-generator/agent.py
        # - Initialize SessionManager for MCP tools
        # - Setup AsyncExitStack for resource management
        # - Configure environment variables and API keys
        
        # PSEUDOCODE: Initialize planning-specific tools:
        # - Load requirement parsing templates
        # - Setup job plan schema validation
        # - Configure output formatting for orchestrator consumption
        pass
    
    async def process_request(self, input: list[Message], context: Context) -> AsyncGenerator:
        """
        Process a user request and create a structured job plan.
        
        Args:
            input: List of input messages containing the user request
            context: Context for the current request
            
        Returns:
            An async generator yielding the structured job plan
        """
        # PSEUDOCODE: Extract user request following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/servers/llm.py
        # - Parse input[0].parts[0].content for user requirements
        # - Use LLM to analyze and structure the request
        # - Apply planning prompt templates from centralized config
        
        # PSEUDOCODE: Create structured job plan using:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/llama-index-rag/agent.py
        # - Use RAG pattern to reference similar project patterns
        # - Break down requirements into discrete feature sets
        # - Generate milestone definitions and success criteria
        
        # PSEUDOCODE: Stream results following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/servers/echo.py
        # - Use AsyncGenerator to yield structured plan components
        # - Format output for orchestrator consumption
        # - Include feature prioritization and dependency mapping
        pass
