#!/usr/bin/env python3
"""Test just the review components."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent


async def test_basic_review():
    """Test basic review functionality."""
    print("🧪 Testing Basic Review Component")
    print("="*60)
    
    # Create review integration
    review_integration = ReviewIntegration(feature_reviewer_agent)
    print("✅ ReviewIntegration instance created")
    
    # Test a simple review
    request = ReviewRequest(
        phase=ReviewPhase.PLANNING,
        content="1. Create a Counter class\n2. Add increment method\n3. Add get_count method",
        context={"requirements": "Create a simple counter"}
    )
    
    print("\n📋 Sending review request...")
    result = await review_integration.request_review(request)
    
    print(f"\n✅ Review completed!")
    print(f"   Approved: {result.approved}")
    print(f"   Feedback: {result.feedback[:200]}...")
    print(f"   Suggestions: {result.suggestions}")
    print(f"   Must fix: {result.must_fix}")
    
    # Check review history
    print(f"\n📊 Review history:")
    for key, reviews in review_integration.review_history.items():
        print(f"   {key}: {len(reviews)} review(s)")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_review())
    print(f"\n{'✅ Test passed!' if success else '❌ Test failed!'}")
    exit(0 if success else 1)