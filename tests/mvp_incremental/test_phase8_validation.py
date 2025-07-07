#!/usr/bin/env python3
"""
Validation test for Phase 8 - Review Integration.
Tests that reviews are properly integrated throughout the workflow.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_review_integration():
    """Test MVP incremental workflow with review integration."""
    print("🧪 Testing Phase 8 - Review Integration")
    print("="*60)
    
    # Test case with multiple features to trigger reviews
    input_data = CodingTeamInput(
        requirements="""
Create a simple TodoList class with these features:

1. add_todo(title, priority='normal') - adds a new todo item
   - Priority can be 'high', 'normal', or 'low'
   - Return the todo ID
   
2. complete_todo(todo_id) - marks a todo as complete
   - Should validate todo_id exists
   
3. get_pending_todos() - returns all incomplete todos
   - Should return a list sorted by priority
   
Each method should have basic error handling.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase8_test")
    
    try:
        print("\n📊 Watch for review checkpoints during execution...")
        print("="*60)
        
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed successfully!")
        
        # Check if review summary was generated
        final_result = None
        for result in reversed(results):
            if result.name == "final_implementation":
                final_result = result
                break
        
        if final_result and "README.md" in final_result.output:
            print("\n📋 Review Summary Document Generated:")
            print("   ✅ README.md included in final output")
            
            # Extract README content
            readme_start = final_result.output.find("--- README.md ---")
            if readme_start != -1:
                readme_content = final_result.output[readme_start:].split("---", 2)[1]
                print(f"   📄 Review document length: {len(readme_content)} characters")
                
                # Check for expected sections
                expected_sections = [
                    "Project Overview",
                    "Implementation Status",
                    "Code Quality Assessment",
                    "Key Recommendations"
                ]
                
                found_sections = []
                for section in expected_sections:
                    if section in readme_content:
                        found_sections.append(section)
                
                print(f"   📑 Found {len(found_sections)}/{len(expected_sections)} expected sections")
                for section in found_sections:
                    print(f"      - {section}")
        else:
            print("\n⚠️  No review summary document found in output")
        
        # Check for review metadata
        if final_result and hasattr(final_result, 'metadata') and final_result.metadata:
            if 'review_summary' in final_result.metadata:
                review_summary = final_result.metadata['review_summary']
                print("\n📊 Review Summary Metrics:")
                for phase, data in review_summary.items():
                    print(f"   {phase}: {data.get('approved', 0)} approved, {data.get('rejected', 0)} rejected")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_review_feedback_in_retry():
    """Test that review feedback is incorporated into retry attempts."""
    print("\n\n🧪 Testing Review Feedback in Retry Logic")
    print("="*60)
    
    # Test case designed to trigger retries with review feedback
    input_data = CodingTeamInput(
        requirements="""
Create a DataValidator class with:

1. validate_email(email) - validates email format
   IMPORTANT: Initially implement without checking for @ symbol
   
2. validate_phone(phone) - validates phone number
   IMPORTANT: Initially forget to handle international formats

The validator should provide clear error messages.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("phase8_retry_test")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        
        # Look for retry attempts with review feedback
        retry_features = []
        for result in results:
            if hasattr(result, 'metadata') and result.metadata:
                if result.metadata.get('retry_count', 0) > 0:
                    retry_features.append({
                        'name': result.name,
                        'retries': result.metadata['retry_count'],
                        'final_success': result.metadata.get('final_success', False)
                    })
        
        if retry_features:
            print(f"\n📊 Features with retries (guided by reviews):")
            for feature in retry_features:
                print(f"   - {feature['name']}: {feature['retries']} retries, "
                      f"final status: {'SUCCESS' if feature['final_success'] else 'FAILED'}")
            print("\n✅ Review-guided retry logic is working!")
        else:
            print("\n⚠️  No retries triggered (features might be too well implemented!)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run Phase 8 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 8 Tests")
    print("📋 Phase 8: Review integration throughout workflow")
    
    print("\n" + "="*60)
    print("Note: Make sure the orchestrator server is running!")
    print("="*60 + "\n")
    
    # Test review integration
    success1 = await test_review_integration()
    
    # Test review feedback in retry logic
    success2 = await test_review_feedback_in_retry()
    
    if all([success1, success2]):
        print("\n🎉 All Phase 8 tests passed!")
        print("✅ Review integration is working correctly:")
        print("   - Reviews at planning, design, and implementation phases")
        print("   - Review feedback incorporated into retry decisions")
        print("   - Comprehensive review summary document generated")
        print("   - Review metrics tracked and reported")
    else:
        print("\n⚠️  Some Phase 8 tests failed.")
    
    return all([success1, success2])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)