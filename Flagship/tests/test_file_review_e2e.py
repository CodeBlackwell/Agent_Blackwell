"""End-to-end test demonstrating file review and iterative development"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from flagship_orchestrator import FlagshipOrchestrator
from models.flagship_models import TDDWorkflowConfig


async def test_file_review_scenario():
    """
    End-to-end test showing how agents review and build upon existing files
    """
    print("\n" + "="*80)
    print("🧪 File Review End-to-End Test")
    print("="*80 + "\n")
    
    # Create orchestrator with custom config
    config = TDDWorkflowConfig(
        max_iterations=3,
        timeout_seconds=300,
        auto_refactor=False
    )
    
    orchestrator = FlagshipOrchestrator(
        config=config,
        session_id="file_review_e2e"
    )
    
    # Pre-populate session with an existing file
    print("📁 Pre-populating session with existing calculator implementation...")
    existing_calc = '''class Calculator:
    """A simple calculator with basic operations"""
    
    def add(self, a, b):
        """Add two numbers"""
        return a + b
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        return a * b
'''
    
    # Write existing code to file manager
    orchestrator.file_manager.write_file("calculator.py", existing_calc, session_scope=False)
    print("✅ Existing calculator.py created with add() and multiply() methods\n")
    
    # Now run TDD workflow asking for subtract and divide methods
    requirements = """
    Extend the existing Calculator class with:
    1. A subtract(a, b) method that returns a - b
    2. A divide(a, b) method that returns a / b
    3. Proper error handling for division by zero
    
    The Calculator class already has add() and multiply() methods.
    """
    
    print("🚀 Starting TDD workflow to add new methods to existing Calculator...\n")
    
    # Run the workflow
    state = await orchestrator.run_tdd_workflow(requirements)
    
    # Save results
    orchestrator.save_workflow_state()
    
    # Verify results
    print("\n" + "="*80)
    print("📊 Test Results")
    print("="*80 + "\n")
    
    # Check that agents found and used existing files
    session_files = orchestrator.file_manager.list_files()
    print(f"📁 Total files in session: {len(session_files)}")
    for file in session_files:
        print(f"  - {file.name}")
    
    # Read final implementation
    final_impl = orchestrator.file_manager.read_file("implementation_generated.py")
    if final_impl:
        print("\n📄 Final Implementation Preview:")
        print("-"*40)
        lines = final_impl.split('\n')[:20]  # First 20 lines
        for line in lines:
            print(line)
        if len(final_impl.split('\n')) > 20:
            print("... (truncated)")
        print("-"*40)
        
        # Verify new methods were added
        has_subtract = "def subtract" in final_impl
        has_divide = "def divide" in final_impl
        has_error_handling = "ZeroDivisionError" in final_impl or "ValueError" in final_impl
        
        print(f"\n✅ Subtract method added: {has_subtract}")
        print(f"✅ Divide method added: {has_divide}")
        print(f"✅ Error handling added: {has_error_handling}")
    
    # Check test results
    test_summary = state.get_test_summary()
    print(f"\n📊 Final Test Summary:")
    print(f"  - Total: {test_summary['total']}")
    print(f"  - Passed: {test_summary['passed']}")
    print(f"  - Failed: {test_summary['failed']}")
    print(f"  - All Passing: {state.all_tests_passing}")
    
    print("\n" + "="*80)
    print("✅ File Review E2E Test Complete!")
    print(f"📁 Results saved to: {orchestrator.file_manager.session_dir}")
    print("="*80 + "\n")
    
    return state.all_tests_passing


async def test_iterative_development():
    """
    Test iterative development where each iteration builds on the previous
    """
    print("\n" + "="*80)
    print("🔄 Iterative Development Test")
    print("="*80 + "\n")
    
    orchestrator = FlagshipOrchestrator(
        session_id="iterative_dev_test"
    )
    
    # First iteration: Create basic structure
    print("📍 Iteration 1: Create basic Person class")
    requirements1 = "Create a Person class with name and age attributes"
    state1 = await orchestrator.run_tdd_workflow(requirements1)
    
    # Save the generated code
    person_code = orchestrator.file_manager.read_file("implementation_generated.py")
    orchestrator.file_manager.write_file("person.py", person_code, session_scope=False)
    
    # Second iteration: Extend with new functionality
    print("\n📍 Iteration 2: Add greeting method")
    orchestrator2 = FlagshipOrchestrator(
        session_id="iterative_dev_test",  # Same session
        project_root=orchestrator.file_manager.project_root
    )
    
    requirements2 = """
    Extend the existing Person class with:
    1. A greet() method that returns "Hello, my name is {name}"
    2. An is_adult() method that returns True if age >= 18
    """
    
    state2 = await orchestrator2.run_tdd_workflow(requirements2)
    
    print("\n📊 Iterative Development Results:")
    print(f"  - Iteration 1 passed: {state1.all_tests_passing}")
    print(f"  - Iteration 2 passed: {state2.all_tests_passing}")
    
    # Verify methods were added
    final_code = orchestrator2.file_manager.read_file("implementation_generated.py")
    if final_code:
        print(f"  - Has greet method: {'def greet' in final_code}")
        print(f"  - Has is_adult method: {'def is_adult' in final_code}")
    
    return state2.all_tests_passing


async def main():
    """Run all end-to-end tests"""
    # Test 1: File review scenario
    success1 = await test_file_review_scenario()
    
    # Test 2: Iterative development
    success2 = await test_iterative_development()
    
    # Summary
    print("\n" + "="*80)
    print("🏁 All E2E Tests Complete!")
    print("="*80)
    print(f"  ✅ File Review Test: {'PASSED' if success1 else 'FAILED'}")
    print(f"  ✅ Iterative Dev Test: {'PASSED' if success2 else 'FAILED'}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())