#!/usr/bin/env python3
"""
Interactive Demo for MVP Incremental Workflow

This script provides an easy way to explore and test the MVP incremental workflow
with pre-configured examples and interactive options.

Usage:
    # Interactive mode (recommended for first-time users)
    python demo_mvp_incremental.py
    
    # CLI mode with preset
    python demo_mvp_incremental.py --preset calculator
    
    # CLI mode with custom requirements
    python demo_mvp_incremental.py --requirements "Create a REST API for managing tasks"
    
    # CLI mode with all phases enabled
    python demo_mvp_incremental.py --preset todo-api --all-phases
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


# Pre-configured examples
EXAMPLES = {
    "calculator": {
        "name": "Simple Calculator",
        "requirements": """Create a Python calculator module with the following features:
1. Add two numbers
2. Subtract two numbers
3. Multiply two numbers
4. Divide two numbers (handle division by zero)
5. Calculate square root
6. Include unit tests for all operations""",
        "config": {
            "run_tests": True,
            "run_integration_verification": False
        }
    },
    "todo-api": {
        "name": "TODO REST API",
        "requirements": """Create a REST API for managing TODO items using FastAPI:
1. Create a TODO item (title, description, completed status)
2. List all TODO items with pagination
3. Get a specific TODO by ID
4. Update a TODO item
5. Delete a TODO item
6. Add input validation
7. Include API documentation
8. Write tests for all endpoints""",
        "config": {
            "run_tests": True,
            "run_integration_verification": True
        }
    },
    "auth-system": {
        "name": "User Authentication System",
        "requirements": """Create a user authentication system with:
1. User registration with email and password
2. Password hashing using bcrypt
3. User login with JWT token generation
4. Token validation middleware
5. Password reset functionality
6. Email verification
7. User profile management
8. Role-based access control (admin, user)
9. Include comprehensive tests
10. Add security best practices""",
        "config": {
            "run_tests": True,
            "run_integration_verification": True
        }
    },
    "file-processor": {
        "name": "CSV File Processor",
        "requirements": """Create a CSV file processing tool that:
