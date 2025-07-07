#!/usr/bin/env python3
"""Test workflow with minimal example to see reviews."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_workflow_reviews():
    """Test workflow with focus on reviews."""
    print("🧪 Testing Workflow Reviews")
    print("="*60)
    
    # First, let's check what the workflow actually prints
    from shared.data_models import CodingTeamInput
    from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
    from workflows.monitoring import WorkflowExecutionTracer
    
    # Very minimal input to speed things up
    input_data = CodingTeamInput(
        requirements="Create a class Adder with method add(a, b) that returns a + b",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("review_test")
    
    print("\n📊 Starting workflow execution...")
    print("🔍 Watch for review outputs...\n")
    
    try:
        results = await execute_mvp_incremental_workflow(input_data, tracer)
        
        print(f"\n✅ Workflow completed with {len(results)} results")
        
        # Check final result
        final = None
        for result in results:
            if result.name == "final_implementation":
                final = result
                break
        
        if final:
            # Check for README
            if "README.md" in final.output:
                print("✅ Found README.md in final output!")
                # Extract just the README part
                readme_start = final.output.find("--- README.md ---")
                if readme_start != -1:
                    readme_end = final.output.find("\n---", readme_start + 20)
                    if readme_end == -1:
                        readme_end = len(final.output)
                    readme_section = final.output[readme_start:readme_end]
                    print("\n📄 README section found:")
                    print(readme_section[:500] + "..." if len(readme_section) > 500 else readme_section)
            else:
                print("❌ No README.md found in final output")
                print(f"   Output preview: {final.output[:200]}...")
            
            # Check metadata
            if hasattr(final, 'metadata') and final.metadata:
                if 'review_summary' in final.metadata:
                    print("\n✅ Review summary in metadata!")
                    summary = final.metadata['review_summary']
                    for phase, data in summary.items():
                        print(f"   {phase}: {data}")
                else:
                    print("\n❌ No review_summary in metadata")
                    print(f"   Available keys: {list(final.metadata.keys())}")
        else:
            print("❌ No final_implementation result found")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Workflow Review Test")
    print("Note: This test runs the actual workflow - may take ~30 seconds")
    
    success = asyncio.run(test_workflow_reviews())
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
    
    exit(0 if success else 1)