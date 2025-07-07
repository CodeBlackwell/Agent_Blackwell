#!/usr/bin/env python3
"""
Validation test for Phase 7 - Feature Reviewer Agent.
Ensures the feature reviewer provides appropriate feedback for different scenarios.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent

async def validate_review_response(test_name: str, input_text: str, expected_keywords: list):
    """Helper to validate review responses"""
    messages = [Message(parts=[MessagePart(content=input_text, content_type="text/plain")])]
    
    response_parts = []
    async for part in feature_reviewer_agent(messages):
        response_parts.append(part.content)
    
    response = ''.join(response_parts).upper()
    
    # Check for expected keywords
    found_keywords = [kw for kw in expected_keywords if kw.upper() in response]
    success = len(found_keywords) > 0
    
    print(f"\n{'✅' if success else '❌'} {test_name}")
    print(f"   Expected keywords: {expected_keywords}")
    print(f"   Found: {found_keywords}")
    print(f"   Response preview: {response[:150]}...")
    
    return success

async def test_phase7_validation():
    """Validate Phase 7 Feature Reviewer functionality"""
    print("🧪 Phase 7 Validation - Feature Reviewer Agent")
    print("=" * 60)
    
    results = []
    
    # Test 1: Good implementation should be approved
    results.append(await validate_review_response(
        "Good implementation approval",
        """
        Feature: Calculate sum
        Implementation:
        ```python
        def calculate_sum(self, numbers):
            if not numbers:
                return 0
            return sum(numbers)
        ```
        """,
        ["APPROVED", "FEATURE APPROVED"]
    ))
    
    # Test 2: Missing error handling should need revision
    results.append(await validate_review_response(
        "Missing error handling detection",
        """
        Feature: Parse JSON data
        Description: Parse JSON string and return dictionary
        Implementation:
        ```python
        def parse_json(self, json_string):
            return json.loads(json_string)
        ```
        """,
        ["REVISION", "ERROR", "HANDLING", "TRY", "EXCEPT"]
    ))
    
    # Test 3: Incomplete implementation should need revision
    results.append(await validate_review_response(
        "Incomplete implementation detection",
        """
        Feature: User authentication
        Description: Authenticate user with username and password
        Implementation:
        ```python
        def authenticate(self, username, password):
            # TODO: implement authentication
            pass
        ```
        """,
        ["REVISION", "INCOMPLETE", "TODO", "IMPLEMENT"]
    ))
    
    # Test 4: Integration issues should be caught
    results.append(await validate_review_response(
        "Integration issue detection",
        """
        Feature: Add item to cart
        Current Implementation:
        ```python
        def add_to_cart(self, item_id, quantity):
            self.cart.append({'id': item_id, 'qty': quantity})
        ```
        Context: The cart is initialized as a dictionary in __init__, not a list.
        """,
        ["REVISION", "INTEGRATION", "DICTIONARY", "LIST", "APPEND"]
    ))
    
    # Test 5: Retry success should be approved
    results.append(await validate_review_response(
        "Successful retry approval",
        """
        Feature: Save user data
        Retry Attempt: 2
        Previous Error: KeyError: 'user_id'
        Previous Feedback: Check if user_id exists before accessing
        
        New Implementation:
        ```python
        def save_user(self, data):
            if 'user_id' not in data:
                raise ValueError("user_id is required")
            user_id = data['user_id']
            self.users[user_id] = data
            return True
        ```
        """,
        ["APPROVED", "ADDRESSED", "FIXED"]
    ))
    
    # Summary
    total = len(results)
    passed = sum(results)
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Phase 7 VALIDATED - Feature Reviewer is working correctly!")
    else:
        print("❌ Some tests failed - Feature Reviewer needs adjustment")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_phase7_validation())
    exit(0 if success else 1)