"""
Test Category Definitions for Live Testing
Organizes tests by complexity level with progressive difficulty
"""

from enum import Enum
from typing import List, Dict, Any
from pathlib import Path


class TestLevel(Enum):
    """Test complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"
    EDGE_CASES = "edge_cases"


# Test definitions by level
TEST_CATALOG = {
    TestLevel.SIMPLE: [
        {
            "name": "calculator",
            "file": "test_calculator.py",
            "requirements": """Create a simple calculator class using TDD that supports:
- Addition of two numbers
- Subtraction of two numbers
- Multiplication of two numbers
- Division of two numbers (with proper error handling for division by zero)

The calculator should be implemented as a Python class with methods for each operation.""",
            "workflow_type": "mvp_incremental",
            "timeout": 120,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/calculator.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_calculator.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "python -m pytest generated/test_calculator.py -v"
                }
            ]
        },
        {
            "name": "hello_world_api",
            "file": "test_hello_world.py",
            "requirements": """Create a simple REST API using FastAPI and TDD that has:
- A GET endpoint at / that returns {"message": "Hello, World!"}
- A GET endpoint at /greet/{name} that returns {"message": "Hello, {name}!"}
- Proper test coverage for both endpoints""",
            "workflow_type": "mvp_incremental",
            "timeout": 120,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/app.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_app.py"
                },
                {
                    "type": "file_contains",
                    "path": "generated/app.py",
                    "content": "FastAPI"
                }
            ]
        },
        {
            "name": "string_utils",
            "file": "test_string_utils.py",
            "requirements": """Create a string utilities module using TDD with functions for:
- reverse_string(s): Reverses a string
- is_palindrome(s): Checks if a string is a palindrome
- count_vowels(s): Counts vowels in a string
- capitalize_words(s): Capitalizes first letter of each word

Include comprehensive tests for edge cases.""",
            "workflow_type": "mvp_incremental",
            "timeout": 120,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/string_utils.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_string_utils.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "python -m pytest generated/test_string_utils.py -v"
                }
            ]
        }
    ],
    
    TestLevel.MODERATE: [
        {
            "name": "todo_api",
            "file": "test_todo_api.py",
            "requirements": """Create a TODO list REST API using FastAPI and TDD with:
- POST /todos - Create a new todo item
- GET /todos - List all todos
- GET /todos/{id} - Get a specific todo
- PUT /todos/{id} - Update a todo
- DELETE /todos/{id} - Delete a todo

Todo items should have: id, title, description, completed status, created_at timestamp.
Use in-memory storage (dictionary) for this implementation.
Include comprehensive tests for all endpoints and edge cases.""",
            "workflow_type": "mvp_incremental",
            "timeout": 180,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/main.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/models.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_main.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "sh -c 'pip install fastapi pytest httpx && python -m pytest generated/test_main.py -v'"
                }
            ]
        },
        {
            "name": "data_processor",
            "file": "test_data_processor.py",
            "requirements": """Create a data processing module using TDD that can:
- Read CSV files and return as list of dictionaries
- Filter rows based on column values
- Sort data by any column
- Export filtered/sorted data to JSON
- Calculate basic statistics (mean, median, mode) for numeric columns

Include error handling for missing files, invalid data types, and malformed CSV.
Write comprehensive tests first.""",
            "workflow_type": "mvp_incremental",
            "timeout": 180,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/data_processor.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_data_processor.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "python -m pytest generated/test_data_processor.py -v"
                }
            ]
        },
        {
            "name": "linked_list",
            "file": "test_linked_list.py",
            "requirements": """Implement a singly linked list data structure using TDD with operations:
- append(value) - Add to end
- prepend(value) - Add to beginning
- insert(index, value) - Insert at specific position
- remove(value) - Remove first occurrence
- find(value) - Return index or -1
- size() - Return number of elements
- to_list() - Convert to Python list

Include edge case handling and comprehensive tests.""",
            "workflow_type": "mvp_incremental",
            "timeout": 180,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/linked_list.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_linked_list.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "python -m pytest generated/test_linked_list.py -v"
                }
            ]
        }
    ],
    
    TestLevel.COMPLEX: [
        {
            "name": "blog_api",
            "file": "test_blog_api.py",
            "requirements": """Create a blog API using FastAPI, SQLAlchemy, and TDD with:
- User registration and authentication (JWT tokens)
- CRUD operations for blog posts
- Comments on posts
- Tags for posts
- Search functionality

Models:
- User (id, username, email, password_hash, created_at)
- Post (id, title, content, author_id, created_at, updated_at)
- Comment (id, content, post_id, author_id, created_at)
- Tag (id, name)

Use SQLite for database. Include proper relationships and comprehensive tests.""",
            "workflow_type": "mvp_incremental",
            "timeout": 300,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/main.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/models.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/auth.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/database.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_api.py"
                }
            ]
        },
        {
            "name": "task_scheduler",
            "file": "test_task_scheduler.py",
            "requirements": """Build a task scheduling system using TDD with:
- Schedule tasks to run at specific times
- Recurring tasks (daily, weekly, monthly)
- Task dependencies (task B runs after task A completes)
- Priority levels
- Concurrent task execution with configurable worker pool
- Task retry on failure with exponential backoff
- Task status tracking and history

Use asyncio for concurrent execution. Include comprehensive tests for all scenarios.""",
            "workflow_type": "mvp_incremental",
            "timeout": 300,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/scheduler.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/task.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/worker.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_scheduler.py"
                }
            ]
        },
        {
            "name": "cache_system",
            "file": "test_cache_system.py",
            "requirements": """Implement a multi-level caching system using TDD with:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) support
