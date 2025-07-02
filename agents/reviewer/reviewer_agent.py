#!/usr/bin/env python3
"""
Reviewer Agent Module - Responsible for code review and quality assurance
"""

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

async def reviewer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for code review and quality assurance"""
    llm = ChatModel.from_name("openai:gpt-3.5-turbo")
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior code reviewer and quality assurance engineer. Your role is to:
                    1. Review code for bugs, security issues, and performance problems
                    2. Check adherence to coding standards and best practices
                    3. Verify that implementations match the design specifications
                    4. Identify potential improvements and optimizations
                    5. Ensure proper testing coverage and documentation
                    6. Provide constructive feedback and suggestions
                    
                    Provide comprehensive review feedback including:
                    - Code Quality Assessment
                    - Security Analysis
                    - Performance Considerations
                    - Best Practice Compliance
                    - Improvement Suggestions
                    - Test Coverage Analysis
                    - Final Approval/Rejection with reasoning
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Review the following work: " + str(input))
    yield MessagePart(content=response.result.text)
