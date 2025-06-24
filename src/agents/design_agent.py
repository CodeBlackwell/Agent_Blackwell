"""
Design Agent for generating architecture diagrams and API contracts.

This agent uses LangChain and OpenAI to generate Mermaid diagrams and API specifications
based on task descriptions.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class DiagramSpec(BaseModel):
    """Specification for a diagram."""

    diagram_type: str = Field(description="Type of diagram (class, sequence, flow, er)")
    mermaid_code: str = Field(description="Mermaid syntax for the diagram")
    description: str = Field(description="Description of what the diagram represents")


class ApiEndpoint(BaseModel):
    """Specification for an API endpoint."""

    path: str = Field(description="Endpoint path")
    method: str = Field(description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    description: str = Field(description="Description of the endpoint")
    request_schema: Optional[Dict] = Field(
        description="JSON schema for request body", default=None
    )
    response_schema: Optional[Dict] = Field(
        description="JSON schema for response body", default=None
    )
    parameters: Optional[List[Dict]] = Field(
        description="URL or query parameters", default=None
    )


class ApiContract(BaseModel):
    """API contract specification."""

    title: str = Field(description="API title")
    version: str = Field(description="API version")
    description: str = Field(description="API description")
    endpoints: List[ApiEndpoint] = Field(description="List of API endpoints")


class DesignOutput(BaseModel):
    """Output from the Design Agent."""

    diagrams: List[DiagramSpec] = Field(
        description="List of generated diagrams", default_factory=list
    )
    api_contract: Optional[ApiContract] = Field(
        description="API contract if applicable", default=None
    )


class DesignAgent:
    """
    Agent for generating architecture diagrams and API contracts.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the Design Agent.

        Args:
            openai_api_key: API key for OpenAI (required for production)
        """
        # Load the prompt template from file
        prompt_path = (
            Path(__file__).parent.parent / "prompts" / "design_agent_prompt.txt"
        )

        with open(prompt_path, "r") as f:
            prompt_template = f.read()

        # Define the prompt template for design generation
        self.prompt_template = PromptTemplate(
            input_variables=["task_description", "additional_context"],
            template=prompt_template,
        )

        # Initialize the LLM
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            temperature=0.2,  # Lower temperature for more deterministic outputs
            model="gpt-4",  # Using GPT-4 for better diagram generation
        )

        # Create the chain using the pipe operator pattern (replacing deprecated LLMChain)
        self.chain = self.prompt_template | self.llm

        logger.info("DesignAgent initialized")

    async def generate_design(
        self, task_description: str, additional_context: str = ""
    ) -> Union[DesignOutput, str]:
        """
        Generate architecture diagrams and API contracts based on the task description.

        Args:
            task_description: Description of the task to design for
            additional_context: Any additional context that might help with design

        Returns:
            DesignOutput object containing diagrams and API contract, or error message
        """
        try:
            logger.info(f"Generating design for task: {task_description[:50]}...")

            # Generate design using the LLM chain
            result = await self.chain.ainvoke(
                {
                    "task_description": task_description,
                    "additional_context": additional_context,
                }
            )

            # Extract the content from the result
            content = result["text"]

            # Parse the content to extract diagrams and API contract
            # This is a simplified version - in a real implementation, we would need
            # more robust parsing logic to extract Mermaid diagrams and API specs

            # For now, we'll return the raw content
            return content

            # In a more complete implementation, we would parse the content and return:
            # return DesignOutput(
            #     diagrams=[...],
            #     api_contract=...
            # )

        except Exception as e:
            error_msg = f"Error generating design: {str(e)}"
            logger.error(error_msg)
            return error_msg


class DesignAgentWrapper:
    """Wrapper for the Design Agent to integrate with the orchestrator."""

    def __init__(self, agent: DesignAgent):
        """Initialize with a Design Agent instance."""
        self.agent = agent

    async def process_task(self, task_data: Dict) -> Dict:
        """
        Process a task using the Design Agent.

        Args:
            task_data: Task data from the orchestrator

        Returns:
            Result dictionary with generated design
        """
        task_description = task_data.get("description", "")
        additional_context = task_data.get("metadata", {}).get("context", "")

        # Generate design
        result = await self.agent.generate_design(task_description, additional_context)

        # Prepare result
        if isinstance(result, str):
            # If result is a string (either raw output or error message)
            return {
                "task_id": task_data.get("task_id"),
                "status": "completed" if "Error" not in result else "error",
                "result": result,
                "agent_type": "design",
            }
        else:
            # If result is a DesignOutput object
            return {
                "task_id": task_data.get("task_id"),
                "status": "completed",
                "result": result.dict(),
                "agent_type": "design",
            }
