"""
Unit tests for the Test Agent.
"""

import json
from unittest.mock import AsyncMock, mock_open, patch

import pytest

from src.agents.test_agent import TestGeneratorAgent


class TestTestAgent:
    """Tests for the Test Generator Agent."""

    __test__ = True  # Mark this class as containing tests

    @pytest.fixture
    def mock_file_read(self):
        """Mock file read operations."""
        with patch("builtins.open", mock_open()) as mock_file:
            # Create a mock file object with a read method
            mock_file_handle = mock_file.return_value.__enter__.return_value
            mock_file_handle.read.return_value = "Test Agent Prompt: {code_files}"
            yield mock_file

    def test_init(self, mock_file_read):
        """Test initialization of the Test Agent."""
        # Act
        agent = TestGeneratorAgent(openai_api_key="test_key")

        # Assert
        assert agent is not None
        assert agent.openai_api_key == "test_key"
        mock_file_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_tests_valid_json_response(self, mock_file_read):
        """Test generating tests with a valid JSON response."""
        # Expected response from the chain
        expected_response = json.dumps(
            {
                "test_files": [
                    {
                        "path": "test_example.py",
                        "content": "def test_something(): assert True",
                    }
                ],
                "coverage_report": {
                    "overall_coverage": "90%",
                    "notes": "Good coverage",
                },
            }
        )

        # Initialize the agent
        agent = TestGeneratorAgent(openai_api_key="test_key")

        # Replace the chain with a mock
        agent.chain = AsyncMock()
        agent.chain.arun = AsyncMock(return_value=expected_response)

        # Act
        code_files = [{"path": "example.py", "content": "def hello(): return 'world'"}]
        result = await agent.generate_tests(code_files)

        # Assert
        agent.chain.arun.assert_called_once()
        assert "test_files" in result
        assert len(result["test_files"]) == 1
        assert result["test_files"][0]["path"] == "test_example.py"
        assert "coverage_report" in result
        assert result["coverage_report"]["overall_coverage"] == "90%"

    @pytest.mark.asyncio
    async def test_generate_tests_invalid_json_response(self, mock_file_read):
        """Test generating tests with an invalid JSON response."""
        # Prepare a response with JSON embedded in text
        invalid_json_response = """
        Here are the tests:

        {
            "test_files": [
                {
                    "path": "test_example.py",
                    "content": "def test_something(): assert True"
                }
            ],
            "coverage_report": {
                "overall_coverage": "85%",
                "notes": "Good coverage"
            }
        }
        """

        # Initialize the agent
        agent = TestGeneratorAgent(openai_api_key="test_key")

        # Replace the chain with a mock
        agent.chain = AsyncMock()
        agent.chain.arun = AsyncMock(return_value=invalid_json_response)

        # Act
        code_files = [{"path": "example.py", "content": "def hello(): return 'world'"}]
        result = await agent.generate_tests(code_files)

        # Assert
        agent.chain.arun.assert_called_once()
        assert "test_files" in result
        assert len(result["test_files"]) == 1
        assert "coverage_report" in result
        assert result["coverage_report"]["overall_coverage"] == "85%"

    @pytest.mark.asyncio
    async def test_generate_tests_completely_invalid_response(self, mock_file_read):
        """Test generating tests with a completely invalid response."""
        # Prepare a completely invalid response
        invalid_response = "Here are some tests that don't include any JSON"

        # Initialize the agent
        agent = TestGeneratorAgent(openai_api_key="test_key")

        # Replace the chain with a mock
        agent.chain = AsyncMock()
        agent.chain.arun = AsyncMock(return_value=invalid_response)

        # Act
        code_files = [{"path": "example.py", "content": "def hello(): return 'world'"}]
        result = await agent.generate_tests(code_files)

        # Assert
        agent.chain.arun.assert_called_once()
        assert "test_files" in result
        assert len(result["test_files"]) == 1
        assert "coverage_report" in result
        assert result["coverage_report"]["overall_coverage"] == "Unknown"

    @pytest.mark.asyncio
    async def test_generate_tests_exception_handling(self, mock_file_read):
        """Test exception handling in generate_tests."""
        # Initialize the agent
        agent = TestGeneratorAgent(openai_api_key="test_key")

        # Replace the chain with a mock that raises an exception
        agent.chain = AsyncMock()
        agent.chain.arun = AsyncMock(side_effect=Exception("Test error"))

        # Act & Assert
        code_files = [{"path": "example.py", "content": "def hello(): return 'world'"}]
        with pytest.raises(Exception):
            await agent.generate_tests(code_files)
