"""
Test script for MVP incremental workflow Phase 2.
Tests validation after each feature implementation.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_calculator_with_validation():
    """Test MVP incremental with validation for each feature."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow Phase 2 - With Docker Validation")
    print("📦 Using Validator Agent with persistent container")
    print("="*60)
    
    # Calculator with intentional error in one feature
    input_data = CodingTeamInput(
        requirements="""
Create a simple calculator class that supports:
1. Addition of two numbers
2. Subtraction of two numbers  
3. Division of two numbers (with error handling for division by zero)
4. Square root of a number (import math module)

Make sure each method has proper error handling and returns appropriate results.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase2_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Check validation results
        validation_count = 0
        validation_passed = 0
        validation_failed = 0
        
        for result in results:
            if hasattr(result, 'metadata') and result.metadata and 'validation_passed' in result.metadata:
                validation_count += 1
                if result.metadata['validation_passed']:
                    validation_passed += 1
                else:
                    validation_failed += 1
                    print(f"\n❌ Validation failed for: {result.name}")
                    if result.metadata.get('validation_error'):
                        print(f"   Error: {result.metadata['validation_error']}")
        
        print(f"\n📊 Validation Summary:")
        print(f"   Total validations: {validation_count}")
        print(f"   Passed: {validation_passed}")
        print(f"   Failed: {validation_failed}")
        
        # Save final implementation
        save_results(results, "phase2_validated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_results(results, suffix=""):
    """Save the final implementation to a file."""
    output_dir = Path("tests/outputs/mvp_incremental")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"calculator_{suffix}_{timestamp}.py"
    
    # Find the final implementation result
    final_result = None
    for result in reversed(results):
        if result.name == "final_implementation":
            final_result = result
            break
    
    if final_result:
        # Extract just the code from the markdown
        import re
        code_blocks = re.findall(r'```python\n(.*?)```', final_result.output, re.DOTALL)
        
        if code_blocks:
            # Save the main implementation
            with open(output_file, 'w') as f:
                f.write(code_blocks[0])
            print(f"\n💾 Saved implementation to: {output_file}")


async def main():
    """Run Phase 2 test."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 2 Tests")
    print("📋 Phase 2: Adding validation after each feature")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run test
    success = await test_calculator_with_validation()
    
    if success:
        print("\n🎉 Phase 2 test passed!")
    else:
        print("\n⚠️  Phase 2 test failed.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)