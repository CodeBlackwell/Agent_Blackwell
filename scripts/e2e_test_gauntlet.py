#!/usr/bin/env python3
"""
Agent Blackwell E2E Test Gauntlet

This script runs a comprehensive end-to-end test suite against the Agent Blackwell API
to validate all major endpoints and workflows.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("e2e_gauntlet")


def docker_is_running() -> bool:
    """Check if Docker is running on the system."""
    try:
        result = subprocess.run(
            ["docker", "info"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def docker_compose_is_running(project_dir: str) -> bool:
    """Check if the Docker Compose services are already running."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            cwd=project_dir
        )
        return len(result.stdout.decode().strip()) > 0
    except Exception as e:
        logger.error(f"Error checking Docker Compose status: {e}")
        return False


def setup_docker(project_dir: str, headless: bool = True) -> Tuple[bool, str]:
    """Set up Docker environment for testing.
    
    Args:
        project_dir: The project directory containing docker-compose.yml
        headless: Whether to run in headless mode (no console output from containers)
        
    Returns:
        Tuple of (success, message)
    """
    if not docker_is_running():
        return False, "🚫 Docker is not running. Please start Docker and try again."
    
    logger.info("\n" + "=" * 70)
    logger.info("🐳 Setting up Docker environment...")
    
    # Check if services are already running
    if docker_compose_is_running(project_dir):
        logger.info("🔄 Docker Compose services are already running")
        return True, "Docker services already running"
    
    try:
        # Build and start the containers
        logger.info("🏗️  Building and starting Docker containers...")
        
        cmd = ["docker", "compose", "up"]
        if headless:
            cmd.append("-d")
            
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if headless else None,
            stderr=subprocess.PIPE if headless else None,
            check=False,
            cwd=project_dir
        )
        
        if result.returncode != 0 and headless:
            error_msg = result.stderr.decode() if result.stderr else "Unknown error"
            return False, f"Failed to start Docker services: {error_msg}"
        
        # Give services time to initialize
        if headless:
            logger.info("⏳ Waiting for services to initialize (30s)...")
            time.sleep(30)
        
        logger.info("✅ Docker environment is ready!")
        logger.info("=" * 70 + "\n")
        return True, "Docker services started successfully"
        
    except Exception as e:
        return False, f"Error setting up Docker: {e}"


