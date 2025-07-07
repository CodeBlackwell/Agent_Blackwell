#!/usr/bin/env python3
"""Test to explicitly trigger retry logic by asking for code with intentional errors."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_retry_trigger():
    """Test with requirements that will likely trigger syntax errors."""
    print("\n" + "="*60)
    print("🧪 Phase 4 Retry Trigger Test")
    print("📦 Testing retry logic with intentional errors")
    print("="*60)
    
    # Request features with subtle issues to trigger retries
    input_data = CodingTeamInput(
        requirements="""
Create a Calculator class with these methods:

1. add(a, b) - returns a + b
   IMPORTANT: Initially implement with syntax error (missing colon after def)
   
2. subtract(a, b) - returns a - b
   IMPORTANT: Initially implement with indentation error
   
3. multiply(a, b) - returns a * b
   IMPORTANT: Initially implement with NameError (use undefined variable)
   
4. divide(a, b) - returns a / b
   IMPORTANT: Initially forget to handle ZeroDivisionError

Make sure each method has an intentional error that can be fixed on retry.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("phase4_retry_trigger")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        
        print(f"\n✅ Workflow completed")
        
        # Analyze retry information
        feature_results = [r for r in results if r.name and r.name.startswith('coder_feature_')]
        retries_found = False
        
        print(f"\n📊 Retry Analysis:")
        for result in feature_results:
            if hasattr(result, 'metadata') and result.metadata:
                retry_count = result.metadata.get('retry_count', 0)
                validation_passed = result.metadata.get('validation_passed', False)
                final_success = result.metadata.get('final_success', False)
                
                if retry_count > 0:
                    retries_found = True
                    print(f"   🔄 {result.name}: {retry_count} retries")
                    print(f"      Initial validation: {'PASS' if validation_passed else 'FAIL'}")
                    print(f"      Final result: {'SUCCESS' if final_success else 'FAILED'}")
        
        if not retries_found:
            print("   ⚠️  No retries were triggered (code might have been too good!)")
        else:
            print("\n   ✅ Retry logic successfully triggered and executed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Phase 4 Retry Trigger")
    success = asyncio.run(test_retry_trigger())
    
    if success:
        print("\n✅ Phase 4 retry trigger test completed")
    else:
        print("\n⚠️  Phase 4 retry trigger test failed")
    
    exit(0 if success else 1)