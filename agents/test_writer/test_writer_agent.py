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
from agents.agent_configs import test_writer_config

# Load environment variables from .env file
load_dotenv()


async def test_writer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for writing business-value focused tests for TDD"""
    llm = ChatModel.from_name(test_writer_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior test engineer specializing in Test-Driven Development (TDD) with a focus on business value.
                    Your role is to:
                    1. Write tests that validate business requirements and user stories
                    2. Create acceptance criteria that define "done" from a business perspective
                    3. Focus on behavior and outcomes rather than implementation details
                    4. Write tests that guide development by defining what success looks like
                    5. Ensure tests capture the WHY (business purpose) not just the WHAT (technical details)
                    6. Create tests that remain valuable even when implementation changes
                    
                    IMPORTANT: Always create concrete test scenarios based on the provided plan and design.
                    Never ask for more details - work with what you have and make reasonable assumptions.
                    Extract business requirements from the plan and create comprehensive test scenarios.
                    
                    Write tests that:
                    - Validate end-to-end user workflows and business processes
                    - Test integration points and system behavior
                    - Focus on user outcomes and business value delivery
                    - Are readable by non-technical stakeholders
                    - Guide implementation rather than constrain it
                    - Test the contract/interface, not internal mechanics
                    
                    Provide:
                    - Business-focused test scenarios
                    - Acceptance criteria in Given-When-Then format
                    - Integration and end-to-end tests
                    - User story validation tests
                    - Performance/scalability tests where business-critical
                    - Clear test descriptions explaining business value
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Write business-value focused tests for TDD approach: " + str(input))
    yield MessagePart(content=response.result.text)
