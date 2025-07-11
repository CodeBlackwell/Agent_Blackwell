#!/usr/bin/env python3
"""Example: Running TDD workflow for a calculator"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from Flagship.workflows.flagship_workflow import FlagshipTDDWorkflow
from Flagship.configs.flagship_config import get_config


async def run_calculator_example():
    """Demonstrate the TDD workflow with a calculator example"""
    
    print("🚀 Flagship TDD Example: Calculator")
    print("=" * 80)
    print()
    print("This example demonstrates the RED-YELLOW-GREEN TDD cycle")
    print("by building a simple calculator with basic operations.")
    print()
    
    # Define requirements
    requirements = """
    Create a Calculator class with the following methods:
    - add(a, b): Returns the sum of two numbers
    - subtract(a, b): Returns a minus b  
    - multiply(a, b): Returns the product of two numbers
    - divide(a, b): Returns a divided by b (handle division by zero)
    
    All methods should validate that inputs are numbers (int or float).
    The calculator should handle edge cases like very large numbers.
    """
    
    # Use demo configuration
    config = get_config("demo")
    
    # Create workflow
    workflow = FlagshipTDDWorkflow(config)
    
    try:
        # Execute the TDD workflow
        print("Starting TDD workflow...")
        print("Configuration: Demo (max 3 iterations, 120s timeout)")
        print()
        
        state = await workflow.execute_workflow(requirements, "calculator_demo")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 Example Complete!")
        print("=" * 80)
        
        if state.all_tests_passing:
            print("✅ Success! All tests are passing.")
            print(f"   Completed in {state.iteration_count} iteration(s)")
        else:
            print("⚠️  Workflow ended with some tests still failing.")
            print("   This demonstrates how TDD helps identify issues.")
        
        # Show generated files
        print("\n📁 Generated Files:")
        print(f"   - Tests: {config.test_directory}/test_generated.py")
        print(f"   - Implementation: {config.code_directory}/implementation_generated.py")
        print(f"   - Workflow State: {config.code_directory}/tdd_workflow_*.json")
        
    except asyncio.TimeoutError:
        print("\n⏱️  Example timed out (this is normal for complex requirements)")
    except Exception as e:
        print(f"\n❌ Example failed with error: {str(e)}")
        raise


async def run_interactive_example():
    """Run an interactive TDD example where user provides requirements"""
    
    print("🚀 Flagship TDD - Interactive Mode")
    print("=" * 80)
    print()
    print("Enter your requirements for the TDD workflow.")
    print("The system will go through RED-YELLOW-GREEN phases automatically.")
    print()
    
    # Get requirements from user
    print("What would you like to build? (or press Enter for calculator example)")
    requirements = input("> ").strip()
    
    if not requirements:
        requirements = "Create a simple calculator with add and subtract methods"
    
    # Ask for configuration
    print("\nSelect configuration:")
    print("1. Quick (2 iterations, 60s timeout)")
    print("2. Default (5 iterations, 300s timeout)")
    print("3. Comprehensive (10 iterations, 600s timeout)")
    choice = input("Choice [1-3, default=2]: ").strip()
    
    config_map = {"1": "quick", "2": "default", "3": "comprehensive"}
    config_name = config_map.get(choice, "default")
    config = get_config(config_name)
    
    # Create and run workflow
    workflow = FlagshipTDDWorkflow(config)
    
    try:
        print(f"\nStarting TDD workflow with {config_name} configuration...")
        state = await workflow.execute_workflow(requirements)
        
        print("\n✅ Workflow complete!")
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(run_interactive_example())
    else:
        asyncio.run(run_calculator_example())


if __name__ == "__main__":
    main()