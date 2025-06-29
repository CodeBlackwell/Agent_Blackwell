"""
Base agent class for all specialized agents in the job pipeline.

This module provides a common foundation for all agents in the system,
handling server setup, ACP integration, and LLM configuration loading.
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from typing import List, Optional, Dict, Any

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Server, Context, RunYield, RunYieldResume

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import LLM_CONFIG, PROMPT_TEMPLATES

class BaseAgent:
    """
    Base class for all agents in the pipeline.
    
    Provides common functionality for agent server initialization,
    endpoint setup, and ACP protocol handling with streaming support.
    """
    
    def __init__(self, name: str, port: int):
        """
        Initialize a new agent with a name and port.
        
        Args:
            name: The name of the agent
            port: The port to run the agent server on
        """
        self.name = name
        self.port = port
        self.server = Server()
        self.system_prompt = self._get_system_prompt()
        self.initialize_agent()
    
    def _get_system_prompt(self) -> str:
        """
        Get the agent-specific system prompt from the centralized config.
        
        Returns:
            The system prompt for this agent type
        """
        if self.name.lower() in PROMPT_TEMPLATES:
            return PROMPT_TEMPLATES[self.name.lower()].get('system', '')
        return ''
    
    def initialize_agent(self):
        """
        Initialize the agent with its specific endpoint and tools.
        
        Must be implemented by subclasses to define agent-specific behavior.
        """
        # Register the main agent endpoint with the agent's name
        @self.server.agent(name=self.name)
        async def agent_endpoint(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
            """Process inputs and generate responses using the agent's specialized logic"""
            async for response in self.process_request(inputs, context):
                yield response
    
    async def process_request(self, inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
        """
        Process the incoming request and generate a response.
        
        This method should be overridden by subclasses to implement agent-specific logic.
        The default implementation yields a simple error message.
        
        Args:
            inputs: List of input messages
            context: The request context
            
        Yields:
            Response message parts
        """
        yield MessagePart(content=f"Error: The {self.name} agent's process_request method has not been implemented.")
    
    async def stream_response(self, content: str) -> AsyncGenerator[MessagePart, None]:
        """
        Stream a response string as individual message parts.
        
        Args:
            content: The content to stream
            
        Yields:
            Message parts with chunks of the content
        """
        # Simple implementation - in a real system, you might chunk by sentences or paragraphs
        chunk_size = 100
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            yield MessagePart(content=chunk)
            # Small delay to simulate streaming
            await asyncio.sleep(0.05)
    
    def run(self):
        """
        Start the agent server on the configured port.
        """
        print(f"Starting {self.name} agent on port {self.port}...")
        self.server.run(port=self.port)
