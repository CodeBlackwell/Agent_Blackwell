#!/usr/bin/env python3
"""
End-to-End Gauntlet Test Script for Agent Blackwell API

This script tests all API endpoints in the Agent Blackwell system, including:
- Feature request creation
- Workflow status checks
- Synchronous workflow execution
- Streaming workflow execution
- Legacy endpoint compatibility

The script includes appropriate wait times between requests and thorough
validation of responses to ensure the system is functioning correctly.
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
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

        # Test feature requests with varying complexity
        self.test_feature_requests = [
            "Create a simple function that calculates the Fibonacci sequence up to n terms",
            "Implement a Python class for a basic REST API client with error handling",
            "Create a data visualization dashboard using pandas and matplotlib",
            "Write a function to convert CSV data to JSON format with type validation",
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

            return workflow_id
        except (RequestException, AssertionError) as e:
            self._record_result("Feature Request Creation", False, {"error": str(e)})
            logger.error(f"Feature request test failed: {e}")
            return ""

    def check_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Test workflow status endpoint."""
        try:
            if not workflow_id:
                workflow_id = str(uuid.uuid4())  # Use random ID if none provided
                logger.warning(
                    f"Using random workflow ID for status check: {workflow_id}"
                )

            logger.info(f"Checking workflow status for ID: {workflow_id}")
            response = self.session.get(
                f"{self.base_url}/api/v1/workflow-status/{workflow_id}"
            )
            response.raise_for_status()
            result = response.json()

            # Validate response format
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            self._record_result(
                "Workflow Status Check",
                True,
                {"workflow_id": workflow_id, "response": result},
            )

            return result
        except (RequestException, AssertionError) as e:
            self._record_result("Workflow Status Check", False, {"error": str(e)})
            logger.error(f"Workflow status check failed: {e}")
            return {}

    def run_synchronous_workflow(self) -> Dict[str, Any]:
        """Test synchronous workflow execution endpoint."""
        try:
            logger.info("Executing synchronous workflow...")
            description = "Write a simple 'Hello World' function in Python"
            payload = {"description": description}

            response = self.session.post(
                f"{self.base_url}/api/v1/execute-workflow",
                json=payload,
                timeout=60,  # Increase timeout for synchronous execution
            )
            response.raise_for_status()
            result = response.json()

            # Validate response format
            assert "workflow_id" in result, "Response missing workflow_id"
            assert "status" in result, "Response missing status"

            self._record_result(
                "Synchronous Workflow Execution",
                True,
                {"description": description, "response": result},
            )

            if "workflow_id" in result:
                self.workflow_ids.append(result["workflow_id"])

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
        with open("e2e_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        logger.info("Test results saved to e2e_test_results.json")

    async def run_all_tests(self):
        """Run all tests in sequence with appropriate waits."""
        start_time = time.time()
        logger.info(f"Starting Agent Blackwell API Gauntlet Test at {time.ctime()}")
        logger.info(f"API Base URL: {self.base_url}")

        # Health check
        if not self.run_health_check():
            logger.error("Health check failed. Aborting remaining tests.")
            self.print_summary()
            return

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Feature request test
        workflow_id = self.run_feature_request_test()

        logger.info("Waiting 5 seconds for workflow processing...")
        time.sleep(5)

        # Workflow status check
        if workflow_id:
            self.check_workflow_status(workflow_id)

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Legacy endpoint test
        self.test_legacy_endpoint()

        logger.info("Waiting 2 seconds...")
        time.sleep(2)

        # Synchronous workflow test (may take longer)
        logger.info("Starting synchronous workflow test (may take a minute)...")
        self.run_synchronous_workflow()

        logger.info("Waiting 5 seconds...")
        time.sleep(5)

        # Streaming test
        logger.info("Testing streaming endpoint...")
        await self.test_stream_workflow()

        # Generate and print summary
        elapsed_time = time.time() - start_time
        logger.info(f"\nAll tests completed in {elapsed_time:.2f} seconds")
        self.print_summary()


async def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="End-to-End Gauntlet Test for Agent Blackwell API"
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL of Agent Blackwell API"
    )
    args = parser.parse_args()

    gauntlet = AgentBlackwellGauntlet(base_url=args.url)
    await gauntlet.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
