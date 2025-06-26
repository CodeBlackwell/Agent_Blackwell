#!/usr/bin/env python3
"""
Agent worker for integration tests.

This worker consumes messages from Redis streams and processes them
using the appropriate agents, then publishes results to output streams.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import redis.asyncio as redis

# Add the project root to Python path
sys.path.insert(0, "/app")

from src.orchestrator.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AgentWorker:
    """Worker that processes agent tasks from Redis streams."""

    def __init__(self, redis_host: str = "redis-test", redis_port: int = 6379):
        """Initialize the agent worker."""
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        self.agent_registry: Optional[AgentRegistry] = None
        self.running = False

    async def connect_redis(self):
        """Connect to Redis."""
        self.redis_client = redis.Redis(
            host=self.redis_host, port=self.redis_port, decode_responses=True
        )
        await self.redis_client.ping()
        logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")

    async def initialize_agents(self):
        """Initialize the agent registry."""
        openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
        self.agent_registry = AgentRegistry(openai_api_key=openai_api_key)
        logger.info("Agent registry initialized")

    async def process_agent_message(
        self, agent_type: str, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a message for a specific agent type."""
        try:
            logger.info(f"Processing {agent_type} message: {message_data}")

            # Get the appropriate agent
            agent = self.agent_registry.get_agent(agent_type)
            if not agent:
                return {"error": f"Agent {agent_type} not found", "status": "failed"}

            # Mock processing based on agent type
            if agent_type == "spec_agent":
                return await self.process_spec_agent(message_data)
            elif agent_type == "design_agent":
                return await self.process_design_agent(message_data)
            elif agent_type == "coding_agent":
                return await self.process_coding_agent(message_data)
            elif agent_type == "review_agent":
                return await self.process_review_agent(message_data)
            elif agent_type == "test_agent":
                return await self.process_test_agent(message_data)
            else:
                return {
                    "error": f"Unknown agent type: {agent_type}",
                    "status": "failed",
                }

        except Exception as e:
            logger.error(f"Error processing {agent_type} message: {e}")
            return {"error": str(e), "status": "failed"}

    async def process_spec_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process spec agent message."""
        content = message_data.get("content", "")

        try:
            import aiohttp

            # Call LLM endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    os.getenv(
                        "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
                    ),
                    json={
                        "messages": [
                            {"role": "user", "content": message_data.get("content", "")}
                        ],
                        "model": "gpt-4",
                    },
                ) as resp:
                    resp_data = await resp.json()

            # Extract LLM response
            choices = resp_data.get("choices", [])
            if choices:
                llm_content = choices[0].get("message", {}).get("content", "")
                # Handle both string and dict responses (for mocked vs real LLM)
                if isinstance(llm_content, dict):
                    parsed_output = llm_content
                elif isinstance(llm_content, str):
                    try:
                        parsed_output = json.loads(llm_content)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse LLM output")
                        parsed_output = {"content": llm_content}
                else:
                    parsed_output = {"content": str(llm_content)}
            else:
                parsed_output = {}
        except Exception as e:
            logger.error(f"Error in spec_agent processing: {e}")
            # Return a fallback response for testing
            parsed_output = {"status": "error", "error": str(e)}

        # Propagate request_id
        parsed_output["request_id"] = message_data.get("request_id", "")
        return parsed_output

    async def process_design_agent(
        self, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process design agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "architecture": {
                "components": ["web-api", "database", "cache"],
                "patterns": ["mvc", "repository"],
                "architecture_type": "Microservices",
            },
            "data_models": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "string", "required": True},
                        {"name": "email", "type": "string", "required": True},
                        {"name": "created_at", "type": "datetime", "required": True},
                    ],
                }
            ],
            "api_design": {
                "endpoints": [
                    {
                        "path": "/api/users",
                        "method": "GET",
                        "description": "Get all users",
                    },
                    {
                        "path": "/api/users/{id}",
                        "method": "GET",
                        "description": "Get user by ID",
                    },
                ],
                "authentication": "JWT",
                "rate_limiting": "100 requests/minute",
            },
            "ui_wireframes": {
                "pages": [
                    {
                        "name": "Dashboard",
                        "components": ["header", "sidebar", "main-content"],
                    },
                    {
                        "name": "User Profile",
                        "components": ["profile-form", "avatar-upload"],
                    },
                ]
            },
            "scalability_plan": {
                "horizontal_scaling": "Auto-scaling groups",
                "load_balancing": "Application Load Balancer with health checks",
                "caching_strategy": "Redis cluster",
                "database_sharding": "User-based sharding",
            },
            "security_design": {
                "authentication": "OAuth 2.0 + JWT",
                "authorization": "Role-based access control",
                "data_encryption": "AES-256 at rest, TLS 1.3 in transit",
            },
            "status": "completed",
        }

    async def process_coding_agent(
        self, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process coding agent message."""
        # Check if the message contains an error status
        if message_data.get("status") == "error" or message_data.get("error"):
            return {
                "request_id": message_data.get("request_id", "unknown"),
                "error": message_data.get("error", "Unknown error occurred"),
                "error_code": message_data.get("error_code", "UNKNOWN_ERROR"),
                "status": "failed",
            }

        # Normal processing for successful requests
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "source_code": {
                "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                "api/users.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users')\ndef get_users():\n    return []",
                "user-service": {
                    "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/users')\ndef get_users():\n    return []\n\n@app.get('/users/{user_id}')\ndef get_user(user_id: int):\n    return {'id': user_id, 'name': 'Test User'}",
                    "models.py": "from sqlalchemy import Column, Integer, String\nfrom sqlalchemy.ext.declarative import declarative_base\n\nBase = declarative_base()\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)\n    email = Column(String, unique=True)\n    name = Column(String)\n",
                },
                "order-service": {
                    "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/orders')\ndef get_orders():\n    return []\n\n@app.get('/orders/{order_id}')\ndef get_order(order_id: int):\n    return {'id': order_id, 'status': 'pending'}"
                },
                "payment-service": {
                    "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/payments')\ndef get_payments():\n    return []\n\n@app.post('/payments')\ndef create_payment():\n    return {'id': 1, 'status': 'completed'}"
                },
            },
            "file_structure": [
                {"path": "main.py", "type": "file"},
                {"path": "api", "type": "directory"},
                {"path": "api/users.py", "type": "file"},
            ],
            "dependencies": {"requirements": ["fastapi>=0.68.0", "uvicorn>=0.15.0"]},
            "documentation": {
                "api_docs": "# API Documentation\n\nThis is a simple API with FastAPI.\n\n## Endpoints\n\n- GET /: Returns a hello world message\n- GET /users: Returns an empty list of users",
                "setup_instructions": "1. Install dependencies\n2. Run with uvicorn main:app",
                "deployment_notes": "Use Docker for production deployment",
            },
            "test_files": {
                "test_main.py": "from fastapi.testclient import TestClient\nfrom main import app\n\nclient = TestClient(app)\n\ndef test_read_root():\n    response = client.get('/')\n    assert response.status_code == 200\n    assert response.json() == {'Hello': 'World'}"
            },
            "linting_config": {
                "pyproject.toml": "[tool.flake8]\nmax-line-length = 88\nextend-ignore = E203\n\n[tool.black]\nline-length = 88"
            },
            "deployment_config": {
                "docker-compose.yml": "version: '3'\nservices:\n  app:\n    build: .\n    ports:\n      - '8000:8000'\n",
                "Dockerfile": 'FROM python:3.9\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0"]\n',
                "services": [
                    {
                        "name": "api-gateway",
                        "port": 8000,
                        "environment": ["PORT=8000", "DEBUG=false"],
                    },
                    {
                        "name": "user-service",
                        "port": 8001,
                        "environment": [
                            "PORT=8001",
                            "DB_URL=postgres://user:pass@db:5432/users",
                        ],
                    },
                    {
                        "name": "order-service",
                        "port": 8002,
                        "environment": [
                            "PORT=8002",
                            "DB_URL=postgres://user:pass@db:5432/orders",
                        ],
                    },
                    {
                        "name": "payment-service",
                        "port": 8003,
                        "environment": [
                            "PORT=8003",
                            "DB_URL=postgres://user:pass@db:5432/payments",
                        ],
                    },
                ],
            },
            "docker_config": {
                "services": [
                    {
                        "name": "api-gateway",
                        "port": 8000,
                        "dockerfile": 'FROM python:3.9-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0"]\n',
                    },
                    {
                        "name": "user-service",
                        "port": 8001,
                        "dockerfile": 'FROM python:3.9-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0"]\n',
                    },
                ],
                "networks": ["api-network", "backend-network"],
                "volumes": ["postgres-data", "redis-data"],
                "docker-compose.yml": "version: '3'\nservices:\n  api-gateway:\n    build: ./api-gateway\n    ports:\n      - '8000:8000'\n    environment:\n      - PORT=8000\n      - DEBUG=false\n  user-service:\n    build: ./user-service\n    ports:\n      - '8001:8001'\n    environment:\n      - PORT=8001\n      - DB_URL=postgres://user:pass@db:5432/users\n  order-service:\n    build: ./order-service\n    ports:\n      - '8002:8002'\n    environment:\n      - PORT=8002\n      - DB_URL=postgres://user:pass@db:5432/orders\n  payment-service:\n    build: ./payment-service\n    ports:\n      - '8003:8003'\n    environment:\n      - PORT=8003\n      - DB_URL=postgres://user:pass@db:5432/payments\n  db:\n    image: postgres:13\n    volumes:\n      - postgres-data:/var/lib/postgresql/data\n    environment:\n      - POSTGRES_PASSWORD=password\n      - POSTGRES_USER=user\nvolumes:\n  postgres-data:\n",
            },
            "status": "completed",
        }

    async def process_review_agent(
        self, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process review agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "review_report": "Mock review report",
            "status": "completed",
        }

    async def process_test_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process test agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "test_results": "Mock test results",
            "status": "completed",
        }

    async def run_worker_loop(self):
        """Main worker loop that processes messages from Redis streams."""
        logger.info("Starting agent worker loop")
        self.running = True

        # Define agent types and their stream names
        agent_types = [
            "spec_agent",
            "design_agent",
            "coding_agent",
            "review_agent",
            "test_agent",
        ]
        stream_mapping = {
            agent_type: {
                "input": f"agent:{agent_type}:input",
                "output": f"agent:{agent_type}:output",
            }
            for agent_type in agent_types
        }

        # Track last message IDs for each stream
        last_ids = {mapping["input"]: "0-0" for mapping in stream_mapping.values()}

        while self.running:
            try:
                # Read from all input streams
                streams_to_read = {
                    stream: last_id for stream, last_id in last_ids.items()
                }

                # Use XREAD to wait for new messages
                messages = await self.redis_client.xread(
                    streams_to_read, count=1, block=1000  # Block for 1 second
                )

                if not messages:
                    continue

                # Process each message
                for stream_name, message_list in messages:
                    for message_id, message_fields in message_list:
                        # Update last seen ID
                        last_ids[stream_name] = message_id

                        # Determine agent type from stream name
                        agent_type = None
                        for atype, mapping in stream_mapping.items():
                            if stream_name == mapping["input"]:
                                agent_type = atype
                                break

                        if not agent_type:
                            logger.warning(f"Unknown stream: {stream_name}")
                            continue

                        # Parse message data
                        try:
                            # Convert Redis stream fields to dictionary
                            # Redis streams store fields as bytes, so decode them
                            message_data = {}
                            for field_name, field_value in message_fields.items():
                                if isinstance(field_name, bytes):
                                    field_name = field_name.decode("utf-8")
                                if isinstance(field_value, bytes):
                                    field_value = field_value.decode("utf-8")

                                # Try to deserialize JSON strings back to objects
                                # Fields that are typically complex objects should be deserialized
                                if field_name in [
                                    "spec_details",
                                    "user_stories",
                                    "acceptance_criteria",
                                    "constraints",
                                    "technical_requirements",
                                    "design",
                                    "architecture",
                                    "data_models",
                                    "api_design",
                                    "ui_wireframes",
                                ]:
                                    try:
                                        message_data[field_name] = json.loads(
                                            field_value
                                        )
                                    except (json.JSONDecodeError, TypeError):
                                        # If it's not valid JSON, keep as string
                                        message_data[field_name] = field_value
                                else:
                                    message_data[field_name] = field_value

                            logger.info(
                                f"Processing {agent_type} message: {message_data}"
                            )
                        except Exception as e:
                            logger.error(f"Error parsing message fields: {e}")
                            continue

                        # Process the message
                        result = await self.process_agent_message(
                            agent_type, message_data
                        )

                        # Serialize complex fields for Redis stream storage
                        # Redis streams can only store string values
                        serialized_result = {}
                        for key, value in result.items():
                            if isinstance(value, (dict, list)):
                                # Serialize complex objects as JSON strings
                                serialized_result[key] = json.dumps(value)
                            else:
                                # Keep simple values as strings
                                serialized_result[key] = str(value)

                        # Publish result to output stream
                        output_stream = stream_mapping[agent_type]["output"]
                        await self.redis_client.xadd(output_stream, serialized_result)

                        logger.info(
                            f"Processed {agent_type} message and published result"
                        )

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    async def start(self):
        """Start the agent worker."""
        try:
            await self.connect_redis()
            await self.initialize_agents()
            await self.run_worker_loop()
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the agent worker."""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Agent worker stopped")


async def main():
    """Main entry point."""
    redis_host = os.getenv("REDIS_HOST", "redis-test")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    worker = AgentWorker(redis_host=redis_host, redis_port=redis_port)
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
