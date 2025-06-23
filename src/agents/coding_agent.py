"""
Coding Agent Module

This module implements the Coding Agent, which generates code based on task descriptions,
design specifications, and architectural diagrams.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class CodingAgent:
    """
    CodingAgent generates code based on task descriptions and design specifications.
    It uses LangChain and OpenAI's GPT models to generate code that follows best practices.
    """

    def __init__(self, openai_api_key: str, model_name: str = "gpt-4"):
        """
        Initialize the CodingAgent with OpenAI API credentials.

        Args:
            openai_api_key: The API key for OpenAI.
            model_name: The name of the model to use (default: "gpt-4").
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=openai_api_key,
            temperature=0.2,
        )
        self._load_prompt_template()

    def _load_prompt_template(self) -> None:
        """Load the prompt template from the file."""
        prompt_path = (
            Path(os.path.dirname(os.path.dirname(__file__)))
            / "prompts"
            / "coding_agent_prompt.txt"
        )

        try:
            with open(prompt_path, "r") as f:
                prompt_content = f.read()

            self.prompt_template = PromptTemplate(
                input_variables=[
                    "task_description",
                    "design_specs",
                    "architecture_diagram",
                ],
                template=prompt_content,
            )

            self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        except FileNotFoundError:
            logger.error(f"Prompt file not found at {prompt_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading prompt template: {e}")
            raise

    async def generate_code(
        self,
        task_description: str,
        design_specs: Optional[str] = None,
        architecture_diagram: Optional[str] = None,
    ) -> Dict[str, Union[List[Dict[str, str]], str]]:
        """
        Generate code based on task description, design specs, and architecture diagram.

        Args:
            task_description: A description of the coding task.
            design_specs: Optional API contracts or design specifications.
            architecture_diagram: Optional Mermaid diagram of the architecture.

        Returns:
            A dictionary containing generated files and an explanation.
        """
        try:
            # Prepare inputs with empty strings for optional parameters if not provided
            inputs = {
                "task_description": task_description,
                "design_specs": design_specs or "",
                "architecture_diagram": architecture_diagram or "",
            }

            # Run the chain to generate code
            result = await self.chain.arun(**inputs)

            # Parse the result - it should be in JSON format
            # In a production system, we'd add more robust parsing and validation here
            import json

            try:
                # Try to parse as JSON
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError:
                # If not valid JSON, return as raw text with a warning
                logger.warning(
                    "Generated code is not in valid JSON format. Returning raw output."
                )
                if not (
                    isinstance(result, dict)
                    and "files" in result
                    and isinstance(result["files"], list)
                ):
                    return {
                        "files": [
                            {
                                "path": "generated_code.py",
                                "content": result,
                                "description": "Generated code (not in expected format)",
                            }
                        ],
                        "explanation": "The model did not return properly formatted JSON. Raw output provided.",
                    }

        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return {"files": [], "explanation": f"Error generating code: {str(e)}"}
