"""
Unit tests for the Review Agent.
"""

import json
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.agents.review_agent import ReviewAgent


class TestReviewAgent:
    """Test suite for the Review Agent."""

    @pytest.fixture
    def mock_file_read(self):
        """Mock file read operations."""
        with patch("builtins.open", mock_open()) as mock_file:
            # Create a mock file object with a read method
            mock_file_handle = mock_file.return_value.__enter__.return_value

            # Define the read method behavior based on file path
            def side_effect(*args, **kwargs):
                # Get the file path from the mock_calls
                for call in mock_file.mock_calls:
                    if call[0] == "()":
                        file_path = call[1][0]
                        if "review_agent_prompt.txt" in file_path:
                            return (
                                "You are a Review Agent. Review code for: {code_files}"
                            )
                return "Default mock content"

            mock_file_handle.read.side_effect = side_effect
            yield mock_file

    @pytest.fixture
    def review_agent(self, mock_file_read):
        """Create a Review Agent instance for testing."""
        return ReviewAgent(openai_api_key="fake-api-key")

    def test_init(self, mock_file_read):
        """Test that the Review Agent initializes correctly."""
        # Arrange & Act
        agent = ReviewAgent(openai_api_key="fake-api-key")

        # Assert
        assert agent.openai_api_key == "fake-api-key"
        assert agent.model_name == "gpt-4o"  # Default model
        assert hasattr(agent, "llm")
        assert hasattr(agent, "chain")
        assert hasattr(agent, "prompt_template")

    def test_init_with_custom_model(self, mock_file_read):
        """Test that the Review Agent initializes with a custom model."""
        # Arrange & Act
        agent = ReviewAgent(openai_api_key="fake-api-key", model_name="gpt-3.5-turbo")

        # Assert
        assert agent.model_name == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.LLMChain")
    async def test_review_code_with_string(self, mock_llm_chain, review_agent):
        """Test reviewing code with a string input."""
        # Arrange
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(
            return_value=json.dumps(
                {
                    "summary": {
                        "linting_score": 7,
                        "security_score": 8,
                        "quality_score": 7,
                        "overall_score": 7.5,
                        "key_findings": [
                            "Good code structure",
                            "Missing input validation",
                        ],
                    },
                    "linting_issues": [],
                    "security_issues": [],
                    "quality_issues": [],
                }
            )
        )
        mock_llm_chain.return_value = mock_chain_instance
        review_agent.chain = mock_chain_instance

        # Act
        code = "def hello_world():\n    return 'Hello, World!'"
        result = await review_agent.review_code(code)

        # Assert
        mock_chain_instance.arun.assert_called_once()
        assert "summary" in result
        assert result["summary"]["overall_score"] == 7.5
        assert len(result["summary"]["key_findings"]) == 2

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.LLMChain")
    async def test_review_code_with_dict(self, mock_llm_chain, review_agent):
        """Test reviewing code with a dictionary input."""
        # Arrange
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(
            return_value=json.dumps(
                {
                    "summary": {
                        "linting_score": 6,
                        "security_score": 5,
                        "quality_score": 6,
                        "overall_score": 5.7,
                        "key_findings": ["SQL injection vulnerability"],
                    },
                    "linting_issues": [],
                    "security_issues": [{"severity": "high"}],
                    "quality_issues": [],
                }
            )
        )
        mock_llm_chain.return_value = mock_chain_instance
        review_agent.chain = mock_chain_instance

        # Act
        code_file = {
            "path": "app.py",
            "content": 'def get_user(user_id):\n    query = f"SELECT * FROM users WHERE id = {user_id}"\n    return db.execute(query)',
        }
        result = await review_agent.review_code(code_file)

        # Assert
        mock_chain_instance.arun.assert_called_once()
        assert result["summary"]["overall_score"] == 5.7
        assert len(result["security_issues"]) == 1
        assert result["security_issues"][0]["severity"] == "high"

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.LLMChain")
    async def test_review_code_with_list(self, mock_llm_chain, review_agent):
        """Test reviewing code with a list of dictionaries input."""
        # Arrange
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(
            return_value=json.dumps(
                {
                    "summary": {
                        "linting_score": 8,
                        "security_score": 9,
                        "quality_score": 8,
                        "overall_score": 8.3,
                        "key_findings": ["Good practices", "Well-documented"],
                    },
                    "linting_issues": [],
                    "security_issues": [],
                    "quality_issues": [],
                }
            )
        )
        mock_llm_chain.return_value = mock_chain_instance
        review_agent.chain = mock_chain_instance

        # Act
        code_files = [
            {
                "path": "math_utils.py",
                "content": 'def add(a, b):\n    """Add two numbers."""\n    return a + b',
            },
            {
                "path": "string_utils.py",
                "content": 'def concat(a, b):\n    """Concatenate two strings."""\n    return str(a) + str(b)',
            },
        ]
        result = await review_agent.review_code(code_files)

        # Assert
        mock_chain_instance.arun.assert_called_once()
        assert result["summary"]["overall_score"] == 8.3
        assert len(result["summary"]["key_findings"]) == 2

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.LLMChain")
    async def test_review_code_with_invalid_json(self, mock_llm_chain, review_agent):
        """Test handling of invalid JSON response."""
        # Arrange
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(return_value="This is not valid JSON")
        mock_llm_chain.return_value = mock_chain_instance
        review_agent.chain = mock_chain_instance

        # Act
        result = await review_agent.review_code("def test(): pass")

        # Assert
        assert "summary" in result
        assert result["summary"]["overall_score"] == 0
        assert len(result["summary"]["key_findings"]) > 0
        assert (
            "Could not parse response as JSON" in result["summary"]["key_findings"][0]
        )

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.LLMChain")
    async def test_review_code_with_exception(self, mock_llm_chain, review_agent):
        """Test handling of exceptions during code review."""
        # Arrange
        mock_chain_instance = MagicMock()
        mock_chain_instance.arun = AsyncMock(side_effect=Exception("Test error"))
        mock_llm_chain.return_value = mock_chain_instance
        review_agent.chain = mock_chain_instance

        # Act
        result = await review_agent.review_code("def test(): pass")

        # Assert
        assert "summary" in result
        assert result["summary"]["overall_score"] == 0
        assert "Error during analysis" in result["summary"]["key_findings"][0]

    def test_format_code_input_string(self, review_agent):
        """Test formatting of string code input."""
        # Arrange
        code = "def test(): pass"

        # Act
        result = review_agent._format_code_input(code)

        # Assert
        assert result == "```\ndef test(): pass\n```"

    def test_format_code_input_dict_with_path(self, review_agent):
        """Test formatting of dictionary code input with path and content."""
        # Arrange
        code_dict = {"path": "test.py", "content": "def test(): pass"}

        # Act
        result = review_agent._format_code_input(code_dict)

        # Assert
        assert "File: test.py" in result
        assert "def test(): pass" in result

    def test_format_code_input_dict_with_files(self, review_agent):
        """Test formatting of dictionary code input with files."""
        # Arrange
        code_dict = {
            "test.py": "def test(): pass",
            "utils.py": "def util(): return True",
        }

        # Act
        result = review_agent._format_code_input(code_dict)

        # Assert
        assert "File: test.py" in result
        assert "File: utils.py" in result
        assert "def test(): pass" in result
        assert "def util(): return True" in result

    def test_format_code_input_list(self, review_agent):
        """Test formatting of list code input."""
        # Arrange
        code_list = [
            {"path": "test.py", "content": "def test(): pass"},
            {"path": "utils.py", "content": "def util(): return True"},
        ]

        # Act
        result = review_agent._format_code_input(code_list)

        # Assert
        assert "File: test.py" in result
        assert "File: utils.py" in result
        assert "def test(): pass" in result
        assert "def util(): return True" in result
