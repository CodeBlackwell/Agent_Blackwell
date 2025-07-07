"""
Test script for MVP incremental workflow.
Tests basic feature breakdown and sequential implementation.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_simple_calculator():
    """Test MVP incremental with a simple calculator example."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow - Simple Calculator")
    print("="*60)
    
    # Simple calculator requirements
    input_data = CodingTeamInput(
        requirements="""
Create a simple calculator class that supports:
1. Addition of two numbers
2. Subtraction of two numbers  
3. Multiplication of two numbers
4. Division of two numbers (with error handling for division by zero)
5. Square root of a number (with error handling for negative numbers)
6. Power of a number (with error handling for negative numbers)
7. Factorial of a number (with error handling for negative numbers)
8. Absolute value of a number (with error handling for negative numbers)
9. Logarithm of a number (with error handling for negative numbers)
10. Exponential of a number (with error handling for negative numbers)

The calculator should have a clean interface and proper error handling.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Print summary of results
        print("\n📊 Results Summary:")
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1}: {result.name} ---")
            print(f"Team Member: {result.team_member}")
            print(f"Output Length: {len(result.output)} characters")
            
            # Show first 500 chars of output
            if len(result.output) > 500:
                print(f"Output Preview:\n{result.output[:500]}...")
            else:
                print(f"Output:\n{result.output}")
        
        # Save final implementation
        save_results(results)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_file_project():
    """Test MVP incremental with a multi-file project."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow - Multi-File Project")
    print("="*60)
    
    # Multi-file project requirements
    input_data = CodingTeamInput(
        requirements="""
Create a simple task management system with:
1. A Task class that has title, description, status (pending/completed)
2. A TaskManager class that can add, remove, and list tasks
3. A CLI interface that allows users to interact with the task manager
4. Persistence using JSON file storage

Structure as multiple files with proper organization.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_multifile_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Check if multiple files were created
        final_result = results[-1] if results else None
        if final_result and "File:" in final_result.output:
            file_count = final_result.output.count("File:")
            print(f"📁 Files created: {file_count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_results(results):
    """Save the final implementation to a file."""
    output_dir = Path("tests/outputs/mvp_incremental")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"calculator_{timestamp}.py"
    
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
    """Run all tests."""
    print("\n🚀 Starting MVP Incremental Workflow Tests")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run tests
    test_results = []
    
    # Test 1: Simple calculator
    test_results.append(("Simple Calculator", await test_simple_calculator())) 
    # Test 2: Multi-file project
    # test_results.append(("Multi-File Project", await test_multi_file_project()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in test_results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)