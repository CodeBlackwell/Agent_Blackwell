"""
Design Agent for creating software architecture designs.

This agent takes specifications from the Specification Agent and develops
detailed technical designs that will guide implementation.

References the Tool Definition Pattern from beeai-orchestrator/translation_tool.py
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


class DesignAgent(BaseAgent):
    """
    Agent responsible for creating technical designs based on specifications.
    
    This agent develops architecture designs, component diagrams, data models,
    and interface definitions based on the specifications.
    """
    
    def initialize_agent(self):
        """
        Initialize the design agent with its endpoint and tools.
        
        Sets up the agent's server endpoint and configures design tools.
        """
        # PSEUDOCODE: Initialize design agent following LLM integration pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/servers/llm.py
        # - Setup Server() with advanced LLM model for technical design
        # - Load architecture and design templates from centralized config
        # - Configure model parameters for detailed technical analysis
        
        # PSEUDOCODE: Setup design knowledge base following RAG pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/llama-index-rag/agent.py
        # - Initialize retrieval system for design patterns and architectures
        # - Setup knowledge base of common technical design approaches
        # - Configure context-aware design recommendation system
        pass
    
    async def create_design(self, input: list[Message], context: Context) -> AsyncGenerator:
        """
        Create a technical design based on specifications.
        
        Args:
            input: List of input messages containing the specifications
            context: Context for the current request
            
        Returns:
            An async generator yielding technical designs
        """
        # PSEUDOCODE: Parse specifications following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/gpt-researcher/agent.py
        # - Extract functional and non-functional requirements from specifications
        # - Research relevant design patterns and architectural approaches
        # - Analyze technical constraints and integration requirements
        
        # PSEUDOCODE: Generate technical design using LLM following:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/openai-story-writer/agent.py
        # - Create system architecture and component diagrams
        # - Define API interfaces, data models, and interaction patterns
        # - Specify technology stack and implementation approaches
        # - Generate detailed class structures and method signatures
        
        # PSEUDOCODE: Stream design sections following:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/clients/stream.py
        # - Yield design components incrementally (architecture first, then details)
        # - Format output for code agent consumption with clear implementation guidance
        # - Include cross-references, dependencies, and integration points
        pass