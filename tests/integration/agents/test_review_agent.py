"""
Integration tests for the ReviewAgent.
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

import redis.asyncio as redis
from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestReviewAgentIntegration(BaseAgentIntegrationTest):
    """Test ReviewAgent integration."""
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_review_agent_with_mock_llm(self, mock_post, redis_client, agent_fixtures, user_request_fixtures):
        """Test ReviewAgent with mock LLM."""
        # Setup mock LLM response using the fixture data
        review_output = agent_fixtures["review"]["sample_outputs"][0]
        mock_response = await self.setup_mock_llm_response(review_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample coding output as input (coding → review transition)
        coding_output = agent_fixtures["coding"]["sample_outputs"][0]
        
        # Prepare input message for the ReviewAgent
        input_message = {
            "request_id": "review-test-123",
            "user_id": "test-user-456",
            "source_code": {
                "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                "models.py": "from sqlalchemy import Column, Integer, String\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)"
            },
            "file_structure": [
                {"path": "main.py", "type": "file", "size": 150},
                {"path": "models.py", "type": "file", "size": 200}
            ],
            "dependencies": {
                "requirements": ["fastapi>=0.104.0", "sqlalchemy>=2.0.0"]
            },
            "timestamp": "2025-06-26T01:55:00Z",
            "request_type": "review",
            "priority": "high"
        }
        
        # Test that the agent produces the expected output
        expected_output_keys = ["request_id", "review_summary", "code_quality_score", "issues_found", "recommendations", "approval_status"]
        
        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "review",
            input_message,
            expected_output_keys,
            timeout=15.0  # Review may take time for analysis
        )
        
        # Assert specific content in the output
        assert "review_summary" in output_data, "review_summary missing from output"
        review_summary = output_data["review_summary"]
        assert isinstance(review_summary, str), "review_summary should be a string"
        assert len(review_summary) > 0, "review_summary is empty"
        
        # Verify code quality score exists and is valid
        assert "code_quality_score" in output_data, "code_quality_score missing from output"
        quality_score = output_data["code_quality_score"]
        assert isinstance(quality_score, (int, float)), "code_quality_score should be numeric"
        assert 0 <= quality_score <= 100, "code_quality_score should be between 0 and 100"
        
        # Verify issues found format
        assert "issues_found" in output_data, "issues_found missing from output"
        issues = output_data["issues_found"]
        assert isinstance(issues, list), "issues_found should be a list"
        if issues:
            assert isinstance(issues[0], dict), "issue should be a dictionary"
            assert "severity" in issues[0], "issue missing 'severity' field"
            assert "description" in issues[0], "issue missing 'description' field"
            assert "file" in issues[0], "issue missing 'file' field"
        
        # Verify recommendations exist
        assert "recommendations" in output_data, "recommendations missing from output"
        recommendations = output_data["recommendations"]
        assert isinstance(recommendations, list), "recommendations should be a list"
        
        # Verify approval status
        assert "approval_status" in output_data, "approval_status missing from output"
        approval = output_data["approval_status"]
        assert approval in ["approved", "rejected", "needs_revision"], "invalid approval_status value"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_review_agent_handles_security_issues(self, mock_post, redis_client, agent_fixtures):
        """Test ReviewAgent identifies security vulnerabilities."""
        # Setup mock LLM response focused on security review
        security_review_output = agent_fixtures["review"]["sample_outputs"][1]
        mock_response = await self.setup_mock_llm_response(security_review_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Prepare input with potentially vulnerable code
        input_message = {
            "request_id": "security-review-789",
            "user_id": "test-user-456",
            "source_code": {
                "auth.py": "import hashlib\n\ndef hash_password(password):\n    return hashlib.md5(password.encode()).hexdigest()",
                "database.py": "import sqlite3\n\ndef get_user(user_id):\n    conn = sqlite3.connect('app.db')\n    query = f'SELECT * FROM users WHERE id = {user_id}'\n    return conn.execute(query).fetchone()"
            },
            "review_focus": ["security", "vulnerabilities", "best_practices"],
            "timestamp": "2025-06-26T02:00:00Z",
            "request_type": "review",
            "priority": "critical"
        }
        
        # Expected output keys for security review
        expected_output_keys = [
            "request_id", "review_summary", "code_quality_score", "issues_found", 
            "recommendations", "approval_status", "security_assessment"
        ]
        
        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "review",
            input_message,
            expected_output_keys,
            timeout=15.0
        )
        
        # Verify security assessment
        assert "security_assessment" in output_data, "security_assessment missing for security review"
        security = output_data["security_assessment"]
        assert isinstance(security, dict), "security_assessment should be a dictionary"
        assert "vulnerabilities" in security, "vulnerabilities missing from security assessment"
        assert "risk_level" in security, "risk_level missing from security assessment"
        
        # Should find security issues
        issues = output_data["issues_found"]
        security_issues = [issue for issue in issues if issue.get("category") == "security"]
        assert len(security_issues) > 0, "No security issues found in vulnerable code"
        
        # Should not approve vulnerable code
        assert output_data["approval_status"] in ["rejected", "needs_revision"], "Vulnerable code should not be approved"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_review_agent_handles_performance_analysis(self, mock_post, redis_client, agent_fixtures):
        """Test ReviewAgent analyzes performance concerns."""
        # Setup mock LLM response focused on performance review
        performance_review_output = agent_fixtures["review"]["sample_outputs"][0]
        mock_response = await self.setup_mock_llm_response(performance_review_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Prepare input with performance-sensitive code
        input_message = {
            "request_id": "performance-review-456",
            "user_id": "test-user-456",
            "source_code": {
                "data_processing.py": "def process_large_dataset(data):\n    result = []\n    for item in data:\n        for sub_item in item:\n            result.append(expensive_operation(sub_item))\n    return result",
                "database_queries.py": "def get_all_user_data():\n    users = []\n    for user_id in get_all_user_ids():\n        user = db.query(f'SELECT * FROM users WHERE id = {user_id}').first()\n        users.append(user)\n    return users"
            },
            "review_focus": ["performance", "scalability", "optimization"],
            "timestamp": "2025-06-26T02:05:00Z",
            "request_type": "review",
            "priority": "high"
        }
        
        # Expected output keys for performance review
        expected_output_keys = [
            "request_id", "review_summary", "code_quality_score", "issues_found", 
            "recommendations", "approval_status", "performance_analysis"
        ]
        
        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "review",
            input_message,
            expected_output_keys,
            timeout=15.0
        )
        
        # Verify performance analysis
        assert "performance_analysis" in output_data, "performance_analysis missing for performance review"
        performance = output_data["performance_analysis"]
        assert isinstance(performance, dict), "performance_analysis should be a dictionary"
        assert "bottlenecks" in performance, "bottlenecks missing from performance analysis"
        assert "optimization_suggestions" in performance, "optimization_suggestions missing"
        
        # Should find performance issues
        issues = output_data["issues_found"]
        performance_issues = [issue for issue in issues if issue.get("category") == "performance"]
        assert len(performance_issues) > 0, "No performance issues found in inefficient code"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_review_agent_handles_llm_error(self, mock_post, redis_client, agent_fixtures):
        """Test ReviewAgent handles LLM errors gracefully."""
        # Setup mock LLM error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value=json.dumps({"error": "Internal Server Error"}))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample coding output as input
        coding_output = agent_fixtures["coding"]["sample_outputs"][0]
        
        # Prepare input message
        input_message = {
            "request_id": "error-review-123",
            "user_id": "test-user-456",
            "source_code": {"main.py": "print('hello world')"},
            "timestamp": "2025-06-26T02:10:00Z",
            "request_type": "review",
            "priority": "normal"
        }
        
        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "review", input_message)
        
        # Wait for output - expecting error handling message
        message_id, message_data = await self.wait_for_agent_output(redis_client, "review", timeout=15.0)
        
        # Should get an error response, not a timeout
        assert message_id is not None, "No error response received"
        assert message_data is not None, "Error message data is None"
        
        # Check for error indicators in response
        assert "error" in message_data or "error_code" in message_data, "Error indicators missing from response"
        assert "request_id" in message_data, "request_id missing in error response"
        assert message_data["request_id"] == input_message["request_id"], "request_id mismatch in error response"
    
    @pytest.mark.asyncio
    async def test_review_agent_persistence(self, redis_client, agent_fixtures):
        """Test that ReviewAgent output is persisted correctly."""
        # Create a sample output message
        output_message = {
            "request_id": "persist-review-123",
            "user_id": "test-user-456",
            "review_summary": "Code review completed. Found 3 minor issues and 1 security concern.",
            "code_quality_score": 75,
            "issues_found": [
                {
                    "severity": "high",
                    "category": "security",
                    "description": "SQL injection vulnerability detected",
                    "file": "database.py",
                    "line": 15
                },
                {
                    "severity": "medium",
                    "category": "performance",
                    "description": "N+1 query problem in data loading",
                    "file": "models.py",
                    "line": 42
                }
            ],
            "recommendations": [
                "Use parameterized queries to prevent SQL injection",
                "Implement batch loading for related data",
                "Add input validation for user data"
            ],
            "approval_status": "needs_revision",
            "security_assessment": {
                "vulnerabilities": ["sql_injection"],
                "risk_level": "high"
            },
            "timestamp": "2025-06-26T02:15:00Z"
        }
        
        # Manually publish to output stream to simulate agent output
        output_stream = "agent:review:output"
        message_id = await redis_client.xadd(output_stream, output_message)
        
        # Verify message was added to stream
        messages = await redis_client.xrange(output_stream, min=message_id, max=message_id)
        assert len(messages) == 1, "Output message not found in stream"
        
        # Check if message content is correct
        _, stored_message = messages[0]
        assert stored_message["request_id"] == output_message["request_id"], "request_id not persisted correctly"
        assert stored_message["code_quality_score"] == str(output_message["code_quality_score"]), "code_quality_score not persisted correctly"
        assert stored_message["approval_status"] == output_message["approval_status"], "approval_status not persisted correctly"
        
        # Cleanup
        await redis_client.xdel(output_stream, message_id)
    
    @pytest.mark.asyncio
    async def test_review_agent_coding_to_review_transition(self, redis_client, agent_fixtures):
        """Test the transition from CodingAgent output to ReviewAgent input."""
        # Simulate coding output → review input transition
        coding_output_message = {
            "request_id": "coding-to-review-456",
            "user_id": "test-user-789",
            "source_code": {
                "app.py": "from fastapi import FastAPI\napp = FastAPI()",
                "models.py": "class User:\n    def __init__(self, name):\n        self.name = name"
            },
            "file_structure": [
                {"path": "app.py", "type": "file"},
                {"path": "models.py", "type": "file"}
            ],
            "dependencies": {"requirements": ["fastapi"]},
            "timestamp": "2025-06-26T02:20:00Z"
        }
        
        # Publish coding output to coding output stream
        coding_output_stream = "agent:coding:output"
        coding_message_id = await redis_client.xadd(coding_output_stream, coding_output_message)
        
        # Create review input based on coding output
        review_input_message = {
            **coding_output_message,  # Inherit from coding output
            "request_type": "review",
            "previous_agent": "coding",
            "previous_message_id": coding_message_id
        }
        
        # Publish to review input stream
        review_input_stream = "agent:review:input"
        review_message_id = await redis_client.xadd(review_input_stream, review_input_message)
        
        # Verify both messages exist
        coding_messages = await redis_client.xrange(coding_output_stream, min=coding_message_id, max=coding_message_id)
        review_messages = await redis_client.xrange(review_input_stream, min=review_message_id, max=review_message_id)
        
        assert len(coding_messages) == 1, "Coding output not persisted"
        assert len(review_messages) == 1, "Review input not persisted"
        
        # Verify content consistency
        _, coding_stored = coding_messages[0]
        _, review_stored = review_messages[0]
        
        assert coding_stored["request_id"] == review_stored["request_id"], "request_id not consistent across transition"
        assert review_stored["previous_agent"] == "coding", "previous_agent not set correctly"
        assert "source_code" in review_stored, "source_code not passed to review agent"
        
        # Cleanup
        await redis_client.xdel(coding_output_stream, coding_message_id)
        await redis_client.xdel(review_input_stream, review_message_id)
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_review_agent_approval_workflow(self, mock_post, redis_client, agent_fixtures):
        """Test ReviewAgent approval workflow with different outcomes."""
        # Test scenarios: approved, needs revision, rejected
        test_cases = [
            {
                "name": "high_quality_code",
                "source_code": {"main.py": "# Well written, secure code\nfrom typing import List\n\ndef process_data(items: List[str]) -> List[str]:\n    return [item.strip().lower() for item in items if item]"},
                "expected_status": "approved",
                "expected_score_range": (80, 100)
            },
            {
                "name": "medium_quality_code", 
                "source_code": {"main.py": "def process_data(items):\n    result = []\n    for item in items:\n        result.append(item.strip())\n    return result"},
                "expected_status": "needs_revision",
                "expected_score_range": (50, 79)
            },
            {
                "name": "poor_quality_code",
                "source_code": {"main.py": "import os\ndef bad_func(x):\n    os.system(f'rm -rf {x}')\n    return eval(x)"},
                "expected_status": "rejected",
                "expected_score_range": (0, 49)
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Setup appropriate mock response based on code quality
            if test_case["expected_status"] == "approved":
                review_output = json.dumps({
                    "review_summary": "High quality code with good practices",
                    "code_quality_score": 85,
                    "issues_found": [],
                    "recommendations": ["Consider adding more unit tests"],
                    "approval_status": "approved"
                })
            elif test_case["expected_status"] == "needs_revision":
                review_output = json.dumps({
                    "review_summary": "Code needs minor improvements",
                    "code_quality_score": 65,
                    "issues_found": [{"severity": "medium", "description": "Missing type hints"}],
                    "recommendations": ["Add type hints", "Improve variable names"],
                    "approval_status": "needs_revision"
                })
            else:  # rejected
                review_output = json.dumps({
                    "review_summary": "Code has critical security issues",
                    "code_quality_score": 25,
                    "issues_found": [
                        {"severity": "critical", "description": "Command injection vulnerability"},
                        {"severity": "critical", "description": "Use of eval() is dangerous"}
                    ],
                    "recommendations": ["Remove all security vulnerabilities", "Rewrite using safe practices"],
                    "approval_status": "rejected"
                })
            
            mock_response = await self.setup_mock_llm_response(review_output)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Prepare input message
            input_message = {
                "request_id": f"approval-test-{i}",
                "user_id": "test-user-456",
                "source_code": test_case["source_code"],
                "timestamp": f"2025-06-26T02:{25+i}:00Z",
                "request_type": "review",
                "priority": "normal"
            }
            
            # Test agent output
            output_data = await self.assert_agent_produces_output(
                redis_client,
                "review",
                input_message,
                ["request_id", "approval_status", "code_quality_score"],
                timeout=10.0
            )
            
            # Verify approval status matches expectation
            assert output_data["approval_status"] == test_case["expected_status"], f"Approval status mismatch for {test_case['name']}"
            
            # Verify quality score is in expected range
            score = int(output_data["code_quality_score"])
            min_score, max_score = test_case["expected_score_range"]
            assert min_score <= score <= max_score, f"Quality score {score} not in expected range {test_case['expected_score_range']} for {test_case['name']}"
