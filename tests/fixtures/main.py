"""
Main fixtures module that combines all test fixtures and provides easy access.
"""
from typing import Dict, Any
from .user_requests import ALL_REQUESTS, generate_user_request_data
from .agent_io import generate_agent_io_fixtures
from .vector_embeddings import generate_comprehensive_vector_fixtures

def get_all_test_fixtures() -> Dict[str, Any]:
    """Get all test fixtures in one consolidated structure."""
    return {
        "user_requests": {
            "categorized": ALL_REQUESTS,
            "structured": generate_user_request_data()
        },
        "agent_io": generate_agent_io_fixtures(),
        "vector_embeddings": generate_comprehensive_vector_fixtures()
    }

def get_fixtures_by_category(category: str) -> Any:
    """Get fixtures by category (user_requests, agent_io, vector_embeddings)."""
    all_fixtures = get_all_test_fixtures()
    return all_fixtures.get(category, {})

def get_sample_workflow() -> Dict[str, Any]:
    """Get a complete sample workflow for end-to-end testing."""
    agent_fixtures = generate_agent_io_fixtures()
    return agent_fixtures["workflow"]
