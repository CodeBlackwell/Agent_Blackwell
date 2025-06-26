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
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("e2e_gauntlet")


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
            # DIFFICULTY: EXTREMELY EASY (⭐)
            """Create a simple password generator utility with the following requirements:

DIFFICULTY LEVEL: ⭐ EXTREMELY EASY

CORE FUNCTIONALITY:
- Generate random passwords with specified length
- Include options for uppercase, lowercase, numbers, and symbols
- Command-line interface with argument parsing
- Basic input validation

PROJECT STRUCTURE:
- Single Python file with main function
- Simple requirements.txt file
- Basic README with usage instructions

FEATURES:
- Customizable password length (8-50 characters)
- Character set selection (letters, numbers, symbols)
- Generate multiple passwords at once
- Copy to clipboard functionality (optional)

TESTING:
- Basic unit tests for password generation logic
- Test different character set combinations
- Validate password length and character requirements

DOCUMENTATION:
- Function docstrings
- Usage examples in README
- Simple installation instructions""",
            # DIFFICULTY: EASY (⭐⭐)
            """Build a personal expense tracker CLI application:

DIFFICULTY LEVEL: ⭐⭐ EASY

CORE FEATURES:
- Add, view, and delete expense entries
- Categories for expenses (food, transport, entertainment, etc.)
- Monthly and weekly expense summaries
- Data persistence using JSON or CSV files

PROJECT STRUCTURE:
- Organized into modules (main, data_handler, calculator)
- Simple configuration file for categories
- Requirements.txt with minimal dependencies
- Clear README with setup instructions

FUNCTIONALITY:
- Command-line interface using argparse
- Input validation and error handling
- Basic data visualization (simple text charts)
- Export data to CSV format

TESTING REQUIREMENTS:
- Unit tests for calculation functions
- Test data persistence and retrieval
- Mock tests for file operations
- Basic integration tests

DOCUMENTATION:
- Function and class docstrings
- Type hints for main functions
- User guide with examples
- Installation and usage instructions""",
            # DIFFICULTY: EASY-MODERATE (⭐⭐⭐)
            """Create a simple Snake game implementation:

DIFFICULTY LEVEL: ⭐⭐⭐ EASY-MODERATE

PROJECT STRUCTURE:
- Organize into logical modules (game, snake, food, ui)
- Include requirements.txt with pygame dependency
- Comprehensive README with setup and play instructions

GAME FEATURES:
- Classic Snake gameplay with arrow key controls
- Score tracking and display
- Game over detection when snake hits walls or itself
- Food spawning with collision detection
- Snake growth mechanics

TECHNICAL REQUIREMENTS:
- Use pygame for graphics and input handling
- Implement basic game loop with FPS control
- Simple configuration for game settings (screen size, colors)
- Basic error handling and input validation

TESTING REQUIREMENTS:
- Unit tests for core game logic (snake movement, collision detection)
- Mock tests for pygame components
- Test coverage for game state management

DOCUMENTATION:
- Docstrings for main classes and functions
- Type hints throughout the codebase
- Installation and play instructions
- Basic code comments for game logic""",
            # DIFFICULTY: MODERATE (⭐⭐⭐⭐)
            """Develop a personal task management API:

DIFFICULTY LEVEL: ⭐⭐⭐⭐ MODERATE

CORE FEATURES:
- CRUD operations for tasks (create, read, update, delete)
- Task categories and priority levels
- Due date tracking and status management
- Simple user authentication with API keys
- Search and filter functionality

TECHNICAL STACK:
- FastAPI framework with basic async operations
- SQLite database with SQLAlchemy ORM
- Pydantic models for request/response validation
- Simple JWT authentication

PROJECT STRUCTURE:
- Modular architecture with separate routers
- Database models and basic migrations
- Service layer for business logic
- Configuration management with environment variables

TESTING & QUALITY:
- Unit tests with pytest
- API integration tests with test database
- Basic error handling and validation
- Simple API documentation with OpenAPI

DEPLOYMENT:
- Docker containerization (basic Dockerfile)
- Environment-based configuration
- Health check endpoint
- Basic logging setup""",
            # DIFFICULTY: MODERATE (⭐⭐⭐⭐)
            """Build a simple web scraper and data processor:

DIFFICULTY LEVEL: ⭐⭐⭐⭐ MODERATE

DATA COLLECTION:
- Web scraping using requests and BeautifulSoup
- Extract data from multiple pages with pagination
- Handle different data formats (HTML tables, lists, text)
- Implement rate limiting and respectful scraping

DATA PROCESSING:
- Clean and validate scraped data
- Store data in CSV and JSON formats
- Basic data analysis and summary statistics
- Simple data visualization with matplotlib

PROJECT STRUCTURE:
- Separate modules for scraping, processing, and analysis
- Configuration file for target websites and settings
- Comprehensive error handling and logging
- Clear documentation and usage examples

FEATURES:
- Command-line interface with multiple options
- Progress tracking for long-running scrapes
- Data export in multiple formats
- Basic duplicate detection and handling

TESTING:
- Unit tests for data processing functions
- Mock tests for web requests
- Test data validation and cleaning
- Integration tests with sample data

QUALITY ASSURANCE:
- Type hints throughout codebase
- Comprehensive error handling
- Logging for debugging and monitoring
- User-friendly error messages""",
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
        self, workflow_id: str = None, limit: int = 20
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
            return response.json().get("messages", [])
        except RequestException as e:
            logger.warning(f"Failed to fetch agent messages: {e}")
            return []

    def display_agent_messages(
        self, workflow_id: str = None, show_new_only: bool = True
    ):
        """Display agent messages in a formatted way."""
        messages = self.fetch_agent_messages(workflow_id, limit=50)

        # Fail if no messages retrieved (treat as test failure)
        if not messages:
            logger.error("📭 No agent messages retrieved from messages endpoint")
            # Raise to let test harness catch and record failure
            raise AssertionError(
                "No agent messages retrieved for workflow_id: {}".format(workflow_id)
            )

        # Filter to new messages if requested
        if show_new_only:
            new_messages = [
                msg
                for msg in messages
                if msg.get("timestamp", 0) > self.last_message_timestamp
            ]
            if new_messages:
                # Update last seen timestamp
                self.last_message_timestamp = max(
                    msg.get("timestamp", 0) for msg in new_messages
                )
                messages = new_messages
            else:
                return  # No new messages

        logger.info("=" * 60)
        logger.info("🤖 AGENT COMMUNICATIONS")
        logger.info("=" * 60)

        for msg in messages[-10:]:  # Show last 10 messages
            timestamp = msg.get("timestamp", 0)
            task_id = msg.get("task_id", "unknown")
            agent_name = msg.get("agent_name", "Unknown Agent")
            message_type = msg.get("message_type", "message")
            content = msg.get("content", {})

            # Format timestamp
            time_str = (
                time.strftime("%H:%M:%S", time.localtime(timestamp))
                if timestamp
                else "unknown"
            )

            logger.info(f"[{time_str}] 🔵 {agent_name} ({message_type})")
            if isinstance(content, dict):
                if "status" in content:
                    logger.info(f"   Status: {content['status']}")
                if "message" in content:
                    logger.info(f"   Message: {content['message']}")
                if "progress" in content:
                    logger.info(f"   Progress: {content['progress']}")
                if "error" in content:
                    logger.info(f"   ❌ Error: {content['error']}")
            else:
                logger.info(f"   Content: {str(content)[:200]}...")

            logger.info("   " + "-" * 40)

        logger.info("=" * 60)

    def monitor_workflow_messages(self, workflow_id: str, duration_seconds: int = 10):
        """Monitor and display agent messages for a specific workflow."""
        logger.info(
            f"📡 Monitoring agent messages for workflow {workflow_id[:8]}... (for {duration_seconds}s)"
        )

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            self.display_agent_messages(workflow_id, show_new_only=True)
            time.sleep(2)  # Check every 2 seconds

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

    def run_feature_request_test(self) -> str:
        """Test feature request creation endpoint."""
        try:
            logger.info("Submitting feature request...")
            description = random.choice(self.test_feature_requests)
            payload = {"description": description}

            response = self.session.post(
                f"{self.base_url}/api/v1/feature-request", json=payload
            )
            response.raise_for_status()
            result = response.json()

            # Validate response format
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            workflow_id = result["workflow_id"]
            self.workflow_ids.append(workflow_id)

            self._record_result(
                "Feature Request Creation",
                True,
                {
                    "description": description,
                    "workflow_id": workflow_id,
                    "response": result,
                },
            )

            # Monitor initial agent messages for this workflow
            logger.info("🔍 Checking for initial agent messages...")
            time.sleep(3)  # Give agents time to start processing
            self.display_agent_messages(workflow_id, show_new_only=False)

            return workflow_id
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

            # Display agent messages for this workflow
            logger.info("🔍 Checking agent messages for this workflow...")
            self.display_agent_messages(workflow_id, show_new_only=True)

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
                    config["selected_tests"] = list(range(1, 7))
                    print("✅ Selected all tests (1-6)")
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
                valid_tests = [t for t in selected if 1 <= t <= 6]
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
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Blackwell E2E Test Gauntlet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python e2e_test_gauntlet.py                    # Run all tests
  python e2e_test_gauntlet.py --max-tests 3     # Run first 3 tests only
  python e2e_test_gauntlet.py -n 1              # Run only health check
        """,
    )

    parser.add_argument(
        "--max-tests",
        "-n",
        type=int,
        help="Maximum number of tests to run (1-6). Useful for debugging specific tests.",
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the Agent Blackwell API (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with customizable test selection",
    )

    parser.add_argument(
        "--output-dir", default="logs", help="Directory to store logs and test outputs"
    )

    args = parser.parse_args()

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

    # Validate max_tests range
    if args.max_tests is not None:
        if args.max_tests < 1 or args.max_tests > 6:
            logger.error("--max-tests must be between 1 and 6")
            return
        logger.info(f"🎯 Debug mode: Running first {args.max_tests} tests only")

    gauntlet = AgentBlackwellGauntlet(base_url=args.base_url)
    gauntlet.output_dir = output_dir
    gauntlet.run_timestamp = timestamp

    if args.interactive:
        config = gauntlet.interactive_menu()
        await gauntlet.run_selected_tests(config)
    else:
        await gauntlet.run_all_tests(max_tests=args.max_tests)


if __name__ == "__main__":
    asyncio.run(main())
