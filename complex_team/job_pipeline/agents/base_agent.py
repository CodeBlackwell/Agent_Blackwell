"""
Base agent class for all specialized agents in the job pipeline.

This module provides a common foundation for all agents in the system,
handling server setup, ACP integration, and LLM configuration loading.
"""

from acp_sdk.server import Server, Context
from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import LLM_CONFIG

class BaseAgent:
    """
    Base class for all agents in the pipeline.
    
    Provides common functionality for agent server initialization,
    endpoint setup, and ACP protocol handling.
    """
    
    def __init__(self, name, port):
        """
        Initialize a new agent with a name and port.
        
        Args:
            name: The name of the agent
            port: The port to run the agent server on
        """
        self.name = name
        self.port = port
        self.server = Server()
        self.initialize_agent()
        
    def initialize_agent(self):
        """
        Initialize the agent with its specific endpoint and tools.
        
        Must be implemented by subclasses to define agent-specific behavior.
        """
        raise NotImplementedError("Subclasses must implement initialize_agent")
    
    def run(self):
        """
        Start the agent server on the configured port.
        """
        self.server.run(port=self.port)
