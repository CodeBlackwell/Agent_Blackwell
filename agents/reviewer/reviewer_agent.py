#!/usr/bin/env python3
"""
Reviewer Agent Module - Responsible for code review and quality assurance
"""

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
from agents.reviewer.reviewer_config import DEFAULT_REVIEWER_INSTRUCTIONS

# Import from agents package using absolute import
from agents.agent_configs import reviewer_config

# Load environment variables from .env file
load_dotenv()

async def reviewer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for code review and quality assurance"""
    llm = ChatModel.from_name(reviewer_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": DEFAULT_REVIEWER_INSTRUCTIONS,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Review the following work: " + str(input))
    yield MessagePart(content=response.result.text)
