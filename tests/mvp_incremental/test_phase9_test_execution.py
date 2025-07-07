#!/usr/bin/env python3
"""
Test script for Phase 9: Test Execution functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.mvp_incremental.test_execution import (
    TestExecutor, TestExecutionConfig, TestResult, execute_and_fix_tests
)
from workflows.mvp_incremental.validator import CodeValidator


async def test_basic_test_execution():
    """Test basic test execution functionality."""
    print("🧪 Testing basic test execution...")
    
    # Create validator and executor
    validator = CodeValidator()
    config = TestExecutionConfig(
        run_tests=True,
        test_command="pytest",
        test_timeout=30,
        fix_on_failure=False
    )
    executor = TestExecutor(validator, config)
    
    # Test code with a simple function
    test_code = '''
def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b
'''
    
    # Execute tests (no test files exist, should return success with 0 tests)
    result = await executor.execute_tests(test_code, "Math Functions")
    
    print(f"✅ Test execution completed")
    print(f"   Success: {result.success}")
    print(f"   Tests found: {len(result.test_files)}")
    print(f"   Output: {result.output[:100]}...")
    
    assert result.success, "Expected success when no tests are found"
    assert result.passed == 0, "Expected 0 tests passed"
    assert result.failed == 0, "Expected 0 tests failed"
    

async def test_test_discovery():
    """Test the test file discovery functionality."""
    print("\n🔍 Testing test file discovery...")
    
    validator = CodeValidator()
    config = TestExecutionConfig()
    executor = TestExecutor(validator, config)
    
    # Code that references test files
    code_with_test_refs = '''
def calculator():
    """Calculator implementation."""
    pass

# Tests are in test_calculator.py
# Also see tests/test_math.py
'''
    
    # Test discovery
    test_files = executor._find_test_files(code_with_test_refs, "Calculator")
    
    print(f"✅ Test discovery completed")
    print(f"   Found patterns: {test_files}")
    
    # Should find references to test files
    assert any("calculator" in f for f in test_files), "Should find calculator test reference"
    

async def test_test_result_parsing():
    """Test parsing of pytest output."""
    print("\n📊 Testing test result parsing...")
    
    validator = CodeValidator()
    config = TestExecutionConfig()
    executor = TestExecutor(validator, config)
    
    # Sample pytest output
    sample_output = """
test_example.py::test_addition PASSED                           [ 33%]
test_example.py::test_subtraction PASSED                        [ 66%]
test_example.py::test_division FAILED                           [100%]

FAILURES
test_example.py::test_division - AssertionError: Division by zero not handled

========================= 2 passed, 1 failed in 0.05s =========================
"""
    
    result = executor._parse_test_output(sample_output, ["test_example.py"])
    
    print(f"✅ Test parsing completed")
    print(f"   Passed: {result.passed}")
    print(f"   Failed: {result.failed}")
    print(f"   Success: {result.success}")
    print(f"   Errors: {result.errors}")
    
    assert result.passed == 2, "Should parse 2 passed tests"
    assert result.failed == 1, "Should parse 1 failed test"
    assert not result.success, "Should not be successful with failures"
    assert len(result.errors) == 1, "Should have 1 error"
    

async def test_execute_and_fix_integration():
    """Test the integrated execute and fix functionality."""
    print("\n🔧 Testing execute and fix integration...")
    
    # Simple code
    code = '''
def multiply(a, b):
    return a * b
'''
    
    validator = CodeValidator()
    config = TestExecutionConfig(
        run_tests=True,
        fix_on_failure=True,
        max_fix_attempts=2
    )
    
    # Execute and potentially fix
    final_code, test_result = await execute_and_fix_tests(
        code,
        "Multiplication Function",
        validator,
        config
    )
    
    print(f"✅ Execute and fix completed")
    print(f"   Code unchanged: {code == final_code}")
    print(f"   Test result: {test_result.success}")
    
    assert final_code == code, "Code should be unchanged when no tests exist"
    assert test_result.success, "Should succeed when no tests exist"
    

async def test_fix_hints_generation():
    """Test generation of fix hints for different error types."""
    print("\n💡 Testing fix hint generation...")
    
    validator = CodeValidator()
    config = TestExecutionConfig()
    executor = TestExecutor(validator, config)
    
    # Test different error types
    test_cases = [
        (TestResult(False, 0, 1, ["test_func - AssertionError: Expected 5, got 4"], "", []),
         "Check that the implementation matches test expectations"),
        (TestResult(False, 0, 1, ["AttributeError: 'Calculator' object has no attribute 'divide'"], "", []),
         "Ensure all required methods/attributes are implemented"),
        (TestResult(False, 0, 1, ["TypeError: add() takes 2 positional arguments but 3 were given"], "", []),
         "Verify function signatures match test calls"),
        (TestResult(False, 0, 1, ["ImportError: cannot import name 'utils' from 'mymodule'"], "", []),
         "Check that all necessary imports are included"),
    ]
    
    for test_result, expected_hint in test_cases:
        hints = executor._generate_test_fix_hints(test_result)
        assert expected_hint in hints, f"Expected hint '{expected_hint}' not found in {hints}"
    
    print(f"✅ All fix hints generated correctly")
    

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 9: Test Execution - Test Suite")
    print("=" * 60)
    
    try:
        await test_basic_test_execution()
        await test_test_discovery()
        await test_test_result_parsing()
        await test_execute_and_fix_integration()
        await test_fix_hints_generation()
        
        print("\n✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())