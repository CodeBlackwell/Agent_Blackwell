#!/usr/bin/env python3
"""Trace test to see if review integration is being called."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent


async def test_review_components():
    """Test individual review components."""
    print("🧪 Testing Review Components Directly")
    print("="*60)
    
    # Test 1: Can we create a review integration instance?
    try:
        review_integration = ReviewIntegration(feature_reviewer_agent)
        print("✅ ReviewIntegration instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create ReviewIntegration: {e}")
        return False
    
    # Test 2: Can we make a simple review request?
    try:
        print("\n📋 Testing simple review request...")
        request = ReviewRequest(
            phase=ReviewPhase.PLANNING,
            content="1. Create a Counter class\n2. Add increment method\n3. Add get_count method",
            context={"requirements": "Create a simple counter"}
        )
        
        result = await review_integration.request_review(request)
        print(f"✅ Review completed!")
        print(f"   Approved: {result.approved}")
        print(f"   Feedback preview: {result.feedback[:100]}...")
        print(f"   Suggestions: {len(result.suggestions)}")
        
    except Exception as e:
        print(f"❌ Review request failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Check if workflow imports the review module
    try:
        print("\n📦 Testing workflow imports...")
        from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
        
        # Check if the workflow has review imports
        import inspect
        source = inspect.getsource(execute_mvp_incremental_workflow)
        
        review_imports = [
            "ReviewIntegration",
            "ReviewPhase", 
            "ReviewRequest",
            "review_integration"
        ]
        
        found = []
        for imp in review_imports:
            if imp in source:
                found.append(imp)
        
        print(f"✅ Found {len(found)}/{len(review_imports)} review-related imports/references in workflow")
        print(f"   Found: {found}")
        
        if len(found) < len(review_imports):
            missing = [imp for imp in review_imports if imp not in found]
            print(f"   Missing: {missing}")
    
    except Exception as e:
        print(f"❌ Import check failed: {e}")
        return False
    
    return True


async def test_workflow_with_print_intercept():
    """Test if review messages are being printed during workflow."""
    print("\n\n🧪 Testing Workflow Execution")
    print("="*60)
    
    from shared.data_models import CodingTeamInput
    from workflows.workflow_manager import execute_workflow
    from workflows.monitoring import WorkflowExecutionTracer
    
    # Capture prints
    import io
    import contextlib
    
    captured_output = io.StringIO()
    
    input_data = CodingTeamInput(
        requirements="Create a simple Counter class with increment() and get_count() methods",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("phase8_trace_test")
    
    try:
        # Intercept stdout to capture prints
        with contextlib.redirect_stdout(captured_output):
            results, report = await execute_workflow(input_data, tracer)
        
        output = captured_output.getvalue()
        
        # Check for review-related output
        review_indicators = [
            "Plan Review:",
            "Design Review:",
            "Feature Review:",
            "Final Implementation Review:",
            "review summary document",
            "Review:"
        ]
        
        found_reviews = []
        for indicator in review_indicators:
            if indicator in output:
                found_reviews.append(indicator)
        
        if found_reviews:
            print(f"✅ Found {len(found_reviews)} review indicators in output:")
            for rev in found_reviews:
                print(f"   - {rev}")
                # Show context
                idx = output.find(rev)
                if idx != -1:
                    context = output[max(0, idx-50):idx+100]
                    print(f"     Context: ...{context}...")
        else:
            print("⚠️  No review indicators found in output")
            print(f"   Output length: {len(output)} characters")
            
            # Search for any "review" mention
            review_count = output.lower().count("review")
            print(f"   Total 'review' mentions: {review_count}")
        
        return len(found_reviews) > 0
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Phase 8 Review Integration Trace Test")
    
    # Test components
    success1 = await test_review_components()
    
    # Test workflow
    success2 = await test_workflow_with_print_intercept()
    
    if all([success1, success2]):
        print("\n\n✅ All tests passed - Review integration is working!")
    else:
        print("\n\n❌ Some tests failed")
    
    return all([success1, success2])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)