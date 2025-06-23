"""
Review Agent module for analyzing code quality and security.

This module provides the ReviewAgent class that uses LLMs to analyze code
for linting issues, security vulnerabilities, and quality problems.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Union

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class ReviewAgent:
    """
    Agent for reviewing and analyzing code quality and security.

    Uses LLMs to perform static analysis, identify potential bugs,
    security vulnerabilities, and code quality issues.
    """

    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o") -> None:
        """
        Initialize the Review Agent.

        Args:
            openai_api_key: The OpenAI API key for accessing the LLM.
            model_name: The name of the model to use for code review.
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name

        self.llm = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.openai_api_key,
            temperature=0.1,
        )
        self._load_prompt_template()

    def _load_prompt_template(self) -> None:
        """Load the prompt template from the file."""
        prompt_path = (
            Path(os.path.dirname(os.path.dirname(__file__)))
            / "prompts"
            / "review_agent_prompt.txt"
        )

        try:
            with open(prompt_path, "r") as f:
                prompt_content = f.read()

            self.prompt_template = PromptTemplate(
                input_variables=["code_files"],
                template=prompt_content,
            )

            self.chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt_template,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
            raise

    async def review_code(
        self, code_files: Union[str, Dict[str, str], List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """
        Analyze code for quality and security issues.

        Args:
            code_files: The code to analyze. Can be:
                - A string containing the code content
                - A dict with "path" and "content" keys
                - A list of dicts with "path" and "content" keys

        Returns:
            Dict containing analysis results with linting, security, and quality issues.
        """
        logger.info("Running code review analysis")
        formatted_code_files = self._format_code_input(code_files)

        try:
            result = await self.chain.arun(code_files=formatted_code_files)

            # Try to parse the JSON response
            try:
                # Find JSON within the text if it's not a clean JSON response
                json_start = result.find("{")
                json_end = result.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = result[json_start:json_end]
                    return json.loads(json_str)

                # If we couldn't find JSON, return a default structure
                logger.warning("Could not find JSON in the response")
                return self._create_default_response("Could not parse response as JSON")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON response: {e}")
                return self._create_default_response(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return self._create_default_response(f"Error during analysis: {str(e)}")

    def _format_code_input(
        self, code_files: Union[str, Dict[str, str], List[Dict[str, str]]]
    ) -> str:
        """
        Format the code input to be passed to the LLM.

        Args:
            code_files: The code to analyze. Can be a string, dict, or list of dicts.

        Returns:
            A formatted string representation of the code files.
        """
        if isinstance(code_files, str):
            return f"```\n{code_files}\n```"

        elif isinstance(code_files, dict):
            if "path" in code_files and "content" in code_files:
                return f"File: {code_files['path']}\n```\n{code_files['content']}\n```"
            else:
                formatted_files = []
                for file_path, content in code_files.items():
                    formatted_files.append(f"File: {file_path}\n```\n{content}\n```")
                return "\n\n".join(formatted_files)

        elif isinstance(code_files, list):
            formatted_files = []
            for file_dict in code_files:
                if "path" in file_dict and "content" in file_dict:
                    formatted_files.append(
                        f"File: {file_dict['path']}\n```\n{file_dict['content']}\n```"
                    )
            return "\n\n".join(formatted_files)

        return str(code_files)

    def _create_default_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create a default response structure when the normal flow fails.

        Args:
            error_message: The error message to include.

        Returns:
            A default response structure.
        """
        return {
            "summary": {
                "linting_score": 0,
                "security_score": 0,
                "quality_score": 0,
                "overall_score": 0,
                "key_findings": [error_message],
            },
            "linting_issues": [],
            "security_issues": [],
            "quality_issues": [],
            "general_recommendations": [
                "Try reviewing the code with a more specific query",
                "Check if the code syntax is valid",
            ],
        }
