#!/usr/bin/env python3
"""
Unit test for the review integration module.
Tests the ReviewIntegration class functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.mvp_incremental.review_integration import (
    ReviewIntegration, ReviewPhase, ReviewRequest, ReviewResult
)
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent


async def test_review_request_parsing():
    """Test that review requests are properly parsed."""
    print("🧪 Testing Review Request Parsing")
    print("="*60)
    
    # Initialize review integration
    review_integration = ReviewIntegration(feature_reviewer_agent)
    
    # Test planning review
    planning_request = ReviewRequest(
        phase=ReviewPhase.PLANNING,
        content="1. Create user authentication\n2. Add database models\n3. Implement API endpoints",
        context={"requirements": "Build a user management system"}
    )
    
    planning_review = await review_integration.request_review(planning_request)
    
    print(f"\n📋 Planning Review Result:")
    print(f"   Approved: {planning_review.approved}")
    print(f"   Feedback length: {len(planning_review.feedback)} chars")
    print(f"   Suggestions: {len(planning_review.suggestions)}")
    print(f"   Must fix items: {len(planning_review.must_fix)}")
    
    # Test feature implementation review
    feature_request = ReviewRequest(
        phase=ReviewPhase.FEATURE_IMPLEMENTATION,
        content="""
def add_user(self, username, email):
    user = {"username": username, "email": email}
    self.users.append(user)
    return len(self.users) - 1
""",
        context={
            "feature_info": {
                "name": "add_user",
                "description": "Add a new user to the system"
            },
            "existing_code": "",
            "dependencies": []
        },
        feature_id="feature_1"
    )
    
    feature_review = await review_integration.request_review(feature_request)
    
    print(f"\n📋 Feature Implementation Review Result:")
    print(f"   Approved: {feature_review.approved}")
    print(f"   Feature ID: {feature_review.feature_id}")
    
    # Check review history
    history = review_integration.review_history
    print(f"\n📊 Review History:")
    print(f"   Total reviews: {sum(len(reviews) for reviews in history.values())}")
    print(f"   Phases reviewed: {list(history.keys())}")
    
    return True


async def test_retry_decision_logic():
    """Test the retry decision logic based on reviews."""
    print("\n\n🧪 Testing Retry Decision Logic")
    print("="*60)
    
    review_integration = ReviewIntegration(feature_reviewer_agent)
    
    # Simulate a validation failure review
    validation_request = ReviewRequest(
        phase=ReviewPhase.VALIDATION_RESULT,
        content="""
VALIDATION_RESULT: FAIL
DETAILS: NameError: name 'json' is not defined at line 5

The code attempts to use json.loads() without importing the json module.
""",
        context={
            "validation_result": {"success": False},
            "error_info": "NameError: name 'json' is not defined",
            "max_retries": 3
        },
        feature_id="feature_2",
        retry_count=1
    )
    
    validation_review = await review_integration.request_review(validation_request)
    
    # Test retry decision
    should_retry, reason = review_integration.should_retry_feature(
        "feature_2",
        {"success": False, "error": "NameError"}
    )
    
    print(f"\n📊 Retry Decision:")
    print(f"   Should retry: {should_retry}")
    print(f"   Reason: {reason}")
    
    # Get retry suggestions
    suggestions = review_integration.get_retry_suggestions("feature_2")
    if suggestions:
        print(f"\n💡 Retry Suggestions:")
        for suggestion in suggestions[:3]:
            print(f"   - {suggestion}")
    
    return True


async def test_approval_summary():
    """Test the approval summary functionality."""
    print("\n\n🧪 Testing Approval Summary")
    print("="*60)
    
    review_integration = ReviewIntegration(feature_reviewer_agent)
    
    # Create multiple reviews
    phases_to_test = [
        (ReviewPhase.PLANNING, "Test plan content"),
        (ReviewPhase.DESIGN, "Test design content"),
        (ReviewPhase.FEATURE_IMPLEMENTATION, "Test implementation", "feature_1"),
        (ReviewPhase.FEATURE_IMPLEMENTATION, "Another implementation", "feature_2")
    ]
    
    for phase_data in phases_to_test:
        phase = phase_data[0]
        content = phase_data[1]
        feature_id = phase_data[2] if len(phase_data) > 2 else None
        
        request = ReviewRequest(
            phase=phase,
            content=content,
            context={},
            feature_id=feature_id
        )
        
        await review_integration.request_review(request)
    
    # Get approval summary
    summary = review_integration.get_approval_summary()
    
    print(f"\n📊 Approval Summary:")
    for phase, data in summary.items():
        print(f"\n   {phase}:")
        print(f"      Approved: {data['approved']}")
        print(f"      Rejected: {data['rejected']}")
        if 'features' in data and data['features']:
            print(f"      Features: {data['features']}")
    
    # Get must-fix items
    must_fix = review_integration.get_must_fix_items()
    print(f"\n⚠️  Total must-fix items: {len(must_fix)}")
    
    return True


async def main():
    """Run review integration tests."""
    print("\n🚀 Starting Review Integration Tests")
    
    tests = [
        test_review_request_parsing,
        test_retry_decision_logic,
        test_approval_summary
    ]
    
    results = []
    for test in tests:
        try:
            success = await test()
            results.append(success)
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    if all(results):
        print("\n\n🎉 All review integration tests passed!")
    else:
        print("\n\n⚠️  Some tests failed")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)