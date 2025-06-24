"""
Test Agent module for generating comprehensive test suites.

This module provides the TestAgent class that uses LLMs to analyze code
and generate appropriate unit and integration tests.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class TestGeneratorAgent:
    """
    Agent responsible for generating comprehensive test suites for code modules.

    This agent analyzes code files and generates appropriate unit and integration tests
    following best practices and achieving high test coverage.
    """

    # Prevent pytest from collecting this class as a test class
    __test__ = False

    def __init__(self, openai_api_key: str):
        """
        Initialize the Test Agent with required parameters.

        Args:
            openai_api_key: API key for OpenAI service
        """
        self.openai_api_key = openai_api_key
        self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Initialize the language model and chain for test generation."""
        try:
            # Load the prompt template from file
            current_dir = Path(__file__).parent.parent
            prompt_path = current_dir / "prompts" / "test_agent_prompt.txt"

            with open(prompt_path, "r") as f:
                prompt_template = f.read()

            # Initialize the language model
            llm = ChatOpenAI(
                model="gpt-4", temperature=0.2, openai_api_key=self.openai_api_key
            )

            # Create the prompt template
            prompt = PromptTemplate(
                template=prompt_template, input_variables=["code_files"]
            )

            # Create the chain using pipe operator pattern (replacing deprecated LLMChain)
            self.chain = prompt | llm
            logger.info("Test Agent LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Test Agent LLM: {e}")
            raise

    async def generate_tests(self, code_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate tests for the provided code files.

        Args:
            code_files: List of dictionaries containing 'path' and 'content' keys
                        for each code file to test

        Returns:
            Dictionary containing test files with their content and coverage metrics
        """
        try:
            # Format the code files for the prompt
            code_files_json = json.dumps(code_files, indent=2)

            # Run the chain to generate tests
            result = await self.chain.arun(code_files=code_files_json)

            # Parse the LLM response
            try:
                # First, try to parse the response as JSON
                test_suite = json.loads(result)
            except json.JSONDecodeError:
                # If not a valid JSON, try to extract a JSON object
                start_idx = result.find("{")
                end_idx = result.rfind("}") + 1

                if start_idx != -1 and end_idx != 0:
                    json_str = result[start_idx:end_idx]
                    try:
                        test_suite = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If still not valid, create a structured response
                        test_suite = {
                            "test_files": [
                                {
                                    "path": f"test_{Path(code_file['path']).name}",
                                    "content": result,
                                }
                                for code_file in code_files
                            ],
                            "coverage_report": {
                                "overall_coverage": "Unknown",
                                "notes": "Could not parse coverage information",
                            },
                        }
                else:
                    # Create a basic structured response
                    test_suite = {
                        "test_files": [
                            {
                                "path": f"test_{Path(code_file['path']).name}",
                                "content": result,
                            }
                            for code_file in code_files
                        ],
                        "coverage_report": {
                            "overall_coverage": "Unknown",
                            "notes": "Could not parse coverage information",
                        },
                    }

            # Ensure the response has the expected structure
            if "test_files" not in test_suite:
                test_suite["test_files"] = []

            if "coverage_report" not in test_suite:
                test_suite["coverage_report"] = {
                    "overall_coverage": "Unknown",
                    "notes": "Coverage information not provided",
                }

            logger.info(f"Generated {len(test_suite['test_files'])} test files")
            return test_suite
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            raise
