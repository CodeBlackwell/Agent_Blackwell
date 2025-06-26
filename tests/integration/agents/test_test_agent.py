"""
Integration tests for the TestAgent.
"""
import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestTestAgentIntegration(BaseAgentIntegrationTest):
    """Test TestAgent integration."""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_test_agent_with_mock_llm(
        self,
        mock_post,
        redis_client,
        agent_fixtures,
        user_request_fixtures,
        agent_worker,
    ):
        """Test TestAgent with mock LLM."""
        # Create mock test output instead of using missing fixtures
        test_output = json.dumps(
            {
                "test_files": {
                    "test_main.py": "import pytest\ndef test_main():\n    assert True",
                    "test_user_service.py": "import pytest\ndef test_create_user():\n    assert True",
                },
                "test_coverage": {
                    "percentage": 85,
                    "covered_lines": 85,
                    "total_lines": 100,
                },
                "test_results": {"passed": 10, "failed": 0, "total": 10},
                "performance_tests": {"load_test": "passed", "stress_test": "passed"},
            }
        )
        mock_response = await self.setup_mock_llm_response(test_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Create mock review output instead of using missing fixtures
        review_output = {
            "source_code": {
                "main.py": "def hello_world():\n    return 'Hello, World!'",
                "utils.py": "def format_greeting(name):\n    return f'Hello, {name}!'",
            },
            "review_summary": "Code is well-structured and follows best practices.",
            "code_quality_score": 85,
        }

        # Prepare input message for the TestAgent
        input_message = {
            "request_id": "test-agent-123",
            "user_id": "test-user-456",
            "source_code": review_output["source_code"],
            "approval_status": "approved",
            "review_summary": "Code quality is good, ready for testing",
            "code_quality_score": 85,
            "timestamp": "2025-06-26T02:30:00Z",
            "request_type": "test",
            "priority": "high",
        }

        # Test that the agent produces the expected output
        expected_output_keys = [
            "request_id",
            "test_files",
            "test_coverage",
            "test_results",
            "performance_tests",
        ]

        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "test",
            input_message,
            expected_output_keys,
            timeout=30.0,  # Increase timeout for agent processing
        )

        # Assert specific content in the output
        assert "test_files" in output_data, "test_files missing from output"
        test_files = output_data["test_files"]
        assert isinstance(test_files, dict), "test_files should be a dictionary"
        assert len(test_files) > 0, "test_files is empty"

        # Verify test coverage exists and is valid
        assert "test_coverage" in output_data, "test_coverage missing from output"
        coverage = output_data["test_coverage"]
        assert isinstance(coverage, dict), "test_coverage should be a dictionary"
        assert "percentage" in coverage, "coverage missing percentage"
        assert "covered_lines" in coverage, "coverage missing covered_lines"
        assert "total_lines" in coverage, "coverage missing total_lines"

        # Verify test results format
        assert "test_results" in output_data, "test_results missing from output"
        results = output_data["test_results"]
        assert isinstance(results, dict), "test_results should be a dictionary"
        assert "passed" in results, "test_results missing 'passed' count"
        assert "failed" in results, "test_results missing 'failed' count"
        assert "total" in results, "test_results missing 'total' count"

        # Verify performance tests exist
        assert (
            "performance_tests" in output_data
        ), "performance_tests missing from output"
        perf_tests = output_data["performance_tests"]
        assert isinstance(perf_tests, dict), "performance_tests should be a dictionary"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_test_agent_generates_comprehensive_tests(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test TestAgent generates comprehensive test suites."""
        # Create mock comprehensive test output instead of using missing fixtures
        comprehensive_test_output = json.dumps(
            {
                "test_files": {
                    "test_user_service.py": "import pytest\n\ndef test_user_creation():\n    # User creation tests\n    assert True\n\ndef test_authentication():\n    # Authentication tests\n    assert True",
                    "test_api_endpoints.py": "import pytest\n\ndef test_endpoints():\n    # API endpoint tests\n    assert True",
                },
                "test_coverage": {
                    "percentage": 90,
                    "covered_lines": 180,
                    "total_lines": 200,
                },
                "test_results": {"passed": 15, "failed": 0, "total": 15},
                "performance_tests": {"load_test": "passed", "stress_test": "passed"},
                "integration_tests": {
                    "api_tests": {"status": "passed"},
                    "database_tests": {"status": "passed"},
                },
                "security_tests": {"vulnerabilities_found": 0},
            }
        )
        mock_response = await self.setup_mock_llm_response(comprehensive_test_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Prepare input with complex code requiring comprehensive testing
        input_message = {
            "request_id": "comprehensive-test-789",
            "user_id": "test-user-456",
            "source_code": {
                "user_service.py": "class UserService:\n    def create_user(self, email, password):\n        # User creation logic\n        pass\n    def authenticate(self, email, password):\n        # Authentication logic\n        pass",
                "payment_service.py": "class PaymentService:\n    def process_payment(self, amount, card_token):\n        # Payment processing logic\n        pass\n    def refund_payment(self, transaction_id):\n        # Refund logic\n        pass",
            },
            "test_requirements": {
                "unit_tests": True,
                "integration_tests": True,
                "performance_tests": True,
                "security_tests": True,
            },
            "timestamp": "2025-06-26T02:35:00Z",
            "request_type": "test",
            "priority": "critical",
        }

        # Expected output keys for comprehensive testing
        expected_output_keys = [
            "request_id",
            "test_files",
            "test_coverage",
            "test_results",
            "performance_tests",
            "integration_tests",
            "security_tests",
        ]

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "test",
            input_message,
            expected_output_keys,
            timeout=20.0,  # More time for comprehensive test generation
        )

        # Verify integration tests
        assert (
            "integration_tests" in output_data
        ), "integration_tests missing for comprehensive testing"
        integration_tests = output_data["integration_tests"]
        assert isinstance(
            integration_tests, dict
        ), "integration_tests should be a dictionary"
        assert len(integration_tests) > 0, "integration_tests is empty"

        # Verify security tests
        assert (
            "security_tests" in output_data
        ), "security_tests missing for comprehensive testing"
        security_tests = output_data["security_tests"]
        assert isinstance(security_tests, dict), "security_tests should be a dictionary"
        assert len(security_tests) > 0, "security_tests is empty"

        # Verify test coverage is high for comprehensive testing
        coverage = output_data["test_coverage"]
        coverage_percentage = coverage.get("percentage", 0)
        assert (
            coverage_percentage >= 80
        ), f"Coverage {coverage_percentage}% too low for comprehensive testing"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_test_agent_handles_test_failures(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test TestAgent handles and reports test failures."""
        # Setup mock LLM response with test failures
        failed_test_output = json.dumps(
            {
                "test_files": {
                    "test_main.py": "import pytest\n\ndef test_failing_function():\n    assert False, 'This test should fail'"
                },
                "test_coverage": {
                    "percentage": 60,
                    "covered_lines": 30,
                    "total_lines": 50,
                },
                "test_results": {
                    "passed": 5,
                    "failed": 3,
                    "total": 8,
                    "failures": [
                        {
                            "test_name": "test_user_creation",
                            "error": "AssertionError: Email validation failed",
                        },
                        {
                            "test_name": "test_payment_processing",
                            "error": "ValueError: Invalid card token",
                        },
                    ],
                },
                "performance_tests": {"load_test": "passed", "stress_test": "failed"},
            }
        )

        mock_response = await self.setup_mock_llm_response(failed_test_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Prepare input message
        input_message = {
            "request_id": "test-failures-456",
            "user_id": "test-user-456",
            "source_code": {
                "buggy_code.py": "def divide(a, b):\n    return a / b  # No zero division check"
            },
            "timestamp": "2025-06-26T02:40:00Z",
            "request_type": "test",
            "priority": "high",
        }

        # Expected output keys
        expected_output_keys = ["request_id", "test_files", "test_results"]

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client, "test", input_message, expected_output_keys, timeout=15.0
        )

        # Verify test failure handling
        test_results = output_data["test_results"]
        assert test_results["failed"] > 0, "Should report failed tests"
        assert "failures" in test_results, "Should include failure details"

        failures = test_results["failures"]
        assert isinstance(failures, list), "failures should be a list"
        if failures:
            assert "test_name" in failures[0], "failure should include test_name"
            assert "error" in failures[0], "failure should include error message"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_test_agent_performance_testing(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test TestAgent includes performance testing capabilities."""
        # Setup mock LLM response focused on performance testing
        performance_test_output = json.dumps(
            {
                "test_files": {
                    "test_performance.py": "import time\nimport pytest\n\ndef test_api_response_time():\n    start = time.time()\n    # API call simulation\n    end = time.time()\n    assert (end - start) < 1.0"
                },
                "test_coverage": {
                    "percentage": 85,
                    "covered_lines": 85,
                    "total_lines": 100,
                },
                "test_results": {"passed": 12, "failed": 0, "total": 12},
                "performance_tests": {
                    "load_test": {
                        "status": "passed",
                        "max_concurrent_users": 100,
                        "avg_response_time": 0.25,
                        "throughput_rps": 400,
                    },
                    "stress_test": {
                        "status": "passed",
                        "breaking_point": 500,
                        "memory_usage_mb": 256,
                    },
                    "endurance_test": {
                        "status": "passed",
                        "duration_minutes": 30,
                        "memory_leak_detected": False,
                    },
                },
            }
        )

        mock_response = await self.setup_mock_llm_response(performance_test_output)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Prepare input with performance requirements
        input_message = {
            "request_id": "performance-test-999",
            "user_id": "test-user-456",
            "source_code": {
                "api_service.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/heavy-computation')\ndef compute():\n    # Heavy computation logic\n    pass"
            },
            "performance_requirements": {
                "max_response_time": 1.0,
                "min_throughput_rps": 100,
                "max_memory_usage_mb": 512,
            },
            "timestamp": "2025-06-26T02:45:00Z",
            "request_type": "test",
            "priority": "high",
        }

        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "test",
            input_message,
            ["request_id", "performance_tests"],
            timeout=15.0,
        )

        # Verify performance testing details
        perf_tests = output_data["performance_tests"]
        assert "load_test" in perf_tests, "load_test missing from performance tests"
        assert "stress_test" in perf_tests, "stress_test missing from performance tests"

        # Verify load test details
        load_test = perf_tests["load_test"]
        assert (
            "avg_response_time" in load_test
        ), "avg_response_time missing from load test"
        assert "throughput_rps" in load_test, "throughput_rps missing from load test"

        # Verify stress test details
        stress_test = perf_tests["stress_test"]
        assert (
            "breaking_point" in stress_test
        ), "breaking_point missing from stress test"
        assert (
            "memory_usage_mb" in stress_test
        ), "memory_usage_mb missing from stress test"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_test_agent_handles_llm_error(
        self, mock_post, redis_client, agent_fixtures, agent_worker
    ):
        """Test TestAgent handles LLM errors gracefully."""
        # Setup mock LLM error response
        mock_response = AsyncMock()
        mock_response.status = 504  # Gateway timeout
        mock_response.text = AsyncMock(
            return_value=json.dumps({"error": "Gateway Timeout"})
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        # Prepare input message
        input_message = {
            "request_id": "error-test-123",
            "user_id": "test-user-456",
            "source_code": {"main.py": "print('hello world')"},
            "timestamp": "2025-06-26T02:50:00Z",
            "request_type": "test",
            "priority": "normal",
        }

        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "test", input_message)

        # Wait for output - expecting error handling message
        message_id, message_data = await self.wait_for_agent_output(
            redis_client, "test", timeout=30.0
        )

        # Should get an error response, not a timeout
        assert message_id is not None, "No error response received"
        assert message_data is not None, "Error message data is None"

        # Check for error indicators in response
        assert (
            "error" in message_data or "error_code" in message_data
        ), "Error indicators missing from response"
        assert "request_id" in message_data, "request_id missing in error response"
        assert (
            message_data["request_id"] == input_message["request_id"]
        ), "request_id mismatch in error response"

    @pytest.mark.asyncio
    async def test_test_agent_persistence(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test that TestAgent output is persisted correctly."""
        # Create a sample output message
        output_message = {
            "request_id": "persist-test-123",
            "user_id": "test-user-456",
            "test_files": {
                "test_main.py": "import pytest\n\ndef test_hello_world():\n    assert True",
                "test_models.py": "import pytest\nfrom models import User\n\ndef test_user_creation():\n    user = User('test')\n    assert user.name == 'test'",
            },
            "test_coverage": {"percentage": 90, "covered_lines": 45, "total_lines": 50},
            "test_results": {
                "passed": 8,
                "failed": 0,
                "total": 8,
                "execution_time": 2.5,
            },
            "performance_tests": {
                "load_test": {"status": "passed", "avg_response_time": 0.15},
                "memory_test": {"status": "passed", "peak_memory_mb": 128},
            },
            "timestamp": "2025-06-26T02:55:00Z",
        }

        # Manually publish to output stream to simulate agent output
        output_stream = "agent:test:output"

        # Serialize dictionary fields to JSON strings
        serialized_message = {}
        for key, value in output_message.items():
            if isinstance(value, (dict, list)):
                serialized_message[key] = json.dumps(value)
            else:
                serialized_message[key] = value

        message_id = await redis_client.xadd(output_stream, serialized_message)

        # Verify message was added to stream
        messages = await redis_client.xrange(
            output_stream, min=message_id, max=message_id
        )
        assert len(messages) == 1, "Output message not found in stream"

        # Check if message content is correct
        _, stored_message = messages[0]
        assert (
            stored_message["request_id"] == output_message["request_id"]
        ), "request_id not persisted correctly"
        assert "test_files" in stored_message, "test_files not persisted correctly"
        assert (
            "test_coverage" in stored_message
        ), "test_coverage not persisted correctly"
        assert "test_results" in stored_message, "test_results not persisted correctly"

        # Cleanup
        await redis_client.xdel(output_stream, message_id)

    @pytest.mark.asyncio
    async def test_test_agent_review_to_test_transition(
        self, redis_client, agent_fixtures, agent_worker
    ):
        """Test the transition from ReviewAgent output to TestAgent input."""
        # Simulate review output → test input transition
        review_output_message = {
            "request_id": "review-to-test-456",
            "user_id": "test-user-789",
            "source_code": {
                "calculator.py": "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b"
            },
            "review_summary": "Code is well-written and ready for testing",
            "code_quality_score": 88,
            "approval_status": "approved",
            "issues_found": [],
            "recommendations": [
                "Add edge case tests",
                "Include performance benchmarks",
            ],
            "timestamp": "2025-06-26T03:00:00Z",
        }

        # Publish review output to review output stream
        review_output_stream = "agent:review:output"

        # Serialize dictionary fields to JSON strings
        serialized_review_message = {}
        for key, value in review_output_message.items():
            if isinstance(value, (dict, list)):
                serialized_review_message[key] = json.dumps(value)
            else:
                serialized_review_message[key] = value

        review_message_id = await redis_client.xadd(
            review_output_stream, serialized_review_message
        )

        # Create test input based on review output
        test_input_message = {
            **review_output_message,  # Inherit from review output
            "request_type": "test",
            "previous_agent": "review",
            "previous_message_id": review_message_id,
        }

        # Publish to test input stream
        test_input_stream = "agent:test:input"

        # Serialize dictionary fields to JSON strings
        serialized_test_message = {}
        for key, value in test_input_message.items():
            if isinstance(value, (dict, list)):
                serialized_test_message[key] = json.dumps(value)
            else:
                serialized_test_message[key] = value

        test_message_id = await redis_client.xadd(
            test_input_stream, serialized_test_message
        )

        # Verify both messages exist
        review_messages = await redis_client.xrange(
            review_output_stream, min=review_message_id, max=review_message_id
        )
        test_messages = await redis_client.xrange(
            test_input_stream, min=test_message_id, max=test_message_id
        )

        assert len(review_messages) == 1, "Review output not persisted"
        assert len(test_messages) == 1, "Test input not persisted"

        # Verify content consistency
        _, review_stored = review_messages[0]
        _, test_stored = test_messages[0]

        assert (
            review_stored["request_id"] == test_stored["request_id"]
        ), "request_id not consistent across transition"
        assert (
            test_stored["previous_agent"] == "review"
        ), "previous_agent not set correctly"
        assert "source_code" in test_stored, "source_code not passed to test agent"
        assert (
            test_stored["approval_status"] == "approved"
        ), "approval_status not passed correctly"

        # Cleanup
        await redis_client.xdel(review_output_stream, review_message_id)
        await redis_client.xdel(test_input_stream, test_message_id)
