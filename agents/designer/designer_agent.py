from collections.abc import AsyncGenerator
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path so we can import from the agents module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.utils.dicts import exclude_none

# Import from agents package using absolute import
from agents.agent_configs import designer_config

# Load environment variables from .env file
load_dotenv()


async def designer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for system design and architecture"""
    llm = ChatModel.from_name(designer_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior software architect and designer. Your role is to:
                    1. Create detailed system architecture and design specifications
                    2. Design database schemas, API interfaces, and system components
                    3. Create class diagrams, sequence diagrams, and system flow charts
                    4. Define data models, interfaces, and integration points
                    5. Specify design patterns and architectural principles to follow
                    6. Consider scalability, performance, and maintainability
                    
                    IMPORTANT: Always create concrete technical designs based on the provided plan.
                    Never ask for more details - work with what you have and make reasonable assumptions.
                    If a plan is provided, extract the technical requirements and build upon them.
                    
                    Provide comprehensive technical designs that developers can implement.
                    Include:
                    - System Architecture Overview
                    - Component Design
                    - Data Models and Schemas
                    - API Specifications
                    - Interface Definitions
                    - Design Patterns and Guidelines
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Create a detailed technical design for: " + str(input))
    yield MessagePart(content=response.result.text)