def teardown_docker(project_dir: str) -> Tuple[bool, str]:
    """Tear down Docker environment after testing.
    
    Args:
        project_dir: The project directory containing docker-compose.yml
        
    Returns:
        Tuple of (success, message)
    """
    logger.info("\n" + "=" * 70)
    logger.info("🧹 Cleaning up Docker environment...")
    
    try:
        # Stop the containers
        result = subprocess.run(
            ["docker", "compose", "down"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            cwd=project_dir
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode() if result.stderr else "Unknown error"
            return False, f"Failed to stop Docker services: {error_msg}"
        
        logger.info("✅ Docker environment cleaned up successfully!")
        logger.info("=" * 70 + "\n")
        return True, "Docker services stopped successfully"
        
    except Exception as e:
        return False, f"Error tearing down Docker: {e}"


class AgentBlackwellGauntlet:
    """End-to-end test gauntlet for Agent Blackwell API endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the test gauntlet.

        Args:
            base_url: Base URL of the Agent Blackwell API
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.test_results = {"passed": [], "failed": []}
        self.workflow_ids = []
        self.last_message_timestamp = 0  # Track last seen message timestamp
        self.output_dir = None  # Directory for logs/results
        self.run_timestamp = None  # Human-readable timestamp for this run

        # Test feature requests with varying complexity
        self.test_feature_requests = [
            # Simple specification request
            """Create a REST API endpoint for user authentication with JWT tokens. 
            Include login, logout, and token refresh functionality.""",
            
            # Design request
            """Design a microservices architecture for an e-commerce platform with 
            user management, product catalog, order processing, and payment services.""",
            
            # Code implementation request
            """Implement a Python class for managing Redis connections with connection pooling, 
            retry logic, and health checks.""",
            
            # Code review request
            """Review this FastAPI application structure and suggest improvements for 
            scalability, security, and maintainability.""",
            
            # Testing request
            """Create comprehensive unit and integration tests for a user registration 
            system with email validation and password hashing.""",
            
            # Complex multi-agent workflow
            """Build a complete CI/CD pipeline configuration for a Python web application 
            including testing, security scanning, and deployment automation.""",
        ]

        # Define test metadata for interactive mode
        self.test_metadata = [
            {
                "id": 1,
                "name": "Health Check",
                "description": "Verify API server is running and responding",
                "duration": "~1 second",
                "method": "run_health_check",
                "dependency": None,
            },
            {
                "id": 2,
                "name": "Feature Request Creation",
                "description": "Test workflow submission and task creation",
                "duration": "~3 seconds",
                "method": "run_feature_request_test",
                "dependency": "Health Check",
            },
            {
                "id": 3,
                "name": "Workflow Status Check",
                "description": "Verify workflow tracking and status reporting",
                "duration": "~2 seconds",
                "method": "check_workflow_status",
                "dependency": "Feature Request Creation",
            },
            {
                "id": 4,
                "name": "Legacy Endpoint Test",
                "description": "Test backward compatibility endpoints",
                "duration": "~2 seconds",
                "method": "test_legacy_endpoint",
                "dependency": "Feature Request Creation",
            },
            {
                "id": 5,
                "name": "Synchronous Workflow",
                "description": "Execute complex blocking workflow (Snake game)",
                "duration": "~60 seconds",
                "method": "run_synchronous_workflow",
                "dependency": None,
            },
            {
                "id": 6,
                "name": "Streaming Workflow",
                "description": "Test real-time streaming capabilities",
                "duration": "~30 seconds",
                "method": "test_stream_workflow",
                "dependency": None,
            },
            {
                "id": 7,
                "name": "ChatOps Commands",
                "description": "Test ChatOps command endpoint with various command types",
                "duration": "~10 seconds",
                "method": "test_chatops_commands",
                "dependency": None,
            },
        ]

    def _record_result(
        self, test_name: str, passed: bool, details: Optional[Dict] = None
    ):
        """Record test result for reporting."""
        result = {
            "test": test_name,
            "passed": passed,
            "timestamp": time.time(),
            "details": details or {},
        }

        if passed:
            self.test_results["passed"].append(result)
            logger.info(f"✅ PASSED: {test_name}")
        else:
            self.test_results["failed"].append(result)
            logger.error(f"❌ FAILED: {test_name}")
            if details:
                logger.error(f"Details: {json.dumps(details, indent=2)}")

    def fetch_agent_messages(
        self, workflow_id: str = None, limit: int = 20, fail_on_error: bool = True
    ) -> List[Dict]:
        """Fetch recent agent messages from the API."""
        try:
            params = {"number_of_messages": limit}
            if workflow_id:
                params["task_id"] = workflow_id

            response = self.session.get(
                f"{self.base_url}/api/v1/messages", params=params
            )
            response.raise_for_status()
            messages = response.json().get("messages", [])
            if not messages and fail_on_error:
                logger.error(f"📭 No messages retrieved for workflow_id: {workflow_id}")
                raise AssertionError(f"No agent messages retrieved for workflow_id: {workflow_id}")
            return messages
        except RequestException as e:
            if fail_on_error:
                logger.error(f"Failed to fetch agent messages: {e}")
                raise
            else:
                logger.warning(f"Failed to fetch agent messages: {e}")
                return []

    def display_agent_messages(
        self, workflow_id: str = None, show_new_only: bool = True, fail_on_error: bool = True
    ) -> bool:
        """Display agent messages from the API.
        
        Returns:
            bool: True if messages were successfully retrieved, False otherwise.
        """
        logger.info("\n" + "✨" * 25)
        logger.info(f"🔍 Checking agent messages for workflow: {workflow_id if workflow_id else 'all'}")
        logger.info("✨" * 25)
        
        try:
            messages = self.fetch_agent_messages(workflow_id, fail_on_error=fail_on_error)
            
            # Initialize seen message IDs for this workflow if needed
            if workflow_id not in self.seen_message_ids:
                self.seen_message_ids[workflow_id] = set()
            
            # Filter out messages we've already seen if requested
            if show_new_only and workflow_id in self.seen_message_ids:
                new_messages = []
                for msg in messages:
                    if msg.get("id") not in self.seen_message_ids[workflow_id]:
                        new_messages.append(msg)
                        self.seen_message_ids[workflow_id].add(msg.get("id"))
                messages = new_messages
            else:
                # Add all message IDs to seen set
                for msg in messages:
                    self.seen_message_ids[workflow_id].add(msg.get("id"))

            if not messages:
                logger.info("💬 No new messages since last check")
                logger.info("✨" * 25 + "\n")
                return True

            logger.info(f"📨 Found {len(messages)} agent messages:\n")
            
            # Get agent emojis for different agent types
            agent_emojis = {
                "spec": "📖",  # 📖
                "design": "📝",  # 📝
                "code": "💻",  # 💻
                "review": "🔍",  # 🔍
                "test": "🚨",  # 🚨
                "system": "⚙️",  # ⚙️
                "orchestrator": "🎸",  # 🎸
            }
            
            # Message type emojis
            type_emojis = {
                "status": "📊",  # 📊
                "error": "❌",  # ❌
                "result": "🎉",  # 🎉
                "progress": "📈",  # 📈
                "message": "💬",  # 💬
            }
            
            for i, msg in enumerate(messages):
                agent_name = msg.get('agent_name', 'unknown')
                message_type = msg.get('message_type', 'message')
                
                # Get appropriate emoji for agent and message type
                agent_emoji = "🤖"  # Default robot emoji
                for agent_key, emoji in agent_emojis.items():
                    if agent_key in agent_name.lower():
                        agent_emoji = emoji
                        break
                        
                type_emoji = type_emojis.get(message_type.lower(), "💬")
                
                # Format message header with emojis
                logger.info(
                    f"\n{agent_emoji} {agent_name.upper()} {type_emoji} {message_type.capitalize()} "
                    f"[Message {i+1}/{len(messages)}]"
                )
                logger.info("-" * 60)
                
                # Format content based on type
                content = msg.get("content", {})
                if isinstance(content, dict):
                    # Pretty print the JSON with indentation
                    formatted_content = json.dumps(content, indent=2)
                    logger.info(f"\n{formatted_content}\n")
                else:
                    logger.info(f"\n{content}\n")
                    
                logger.info("-" * 60)
            
            logger.info("\n" + "✨" * 25)
            logger.info(f"🌐 End of messages for workflow: {workflow_id if workflow_id else 'all'}")
            logger.info("✨" * 25 + "\n")
            return True
            
        except Exception as e:
            if fail_on_error:
                logger.error(f"\n❌ Error retrieving or displaying agent messages: {e}")
                self._record_result("Agent Message Retrieval", False, {"error": str(e), "workflow_id": workflow_id})
                logger.info("✨" * 25 + "\n")
                return False
            else:
                logger.warning(f"\n⚠️ Warning displaying agent messages: {e}")
                logger.info("✨" * 25 + "\n")
                return True

    def monitor_workflow_messages(self, workflow_id: str, duration_seconds: int = None, fail_on_error: bool = True):
        """Monitor agent messages for a workflow for a specified duration.
        
        Args:
            workflow_id: The workflow ID to monitor
            duration_seconds: How long to monitor for messages (in seconds)
            fail_on_error: Whether to fail the test if no messages are found
        """
        # Use class-level timeout if available, otherwise use parameter or default
        if duration_seconds is None:
            duration_seconds = getattr(self, 'message_timeout', 45)
            
        logger.info("\n" + "🔭" * 20)
        logger.info(f"📡 Monitoring agent messages for workflow {workflow_id}")
        logger.info(f"⏱️  Monitoring duration: {duration_seconds} seconds")
        logger.info("🔭" * 20)
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        message_count = 0
        last_check_time = start_time
        
        # Show progress indicators during long waits
        progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        progress_idx = 0
        
        while time.time() < end_time:
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                remaining = end_time - current_time
                
                # Update progress indicator every second
                if current_time - last_check_time >= 1:
                    progress_char = progress_chars[progress_idx % len(progress_chars)]
                    progress_idx += 1
                    print(f"\r{progress_char} Monitoring: {elapsed:.1f}s elapsed, {remaining:.1f}s remaining...", end="")
                    last_check_time = current_time
                    
                    # Check for new messages every 2 seconds
                    if progress_idx % 2 == 0:
                        if self.display_agent_messages(workflow_id, show_new_only=True, fail_on_error=False):
                            message_count += 1
                
                # Sleep briefly to avoid hammering the API and CPU
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ Error during message monitoring: {e}")
        
        # Clear the progress line and show final status
        print("\r" + " " * 80, end="\r")
        
        elapsed = time.time() - start_time
        logger.info(f"\n📊 Monitoring complete after {elapsed:.1f}s")
        logger.info(f"📬 Messages received: {message_count}")
        
        if message_count == 0 and fail_on_error:
            logger.error("\n❌ No agent messages detected during monitoring period")
            self._record_result(
                "Agent Message Monitoring", 
                False, 
                {"error": "No messages detected", "workflow_id": workflow_id, "duration": duration_seconds}
            )
            logger.info("🔭" * 20 + "\n")
            return False
        
        logger.info("✅ Message monitoring successful")
        logger.info("🔭" * 20 + "\n")
        return True

    def run_health_check(self) -> bool:
        """Test API health/root endpoint."""
        try:
            logger.info("Running health check...")
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            self._record_result("Health Check", True)
            return True
        except RequestException as e:
            self._record_result("Health Check", False, {"error": str(e)})
            logger.error(f"Health check failed: {e}")
            return False

    def run_feature_request_test(self) -> Optional[str]:
        """Run the feature request test.
        
        Returns:
            str: The workflow ID if successful, None otherwise
        """
        logger.info("\n" + "🚀" * 30)
        logger.info("🚀 RUNNING FEATURE REQUEST TEST")
        logger.info("🚀" * 30)
        
        try:
            # Generate a unique test description
            test_id = str(uuid.uuid4())[:8]
            description = f"Test feature request {test_id}"
            
            logger.info(f"📝 Request description: {description}")
            
            # Send the feature request
            logger.info("📤 Sending feature request to API...")
            response = requests.post(
                f"{self.base_url}/api/v1/feature-request",
                json={"description": description},
                timeout=10,
            )
            
            if response.status_code != 200:
                logger.error(f"\n❌ FAILED: Feature Request API returned {response.status_code}")
                logger.error(f"Details: {response.text}")
                self._record_result("Feature Request", False, {"status_code": response.status_code, "response": response.text})
                return None
                
            data = response.json()
            workflow_id = data.get("workflow_id")
            
            if not workflow_id:
                logger.error("\n❌ FAILED: No workflow ID returned")
                self._record_result("Feature Request", False, {"error": "No workflow ID", "response": data})
                return None
                
            logger.info(f"\n✅ PASSED: Feature request submitted successfully")
            logger.info(f"📋 Workflow ID: {workflow_id}")
            self._record_result("Feature Request", True, {"workflow_id": workflow_id})
            
            # Wait a bit before monitoring messages to allow the workflow to start
            wait_time = 10
            logger.info(f"\n⏳ Waiting {wait_time}s for workflow to initialize...")
            
            # Show a spinner while waiting
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            for i in range(wait_time * 2):
                print(f"\r{spinner_chars[i % len(spinner_chars)]} Initializing workflow...", end="")
                time.sleep(0.5)
            print("\r" + " " * 50, end="\r")
            
            # Get timeout from class attribute if available
            monitor_duration = getattr(self, 'message_timeout', 45)
            logger.info(f"📡 Starting message monitoring for {monitor_duration}s...")
            
            # Monitor for agent messages
            self.monitor_workflow_messages(workflow_id, duration_seconds=monitor_duration)
            
            logger.info("\n" + "🏁" * 30)
            logger.info("🏁 FEATURE REQUEST TEST COMPLETE")
            logger.info("🏁" * 30 + "\n")
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"\n❌ FAILED: Feature Request test")
            logger.error(f"Details: {str(e)}")
            self._record_result("Feature Request", False, {"error": str(e)})
            logger.info("\n" + "🏁" * 30)
            logger.info("🏁 FEATURE REQUEST TEST FAILED")
            logger.info("🏁" * 30 + "\n")
            return None
        except (RequestException, AssertionError) as e:
            self._record_result("Feature Request Creation", False, {"error": str(e)})
            logger.error(f"Feature request creation failed: {e}")
            return ""

    def check_workflow_status(self, workflow_id: str) -> bool:
        """Test workflow status endpoint."""
        try:
            logger.info(f"Checking workflow status for ID: {workflow_id}")
            response = self.session.get(
                f"{self.base_url}/api/v1/workflow-status/{workflow_id}"
            )
            response.raise_for_status()
            result = response.json()

            # Validate response format
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            logger.info(f"Workflow status: {result.get('status', 'unknown')}")

            # Display agent messages for this workflow with proper error handling
            logger.info("🔍 Checking agent messages for this workflow...")
            if not self.display_agent_messages(workflow_id, show_new_only=True, fail_on_error=True):
                logger.error(f"Failed to retrieve agent messages for workflow {workflow_id}")
                # We'll continue with the test but mark this step as failed
                self._record_result("Workflow Status Message Retrieval", False, {"workflow_id": workflow_id})

            self._record_result(
                "Workflow Status Check",
                True,
                {"workflow_id": workflow_id, "response": result},
            )
            return True
        except (RequestException, AssertionError) as e:
            self._record_result("Workflow Status Check", False, {"error": str(e)})
            logger.error(f"Workflow status check failed: {e}")
            return False

    def run_synchronous_workflow(self) -> Dict[str, Any]:
        """Test synchronous workflow execution endpoint."""
        try:
            logger.info("Executing synchronous workflow...")
            description = """Create a complete Snake game implementation with the following requirements:

PROJECT STRUCTURE:
- Create a proper Python package structure with __init__.py files
- Organize code into logical modules (game logic, UI, utilities)
- Include a requirements.txt file with all dependencies
- Add a comprehensive README.md with setup and play instructions

GAME FEATURES:
- Classic Snake gameplay with arrow key controls
- Score tracking and display
- Game over detection when snake hits walls or itself
- Increasing difficulty (speed) as score increases
- Food spawning with collision detection
- Snake growth mechanics

TECHNICAL REQUIREMENTS:
- Use pygame for graphics and input handling
- Implement proper game loop with FPS control
- Clean separation of concerns (Model-View-Controller pattern)
- Configuration file for game settings (screen size, colors, speeds)
- Error handling and input validation

TESTING REQUIREMENTS:
- Unit tests for core game logic (snake movement, collision detection, scoring)
- Integration tests for game state management
- Mock tests for pygame components
- Test coverage report
- Organize tests in a separate tests/ directory

DOCUMENTATION:
- Docstrings for all classes and functions
- Type hints throughout the codebase
- Code comments for complex logic
- Installation and usage instructions
- Architecture overview diagram

Please ensure the code is production-ready with proper error handling, logging, and follows Python best practices."""
            payload = {"description": description}

            # Start monitoring messages in a separate thread-like approach
            logger.info("🚀 Starting synchronous workflow execution...")
            start_time = time.time()

            response = self.session.post(
                f"{self.base_url}/api/v1/execute-workflow",
                json=payload,
                timeout=120,  # Increase timeout for complex synchronous execution
            )
            response.raise_for_status()
            result = response.json()

            execution_time = time.time() - start_time
            logger.info(
                f"⏱️ Synchronous workflow completed in {execution_time:.2f} seconds"
            )

            # Validate response format
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            workflow_id = result.get("workflow_id")
            if workflow_id:
                self.workflow_ids.append(workflow_id)

                # Display all agent messages for this workflow
                logger.info(
                    "🔍 Displaying all agent messages from synchronous workflow..."
                )
                self.display_agent_messages(workflow_id, show_new_only=False)

            self._record_result(
                "Synchronous Workflow Execution",
                True,
                {
                    "description": description,
                    "response": result,
                    "execution_time": execution_time,
                },
            )

            return result
        except (RequestException, AssertionError) as e:
            self._record_result(
                "Synchronous Workflow Execution", False, {"error": str(e)}
            )
            logger.error(f"Synchronous workflow execution failed: {e}")
            return {}

    async def test_stream_workflow(self) -> bool:
        """Test streaming workflow endpoint using aiohttp."""
        try:
            logger.info("Testing streaming workflow endpoint...")
            workflow_id = str(uuid.uuid4())
            description = "Create a simple Python utility that formats JSON data"

            async with aiohttp.ClientSession() as session:
                params = {"description": description}
                url = f"{self.base_url}/api/v1/stream-workflow/{workflow_id}"

                logger.info(f"Connecting to streaming endpoint: {url}")
                update_count = 0
                timeout = aiohttp.ClientTimeout(total=30)

                try:
                    async with session.get(
                        url, params=params, timeout=timeout
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(
                                f"Error response: {response.status}, {error_text}"
                            )

                        # Process streaming updates (SSE format)
                        async for line in response.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                update = json.loads(line[6:])
                                update_count += 1
                                logger.info(
                                    f"Received stream update {update_count}: {update.get('status', 'unknown')}"
                                )

                                # Break after receiving a few updates to avoid waiting too long
                                if update_count >= 3:
                                    break
                except asyncio.TimeoutError:
                    # Timeout is expected as the stream might be long-running
                    logger.info("Stream test completed (timeout)")

                # Check for agent messages during streaming
                logger.info("🔍 Checking agent messages during streaming test...")
                self.display_agent_messages(workflow_id, show_new_only=True)

                success = update_count > 0
                self._record_result(
                    "Streaming Workflow",
                    success,
                    {"workflow_id": workflow_id, "updates_received": update_count},
                )
                return success
        except Exception as e:
            self._record_result("Streaming Workflow", False, {"error": str(e)})
            logger.error(f"Streaming workflow test failed: {e}")
            return False

    def test_legacy_endpoint(self) -> bool:
        """Test legacy task status endpoint."""
        try:
            # Use a previously created workflow ID or generate a new one
            task_id = self.workflow_ids[0] if self.workflow_ids else str(uuid.uuid4())

            logger.info(f"Testing legacy task status endpoint with ID: {task_id}")
            response = self.session.get(f"{self.base_url}/api/v1/task-status/{task_id}")
            response.raise_for_status()
            result = response.json()

            # Validate response format (should match workflow status)
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            self._record_result(
                "Legacy Task Status", True, {"task_id": task_id, "response": result}
            )
            return True
        except (RequestException, AssertionError) as e:
            self._record_result("Legacy Task Status", False, {"error": str(e)})
            logger.error(f"Legacy task status test failed: {e}")
            return False

    def test_chatops_commands(self) -> bool:
        """Test ChatOps command endpoint with various command types."""
        try:
            logger.info("🤖 Testing ChatOps commands...")
            
            # Test commands to try - Updated payload structure based on API schema
            # From the schema: ChatCommandRequest requires platform, user_id, channel_id, command, timestamp
            test_commands = [
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!help",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!spec Create a user authentication system",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!design Microservices architecture for e-commerce",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!code Implement Redis connection pool",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!review Review this FastAPI application structure",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "platform": "slack",
                    "user_id": "test_user",
                    "channel_id": "test_channel",
                    "command": "!test Create comprehensive unit and integration tests",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            chatops_results = []
            success_count = 0
            
            for cmd_test in test_commands:
                command_text = cmd_test['command']
                logger.info(f"Testing command: {command_text}")
                
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/chatops/command",
                        json=cmd_test
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Validate response format
                    assert "message" in result, "ChatOps response missing message"
                    
                    chatops_results.append({
                        "command": command_text,
                        "status": "success",
                        "response": result
                    })
                    
                    logger.info(f"✅ Command '{command_text}' executed successfully")
                    success_count += 1
                    
                except RequestException as e:
                    # Log the error but continue testing other commands
                    logger.warning(f"Command '{command_text}' failed: {e}")
                    chatops_results.append({
                        "command": command_text,
                        "status": "failed",
                        "error": str(e)
                    })
                
                time.sleep(1)  # Brief pause between commands
            
            # Consider test successful if at least one command worked
            if success_count > 0:
                self._record_result(
                    "ChatOps Commands Test",
                    True,
                    {"commands_tested": len(test_commands), 
                     "successful": success_count,
                     "results": chatops_results}
                )
                logger.info(f"✅ {success_count}/{len(test_commands)} ChatOps commands executed successfully")
                return True
            else:
                self._record_result(
                    "ChatOps Commands Test",
                    False,
                    {"commands_tested": len(test_commands), 
                     "successful": 0,
                     "results": chatops_results}
                )
                logger.error("All ChatOps commands failed")
                return False
        
        except Exception as e:
            self._record_result("ChatOps Commands Test", False, {"error": str(e)})
            logger.error(f"ChatOps commands test failed: {e}")
            return False

    def print_summary(self):
        """Print test results summary."""
        passed = len(self.test_results["passed"])
        failed = len(self.test_results["failed"])
        total = passed + failed

        logger.info("\n" + "=" * 50)
        logger.info(f"TEST SUMMARY: {passed}/{total} tests passed ({failed} failed)")

        if failed > 0:
            logger.info("\nFailed Tests:")
            for test in self.test_results["failed"]:
                logger.info(
                    f"- {test['test']}: {test.get('details', {}).get('error', 'Unknown error')}"
                )

        logger.info("=" * 50)

        # Save results to file
        results_file = os.path.join(
            self.output_dir, f"e2e_test_results_{self.run_timestamp}.json"
        )
        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"Test results saved to {results_file}")

    async def run_all_tests(self, max_tests: Optional[int] = None):
        """Run all tests in sequence with appropriate waits.

        Args:
            max_tests: Optional maximum number of tests to run (for debugging)
        """
        start_time = time.time()
        logger.info(f"Starting Agent Blackwell API Gauntlet Test at {time.ctime()}")
        logger.info(f"API Base URL: {self.base_url}")

        if max_tests:
            logger.info(f"🎯 Running first {max_tests} tests only (debug mode)")

        test_count = 0

        # Test 1: Health check
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        if not self.run_health_check():
            logger.error("Health check failed. Aborting remaining tests.")
            self.print_summary()
            return

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Test 2: Feature request test
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        workflow_id = self.run_feature_request_test()

        logger.info("Waiting 5 seconds for workflow processing...")
        # Monitor messages during processing wait
        if workflow_id:
            logger.info("📡 Monitoring agent activity during processing...")
            for i in range(2):  # Monitor for 4 seconds total
                time.sleep(2)
                self.display_agent_messages(workflow_id, show_new_only=True)

        time.sleep(1)  # Final wait

        # Test 3: Workflow status check
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        if workflow_id:
            self.check_workflow_status(workflow_id)

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Test 4: Legacy endpoint test
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        self.test_legacy_endpoint()

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Display all accumulated messages before synchronous test
        logger.info("🔍 Displaying all agent messages accumulated so far...")
        self.display_agent_messages(show_new_only=False)

        # Test 5: Synchronous workflow test (may take longer)
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        logger.info("Starting synchronous workflow test (may take a minute)...")
        self.run_synchronous_workflow()

        logger.info("Waiting 5 seconds...")
        time.sleep(5)

        # Display final batch of messages
        logger.info("🔍 Final check for any remaining agent messages...")
        self.display_agent_messages(show_new_only=True)

        # Test 6: Streaming test
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        logger.info("Testing streaming endpoint...")
        await self.test_stream_workflow()

        # Test 7: ChatOps commands test
        test_count += 1
        if max_tests and test_count > max_tests:
            logger.info(f"⏹️ Stopping after {max_tests} tests")
            self._print_partial_summary(test_count - 1)
            return

        logger.info("Testing ChatOps commands...")
        self.test_chatops_commands()

        # Generate and print summary
        elapsed_time = time.time() - start_time
        logger.info(f"\nAll tests completed in {elapsed_time:.2f} seconds")

        # Final comprehensive message display
        logger.info("🔍 FINAL: Displaying all agent messages from entire test run...")
        self.display_agent_messages(show_new_only=False)

        self.print_summary()

    def _print_partial_summary(self, tests_run: int):
        """Print a partial summary when tests are stopped early."""
        logger.info(f"\n🔹 PARTIAL TEST SUMMARY: Ran {tests_run} tests")
        logger.info("=" * 50)

        passed = sum(1 for result in self.test_results["passed"])
        failed = len(self.test_results["failed"])

        if failed == 0:
            logger.info(f"✅ {passed}/{tests_run} tests passed")
        else:
            logger.info(f"⚠️ {passed}/{tests_run} tests passed, {failed} failed")

        logger.info("=" * 50)

        # Save partial results
        timestamp = datetime.now().isoformat()
        results_data = {
            "timestamp": timestamp,
            "total_tests_run": tests_run,
            "results": self.test_results,
            "summary": {"passed": passed, "failed": failed},
        }

        partial_file = os.path.join(
            self.output_dir, f"e2e_test_results_partial_{self.run_timestamp}.json"
        )
        with open(partial_file, "w") as f:
            json.dump(results_data, f, indent=2)
        logger.info(f"Partial test results saved to {partial_file}")

    def interactive_menu(self) -> Dict[str, Any]:
        """Interactive menu for customizing test runs."""
        print("\n" + "=" * 70)
        print("🎯 AGENT BLACKWELL E2E TEST GAUNTLET - INTERACTIVE MODE")
        print("=" * 70)
        print(f"API Base URL: {self.base_url}")
        print()

        # Display available tests
        print("📋 AVAILABLE TESTS:")
        print("-" * 50)
        for test in self.test_metadata:
            dependency_str = (
                f" (requires: {test['dependency']})" if test["dependency"] else ""
            )
            print(f"{test['id']}. {test['name']} - {test['duration']}")
            print(f"   {test['description']}{dependency_str}")
            print()

        config = {
            "selected_tests": [],
            "base_url": self.base_url,
            "include_agent_monitoring": True,
            "custom_timeout": None,
        }

        while True:
            print("\n" + "=" * 50)
            print("🔧 CONFIGURATION OPTIONS")
            print("=" * 50)
            print("1. Select specific tests to run")
            print("2. Run all tests")
            print("3. Quick presets")
            print("4. Configure base URL")
            print("5. Toggle agent message monitoring")
            print("6. Set custom timeouts")
            print("7. Show current configuration")
            print("8. Start test run")
            print("9. Exit")

            try:
                choice = input("\nEnter your choice (1-9): ").strip()

                if choice == "1":
                    config["selected_tests"] = self._select_individual_tests()
                elif choice == "2":
                    config["selected_tests"] = list(range(1, 8))
                    print("✅ Selected all tests (1-7)")
                elif choice == "3":
                    config["selected_tests"] = self._quick_presets()
                elif choice == "4":
                    new_url = input(
                        f"Enter base URL (current: {config['base_url']}): "
                    ).strip()
                    if new_url:
                        config["base_url"] = new_url
                        self.base_url = new_url
                        print(f"✅ Base URL updated to: {new_url}")
                elif choice == "5":
                    config["include_agent_monitoring"] = not config[
                        "include_agent_monitoring"
                    ]
                    status = (
                        "enabled" if config["include_agent_monitoring"] else "disabled"
                    )
                    print(f"✅ Agent message monitoring {status}")
                elif choice == "6":
                    timeout = input(
                        "Enter custom timeout in seconds (or press Enter for default): "
                    ).strip()
                    if timeout.isdigit():
                        config["custom_timeout"] = int(timeout)
                        print(f"✅ Custom timeout set to {timeout} seconds")
                    elif timeout == "":
                        config["custom_timeout"] = None
                        print("✅ Using default timeouts")
                    else:
                        print("❌ Invalid timeout value")
                elif choice == "7":
                    self._show_current_config(config)
                elif choice == "8":
                    if not config["selected_tests"]:
                        print("❌ Please select at least one test to run")
                        continue
                    return config
                elif choice == "9":
                    print("👋 Goodbye!")
                    exit(0)
                else:
                    print("❌ Invalid choice. Please enter 1-9.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                exit(0)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    def _select_individual_tests(self) -> List[int]:
        """Allow user to select individual tests."""
        print("\n📝 SELECT TESTS TO RUN")
        print("=" * 30)
        print("Enter test numbers separated by commas (e.g., 1,3,5)")
        print("Or enter ranges (e.g., 1-3,5-6)")
        print("Press Enter to go back")

        while True:
            try:
                selection = input("\nYour selection: ").strip()
                if not selection:
                    return []

                selected = []
                parts = selection.split(",")

                for part in parts:
                    part = part.strip()
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        selected.extend(range(start, end + 1))
                    else:
                        selected.append(int(part))

                # Validate selections
                valid_tests = [t for t in selected if 1 <= t <= 7]
                invalid_tests = [t for t in selected if t not in valid_tests]

                if invalid_tests:
                    print(f"❌ Invalid test numbers: {invalid_tests}")
                    continue

                # Remove duplicates and sort
                valid_tests = sorted(list(set(valid_tests)))

                print(f"✅ Selected tests: {valid_tests}")
                return valid_tests

            except ValueError:
                print(
                    "❌ Invalid format. Use numbers separated by commas or ranges (e.g., 1-3)"
                )
            except KeyboardInterrupt:
                return []

    def _quick_presets(self) -> List[int]:
        """Quick preset configurations."""
        print("\n⚡ QUICK PRESETS")
        print("=" * 20)
        print("1. Basic validation (Health + Feature Request)")
        print("2. Core functionality (Tests 1-4)")
        print("3. Skip slow tests (Tests 1-4, 6)")
        print("4. Only fast tests (Tests 1-3)")
        print("5. Full workflow test (Test 5 only)")
        print("6. Development suite (Tests 1-3)")
        print("7. Back to main menu")

        presets = {
            "1": [1, 2],
            "2": [1, 2, 3, 4],
            "3": [1, 2, 3, 4, 6],
            "4": [1, 2, 3],
            "5": [5],
            "6": [1, 2, 3],
        }

        while True:
            try:
                choice = input("\nSelect preset (1-7): ").strip()
                if choice == "7":
                    return []
                elif choice in presets:
                    selected = presets[choice]
                    print(f"✅ Selected preset: {selected}")
                    return selected
                else:
                    print("❌ Invalid choice. Please enter 1-7.")
            except KeyboardInterrupt:
                return []

    def _show_current_config(self, config: Dict[str, Any]):
        """Display current configuration."""
        print("\n📊 CURRENT CONFIGURATION")
        print("=" * 30)
        print(f"Base URL: {config['base_url']}")
        print(
            f"Agent Monitoring: {'Enabled' if config['include_agent_monitoring'] else 'Disabled'}"
        )
        print(f"Custom Timeout: {config['custom_timeout'] or 'Default'}")

        if config["selected_tests"]:
            print(f"Selected Tests: {config['selected_tests']}")
            print("\nTest Details:")
            for test_id in config["selected_tests"]:
                test = next(t for t in self.test_metadata if t["id"] == test_id)
                print(f"  {test_id}. {test['name']} ({test['duration']})")
        else:
            print("Selected Tests: None")

        print("\n" + "=" * 30)

    async def run_selected_tests(self, config: Dict[str, Any]):
        """Run only the selected tests based on configuration."""
        start_time = time.time()
        selected_tests = config["selected_tests"]

        logger.info(f"🎯 Interactive Mode: Running tests {selected_tests}")
        logger.info(f"Starting Agent Blackwell API Gauntlet Test at {time.ctime()}")
        logger.info(f"API Base URL: {config['base_url']}")

        # Update base URL if changed
        self.base_url = config["base_url"]

        workflow_id = None
        test_count = 0

        for test_id in selected_tests:
            test_count += 1
            test = next(t for t in self.test_metadata if t["id"] == test_id)

            logger.info(
                f"\n🧪 Running Test {test_id}/{len(selected_tests)}: {test['name']}"
            )
            logger.info(f"📝 {test['description']}")

            # Run the specific test
            if test_id == 1:  # Health Check
                if not self.run_health_check():
                    logger.error(
                        "Health check failed. Consider aborting remaining tests."
                    )
                    if input("Continue with remaining tests? (y/N): ").lower() != "y":
                        break

            elif test_id == 2:  # Feature Request
                workflow_id = self.run_feature_request_test()
                if config["include_agent_monitoring"] and workflow_id:
                    logger.info("📡 Monitoring agent activity...")
                    time.sleep(2)
                    self.display_agent_messages(workflow_id, show_new_only=True)

            elif test_id == 3:  # Workflow Status
                if workflow_id:
                    self.check_workflow_status(workflow_id)
                    if config["include_agent_monitoring"]:
                        self.display_agent_messages(workflow_id, show_new_only=True)
                else:
                    logger.warning("No workflow ID available for status check")

            elif test_id == 4:  # Legacy Endpoint
                if workflow_id:
                    self.test_legacy_endpoint()
                else:
                    logger.warning("No workflow ID available for legacy test")

            elif test_id == 5:  # Synchronous Workflow
                logger.info("⚠️ This test may take up to 60 seconds...")
                self.run_synchronous_workflow()
                if config["include_agent_monitoring"]:
                    self.display_agent_messages(show_new_only=True)

            elif test_id == 6:  # Streaming Workflow
                logger.info("⚠️ This test may take up to 30 seconds...")
                await self.test_stream_workflow()
                if config["include_agent_monitoring"]:
                    self.display_agent_messages(show_new_only=True)

            elif test_id == 7:  # ChatOps Commands
                logger.info("⚠️ This test may take up to 10 seconds...")
                self.test_chatops_commands()
                if config["include_agent_monitoring"]:
                    self.display_agent_messages(show_new_only=True)

            # Brief pause between tests
            if test_count < len(selected_tests):
                logger.info("⏱️ Waiting 2 seconds before next test...")
                time.sleep(2)

        # Final summary
        elapsed_time = time.time() - start_time
        logger.info(f"\n✅ Selected tests completed in {elapsed_time:.2f} seconds")

        if config["include_agent_monitoring"]:
            logger.info("🔍 FINAL: Displaying all agent messages from test run...")
            self.display_agent_messages(show_new_only=False)

        self.print_summary()


async def main():
    """Main entry point for the test gauntlet."""
    parser = argparse.ArgumentParser(
        description="🤖 Agent Blackwell E2E Test Gauntlet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
✨ Examples:
  python e2e_test_gauntlet.py                           # Run all tests
  python e2e_test_gauntlet.py --max-tests 3            # Run first 3 tests only
  python e2e_test_gauntlet.py --docker                 # Start Docker before running tests
  python e2e_test_gauntlet.py --docker --no-headless   # Start Docker in interactive mode
  python e2e_test_gauntlet.py --docker-only            # Only start Docker, don't run tests
  python e2e_test_gauntlet.py --teardown-docker        # Stop Docker containers
        """,
    )

    # Test selection options
    test_group = parser.add_argument_group('📝 Test Selection Options')
    test_group.add_argument(
        "--max-tests",
        "-n",
        type=int,
        help="Maximum number of tests to run (1-7). Useful for debugging specific tests.",
    )
    test_group.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with customizable test selection",
    )
    
    # Docker management options
    docker_group = parser.add_argument_group('🐳 Docker Management Options')
    docker_group.add_argument(
        "--docker",
        action="store_true",
        help="Start Docker containers before running tests",
    )
    docker_group.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Docker in interactive mode (not detached)",
    )
    docker_group.add_argument(
        "--docker-only",
        action="store_true",
        help="Only start Docker containers, don't run tests",
    )
    docker_group.add_argument(
        "--teardown-docker",
        action="store_true",
        help="Stop Docker containers after tests (or immediately if --docker-only)",
    )
    
    # API and output options
    config_group = parser.add_argument_group('⚙️ Configuration Options')
    config_group.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the Agent Blackwell API (default: http://localhost:8000)",
    )
    config_group.add_argument(
        "--output-dir", 
        default="logs", 
        help="Directory to store logs and test outputs"
    )
    config_group.add_argument(
        "--message-timeout",
        type=int,
        default=45,
        help="Timeout in seconds when waiting for agent messages (default: 45)"
    )

    args = parser.parse_args()
    
    # Print fancy banner
    print("\n" + "=" * 80)
    print("🤖 🚨 💻  AGENT BLACKWELL E2E TEST GAUNTLET  💻 🚨 🤖")
    print("=" * 80)
    print(f"\n📅 Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API URL: {args.base_url}")
    if args.docker:
        print(f"🐳 Docker: {'Interactive' if args.no_headless else 'Headless'} Mode")
    print("\n" + "-" * 80 + "\n")

    # Prepare output directory and file logging
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configure file logging
    log_file = os.path.join(output_dir, f"gauntlet_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    
    # Get project directory (parent of script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    # Handle Docker operations
    docker_started = False
    if args.docker or args.docker_only:
        success, message = setup_docker(project_dir, headless=not args.no_headless)
        if not success:
            logger.error(f"🚫 Docker setup failed: {message}")
            return
        docker_started = True
        
        # If docker-only flag is set, exit after starting Docker
        if args.docker_only:
            logger.info("🐳 Docker containers started successfully. Exiting as requested.")
            if args.teardown_docker:
                teardown_docker(project_dir)
            return
    
    # Validate max_tests range
    if args.max_tests is not None:
        if args.max_tests < 1 or args.max_tests > 7:
            logger.error("--max-tests must be between 1 and 7")
            return
        logger.info(f"🎯 Debug mode: Running first {args.max_tests} tests only")

    # Initialize and run tests
    gauntlet = AgentBlackwellGauntlet(base_url=args.base_url)
    gauntlet.output_dir = output_dir
    gauntlet.run_timestamp = timestamp
    gauntlet.message_timeout = args.message_timeout

    try:
        if args.interactive:
            config = gauntlet.interactive_menu()
            await gauntlet.run_selected_tests(config)
        else:
            await gauntlet.run_all_tests(max_tests=args.max_tests)
    finally:
        # Teardown Docker if requested
        if docker_started and args.teardown_docker:
            logger.info("🐳 Tests completed, tearing down Docker containers...")
            teardown_docker(project_dir)


if __name__ == "__main__":
    asyncio.run(main())