- Multiple cache levels (memory -> disk -> remote)
- Cache warming and preloading
- Statistics tracking (hits, misses, evictions)
- Thread-safe operations
- Serialization support for complex objects

Include performance tests and edge case handling.""",
            "workflow_type": "mvp_incremental",
            "timeout": 300,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/cache.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/lru_cache.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/cache_stats.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_cache.py"
                }
            ]
        }
    ],
    
    TestLevel.ADVANCED: [
        {
            "name": "microservice_orchestrator",
            "file": "test_microservice_orchestrator.py",
            "requirements": """Create a microservice orchestration system using TDD with:
- Service discovery and registration
- Load balancing with multiple strategies (round-robin, least-connections, weighted)
- Circuit breaker pattern for fault tolerance
- Request retry with exponential backoff
- Distributed tracing
- Health checks and auto-recovery
- Configuration management
- Metrics collection and aggregation

Build a demo with 3 microservices that communicate through the orchestrator.""",
            "workflow_type": "mvp_incremental",
            "timeout": 600,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/orchestrator.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/service_registry.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/load_balancer.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/circuit_breaker.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_orchestrator.py"
                }
            ]
        },
        {
            "name": "distributed_queue",
            "file": "test_distributed_queue.py",
            "requirements": """Build a distributed task queue system using TDD similar to Celery with:
- Multiple queue priorities
- Task routing based on type
- Worker pool management
- Task result storage
- Scheduled/periodic tasks
- Task chaining and workflows
- Dead letter queue for failed tasks
- Monitoring dashboard API
- At-least-once delivery guarantee

Use Redis for queue backend and include comprehensive tests.""",
            "workflow_type": "mvp_incremental",
            "timeout": 600,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/queue.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/worker.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/scheduler.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/monitor.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_queue.py"
                }
            ]
        }
    ],
    
    TestLevel.EDGE_CASES: [
        {
            "name": "resilient_api",
            "file": "test_resilient_api.py",
            "requirements": """Create an API using TDD that handles these edge cases:
- Malformed JSON in requests
- Extremely large payloads (>100MB)
- Concurrent modifications to same resource
- Database connection failures
- Slow/timeout scenarios
- Memory exhaustion attempts
- SQL injection attempts
- Rate limiting and DDoS protection

Include chaos engineering tests that randomly inject failures.""",
            "workflow_type": "mvp_incremental",
            "timeout": 300,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/resilient_api.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/middleware.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_resilience.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/chaos_tests.py"
                }
            ]
        },
        {
            "name": "unicode_processor",
            "file": "test_unicode_processor.py",
            "requirements": """Create a text processing system using TDD that correctly handles:
- All Unicode categories (letters, marks, symbols, etc.)
- Right-to-left languages
- Emoji and multi-codepoint graphemes
- Different text normalization forms (NFC, NFD, NFKC, NFKD)
- Surrogate pairs and invalid UTF-8 sequences
- Zero-width characters and control characters
- Case folding for different languages
- Text segmentation (words, sentences, graphemes)

Include tests with real-world text in multiple languages.""",
            "workflow_type": "mvp_incremental",
            "timeout": 300,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/unicode_processor.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_unicode.py"
                },
                {
                    "type": "docker_test",
                    "image": "python:3.9-slim",
                    "command": "python -m pytest generated/test_unicode.py -v"
                }
            ]
        },
        {
            "name": "concurrent_state_manager",
            "file": "test_concurrent_state.py",
            "requirements": """Build a concurrent state management system using TDD that handles:
- Race conditions in state updates
- Deadlock detection and recovery
- ABA problem scenarios
- Memory ordering issues
- Lock-free data structures
- Optimistic concurrency control
- Event sourcing for state changes
- Distributed consensus (simple Raft implementation)

Include stress tests with thousands of concurrent operations.""",
            "workflow_type": "mvp_incremental",
            "timeout": 600,
            "validations": [
                {
                    "type": "file_exists",
                    "path": "generated/state_manager.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/lock_free.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/consensus.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/test_concurrency.py"
                },
                {
                    "type": "file_exists",
                    "path": "generated/stress_tests.py"
                }
            ]
        }
    ]
}


def get_tests_by_level(level: TestLevel) -> List[Dict[str, Any]]:
    """Get all tests for a specific complexity level
    
    Args:
        level: Test complexity level
        
    Returns:
        List of test configurations
    """
    return TEST_CATALOG.get(level, [])


def get_all_tests() -> Dict[TestLevel, List[Dict[str, Any]]]:
    """Get all tests organized by level
    
    Returns:
        Dictionary mapping levels to test lists
    """
    return TEST_CATALOG.copy()


def get_test_by_name(name: str) -> Dict[str, Any]:
    """Find a specific test by name
    
    Args:
        name: Test name
        
    Returns:
        Test configuration or None
    """
    for level, tests in TEST_CATALOG.items():
        for test in tests:
            if test["name"] == name:
                return {**test, "level": level}
    return None


def get_test_count() -> Dict[TestLevel, int]:
    """Get count of tests by level
    
    Returns:
        Dictionary with test counts per level
    """
    return {level: len(tests) for level, tests in TEST_CATALOG.items()}


def estimate_total_runtime() -> Dict[str, float]:
    """Estimate total runtime for all tests
    
    Returns:
        Runtime estimates in seconds
    """
    total = 0
    by_level = {}
    
    for level, tests in TEST_CATALOG.items():
        level_total = sum(test.get("timeout", 300) for test in tests)
        by_level[level.value] = level_total
        total += level_total
        
    return {
        "total_seconds": total,
        "total_minutes": total / 60,
        "by_level": by_level
    }