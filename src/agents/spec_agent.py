"""
Requirements/Specification Agent.

This agent is responsible for extracting tasks from user requests and
generating structured task specifications using LangChain.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate
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
    description: str = Field(
        description="Detailed description of what needs to be done"
    )
    priority: str = Field(description="Priority level (high, medium, low)")
    estimated_hours: float = Field(description="Estimated hours to complete")
    dependencies: List[str] = Field(
        default_factory=list, description="List of task IDs this task depends on"
    )
    assignee: Optional[str] = Field(
        default=None, description="Agent type that should handle this task"
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

    This agent uses LangChain and an LLM
    to analyze user requests and break them
    down into structured tasks
    -- with priorities, estimates, and dependencies.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the SpecAgent.

        Args:
            openai_api_key: API key for OpenAI (required for production)
        """
        # Load the prompt template from file
        prompt_path = Path(__file__).parent.parent / "prompts" / "spec_agent_prompt.txt"

        with open(prompt_path, "r") as f:
            prompt_template = f.read()
        # Define the prompt template for task extraction
        self.prompt_template = PromptTemplate(
            input_variables=["user_request"],
            template=prompt_template,
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
    import asyncio

    asyncio.run(main())
