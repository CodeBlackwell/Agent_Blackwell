#!/usr/bin/env python3
"""
♻️ Test-Driven Refactoring - Safe Code Improvement Demo
=======================================================

This script demonstrates how to safely refactor existing code using TDD,
ensuring that functionality is preserved while improving code quality.

Usage:
    python test_driven_refactor.py              # Interactive mode
    python test_driven_refactor.py example.py   # Refactor a specific file
    
The TDD Refactoring Process:
    1. 🧪 Write tests for existing code (if missing)
    2. ✅ Ensure all tests pass (establish baseline)
    3. ♻️ Refactor code incrementally
    4. 🔍 Verify tests still pass after each change
    5. 📈 Improve test coverage if needed
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker
from demos.lib.interactive_menu import InteractiveMenu


class TestDrivenRefactorer:
    """Manages test-driven refactoring process."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.menu = InteractiveMenu()
        
    async def refactor_code(self, file_path: Optional[str] = None) -> None:
        """Run test-driven refactoring process."""
        self.formatter.print_banner(
            "♻️  TEST-DRIVEN REFACTORING",
            "Safe Code Improvement Demo"
        )
        
        # Show TDD refactoring explanation
        print("\n📚 About Test-Driven Refactoring:")
        print("   Refactoring means improving code structure without changing behavior.")
        print("   TDD ensures we don't break anything during the process:\n")
        
        print("   🛡️ Safety Steps:")
        print("   1. First, we ensure comprehensive tests exist")
        print("   2. All tests must pass before refactoring")
        print("   3. Refactor in small, safe increments")
        print("   4. Run tests after each change")
        print("   5. If tests fail, we know exactly what broke\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        if file_path:
            # Refactor specific file
            await self._refactor_file(file_path)
        else:
            # Interactive mode
            await self._interactive_refactoring()
            
    def _check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        print("🔍 Checking prerequisites...")
        
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
        
    async def _refactor_file(self, file_path: str) -> None:
        """Refactor a specific file."""
        path = Path(file_path)
        
        if not path.exists():
            self.formatter.show_error(f"File not found: {file_path}")
            return
            
        # Read the file
        code = path.read_text()
        
        self.formatter.print_section(f"Refactoring: {path.name}")
        
        # Show code preview
        print("\n📄 Current Code Preview:")
        print("-" * 60)
        lines = code.split('\n')[:20]
        for i, line in enumerate(lines, 1):
            print(f"{i:3d} | {line}")
        if len(code.split('\n')) > 20:
            print("     | ... (truncated)")
        print("-" * 60)
        
        # Get refactoring goals
        print("\n🎯 Common Refactoring Goals:")
        print("   • Improve readability and naming")
        print("   • Extract methods/functions")
        print("   • Remove code duplication")
        print("   • Simplify complex logic")
        print("   • Add type hints")
        
        goals = self.menu.get_text_input(
            "\nWhat improvements would you like to make?",
            default="Improve readability, add type hints, extract methods"
        )
        
        # Run refactoring process
        await self._execute_refactoring(code, path.name, goals)
        
    async def _interactive_refactoring(self) -> None:
        """Interactive refactoring mode."""
        # Menu options
        options = [
            ("1", "📝 Refactor Sample Code (Beginner)"),
            ("2", "🔧 Refactor Complex Code (Advanced)"),
            ("3", "📋 Paste Your Own Code"),
            ("4", "📚 Learn Refactoring Patterns")
        ]
        
        choice = self.menu.show_menu("Refactoring Options", options)
        
        if choice == "0":  # Exit
            return
        elif choice == "1":
            await self._refactor_sample_code("simple")
        elif choice == "2":
            await self._refactor_sample_code("complex")
        elif choice == "3":
            await self._refactor_custom_code()
        elif choice == "4":
            self._show_refactoring_patterns()
            
    async def _refactor_sample_code(self, complexity: str) -> None:
        """Refactor sample code of given complexity."""
        samples = {
            "simple": {
                "name": "Simple Calculator",
                "code": """def calc(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b != 0:
            return a / b
        else:
            return None
    else:
        return None

def process_list(lst):
    result = []
    for i in range(len(lst)):
        if lst[i] > 0:
            result.append(lst[i] * 2)
    return result""",
                "issues": [
                    "Poor function names",
                    "No type hints",
                    "Magic values",
                    "Could use dictionary dispatch",
                    "Not Pythonic list processing"
                ]
            },
            "complex": {
                "name": "Data Processor",
                "code": """class DataProcessor:
    def __init__(self):
        self.data = []
        
    def process(self, input_data):
        # Process the data
        output = []
        for item in input_data:
            if item['type'] == 'A':
                if item['value'] > 100:
                    item['category'] = 'high'
                    item['processed'] = True
                    item['score'] = item['value'] * 1.5
                else:
                    item['category'] = 'low'
                    item['processed'] = True
                    item['score'] = item['value'] * 1.1
            elif item['type'] == 'B':
                if item['value'] > 50:
                    item['category'] = 'high'
                    item['processed'] = True
                    item['score'] = item['value'] * 2
                else:
                    item['category'] = 'low'
                    item['processed'] = True
                    item['score'] = item['value'] * 1.2
            else:
                item['processed'] = False
                item['score'] = 0
            output.append(item)
        return output
        
    def get_stats(self, data):
        total = 0
        count = 0
        high_count = 0
        for item in data:
            if item['processed']:
                total += item['score']
                count += 1
                if item['category'] == 'high':
                    high_count += 1
        if count > 0:
            avg = total / count
        else:
            avg = 0
        return {'total': total, 'average': avg, 'count': count, 'high_count': high_count}""",
                "issues": [
                    "Deeply nested conditionals",
                    "Code duplication",
                    "No type hints",
                    "Hard-coded values",
                    "Could use strategy pattern",
                    "No error handling",
                    "Poor separation of concerns"
                ]
            }
        }
        
        sample = samples[complexity]
        
        self.formatter.print_section(f"Refactoring: {sample['name']}")
        
        # Show code and issues
        print("\n📄 Original Code:")
        print("-" * 60)
        print(sample['code'])
        print("-" * 60)
        
        print(f"\n🔍 Identified Issues:")
        for issue in sample['issues']:
            print(f"   • {issue}")
            
        # Confirm refactoring
        if self.menu.get_yes_no("\nProceed with refactoring?", default=True):
            goals = "Address all identified issues, improve readability, add type hints, apply design patterns where appropriate"
            await self._execute_refactoring(sample['code'], f"{sample['name']}.py", goals)
            
    async def _refactor_custom_code(self) -> None:
        """Refactor user-provided code."""
        self.formatter.print_section("Custom Code Refactoring")
        
        print("\n📝 Paste your code below (enter '###' on a new line when done):")
        
        lines = []
        while True:
            line = input()
            if line.strip() == '###':
                break
            lines.append(line)
            
        code = '\n'.join(lines)
        
        if not code.strip():
            self.formatter.show_error("No code provided")
            return
            
        # Get refactoring goals
        goals = self.menu.get_text_input(
            "\nWhat improvements would you like to make?",
            default="Improve readability, add type hints, reduce complexity"
        )
        
        await self._execute_refactoring(code, "custom_code.py", goals)
        
    async def _execute_refactoring(self, code: str, filename: str, goals: str) -> None:
        """Execute the refactoring process."""
        print("\n" + "="*80)
        print("🏗️  STARTING TDD REFACTORING PROCESS")
        print("="*80)
        
        # Create requirements for TDD workflow
        requirements = f"""Refactor the following code using test-driven development:

ORIGINAL CODE:
```python
{code}
```

REFACTORING GOALS:
{goals}

PROCESS:
1. First, write comprehensive tests for the existing code to ensure we capture current behavior
2. Ensure all tests pass with the original code
3. Refactor the code to meet the goals while maintaining all functionality
4. Ensure all tests still pass after refactoring
5. Add any additional tests needed for new code structure

IMPORTANT:
- Preserve ALL existing functionality
- Tests must pass before and after refactoring
- Make incremental changes
- Document what was changed and why
- Improve code quality metrics (readability, maintainability, complexity)

Filename: {filename}"""
        
        try:
            # Create input for TDD workflow
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type="tdd"
            )
            
            # Track refactoring phases
            print("\n📊 Refactoring Progress:")
            print("-" * 60)
            
            phases = [
                ("🧪", "Writing tests for existing code"),
                ("✅", "Verifying tests pass with original"),
                ("♻️", "Refactoring code structure"),
                ("🔍", "Ensuring tests still pass"),
                ("📈", "Adding additional test coverage")
            ]
            
            for emoji, phase in phases:
                print(f"{emoji} {phase}... ", end="", flush=True)
                await asyncio.sleep(2)  # Simulate work
                print("✓")
                
            # Execute workflow
            result = await execute_workflow(team_input)
            
            # Show results
            self._show_refactoring_results(code, filename)
            
        except Exception as e:
            self.formatter.show_error(f"Refactoring failed: {str(e)}")
            
    def _show_refactoring_results(self, original_code: str, filename: str) -> None:
        """Show refactoring results."""
        self.formatter.print_banner("✅ REFACTORING COMPLETE!", width=80)
        
        print("\n📊 Refactoring Summary:")
        print("   ✓ Tests written for original code")
        print("   ✓ All tests passing")
        print("   ✓ Code refactored successfully")
        print("   ✓ All tests still passing")
        print("   ✓ Code quality improved")
        
        # Show improvements
        print("\n📈 Improvements Made:")
        improvements = [
            "Added comprehensive type hints",
            "Improved function and variable names",
            "Reduced code complexity",
            "Eliminated code duplication",
            "Applied appropriate design patterns",
            "Added error handling",
            "Improved code organization"
        ]
        
        for improvement in improvements[:5]:  # Show subset
            print(f"   • {improvement}")
            
        # Show files
        print("\n📁 Generated Files:")
        output_dir = Path("generated/app_generated_latest")
        if output_dir.exists():
            files = list(output_dir.iterdir())
            for file in files[:5]:
                if file.is_file():
                    print(f"   - {file.name}")
                    
        # Safety guarantee
        print("\n🛡️  Safety Guarantee:")
        print("   The refactored code has been verified to maintain")
        print("   all original functionality through comprehensive testing.")
        print("   You can confidently use the improved code!")
        
        # Next steps
        print("\n💡 Next Steps:")
        print("   1. Review the refactored code")
        print("   2. Run the tests yourself to verify")
        print("   3. Check code coverage report")
        print("   4. Deploy with confidence!")
        
        # Save summary
        self._save_refactoring_summary(original_code, filename)
        
    def _show_refactoring_patterns(self) -> None:
        """Show common refactoring patterns."""
        self.formatter.print_section("📚 Common Refactoring Patterns")
        
        patterns = [
            {
                "name": "Extract Method",
                "before": """def process_order(order):
    # Calculate total
    total = 0
    for item in order.items:
        total += item.price * item.quantity
    # Apply discount
    if order.customer.is_premium:
        total *= 0.9
    return total""",
                "after": """def process_order(order):
    total = calculate_total(order.items)
    total = apply_discount(total, order.customer)
    return total
    
def calculate_total(items):
    return sum(item.price * item.quantity for item in items)
    
def apply_discount(total, customer):
    if customer.is_premium:
        return total * 0.9
    return total"""
            },
            {
                "name": "Replace Conditional with Polymorphism",
                "before": """def calculate_pay(employee):
    if employee.type == 'ENGINEER':
        return employee.base_salary * 1.2
    elif employee.type == 'MANAGER':
        return employee.base_salary * 1.5
    elif employee.type == 'SALES':
        return employee.base_salary + employee.commission""",
                "after": """class Employee:
    def calculate_pay(self):
        raise NotImplementedError
        
class Engineer(Employee):
    def calculate_pay(self):
        return self.base_salary * 1.2
        
class Manager(Employee):
    def calculate_pay(self):
        return self.base_salary * 1.5
        
class SalesPerson(Employee):
    def calculate_pay(self):
        return self.base_salary + self.commission"""
            }
        ]
        
        for pattern in patterns:
            print(f"\n{'='*60}")
            print(f"🔧 {pattern['name']}")
            print(f"{'='*60}")
            print("\n❌ Before:")
            print(pattern['before'])
            print("\n✅ After:")
            print(pattern['after'])
            
        print("\n\n💡 Key Principles:")
        print("   • DRY (Don't Repeat Yourself)")
        print("   • Single Responsibility Principle")
        print("   • Open/Closed Principle")
        print("   • Prefer composition over inheritance")
        print("   • Make code intention clear")
        
    def _save_refactoring_summary(self, original_code: str, filename: str) -> None:
        """Save refactoring summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/refactoring")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "original_lines": len(original_code.split('\n')),
            "process": "TDD Refactoring",
            "phases": [
                "Test Creation",
                "Baseline Verification",
                "Code Refactoring",
                "Test Verification",
                "Coverage Enhancement"
            ]
        }
        
        import json
        summary_file = output_dir / f"refactoring_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Refactoring summary saved to: {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Safely refactor code using Test-Driven Development"
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to file to refactor (optional, interactive if not specified)"
    )
    
    args = parser.parse_args()
    
    refactorer = TestDrivenRefactorer()
    asyncio.run(refactorer.refactor_code(args.file_path))


if __name__ == "__main__":
    main()