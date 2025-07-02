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
from agents.agent_configs import planner_config

# Load environment variables from .env file
load_dotenv()


async def planner_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for creating project plans and breaking down requirements"""
    llm = ChatModel.from_name(planner_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior software planner. Your role is to:
                    1. Analyze project requirements and break them down into clear, actionable tasks
                    2. Create a structured project plan with phases and milestones
                    3. Identify potential risks, dependencies, and technical considerations
                    4. Suggest appropriate technologies, frameworks, and architectural patterns
                    5. Provide time estimates and priority levels for each task
                    
                    Always provide a detailed, structured plan that other team members can follow.
                    Format your response as a clear project plan with sections for:
                    - Project Overview
                    - Technical Requirements
                    - Task Breakdown
                    - Architecture Recommendations
                    - Risk Assessment
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm=llm)
    )
    
    response = await agent.run(prompt="Create a detailed project plan for: " + str(input))
    yield MessagePart(content=response.result.text)
