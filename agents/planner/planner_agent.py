from collections.abc import AsyncGenerator
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
                    
                    CRITICAL REQUIREMENTS:
                    ======================
                    1. When requirements are vague (e.g., "Create a REST API"), expand them into a COMPLETE project plan
                    2. Always include ALL essential components for the project type:
                       - APIs: Setup, Models, Auth, Endpoints, Validation, Testing, Documentation
                       - Web Apps: Frontend, Backend, State Management, UI Components, Testing
                       - CLI Tools: Command Structure, I/O, Configuration, Error Handling, Testing
                    3. Each task must have CONCRETE DELIVERABLES (specific files, endpoints, features)
                    4. Include TESTABLE ACCEPTANCE CRITERIA for each major component
                    
                    Format your response as a clear project plan with sections for:
                    - Project Overview
                    - Technical Requirements
                    - Task Breakdown (with specific deliverables)
                    - Architecture Recommendations
                    - Risk Assessment
                    
                    Task Breakdown Example:
                    =====================
                    Task 1: Project Setup and Configuration
                    - Deliverables: app.py, config.py, requirements.txt, .env.example
                    - Acceptance Criteria: Application starts, configuration loads from environment
                    - Priority: High
                    
                    Task 2: Database Models and Schema
                    - Deliverables: models/user.py, models/resource.py, migrations/
                    - Acceptance Criteria: Models created, migrations run successfully
                    - Priority: High
                    
                    IMPORTANT: For vague requirements, assume the user wants an MVP implementation with all basic-standard features.
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm=llm)
    )
    
    response = await agent.run(prompt="Create a detailed project plan for: " + str(input))
    yield MessagePart(content=response.result.text)
