#!/usr/bin/env python3
"""
Example: Calculator with Tests
Demonstrates Phase 9 (Test Execution) with automatic test running and fixing
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow


async def run_calculator_example():
    """Run calculator example with test execution enabled."""
    
    print("🧮 Calculator with Tests Example")
    print("=" * 60)
    print("This example demonstrates:")
    print("- Feature-by-feature implementation")
    print("- Automatic test execution (Phase 9)")
    print("- Test-driven development workflow")
    print()
    
    # Requirements for a calculator with comprehensive tests
    requirements = """
Create a Python calculator module with comprehensive test coverage:

1. Basic Operations:
   - Add two numbers
   - Subtract two numbers
   - Multiply two numbers
   - Divide two numbers (handle division by zero)

2. Advanced Operations:
   - Calculate square root (handle negative numbers)
   - Calculate power (x^y)
   - Calculate factorial (handle negative numbers)
   - Calculate percentage

3. Testing Requirements:
   - Write unit tests for all operations
   - Test edge cases (zero, negative numbers, large numbers)
   - Test error handling (division by zero, invalid inputs)
   - Achieve 100% code coverage
   - Use pytest framework
   - Include parametrized tests where appropriate

4. Code Quality:
   - Add type hints
   - Include docstrings
   - Handle errors gracefully
   - Follow PEP 8 style guide
"""
    
    # Create input with test execution enabled
    input_data = CodingTeamInput(
        requirements=requirements,
        run_tests=True,  # Enable Phase 9
        run_integration_verification=False  # Skip Phase 10 for this example
    )
    
    print("📋 Configuration:")
    print("   Phase 9 (Test Execution): ✅ Enabled")
    print("   Phase 10 (Integration): ❌ Disabled")
    print()
    print("🚀 Starting workflow...")
    print("-" * 60)
    
    try:
        # Execute the workflow
        result = await execute_workflow(
            "mvp_incremental",
            input_data
        )
        
        print()
        print("✅ Workflow completed successfully!")
        print()
        print("📊 Results:")
        print("   - Calculator implementation with all operations")
        print("   - Comprehensive test suite")
        print("   - Tests automatically executed and verified")
        print()
        print("💡 Key Learnings:")
        print("   - Tests were run after each feature implementation")
        print("   - Failed tests triggered automatic fixes")
        print("   - Final code passed all test validations")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_calculator_example())
    sys.exit(exit_code)