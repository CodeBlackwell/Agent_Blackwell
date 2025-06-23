"""
Unit tests for the Requirements/Specification Agent.

These tests verify that the SpecAgent correctly extracts tasks from user requests
by mocking the LLM responses.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.spec_agent import SpecAgent, Task


@pytest.fixture
def mock_llm_response():
    """Sample LLM response with tasks."""
    return """
    [
        {
            "task_id": "T-001",
            "title": "Define CSV upload functionality",
            "description": "Create a file upload component that accepts CSV files and validates their format",
            "priority": "high",
            "estimated_hours": 2.0,
            "dependencies": [],
            "assignee": "spec_agent"
        },
        {
            "task_id": "T-002",
            "title": "Design data visualization components",
            "description": "Create wireframes for chart visualization components",
            "priority": "medium",
            "estimated_hours": 3.0,
            "dependencies": ["T-001"],
            "assignee": "design_agent"
        },
        {
            "task_id": "T-003",
            "title": "Implement CSV parser",
            "description": "Develop backend logic to parse and validate uploaded CSV files",
            "priority": "high",
            "estimated_hours": 4.0,
            "dependencies": ["T-001"],
            "assignee": "coding_agent"
        }
    ]
    """


@pytest.mark.asyncio
async def test_generate_tasks(mock_llm_response):
    """Test that the SpecAgent correctly generates from a user request."""
    # Create a mock LLMChain
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = [
        Task(
            task_id="T-001",
            title="Define CSV upload functionality",
            description="Create a file upload component that accepts CSV files and validates their format",
            priority="high",
            estimated_hours=2.0,
            dependencies=[],
            assignee="spec_agent",
        ),
        Task(
            task_id="T-002",
            title="Design data visualization components",
            description="Create wireframes for chart visualization components",
            priority="medium",
            estimated_hours=3.0,
            dependencies=["T-001"],
            assignee="design_agent",
        ),
        Task(
            task_id="T-003",
            title="Implement CSV parser",
            description="Develop backend logic to parse and validate uploaded CSV files",
            priority="high",
            estimated_hours=4.0,
            dependencies=["T-001"],
            assignee="coding_agent",
        ),
    ]

    # Create the agent with the mocked chain
    with patch("src.agents.spec_agent.LLMChain", return_value=mock_chain):
        with patch("src.agents.spec_agent.ChatOpenAI"):
            agent = SpecAgent(openai_api_key="fake-key")

            # Test with a sample user request
            user_request = """
            I need a simple web application that allows users to upload CSV files,
            visualize the data as charts, and download the charts as images.
            """

            tasks = await agent.generate_tasks(user_request)

            # Verify the results
            assert len(tasks) == 3
            assert tasks[0].task_id == "T-001"
            assert tasks[0].title == "Define CSV upload functionality"
            assert tasks[0].assignee == "spec_agent"

            assert tasks[1].task_id == "T-002"
            assert tasks[1].dependencies == ["T-001"]
            assert tasks[1].assignee == "design_agent"

            assert tasks[2].task_id == "T-003"
            assert tasks[2].estimated_hours == 4.0
            assert tasks[2].assignee == "coding_agent"

            # Verify the chain was called with the correct input
            mock_chain.ainvoke.assert_called_once()
            call_args = mock_chain.ainvoke.call_args[0][0]
            assert "user_request" in call_args
            assert user_request.strip() in call_args["user_request"]


@pytest.mark.asyncio
async def test_task_list_output_parser():
    """Test that the TaskListOutputParser correctly parses LLM output."""
    from src.agents.spec_agent import TaskListOutputParser

    # Create the parser
    parser = TaskListOutputParser()

    # Test with a valid JSON response
    valid_response = """
    Here are the tasks I've extracted:

    [
        {
            "task_id": "T-001",
            "title": "Define API endpoints",
            "description": "Define the REST API endpoints for the application",
            "priority": "high",
            "estimated_hours": 1.5,
            "dependencies": [],
            "assignee": "spec_agent"
        },
        {
            "task_id": "T-002",
            "title": "Implement authentication",
            "description": "Add user authentication using JWT",
            "priority": "high",
            "estimated_hours": 3.0,
            "dependencies": ["T-001"],
            "assignee": "coding_agent"
        }
    ]

    Let me know if you need any clarification.
    """

    tasks = parser.parse(valid_response)

    # Verify the results
    assert len(tasks) == 2
    assert tasks[0].task_id == "T-001"
    assert tasks[0].title == "Define API endpoints"
    assert tasks[1].task_id == "T-002"
    assert tasks[1].dependencies == ["T-001"]

    # Test with an invalid response
    invalid_response = "I couldn't extract any tasks from this request."

    tasks = parser.parse(invalid_response)

    # Verify the results
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_error_handling():
    """Test that the SpecAgent handles errors gracefully."""
    # Create a mock LLMChain that raises an exception
    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = Exception("LLM error")

    # Create the agent with the mocked chain
    with patch("src.agents.spec_agent.LLMChain", return_value=mock_chain):
        with patch("src.agents.spec_agent.ChatOpenAI"):
            agent = SpecAgent(openai_api_key="fake-key")

            # Test with a sample user request
            user_request = "Build me a website"

            tasks = await agent.generate_tasks(user_request)

            # Verify the results
            assert len(tasks) == 0  # Should return an empty list on error
