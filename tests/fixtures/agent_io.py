"""
Sample agent inputs and outputs for integration testing.
"""
from typing import Dict, List, Any
from datetime import datetime, timezone

# SpecAgent fixtures
SPEC_AGENT_IO = {
    "inputs": [
        {
            "user_request": "Create a REST API for managing books",
            "context": "Building a library management system",
            "requirements": ["CRUD operations", "Authentication", "Search functionality"]
        },
        {
            "user_request": "Build a real-time chat application",
            "context": "Team communication platform",
            "requirements": ["WebSocket support", "Message persistence", "User presence"]
        }
    ],
    "outputs": [
        {
            "specifications": {
                "title": "Book Management REST API",
                "description": "A RESTful API for managing books in a library system",
                "endpoints": [
                    {"method": "GET", "path": "/books", "description": "List all books"},
                    {"method": "POST", "path": "/books", "description": "Create a new book"},
                    {"method": "GET", "path": "/books/{id}", "description": "Get book by ID"},
                    {"method": "PUT", "path": "/books/{id}", "description": "Update book"},
                    {"method": "DELETE", "path": "/books/{id}", "description": "Delete book"}
                ],
                "data_models": {
                    "Book": {
                        "id": "string",
                        "title": "string",
                        "author": "string",
                        "isbn": "string",
                        "published_date": "date"
                    }
                },
                "authentication": "JWT Bearer Token",
                "database": "PostgreSQL"
            },
            "task_id": "spec_001",
            "created_at": "2025-01-01T12:00:00Z"
        }
    ]
}

# DesignAgent fixtures
DESIGN_AGENT_IO = {
    "inputs": [
        {
            "specifications": SPEC_AGENT_IO["outputs"][0]["specifications"],
            "requirements": ["High availability", "Scalability", "Security"]
        }
    ],
    "outputs": [
        {
            "design": {
                "architecture_type": "Microservices",
                "components": [
                    {"name": "API Gateway", "type": "service", "technology": "Kong"},
                    {"name": "Book Service", "type": "service", "technology": "FastAPI"},
                    {"name": "Auth Service", "type": "service", "technology": "FastAPI"},
                    {"name": "Database", "type": "database", "technology": "PostgreSQL"}
                ],
                "diagrams": {
                    "system_architecture": "```mermaid\ngraph TB\n    A[Client] --> B[API Gateway]\n    B --> C[Book Service]\n    B --> D[Auth Service]\n    C --> E[PostgreSQL]\n```",
                    "data_flow": "```mermaid\nsequenceDiagram\n    Client->>API Gateway: Request\n    API Gateway->>Auth Service: Validate Token\n    Auth Service-->>API Gateway: Valid\n    API Gateway->>Book Service: Forward Request\n    Book Service->>Database: Query\n    Database-->>Book Service: Result\n    Book Service-->>API Gateway: Response\n    API Gateway-->>Client: Response\n```"
                }
            },
            "task_id": "design_001",
            "created_at": "2025-01-01T12:15:00Z"
        }
    ]
}

# CodingAgent fixtures
CODING_AGENT_IO = {
    "inputs": [
        {
            "specifications": SPEC_AGENT_IO["outputs"][0]["specifications"],
            "design": DESIGN_AGENT_IO["outputs"][0]["design"],
            "component": "Book Service"
        }
    ],
    "outputs": [
        {
            "code": {
                "files": [
                    {
                        "path": "main.py",
                        "content": '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI(title="Book Management API")

class Book(BaseModel):
    id: Optional[str] = None
    title: str
    author: str
    isbn: str
    published_date: date

books_db = []

@app.get("/books", response_model=List[Book])
async def get_books():
    return books_db

@app.post("/books", response_model=Book)
async def create_book(book: Book):
    book.id = f"book_{len(books_db) + 1}"
    books_db.append(book)
    return book
'''
                    },
                    {
                        "path": "requirements.txt",
                        "content": "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0"
                    }
                ]
            },
            "task_id": "code_001",
            "created_at": "2025-01-01T12:30:00Z"
        }
    ]
}

# ReviewAgent fixtures
REVIEW_AGENT_IO = {
    "inputs": [
        {
            "code": CODING_AGENT_IO["outputs"][0]["code"],
            "review_criteria": ["Security", "Performance", "Best Practices", "Testing"]
        }
    ],
    "outputs": [
        {
            "review": {
                "overall_score": 7.5,
                "security_score": 8.0,
                "performance_score": 7.0,
                "best_practices_score": 8.0,
                "testing_score": 6.0,
                "issues": [
                    {
                        "severity": "medium",
                        "category": "security",
                        "description": "No input validation for ISBN format",
                        "line": 15,
                        "suggestion": "Add ISBN validation using regex or library"
                    },
                    {
                        "severity": "low",
                        "category": "performance",
                        "description": "In-memory storage not suitable for production",
                        "line": 18,
                        "suggestion": "Implement database integration"
                    }
                ],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Implement authentication middleware",
                    "Add logging and monitoring",
                    "Create unit tests"
                ]
            },
            "task_id": "review_001",
            "created_at": "2025-01-01T12:45:00Z"
        }
    ]
}

# TestAgent fixtures
TEST_AGENT_IO = {
    "inputs": [
        {
            "code": CODING_AGENT_IO["outputs"][0]["code"],
            "test_types": ["unit", "integration"],
            "coverage_target": 90
        }
    ],
    "outputs": [
        {
            "tests": {
                "files": [
                    {
                        "path": "test_main.py",
                        "content": '''import pytest
from fastapi.testclient import TestClient
from main import app, Book

client = TestClient(app)

def test_create_book():
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-0123456789",
        "published_date": "2023-01-01"
    }
    response = client.post("/books", json=book_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"

def test_get_books():
    response = client.get("/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
'''
                    }
                ],
                "coverage_report": {
                    "total_coverage": 85.0,
                    "files": {
                        "main.py": {"coverage": 85.0, "lines_covered": 17, "lines_total": 20}
                    }
                }
            },
            "task_id": "test_001",
            "created_at": "2025-01-01T13:00:00Z"
        }
    ]
}

# Combined agent workflow fixture
AGENT_WORKFLOW_FIXTURE = {
    "task_id": "workflow_001",
    "user_request": "Create a REST API for managing books",
    "stages": {
        "spec": SPEC_AGENT_IO["outputs"][0],
        "design": DESIGN_AGENT_IO["outputs"][0],
        "code": CODING_AGENT_IO["outputs"][0],
        "review": REVIEW_AGENT_IO["outputs"][0],
        "test": TEST_AGENT_IO["outputs"][0]
    },
    "metadata": {
        "total_time": "1 hour 15 minutes",
        "started_at": "2025-01-01T12:00:00Z",
        "completed_at": "2025-01-01T13:15:00Z",
        "status": "completed"
    }
}

def generate_agent_io_fixtures() -> Dict[str, Any]:
    """Generate comprehensive agent I/O fixtures for testing."""
    return {
        "spec_agent": SPEC_AGENT_IO,
        "design_agent": DESIGN_AGENT_IO,
        "coding_agent": CODING_AGENT_IO,
        "review_agent": REVIEW_AGENT_IO,
        "test_agent": TEST_AGENT_IO,
        "workflow": AGENT_WORKFLOW_FIXTURE
    }
