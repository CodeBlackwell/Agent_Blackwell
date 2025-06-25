"""
Unit tests for the Coding Agent.
"""

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.agents.coding_agent import CodingAgent


class TestCodingAgent:
    """Test suite for the Coding Agent."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        mock = MagicMock()
        mock.ainvoke = AsyncMock()
        return mock

    @pytest.fixture
    def mock_prompt_content(self):
        """Return mock prompt content for testing."""
        return "You are a Coding Agent. Generate code based on: {task_description}, {design_specs}, {architecture_diagram}"

    @patch("src.agents.coding_agent.ChatOpenAI")
    @patch("src.agents.coding_agent.PromptTemplate")
    @patch("builtins.open", new_callable=mock_open, read_data="You are a Coding Agent")
    def test_initialization(self, mock_file, mock_prompt, mock_chat_openai):
        """Test that the Coding Agent initializes correctly."""
        # Arrange
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        mock_prompt_instance = MagicMock()
        mock_prompt.return_value = mock_prompt_instance

        # Mock the pipe operation
        mock_prompt_instance.__or__ = MagicMock(return_value=MagicMock())

        # Act
        agent = CodingAgent(openai_api_key="fake-api-key")

        # Assert
        mock_chat_openai.assert_called_once()
        mock_prompt.assert_called_once()
        mock_prompt_instance.__or__.assert_called_once_with(mock_chat_instance)
        assert agent.openai_api_key == "fake-api-key"
        assert agent.model_name == "gpt-4"
        assert agent.llm == mock_chat_instance

    @patch("builtins.open", new_callable=mock_open, read_data="You are a Coding Agent")
    def test_load_prompt_template_file_not_found(self, mock_file):
        """Test handling of FileNotFoundError when loading prompt template."""
        # Arrange
        mock_file.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            CodingAgent(openai_api_key="fake-api-key")

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data="You are a Coding Agent")
    async def test_generate_code_success(self, mock_file):
        """Test successful code generation."""
        # Arrange
        mock_result = """
        {
            "files": [
                {
                    "path": "test_file.py",
                    "content": "def hello_world():\\n    return 'Hello, World!'",
                    "description": "A simple test file"
                }
            ],
            "explanation": "This is a simple hello world function."
        }
        """

        with patch.object(CodingAgent, "_load_prompt_template") as mock_load_prompt:
            agent = CodingAgent(openai_api_key="fake-api-key")

            # Mock the chain's ainvoke method
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_result)
            agent.chain = mock_chain

            # Act
            result = await agent.generate_code(
                task_description="Create a hello world function",
                design_specs="Function should return 'Hello, World!'",
                architecture_diagram="No diagram needed",
            )

            # Assert
            mock_chain.ainvoke.assert_called_once()
            assert "files" in result
            assert "explanation" in result
            assert len(result["files"]) == 1
            assert result["files"][0]["path"] == "test_file.py"
            assert "hello_world" in result["files"][0]["content"]

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data="You are a Coding Agent")
    async def test_generate_code_invalid_json(self, mock_file):
        """Test handling of invalid JSON response."""
        # Arrange
        mock_result = "This is not valid JSON"

        with patch.object(CodingAgent, "_load_prompt_template") as mock_load_prompt:
            agent = CodingAgent(openai_api_key="fake-api-key")

            # Mock the chain's ainvoke method
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_result)
            agent.chain = mock_chain

            # Act
            result = await agent.generate_code(task_description="Create something")

            # Assert
            assert "files" in result
            assert len(result["files"]) == 1
            assert result["files"][0]["path"] == "generated_code.py"
            assert result["files"][0]["content"] == mock_result

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data="You are a Coding Agent")
    async def test_generate_code_exception(self, mock_file):
        """Test handling of exceptions during code generation."""
        # Arrange
        with patch.object(CodingAgent, "_load_prompt_template") as mock_load_prompt:
            agent = CodingAgent(openai_api_key="fake-api-key")

            # Mock the chain's ainvoke method
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(side_effect=Exception("Test exception"))
            agent.chain = mock_chain

            # Act
            result = await agent.generate_code(task_description="Create something")

            # Assert
            assert "files" in result
            assert len(result["files"]) == 0
            assert "explanation" in result
            assert "Test exception" in result["explanation"]
