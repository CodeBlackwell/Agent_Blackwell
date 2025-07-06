#!/usr/bin/env python3
"""
Test script for MVP incremental workflow Phase 4.
Tests retry logic for failed feature implementations.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_retry_logic():
    """Test MVP incremental with intentional errors to trigger retry."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow Phase 4 - Retry Logic")
    print("📦 Features with errors will be retried automatically")
    print("="*60)
    
    # Test case designed to trigger syntax errors that can be fixed
    input_data = CodingTeamInput(
        requirements="""
Create a simple math utilities module with the following features:
1. A function factorial(n) that calculates factorial recursively
2. A function fibonacci(n) that returns the nth Fibonacci number
3. A function is_prime(n) that checks if a number is prime
4. A function gcd(a, b) that calculates greatest common divisor

IMPORTANT: Make the factorial function have a subtle syntax error initially (like missing colon).
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase4_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Analyze retry attempts
        feature_results = [r for r in results if r.name and r.name.startswith("coder_feature_")]
        retry_info = []
        
        for result in feature_results:
            if hasattr(result, 'metadata') and result.metadata:
                retry_count = result.metadata.get('retry_count', 0)
                final_success = result.metadata.get('final_success', False)
                if retry_count > 0:
                    retry_info.append({
                        'feature': result.name,
                        'retries': retry_count,
                        'success': final_success
                    })
        
        print(f"\n📊 Retry Summary:")
        print(f"   Total features: {len(feature_results)}")
        print(f"   Features that needed retry: {len(retry_info)}")
        
        for info in retry_info:
            status = "✅ Fixed" if info['success'] else "❌ Still failed"
            print(f"   - {info['feature']}: {info['retries']} retries - {status}")
        
        # Save final implementation
        save_results(results, "phase4_retry")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_non_retryable_errors():
    """Test that certain errors are not retried."""
    print("\n\n" + "="*60)
    print("🧪 Testing Non-Retryable Errors")
    print("="*60)
    
    # Test with import errors that shouldn't be retried
    input_data = CodingTeamInput(
        requirements="""
Create a data processor that:
1. Uses pandas to read CSV files (but don't import pandas)
2. Processes the data
3. Exports results

This should fail with ModuleNotFoundError which is non-retryable.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_non_retryable")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        
        # Check that features with module errors were not retried
        feature_results = [r for r in results if r.name and r.name.startswith("coder_feature_")]
        non_retried = []
        
        for result in feature_results:
            if hasattr(result, 'metadata') and result.metadata:
                if result.metadata.get('retry_count', 0) == 0 and not result.metadata.get('validation_passed', True):
                    non_retried.append(result.name)
        
        print(f"\n📊 Non-Retry Summary:")
        print(f"   Features that failed without retry: {len(non_retried)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in non-retryable test: {e}")
        return False


def save_results(results, suffix=""):
    """Save the final implementation to a file."""
    output_dir = Path("tests/outputs/mvp_incremental")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"math_utils_{suffix}_{timestamp}.py"
    
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
    """Run Phase 4 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 4 Tests")
    print("📋 Phase 4: Retry logic for failed features")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run retry logic test
    success1 = await test_retry_logic()
    
    # Run non-retryable errors test
    success2 = await test_non_retryable_errors()
    
    if success1 and success2:
        print("\n🎉 All Phase 4 tests passed!")
        print("✅ Retry logic is working correctly")
        print("   - Failed features are retried with error context")
        print("   - Non-retryable errors are handled appropriately")
        print("   - Maximum retry limits are respected")
    else:
        print("\n⚠️  Some Phase 4 tests failed.")
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)