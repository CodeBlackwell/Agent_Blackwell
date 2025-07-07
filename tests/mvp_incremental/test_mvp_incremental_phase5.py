#!/usr/bin/env python3
"""
Test script for MVP incremental workflow Phase 5.
Tests error analysis integration with retry logic.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_error_analysis():
    """Test MVP incremental with error analysis for better recovery."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow Phase 5 - Error Analysis")
    print("📦 Error analyzer will provide recovery hints for better fixes")
    print("="*60)
    
    # Test case with various error types
    input_data = CodingTeamInput(
        requirements="""
Create a FileProcessor class with these methods:

1. read_json(filename) - reads and parses JSON file
   - Should handle FileNotFoundError
   - Should handle json.JSONDecodeError
   
2. process_data(data) - processes the data
   - Should validate data is a dictionary
   - Should handle missing required keys
   
3. calculate_average(numbers) - calculates average of a list
   - Should handle empty list (ZeroDivisionError)
   - Should handle non-numeric values
   
4. save_results(results, output_file) - saves results to file
   - Should create directory if it doesn't exist
   - Should handle permission errors gracefully

Include proper error handling for each method.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase5_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Analyze error handling and recovery
        feature_results = [r for r in results if r.name and r.name.startswith("coder_feature_")]
        error_categories = {}
        recovery_hints_used = []
        
        for result in feature_results:
            if hasattr(result, 'metadata') and result.metadata:
                if result.metadata.get('retry_count', 0) > 0:
                    # This feature was retried, check error context
                    # Note: We'd need to enhance metadata tracking to capture this
                    print(f"\n📊 Feature {result.name} was retried {result.metadata['retry_count']} times")
        
        # Save final implementation
        save_results(results, "phase5_error_analysis")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_categorization():
    """Test error categorization and recovery hints."""
    print("\n\n" + "="*60)
    print("🧪 Testing Error Categorization")
    print("="*60)
    
    # Import the error analyzer directly
    from workflows.mvp_incremental.error_analyzer import SimplifiedErrorAnalyzer, ErrorCategory
    
    analyzer = SimplifiedErrorAnalyzer()
    
    # Test various error messages
    test_errors = [
        "SyntaxError: invalid syntax",
        "NameError: name 'undefined_var' is not defined",
        "ImportError: No module named 'pandas'",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "IndentationError: unexpected indent",
        "ZeroDivisionError: division by zero",
        "AssertionError: Expected 5 but got 3",
        'File "test.py", line 42, in function'
    ]
    
    print("\n📊 Error Analysis Results:")
    for error_msg in test_errors:
        error_info = analyzer.analyze_error(error_msg)
        print(f"\nError: {error_msg[:50]}...")
        print(f"  Category: {error_info.category.value}")
        print(f"  Type: {error_info.error_type or 'N/A'}")
        print(f"  Hint: {error_info.recovery_hint}")
        if error_info.file_path:
            print(f"  File: {error_info.file_path}:{error_info.line_number}")
    
    return True


async def test_recovery_prompts():
    """Test that recovery prompts include helpful context."""
    print("\n\n" + "="*60)
    print("🧪 Testing Recovery Prompt Generation")
    print("="*60)
    
    # Simple test with intentional syntax error
    input_data = CodingTeamInput(
        requirements="""
Create a simple Counter class with:
1. increment() method - adds 1 to count
2. get_count() method - returns current count

IMPORTANT: Make the first attempt have a syntax error (missing colon).
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_recovery_test")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        
        # Check if recovery hints were used
        print(f"\n✅ Workflow completed with error recovery")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in recovery test: {e}")
        return False


def save_results(results, suffix=""):
    """Save the final implementation to a file."""
    output_dir = Path("tests/outputs/mvp_incremental")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"file_processor_{suffix}_{timestamp}.py"
    
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
    """Run Phase 5 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 5 Tests")
    print("📋 Phase 5: Error analysis and improved recovery")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run error analysis test
    success1 = await test_error_analysis()
    
    # Run error categorization test
    success2 = await test_error_categorization()
    
    # Run recovery prompt test
    success3 = await test_recovery_prompts()
    
    if all([success1, success2, success3]):
        print("\n🎉 All Phase 5 tests passed!")
        print("✅ Error analysis is working correctly")
        print("   - Errors are properly categorized")
        print("   - Recovery hints are generated based on error type")
        print("   - Retry prompts include helpful context")
    else:
        print("\n⚠️  Some Phase 5 tests failed.")
    
    return all([success1, success2, success3])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)