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

from agents.agent_configs import feature_coder_config

# Load environment variables from .env file
load_dotenv()


async def feature_coder_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for implementing specific features in an existing codebase"""
    llm = ChatModel.from_name(feature_coder_config["model"])
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a feature implementation specialist. Your role is to:
                    1. Implement SPECIFIC features in an EXISTING codebase
                    2. Modify and extend existing code rather than creating new projects
                    3. Focus only on the requested feature
                    4. Preserve all existing functionality
                    5. Follow the code style and patterns already established
                    
                    CRITICAL RULES:
                    - NEVER create a new project or use "PROJECT CREATED" format
                    - NEVER generate timestamps or project folders
                    - ONLY show the code for files you're modifying or creating
                    - Always build upon the existing code provided
                    - If no existing code is provided, create minimal initial structure
                    
                    OUTPUT FORMAT:
                    For each file, use this exact format:
                    
                    ```language
                    # filename: path/to/file.ext
                    <complete file contents>
                    ```
                    
                    Example:
                    ```python
                    # filename: calculator.py
                    class Calculator:
                        def __init__(self):
                            self.result = 0
                        
                        def add(self, a, b):
                            return a + b
                    ```
                    
                    IMPORTANT:
                    - Show the COMPLETE file contents, not just the changes
                    - Include all necessary imports and existing code
                    - Each file should be runnable and complete
                    - Do not include any explanatory text outside of code blocks
                    - Do not create README files unless specifically requested
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt=str(input))
    
    # Return just the response text without any file creation or project metadata
    yield Message(parts=[MessagePart(content=response.result.text, content_type="text/plain")])