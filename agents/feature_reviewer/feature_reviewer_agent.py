#!/usr/bin/env python3
"""
Feature Reviewer Agent Module - Specialized for reviewing individual features
in incremental development workflows.
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
from agents.feature_reviewer.feature_reviewer_config import DEFAULT_FEATURE_REVIEWER_INSTRUCTIONS

# Load environment variables from .env file
load_dotenv()

async def feature_reviewer_agent(input: list[Message]) -> AsyncGenerator:
    """
    Agent responsible for reviewing individual feature implementations
    in the context of incremental development.
    
    This agent is specialized for:
    - Reviewing single features rather than complete projects
    - Understanding incremental development context
    - Providing actionable feedback for retry attempts
    - Coordinating with error analysis for better reviews
    """
    # Use agent registry instead of circular imports
    from core.agent_registry import get_agent_config
    feature_reviewer_config = get_agent_config("feature_reviewer")
    
    llm = ChatModel.from_name(feature_reviewer_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": DEFAULT_FEATURE_REVIEWER_INSTRUCTIONS,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    # Extract feature context from input if available
    input_text = str(input)
    
    # Add context about this being a feature review
    review_prompt = f"""As a feature reviewer, evaluate the following implementation:

{input_text}

Remember to:
- Focus on the specific feature being implemented
- Consider the incremental development context
- Provide actionable feedback if revision is needed
- Be pragmatic about what constitutes "good enough"
"""
    
    response = await agent.run(prompt=review_prompt)
    yield MessagePart(content=response.result.text)