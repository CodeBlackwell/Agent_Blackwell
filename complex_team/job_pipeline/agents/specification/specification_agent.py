"""
Specification Agent for developing detailed feature specifications.

This agent takes feature sets from the orchestrator and develops
detailed specifications that will guide the design and implementation.

References the RAG implementation pattern from llama-index-rag/agent.py
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


class SpecificationAgent(BaseAgent):
    """
    Agent responsible for developing detailed specifications for features.
    
    This agent analyzes feature requirements from the orchestrator and creates
    comprehensive specifications including functional requirements, acceptance 
    criteria, and constraints.
    """
    
    def initialize_agent(self):
        """
        Initialize the specification agent with its endpoint and tools.
        
        Sets up the agent's server endpoint and configures specification tools.
        """
        # PSEUDOCODE: Initialize specification agent following basic server pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/servers/llm.py
        # - Setup Server() instance with LLM integration
        # - Load specification templates from centralized config
        # - Initialize chat model with appropriate parameters for detailed analysis
        
        # PSEUDOCODE: Setup RAG capabilities following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/llama-index-rag/agent.py
        # - Initialize document retrieval for similar specifications
        # - Setup knowledge base of common specification patterns
        # - Configure context-aware specification generation
        pass
    
    async def create_specification(self, input: list[Message], context: Context) -> AsyncGenerator:
        """
        Create detailed specifications based on orchestrator input.
        
        Args:
            input: List of input messages containing feature requirements
            context: Context for the current request
            
        Returns:
            An async generator yielding detailed specifications
        """
        # PSEUDOCODE: Parse feature requirements following pattern from:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/gpt-researcher/agent.py
        # - Extract feature description and context from orchestrator
        # - Research similar features and specification patterns
        # - Gather relevant technical constraints and requirements
        
        # PSEUDOCODE: Generate detailed specification using LLM following:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/openai-story-writer/agent.py
        # - Use structured prompts for specification generation
        # - Include functional requirements, non-functional requirements
        # - Define acceptance criteria and testing scenarios
        # - Generate API specifications and data models if applicable
        
        # PSEUDOCODE: Stream specification sections following:
        # /Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/clients/stream.py
        # - Yield specification sections incrementally
        # - Format output for design agent consumption
        # - Include cross-references and dependencies
        pass
