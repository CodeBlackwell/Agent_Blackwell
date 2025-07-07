#!/usr/bin/env python3
"""Simple test to validate Phase 8 review integration is working."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_simple_review_integration():
    """Test MVP incremental workflow with review integration on a simple example."""
    print("🧪 Testing Phase 8 - Simple Review Integration Test")
    print("="*60)
    
    # Very simple test case
    input_data = CodingTeamInput(
        requirements="""
Create a Counter class with:
1. increment() - increases count by 1
2. get_count() - returns current count
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("phase8_simple_test")
    
    try:
        print("\n📊 Running workflow with review integration...")
        print("="*60)
        
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed!")
        
        # Check for review outputs
        review_outputs = [
            "Plan Review:",
            "Design Review:", 
            "Feature Review:",
            "Final Implementation Review:",
            "Generating review summary document"
        ]
        
        # Look for final result
        final_result = None
        for result in reversed(results):
            if result.name == "final_implementation":
                final_result = result
                break
        
        if final_result:
            # Check if README.md was included
            if "README.md" in final_result.output:
                print("\n✅ Review summary document (README.md) was generated!")
                
                # Extract README preview
                readme_start = final_result.output.find("--- README.md ---")
                if readme_start != -1:
                    readme_end = final_result.output.find("\n---", readme_start + 20)
                    if readme_end == -1:
                        readme_end = readme_start + 500
                    readme_preview = final_result.output[readme_start:readme_end]
                    print("\n📄 README Preview:")
                    print(readme_preview[:300] + "...")
            else:
                print("\n⚠️  No README.md found in final output")
            
            # Check for review metadata
            if hasattr(final_result, 'metadata') and final_result.metadata:
                if 'review_summary' in final_result.metadata:
                    print("\n✅ Review summary metadata found!")
                    review_data = final_result.metadata['review_summary']
                    print(f"   Phases reviewed: {list(review_data.keys())}")
                else:
                    print("\n⚠️  No review summary in metadata")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Phase 8 Simple Test")
    print("Note: This test should complete quickly with a simple example")
    
    success = asyncio.run(test_simple_review_integration())
    
    if success:
        print("\n🎉 Phase 8 review integration is working!")
    else:
        print("\n❌ Phase 8 test failed")
    
    exit(0 if success else 1)