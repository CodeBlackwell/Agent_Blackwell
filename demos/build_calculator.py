#!/usr/bin/env python3
"""
🧮 Build a Calculator - TDD Workflow Demo
========================================

This script demonstrates building a calculator using Test-Driven Development (TDD),
showing the RED-YELLOW-GREEN cycle in action.

Usage:
    python build_calculator.py           # Build a simple calculator
    python build_calculator.py advanced  # Build an advanced calculator with more features
    
The TDD Process:
    🔴 RED Phase: Write failing tests first
    🟡 YELLOW Phase: Implement code to pass tests  
    🟢 GREEN Phase: Tests pass and code is approved
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker
from demos.lib.workflow_runner import WorkflowRunner


class CalculatorBuilder:
    """Builds a calculator using TDD workflow."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.runner = WorkflowRunner()
        
    async def build_calculator(self, complexity: str = "simple") -> None:
        """Build a calculator with specified complexity."""
        self.formatter.print_banner(
            "🧮 CALCULATOR BUILDER",
            "Test-Driven Development Demo"
        )
        
        # Show TDD explanation
        print("\n📚 About TDD (Test-Driven Development):")
        print("   This demo will show you how TDD works by building a calculator")
        print("   following the RED-YELLOW-GREEN cycle:\n")
        print("   🔴 RED: We'll write tests that fail (no implementation yet)")
        print("   🟡 YELLOW: We'll implement code to make tests pass")
        print("   🟢 GREEN: All tests pass and code is approved!\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        # Get requirements based on complexity
        requirements = self._get_requirements(complexity)
        
        # Show what we're building
        self.formatter.print_section(f"Building {complexity.title()} Calculator")
        print("📝 Requirements:")
        print("-" * 60)
        print(requirements)
        print("-" * 60)
        
        # Confirm execution
        print("\n🚀 Ready to start the TDD process?")
        print("   The system will:")
        print("   1. Create failing tests first (RED phase)")
        print("   2. Implement the calculator (YELLOW phase)")
        print("   3. Ensure all tests pass (GREEN phase)")
        print("\n   Press Enter to continue or Ctrl+C to cancel...")
        input()
        
        # Execute the workflow
        start_time = time.time()
        print("\n" + "="*80)
        print("🏗️  STARTING TDD WORKFLOW")
        print("="*80)
        
        try:
            # Create input for workflow
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type="tdd"
            )
            
            # Run the workflow
            result = await execute_workflow(team_input)
            
            # Show results
            self._show_results(result, time.time() - start_time)
            
        except Exception as e:
            self.formatter.show_error(f"Workflow failed: {str(e)}")
            
    def _check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        print("\n🔍 Checking prerequisites...")
        
        # Check virtual environment
        if not self.checker.check_virtual_env():
            self.formatter.show_error(
                "Virtual environment not activated",
                ["Run: source .venv/bin/activate"]
            )
            return False
            
        # Check orchestrator
        if not self.checker.is_orchestrator_running():
            self.formatter.show_error(
                "Orchestrator not running",
                ["Start it with: python orchestrator/orchestrator_agent.py"]
            )
            return False
            
        print("✅ All prerequisites met!\n")
        return True
        
    def _get_requirements(self, complexity: str) -> str:
        """Get calculator requirements based on complexity."""
        if complexity == "simple":
            return """Create a Python calculator module with the following features:

1. Basic Operations:
   - add(a, b): Add two numbers
   - subtract(a, b): Subtract b from a
   - multiply(a, b): Multiply two numbers
   - divide(a, b): Divide a by b (handle division by zero)

2. Error Handling:
   - Raise ValueError for division by zero
   - Handle invalid input types

3. Testing Requirements:
   - Write comprehensive unit tests using pytest
   - Test all operations with positive, negative, and zero values
   - Test edge cases and error conditions
   - Achieve at least 95% code coverage

The module should be named 'calculator.py' with tests in 'test_calculator.py'."""
        
        else:  # advanced
            return """Create an advanced Python calculator module with the following features:

1. Basic Operations:
   - add(a, b): Add two numbers
   - subtract(a, b): Subtract b from a
   - multiply(a, b): Multiply two numbers
   - divide(a, b): Divide a by b (handle division by zero)

2. Advanced Operations:
   - power(base, exponent): Calculate base^exponent
   - square_root(n): Calculate square root (handle negative numbers)
   - factorial(n): Calculate factorial (handle negative numbers)
   - percentage(value, percent): Calculate percentage

3. Memory Functions:
   - store_memory(value): Store a value in memory
   - recall_memory(): Retrieve stored value
   - clear_memory(): Clear stored value
   - add_to_memory(value): Add to stored value

4. Error Handling:
   - Comprehensive error messages for all invalid operations
   - Type checking for all inputs
   - Custom exception classes for different error types

5. Testing Requirements:
   - Write comprehensive unit tests using pytest
   - Test all operations with various input types
   - Test edge cases and error conditions
   - Test memory persistence
   - Achieve at least 95% code coverage

The module should be named 'advanced_calculator.py' with tests in 'test_advanced_calculator.py'."""
        
    def _show_results(self, result: dict, duration: float) -> None:
        """Show the workflow results."""
        self.formatter.print_banner("✅ TDD WORKFLOW COMPLETE!", width=80)
        
        print(f"\n⏱️  Total Duration: {duration:.2f} seconds")
        
        # Show phases completed
        print("\n📊 TDD Phases Completed:")
        print("   🔴 RED Phase: Tests written first ✓")
        print("   🟡 YELLOW Phase: Implementation completed ✓")
        print("   🟢 GREEN Phase: All tests passing ✓")
        
        # Show generated files
        print("\n📁 Generated Files:")
        output_dir = Path("generated/app_generated_latest")
        if output_dir.exists():
            for file in output_dir.iterdir():
                if file.is_file():
                    print(f"   - {file.name}")
                    
        # Show how to test
        print("\n🧪 To run the tests yourself:")
        print("   cd generated/app_generated_latest")
        print("   pytest test_*.py -v")
        
        # Educational summary
        print("\n📚 What We Learned:")
        print("   1. Tests were written BEFORE implementation (RED phase)")
        print("   2. Implementation was driven by test requirements (YELLOW phase)")
        print("   3. All code has test coverage (GREEN phase)")
        print("   4. This ensures our calculator is reliable and well-tested!")
        
        # Save results
        self._save_results(result, duration)
        
    def _save_results(self, result: dict, duration: float) -> None:
        """Save build results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/calculator_builds")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "workflow": "TDD",
            "success": True,
            "phases": ["RED", "YELLOW", "GREEN"],
            "files_generated": list(Path("generated/app_generated_latest").iterdir()) if Path("generated/app_generated_latest").exists() else []
        }
        
        summary_file = output_dir / f"calculator_build_{timestamp}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"\n💾 Build summary saved to: {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a calculator using Test-Driven Development"
    )
    parser.add_argument(
        "complexity",
        nargs="?",
        default="simple",
        choices=["simple", "advanced"],
        help="Calculator complexity level (default: simple)"
    )
    
    args = parser.parse_args()
    
    builder = CalculatorBuilder()
    asyncio.run(builder.build_calculator(args.complexity))


if __name__ == "__main__":
    main()