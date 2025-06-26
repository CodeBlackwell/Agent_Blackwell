"""
Sample user requests for integration testing.
"""
from typing import Dict, List

# Sample user requests of varying complexity
SIMPLE_REQUESTS = [
    "Create a hello world function in Python",
    "Write a function to add two numbers",
    "Make a simple calculator class",
]

MEDIUM_REQUESTS = [
    "Create a REST API for a todo list application with FastAPI",
    "Build a user authentication system with JWT tokens",
    "Design a database schema for an e-commerce platform",
]

COMPLEX_REQUESTS = [
    "Create a microservices architecture for a social media platform with user management, posts, comments, and real-time messaging",
    "Build a distributed task queue system with Redis that can handle millions of jobs per hour",
    "Design and implement a machine learning pipeline for real-time fraud detection in financial transactions",
]

# Requests organized by agent type
SPEC_AGENT_REQUESTS = [
    "I need to build a web scraper that can handle JavaScript-rendered pages",
    "Create specifications for a chat application with real-time messaging",
    "Design a system for processing large CSV files efficiently",
]

DESIGN_AGENT_REQUESTS = [
    "Design the architecture for a high-traffic blog platform",
    "Create a system design for a real-time analytics dashboard",
    "Design a scalable file storage system",
]

CODING_AGENT_REQUESTS = [
    "Implement a binary search tree in Python with all standard operations",
    "Create a web server using Flask with user authentication",
    "Build a command-line tool for managing configuration files",
]

REVIEW_AGENT_REQUESTS = [
    "Review this Python function for potential bugs and performance issues",
    "Analyze this code for security vulnerabilities",
    "Check this implementation for best practices compliance",
]

TEST_AGENT_REQUESTS = [
    "Create comprehensive unit tests for this utility class",
    "Generate integration tests for this API endpoint",
    "Write performance tests for this database query function",
]

# Sample user request data structures
def generate_user_request_data() -> List[Dict]:
    """Generate sample user request data for testing."""
    return [
        {
            "id": "req_001",
            "user_id": "user_123",
            "content": "Create a REST API for managing books",
            "complexity": "medium",
            "timestamp": "2025-01-01T12:00:00Z",
            "tags": ["api", "crud", "books"],
            "priority": "normal"
        },
        {
            "id": "req_002",
            "user_id": "user_456",
            "content": "Build a real-time chat application",
            "complexity": "complex",
            "timestamp": "2025-01-01T12:05:00Z",
            "tags": ["realtime", "websocket", "chat"],
            "priority": "high"
        },
        {
            "id": "req_003",
            "user_id": "user_789",
            "content": "Write a function to validate email addresses",
            "complexity": "simple",
            "timestamp": "2025-01-01T12:10:00Z",
            "tags": ["validation", "email", "utility"],
            "priority": "low"
        }
    ]

# Request variations for testing edge cases
EDGE_CASE_REQUESTS = [
    "",  # Empty request
    "a" * 10000,  # Very long request
    "🚀 Create a rocket ship simulator! 🚀",  # Unicode characters
    "CREATE A FUNCTION IN ALL CAPS",  # All caps
    "create\na\nmultiline\nrequest",  # Multiline request
]

ALL_REQUESTS = {
    "simple": SIMPLE_REQUESTS,
    "medium": MEDIUM_REQUESTS,
    "complex": COMPLEX_REQUESTS,
    "spec_agent": SPEC_AGENT_REQUESTS,
    "design_agent": DESIGN_AGENT_REQUESTS,
    "coding_agent": CODING_AGENT_REQUESTS,
    "review_agent": REVIEW_AGENT_REQUESTS,
    "test_agent": TEST_AGENT_REQUESTS,
    "edge_cases": EDGE_CASE_REQUESTS,
}
