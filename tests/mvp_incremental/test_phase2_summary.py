#!/usr/bin/env python3
"""Simple test to verify Phase 2 MVP incremental workflow with validation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_phase2():
    """Test Phase 2 - MVP incremental with validation."""
    print("\n" + "="*60)
    print("🧪 Phase 2 Validation Test - Simple Calculator")
    print("="*60)
    
    # Simple test case
    input_data = CodingTeamInput(
        requirements="""
Create a Calculator class with:
1. add(a, b) - returns a + b
2. divide(a, b) - returns a / b with ZeroDivisionError handling
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("phase2_test")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        
        print(f"\n✅ Workflow completed")
        print(f"📊 Results: {len(results)} outputs")
        
        # Count validations
        validations = [r for r in results if hasattr(r, 'metadata') and r.metadata and 'validation_passed' in r.metadata]
        passed = sum(1 for r in validations if r.metadata.get('validation_passed', False))
        failed = len(validations) - passed
        
        print(f"\n📋 Validation Summary:")
        print(f"   Total features: {len([r for r in results if r.name and r.name.startswith('coder_feature_')])}")
        print(f"   Validations run: {len(validations)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        
        # Show final code
        final = next((r for r in reversed(results) if r.name == "final_implementation"), None)
        if final:
            print(f"\n📄 Final implementation length: {len(final.output)} chars")
            
        return len(validations) > 0  # Success if we ran validations
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Phase 2 - MVP Incremental with Validation")
    success = asyncio.run(test_phase2())
    
    if success:
        print("\n✅ Phase 2 VALIDATED - Validation is integrated!")
    else:
        print("\n⚠️  Phase 2 needs more work")
    
    exit(0 if success else 1)