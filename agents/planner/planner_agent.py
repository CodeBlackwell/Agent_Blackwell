from collections.abc import AsyncGenerator
import os
from dotenv import load_dotenv

from acp_sdk import Message
from acp_sdk.models import MessagePart
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.utils.dicts import exclude_none

# Load environment variables from .env file
load_dotenv()


async def planner_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for creating project plans and breaking down requirements"""
    llm = ChatModel.from_name("openai:gpt-3.5-turbo")
    
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
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Create a detailed project plan for: " + str(input))
    yield MessagePart(content=response.result.text)
