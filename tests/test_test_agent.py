"""
Unit tests for the Test Agent.
"""

import json
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.agents.test_agent import TestAgent


class TestTestAgent:
    """Test suite for the Test Agent."""

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
        agent = TestAgent(openai_api_key="test_key")

        # Assert
        assert agent is not None
        assert agent.openai_api_key == "test_key"
        mock_file_read.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.agents.test_agent.ChatOpenAI")
    async def test_generate_tests_valid_json_response(
        self, mock_chat_openai, mock_file_read
    ):
        """Test generating tests with a valid JSON response."""
        # Arrange
        mock_llm = AsyncMock()
        mock_llm_chain = MagicMock()
        mock_llm_chain.arun = AsyncMock(
            return_value=json.dumps(
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
        )
        mock_chat_openai.return_value = mock_llm

        with patch("src.agents.test_agent.LLMChain", return_value=mock_llm_chain):
            agent = TestAgent(openai_api_key="test_key")

            # Act
            code_files = [
                {"path": "example.py", "content": "def hello(): return 'world'"}
            ]
            result = await agent.generate_tests(code_files)

            # Assert
            mock_llm_chain.arun.assert_called_once()
            assert "test_files" in result
            assert len(result["test_files"]) == 1
            assert result["test_files"][0]["path"] == "test_example.py"
            assert "coverage_report" in result
            assert result["coverage_report"]["overall_coverage"] == "90%"

    @pytest.mark.asyncio
    @patch("src.agents.test_agent.ChatOpenAI")
    async def test_generate_tests_invalid_json_response(
        self, mock_chat_openai, mock_file_read
    ):
        """Test generating tests with an invalid JSON response."""
        # Arrange
        mock_llm = AsyncMock()
        mock_llm_chain = MagicMock()
        mock_llm_chain.arun = AsyncMock(
            return_value="""
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
        )
        mock_chat_openai.return_value = mock_llm

        with patch("src.agents.test_agent.LLMChain", return_value=mock_llm_chain):
            agent = TestAgent(openai_api_key="test_key")

            # Act
            code_files = [
                {"path": "example.py", "content": "def hello(): return 'world'"}
            ]
            result = await agent.generate_tests(code_files)

            # Assert
            mock_llm_chain.arun.assert_called_once()
            assert "test_files" in result
            assert len(result["test_files"]) == 1
            assert "coverage_report" in result
            assert result["coverage_report"]["overall_coverage"] == "85%"

    @pytest.mark.asyncio
    @patch("src.agents.test_agent.ChatOpenAI")
    async def test_generate_tests_completely_invalid_response(
        self, mock_chat_openai, mock_file_read
    ):
        """Test generating tests with a completely invalid response."""
        # Arrange
        mock_llm = AsyncMock()
        mock_llm_chain = MagicMock()
        mock_llm_chain.arun = AsyncMock(
            return_value="Here are some tests that don't include any JSON"
        )
        mock_chat_openai.return_value = mock_llm

        with patch("src.agents.test_agent.LLMChain", return_value=mock_llm_chain):
            agent = TestAgent(openai_api_key="test_key")

            # Act
            code_files = [
                {"path": "example.py", "content": "def hello(): return 'world'"}
            ]
            result = await agent.generate_tests(code_files)

            # Assert
            mock_llm_chain.arun.assert_called_once()
            assert "test_files" in result
            assert len(result["test_files"]) == 1
            assert "coverage_report" in result
            assert result["coverage_report"]["overall_coverage"] == "Unknown"

    @pytest.mark.asyncio
    @patch("src.agents.test_agent.ChatOpenAI")
    async def test_generate_tests_exception_handling(
        self, mock_chat_openai, mock_file_read
    ):
        """Test exception handling in generate_tests."""
        # Arrange
        mock_llm = AsyncMock()
        mock_llm_chain = MagicMock()
        mock_llm_chain.arun = AsyncMock(side_effect=Exception("Test error"))
        mock_chat_openai.return_value = mock_llm

        with patch("src.agents.test_agent.LLMChain", return_value=mock_llm_chain):
            agent = TestAgent(openai_api_key="test_key")

            # Act & Assert
            code_files = [
                {"path": "example.py", "content": "def hello(): return 'world'"}
            ]
            with pytest.raises(Exception):
                await agent.generate_tests(code_files)
