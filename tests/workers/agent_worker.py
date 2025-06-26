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
from typing import Dict, Any, Optional

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
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        await self.redis_client.ping()
        logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        
    async def initialize_agents(self):
        """Initialize the agent registry."""
        openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
        self.agent_registry = AgentRegistry(openai_api_key=openai_api_key)
        logger.info("Agent registry initialized")
        
    async def process_agent_message(self, agent_type: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message for a specific agent type."""
        try:
            logger.info(f"Processing {agent_type} message: {message_data}")
            
            # Get the appropriate agent
            agent = self.agent_registry.get_agent(agent_type)
            if not agent:
                return {
                    "error": f"Agent {agent_type} not found",
                    "status": "failed"
                }
            
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
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Error processing {agent_type} message: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def process_spec_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process spec agent message."""
        content = message_data.get("content", "")
        
        # Mock spec agent output
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "spec_details": {
                "title": f"Specification for: {content[:50]}...",
                "overview": f"System to implement: {content}",
                "functional_requirements": [
                    "User authentication and authorization",
                    "Core business logic implementation", 
                    "Data persistence and retrieval",
                    "API endpoints for client interaction"
                ],
                "non_functional_requirements": [
                    "Performance: Sub-200ms response time",
                    "Security: HTTPS and input validation",
                    "Scalability: Handle 1000+ concurrent users",
                    "Reliability: 99.9% uptime SLA"
                ]
            },
            "user_stories": [
                {
                    "id": "US001",
                    "title": "User Registration",
                    "description": "As a user, I want to register an account",
                    "acceptance_criteria": ["Valid email required", "Password strength validation"]
                },
                {
                    "id": "US002", 
                    "title": "Core Functionality",
                    "description": f"As a user, I want to {content.lower()}",
                    "acceptance_criteria": ["Feature works as expected", "Error handling implemented"]
                }
            ],
            "acceptance_criteria": [
                "All functional requirements implemented",
                "All user stories completed",
                "Security requirements met",
                "Performance targets achieved"
            ],
            "status": "completed",
            "timestamp": message_data.get("timestamp", "2025-01-01T00:00:00Z")
        }
    
    async def process_design_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process design agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "design_document": "Mock design document generated",
            "status": "completed"
        }
    
    async def process_coding_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process coding agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "code_implementation": "Mock code implementation",
            "status": "completed"
        }
    
    async def process_review_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process review agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "review_report": "Mock review report",
            "status": "completed"
        }
    
    async def process_test_agent(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process test agent message."""
        return {
            "request_id": message_data.get("request_id", "unknown"),
            "test_results": "Mock test results",
            "status": "completed"
        }
    
    async def run_worker_loop(self):
        """Main worker loop that processes messages from Redis streams."""
        logger.info("Starting agent worker loop")
        self.running = True
        
        # Define agent types and their stream names
        agent_types = ["spec_agent", "design_agent", "coding_agent", "review_agent", "test_agent"]
        stream_mapping = {
            agent_type: {
                "input": f"agent:{agent_type}:input",
                "output": f"agent:{agent_type}:output"
            }
            for agent_type in agent_types
        }
        
        # Track last message IDs for each stream
        last_ids = {mapping["input"]: "0-0" for mapping in stream_mapping.values()}
        
        while self.running:
            try:
                # Read from all input streams
                streams_to_read = {stream: last_id for stream, last_id in last_ids.items()}
                
                # Use XREAD to wait for new messages
                messages = await self.redis_client.xread(
                    streams_to_read,
                    count=1,
                    block=1000  # Block for 1 second
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
                                    field_name = field_name.decode('utf-8')
                                if isinstance(field_value, bytes):
                                    field_value = field_value.decode('utf-8')
                                message_data[field_name] = field_value
                            
                            logger.info(f"Processing {agent_type} message: {message_data}")
                        except Exception as e:
                            logger.error(f"Error parsing message fields: {e}")
                            continue
                        
                        # Process the message
                        result = await self.process_agent_message(agent_type, message_data)
                        
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
                        await self.redis_client.xadd(
                            output_stream,
                            serialized_result
                        )
                        
                        logger.info(f"Processed {agent_type} message and published result")
                        
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
