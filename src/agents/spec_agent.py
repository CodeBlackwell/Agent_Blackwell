"""
Requirements/Specification Agent.

This agent is responsible for extracting tasks from user requests and generating
structured task specifications using LangChain.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from langchain_community.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Task(BaseModel):
    """Task model representing a single task extracted from a user request."""
    
    task_id: str = Field(description="Unique identifier for the task")
    title: str = Field(description="Short descriptive title for the task")
    description: str = Field(description="Detailed description of what needs to be done")
    priority: str = Field(description="Priority level (high, medium, low)")
    estimated_hours: float = Field(description="Estimated hours to complete")
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of task IDs this task depends on"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Agent type that should handle this task"
    )


class TaskListOutputParser(BaseOutputParser):
    """Parser that converts LLM output to a list of Task objects."""
    
    def parse(self, text: str) -> List[Task]:
        """
        Parse the LLM output into a list of Task objects.
        
        Args:
            text: Raw text output from the LLM
            
        Returns:
            List of Task objects
        """
        try:
            # Extract JSON from the text (in case there's additional text)
            json_start = text.find("[")
            json_end = text.rfind("]") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in the output")
                
            json_str = text[json_start:json_end]
            tasks_data = json.loads(json_str)
            
            # Convert to Task objects
            tasks = [Task(**task_data) for task_data in tasks_data]
            return tasks
            
        except Exception as e:
            logger.error(f"Error parsing tasks: {e}")
            logger.error(f"Raw text: {text}")
            return []


class SpecAgent:
    """
    Agent that extracts tasks from user requests.
    
    This agent uses LangChain and an LLM to analyze user requests and break them down
    into structured tasks with priorities, estimates, and dependencies.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the SpecAgent.
        
        Args:
            openai_api_key: API key for OpenAI (required for production)
        """
        # Define the prompt template for task extraction
        self.prompt_template = PromptTemplate(
            input_variables=["user_request"],
            template="""
            You are a requirements analyst and project manager. Your job is to analyze a user's feature request
            and break it down into specific, actionable tasks that can be assigned to different specialized agents.
            
            User Request:
            {user_request}
            
            Extract a list of tasks from this request. For each task, provide:
            1. A unique task_id (format: T-001, T-002, etc.)
            2. A short, descriptive title
            3. A detailed description of what needs to be done
            4. Priority (high, medium, low)
            5. Estimated hours to complete
            6. Dependencies (list of task_ids this task depends on)
            7. Assignee (which type of agent should handle this task):
               - spec_agent: For requirements analysis
               - design_agent: For architecture and diagrams
               - coding_agent: For code implementation
               - review_agent: For code review and quality checks
               - test_agent: For test creation and execution
            
            Format your response as a JSON array of task objects. Example:
            [
                {{
                    "task_id": "T-001",
                    "title": "Extract user requirements",
                    "description": "Analyze the user request and identify key requirements and constraints",
                    "priority": "high",
                    "estimated_hours": 0.5,
                    "dependencies": [],
                    "assignee": "spec_agent"
                }},
                {{
                    "task_id": "T-002",
                    "title": "Design database schema",
                    "description": "Create an entity-relationship diagram for the required data model",
                    "priority": "high",
                    "estimated_hours": 1.0,
                    "dependencies": ["T-001"],
                    "assignee": "design_agent"
                }}
            ]
            
            Be thorough and make sure all tasks are properly connected through dependencies.
            """
        )
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4",
            api_key=openai_api_key,
        )
        
        # Create the chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_template,
            output_parser=TaskListOutputParser(),
        )
        
        logger.info("SpecAgent initialized")
    
    async def generate_tasks(self, user_request: str) -> List[Task]:
        """
        Generate tasks from a user request.
        
        Args:
            user_request: Raw text of the user's feature request
            
        Returns:
            List of Task objects
        """
        try:
            # Run the chain
            tasks = await self.chain.ainvoke({"user_request": user_request})
            
            logger.info(f"Generated {len(tasks)} tasks from user request")
            return tasks
            
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            return []


# Example usage
async def main():
    """Example usage of the SpecAgent."""
    import os
    import asyncio
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize agent
    agent = SpecAgent(openai_api_key=api_key)
    
    # Example request
    user_request = """
    I need a simple web application that allows users to upload CSV files,
    visualize the data as charts, and download the charts as images.
    """
    
    # Generate tasks
    tasks = await agent.generate_tasks(user_request)
    
    # Print tasks
    for task in tasks:
        print(f"Task: {task.title}")
        print(f"Description: {task.description}")
        print(f"Priority: {task.priority}")
        print(f"Estimate: {task.estimated_hours} hours")
        print(f"Assignee: {task.assignee}")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())