1. Read CSV files with configurable delimiter
2. Validate data types in columns
3. Handle missing values
4. Filter rows based on conditions
5. Aggregate data (sum, average, count)
6. Export results to JSON or new CSV
7. Support large files with streaming
8. Include error handling and logging""",
        "config": {
            "run_tests": False,
            "run_integration_verification": True
        }
    }
}


class MVPIncrementalDemo:
    """Interactive demo for MVP Incremental workflow."""
    
    def __init__(self):
        self.selected_example = None
        self.custom_requirements = None
        self.config = {
            "run_tests": False,
            "run_integration_verification": False
        }
        
    def print_banner(self):
        """Print welcome banner."""
        print("=" * 70)
        print("🚀 MVP Incremental Workflow Demo")
        print("=" * 70)
        print("This demo helps you explore the MVP incremental workflow with")
        print("pre-configured examples or your own requirements.")
        print()
        
    def print_examples(self):
        """Display available examples."""
        print("\n📚 Available Examples:")
        print("-" * 50)
        for key, example in EXAMPLES.items():
            print(f"  {key:<15} - {example['name']}")
        print()
        
    def get_user_choice(self) -> str:
        """Get user's choice for example or custom."""
        print("\n🎯 Choose an option:")
        print("  1. Use a pre-configured example")
        print("  2. Enter custom requirements")
        print("  3. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
            
    def select_example(self) -> Optional[str]:
        """Let user select an example."""
        self.print_examples()
        
        while True:
            choice = input("Enter example name (or 'back' to return): ").strip().lower()
            if choice == 'back':
                return None
            if choice in EXAMPLES:
                return choice
            print(f"❌ Invalid example. Choose from: {', '.join(EXAMPLES.keys())}")
            
    def get_custom_requirements(self) -> str:
        """Get custom requirements from user."""
        print("\n📝 Enter your requirements:")
        print("(Type 'END' on a new line when finished)")
        
        lines = []
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
            
        return '\n'.join(lines)
        
    def configure_phases(self):
        """Let user configure which phases to run."""
        print("\n⚙️  Phase Configuration:")
        print("-" * 50)
        print("The MVP incremental workflow has 10 phases.")
        print("Phases 1-8 are always enabled. You can enable:")
        
        # Phase 9
        print("\n📍 Phase 9 - Test Execution")
        print("   Runs tests after each feature implementation")
        choice = input("   Enable Phase 9? (y/N): ").strip().lower()
        self.config["run_tests"] = choice == 'y'
        
        # Phase 10
        print("\n📍 Phase 10 - Integration Verification")
        print("   Performs full integration testing after all features")
        choice = input("   Enable Phase 10? (y/N): ").strip().lower()
        self.config["run_integration_verification"] = choice == 'y'
        
    def show_configuration_summary(self, requirements: str):
        """Display configuration summary before running."""
        print("\n📋 Configuration Summary:")
        print("=" * 70)
        print(f"Requirements: {requirements[:100]}..." if len(requirements) > 100 else f"Requirements: {requirements}")
        print(f"Phase 9 (Test Execution): {'✅ Enabled' if self.config['run_tests'] else '❌ Disabled'}")
        print(f"Phase 10 (Integration Verification): {'✅ Enabled' if self.config['run_integration_verification'] else '❌ Disabled'}")
        print("=" * 70)
        
    async def run_workflow(self, requirements: str) -> Dict:
        """Execute the MVP incremental workflow."""
        print("\n🏃 Starting MVP Incremental Workflow...")
        print("This may take a few minutes. Watch the progress below:\n")
        
        # Create input
        input_data = CodingTeamInput(
            requirements=requirements,
            run_tests=self.config["run_tests"],
            run_integration_verification=self.config["run_integration_verification"]
        )
        
        # Create tracer for monitoring
        tracer = WorkflowExecutionTracer("mvp_incremental_demo")
        
        # Execute workflow
        result = await execute_workflow(
            "mvp_incremental",
            input_data,
            tracer
        )
        
        return result
        
    def save_results(self, result: Dict):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Save result summary
        summary_file = output_dir / f"mvp_demo_{timestamp}_summary.json"
        summary = {
            "timestamp": timestamp,
            "example": self.selected_example,
            "config": self.config,
            "success": True,  # You might want to determine this from the result
            "generated_files": []  # Extract from result if available
        }
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Results saved to: {summary_file}")
        
    async def run_interactive(self):
        """Run in interactive mode."""
        self.print_banner()
        
        while True:
            choice = self.get_user_choice()
            
            if choice == '3':
                print("\n👋 Goodbye!")
                break
                
            elif choice == '1':
                # Use pre-configured example
                example_key = self.select_example()
                if example_key:
                    self.selected_example = example_key
                    example = EXAMPLES[example_key]
                    requirements = example["requirements"]
                    
                    # Use example's default config
                    self.config = example["config"].copy()
                    
                    # Ask if user wants to modify phases
                    modify = input("\n🔧 Modify phase configuration? (y/N): ").strip().lower()
                    if modify == 'y':
                        self.configure_phases()
                else:
                    continue
                    
            else:
                # Custom requirements
                requirements = self.get_custom_requirements()
                if not requirements.strip():
                    print("❌ Requirements cannot be empty.")
                    continue
                    
                self.configure_phases()
                
            # Show summary and confirm
            self.show_configuration_summary(requirements)
            confirm = input("\n▶️  Proceed with workflow? (Y/n): ").strip().lower()
            
            if confirm != 'n':
                try:
                    result = await self.run_workflow(requirements)
                    
                    print("\n✅ Workflow completed successfully!")
                    
                    # Save results
                    save = input("\n💾 Save results? (Y/n): ").strip().lower()
                    if save != 'n':
                        self.save_results(result)
                        
                except Exception as e:
                    print(f"\n❌ Error during workflow execution: {e}")
                    
            # Ask if user wants to run another
            another = input("\n🔄 Run another workflow? (y/N): ").strip().lower()
            if another != 'y':
                print("\n👋 Thanks for using MVP Incremental Demo!")
                break


async def run_cli(args):
    """Run in CLI mode."""
    demo = MVPIncrementalDemo()
    
    # Determine requirements
    if args.preset:
        if args.preset not in EXAMPLES:
            print(f"❌ Invalid preset: {args.preset}")
            print(f"Available presets: {', '.join(EXAMPLES.keys())}")
            return 1
            
        example = EXAMPLES[args.preset]
        requirements = example["requirements"]
        demo.config = example["config"].copy()
        
    elif args.requirements:
        requirements = args.requirements
    else:
        print("❌ Either --preset or --requirements must be specified")
        return 1
        
    # Override config if specified
    if args.all_phases:
        demo.config["run_tests"] = True
        demo.config["run_integration_verification"] = True
    else:
        if args.tests is not None:
            demo.config["run_tests"] = args.tests
        if args.integration is not None:
            demo.config["run_integration_verification"] = args.integration
            
    # Show configuration
    print(f"🚀 Running MVP Incremental Workflow")
    print(f"📋 Requirements: {requirements[:100]}...")
    print(f"⚙️  Phase 9 (Tests): {'✅' if demo.config['run_tests'] else '❌'}")
    print(f"⚙️  Phase 10 (Integration): {'✅' if demo.config['run_integration_verification'] else '❌'}")
    print()
    
    try:
        result = await demo.run_workflow(requirements)
        print("\n✅ Workflow completed successfully!")
        
        if args.save_output:
            demo.save_results(result)
            
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MVP Incremental Workflow Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python demo_mvp_incremental.py
  
  # Use a preset
  python demo_mvp_incremental.py --preset calculator
  
  # Custom requirements with all phases
  python demo_mvp_incremental.py --requirements "Create a web scraper" --all-phases
  
  # Preset with custom phase config
  python demo_mvp_incremental.py --preset todo-api --tests --no-integration
        """
    )
    
    parser.add_argument(
        "--preset",
        choices=list(EXAMPLES.keys()),
        help="Use a pre-configured example"
    )
    
    parser.add_argument(
        "--requirements",
        help="Custom requirements (alternative to preset)"
    )
    
    parser.add_argument(
        "--all-phases",
        action="store_true",
        help="Enable all phases (9 and 10)"
    )
    
    parser.add_argument(
        "--tests",
        action="store_true",
        default=None,
        help="Enable Phase 9 (test execution)"
    )
    
    parser.add_argument(
        "--no-tests",
        dest="tests",
        action="store_false",
        help="Disable Phase 9 (test execution)"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        default=None,
        help="Enable Phase 10 (integration verification)"
    )
    
    parser.add_argument(
        "--no-integration",
        dest="integration",
        action="store_false",
        help="Disable Phase 10 (integration verification)"
    )
    
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save output to file"
    )
    
    args = parser.parse_args()
    
    # Check if running without arguments (interactive mode)
    if not any(vars(args).values()):
        asyncio.run(MVPIncrementalDemo().run_interactive())
    else:
        # CLI mode
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)


if __name__ == "__main__":
    main()