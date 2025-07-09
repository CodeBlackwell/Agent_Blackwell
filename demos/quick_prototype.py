#!/usr/bin/env python3
"""
⚡ Quick Prototype - Individual Steps Demo
=========================================

This script demonstrates how to use individual agent steps for rapid prototyping,
showing how to call specific agents directly without a full workflow.

Usage:
    python quick_prototype.py              # Interactive mode
    python quick_prototype.py algorithm    # Prototype an algorithm
    python quick_prototype.py api-endpoint # Prototype an API endpoint
    
Individual Steps Available:
    - Planning: Get a development plan
    - Design: Create system architecture
    - Implementation: Generate code
    - Testing: Write tests
    - Review: Get code review feedback
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker
from demos.lib.interactive_menu import InteractiveMenu


class QuickPrototyper:
    """Enables rapid prototyping using individual agent steps."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.menu = InteractiveMenu()
        self.generated_artifacts = {}
        
    async def run_prototype(self, prototype_type: Optional[str] = None) -> None:
        """Run quick prototyping session."""
        self.formatter.print_banner(
            "⚡ QUICK PROTOTYPE",
            "Individual Agent Steps Demo"
        )
        
        # Show individual steps explanation
        print("\n📚 About Individual Steps:")
        print("   Sometimes you don't need a full workflow - you just want")
        print("   to quickly use a specific agent for a task:\n")
        
        print("   🎯 Available Agents:")
        print("   • Planner - Create development plans and break down tasks")
        print("   • Designer - Design system architecture and interfaces")
        print("   • Coder - Generate implementation code")
        print("   • Test Writer - Create comprehensive tests")
        print("   • Reviewer - Review code and suggest improvements\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        if prototype_type:
            # Run specific prototype
            await self._run_specific_prototype(prototype_type)
        else:
            # Interactive mode
            await self._run_interactive_mode()
            
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
        
    async def _run_specific_prototype(self, prototype_type: str) -> None:
        """Run a specific prototype example."""
        prototypes = {
            "algorithm": {
                "name": "Algorithm Prototype",
                "requirements": "Create a binary search algorithm that works with any comparable items",
                "steps": ["planning", "implementation", "testing"]
            },
            "api-endpoint": {
                "name": "API Endpoint Prototype",
                "requirements": "Create a REST endpoint for user authentication with JWT",
                "steps": ["design", "implementation", "review"]
            }
        }
        
        if prototype_type not in prototypes:
            self.formatter.show_error(f"Unknown prototype type: {prototype_type}")
            return
            
        prototype = prototypes[prototype_type]
        
        self.formatter.print_section(f"Prototyping: {prototype['name']}")
        print(f"\n📝 Requirements: {prototype['requirements']}")
        print(f"\n🔧 Using agents: {', '.join(prototype['steps'])}")
        
        # Execute each step
        for step in prototype['steps']:
            await self._execute_step(step, prototype['requirements'])
            
        # Show summary
        self._show_prototype_summary()
        
    async def _run_interactive_mode(self) -> None:
        """Run interactive prototyping mode."""
        while True:
            # Main menu
            options = [
                ("1", "🎯 Create a Plan (Planner Agent)"),
                ("2", "🏗️ Design Architecture (Designer Agent)"),
                ("3", "💻 Generate Code (Coder Agent)"),
                ("4", "🧪 Write Tests (Test Writer Agent)"),
                ("5", "🔍 Review Code (Reviewer Agent)"),
                ("6", "📦 Run Custom Sequence"),
                ("7", "📊 View Generated Artifacts")
            ]
            
            choice = self.menu.show_menu("Quick Prototype Menu", options)
            
            if choice == "0":  # Exit
                break
            elif choice == "1":
                await self._interactive_planning()
            elif choice == "2":
                await self._interactive_design()
            elif choice == "3":
                await self._interactive_coding()
            elif choice == "4":
                await self._interactive_testing()
            elif choice == "5":
                await self._interactive_review()
            elif choice == "6":
                await self._custom_sequence()
            elif choice == "7":
                self._view_artifacts()
                
    async def _interactive_planning(self) -> None:
        """Interactive planning session."""
        self.formatter.print_section("🎯 Planning Session")
        
        print("\nThe Planner agent will:")
        print("• Analyze your requirements")
        print("• Break down the task into components")
        print("• Create a development roadmap")
        
        requirements = self.menu.get_text_input(
            "\nWhat would you like to plan?",
            default="A simple todo list application"
        )
        
        await self._execute_step("planning", requirements)
        
    async def _interactive_design(self) -> None:
        """Interactive design session."""
        self.formatter.print_section("🏗️ Design Session")
        
        print("\nThe Designer agent will:")
        print("• Create system architecture")
        print("• Define interfaces and data flow")
        print("• Suggest design patterns")
        
        requirements = self.menu.get_text_input(
            "\nWhat would you like to design?",
            default="A REST API for user management"
        )
        
        # Check if we have a plan
        if "planning" in self.generated_artifacts:
            use_plan = self.menu.get_yes_no(
                "Use the existing plan as context?",
                default=True
            )
            if use_plan:
                requirements = f"{requirements}\n\nPlan:\n{self.generated_artifacts['planning']}"
                
        await self._execute_step("design", requirements)
        
    async def _interactive_coding(self) -> None:
        """Interactive coding session."""
        self.formatter.print_section("💻 Coding Session")
        
        print("\nThe Coder agent will:")
        print("• Generate implementation code")
        print("• Add error handling")
        print("• Follow best practices")
        
        requirements = self.menu.get_text_input(
            "\nWhat would you like to implement?",
            default="A function to validate email addresses"
        )
        
        # Check for existing artifacts
        context = ""
        if "design" in self.generated_artifacts:
            if self.menu.get_yes_no("Use existing design as context?", default=True):
                context += f"\n\nDesign:\n{self.generated_artifacts['design']}"
        if "planning" in self.generated_artifacts and not context:
            if self.menu.get_yes_no("Use existing plan as context?", default=True):
                context += f"\n\nPlan:\n{self.generated_artifacts['planning']}"
                
        await self._execute_step("implementation", requirements + context)
        
    async def _interactive_testing(self) -> None:
        """Interactive test writing session."""
        self.formatter.print_section("🧪 Test Writing Session")
        
        print("\nThe Test Writer agent will:")
        print("• Create comprehensive unit tests")
        print("• Cover edge cases")
        print("• Use appropriate testing frameworks")
        
        if "implementation" in self.generated_artifacts:
            print("\n📋 Found existing implementation!")
            use_impl = self.menu.get_yes_no(
                "Write tests for the existing implementation?",
                default=True
            )
            if use_impl:
                requirements = f"Write comprehensive tests for this code:\n\n{self.generated_artifacts['implementation']}"
            else:
                requirements = self.menu.get_text_input(
                    "\nWhat would you like to write tests for?"
                )
        else:
            requirements = self.menu.get_text_input(
                "\nWhat would you like to write tests for?",
                default="A calculator module with add, subtract, multiply, divide"
            )
            
        await self._execute_step("testing", requirements)
        
    async def _interactive_review(self) -> None:
        """Interactive code review session."""
        self.formatter.print_section("🔍 Code Review Session")
        
        print("\nThe Reviewer agent will:")
        print("• Analyze code quality")
        print("• Suggest improvements")
        print("• Check for best practices")
        
        if "implementation" in self.generated_artifacts:
            print("\n📋 Found existing implementation!")
            review_impl = self.menu.get_yes_no(
                "Review the existing implementation?",
                default=True
            )
            if review_impl:
                code = self.generated_artifacts['implementation']
                requirements = f"Review this code:\n\n{code}"
            else:
                code = self.menu.get_text_input(
                    "\nPaste the code to review (or describe what to review):"
                )
                requirements = f"Review this: {code}"
        else:
            code = self.menu.get_text_input(
                "\nPaste the code to review (or describe what to review):"
            )
            requirements = f"Review this: {code}"
            
        await self._execute_step("review", requirements)
        
    async def _custom_sequence(self) -> None:
        """Run a custom sequence of agents."""
        self.formatter.print_section("📦 Custom Agent Sequence")
        
        print("\nCreate your own sequence of agents to run.")
        print("Available agents: planning, design, implementation, testing, review")
        
        sequence = self.menu.get_text_input(
            "\nEnter agents to run (comma-separated)",
            default="planning,implementation,testing"
        )
        
        agents = [a.strip() for a in sequence.split(",")]
        
        requirements = self.menu.get_text_input(
            "\nWhat are you building?"
        )
        
        print(f"\n🔄 Running sequence: {' → '.join(agents)}")
        
        for agent in agents:
            if agent in ["planning", "design", "implementation", "testing", "review"]:
                await self._execute_step(agent, requirements)
                # Use output as input for next agent
                if agent in self.generated_artifacts:
                    requirements = f"Previous step output:\n{self.generated_artifacts[agent]}\n\nOriginal requirements: {requirements}"
            else:
                print(f"⚠️  Unknown agent: {agent}")
                
    def _view_artifacts(self) -> None:
        """View generated artifacts."""
        self.formatter.print_section("📊 Generated Artifacts")
        
        if not self.generated_artifacts:
            print("\n📭 No artifacts generated yet.")
            return
            
        for step, content in self.generated_artifacts.items():
            print(f"\n{'='*60}")
            print(f"📄 {step.upper()}")
            print(f"{'='*60}")
            print(content[:500] + "..." if len(content) > 500 else content)
            
        # Save option
        if self.menu.get_yes_no("\nSave all artifacts to file?", default=True):
            self._save_artifacts()
            
    async def _execute_step(self, step: str, requirements: str) -> None:
        """Execute a single workflow step."""
        print(f"\n🔄 Executing {step} step...")
        start_time = time.time()
        
        try:
            # Create input for individual step
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type="individual",
                step_type=step
            )
            
            # Execute the step
            result = await execute_workflow(team_input)
            
            duration = time.time() - start_time
            
            # Store result
            self.generated_artifacts[step] = str(result)
            
            print(f"✅ {step.title()} completed in {duration:.2f} seconds")
            
            # Show preview
            print(f"\n📄 {step.title()} Output Preview:")
            print("-" * 60)
            output = str(result)
            print(output[:300] + "..." if len(output) > 300 else output)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ {step.title()} failed: {str(e)}")
            
    def _show_prototype_summary(self) -> None:
        """Show summary of prototyping session."""
        self.formatter.print_banner("📊 PROTOTYPE SUMMARY", width=80)
        
        print(f"\n✅ Generated Artifacts: {len(self.generated_artifacts)}")
        
        for step in self.generated_artifacts:
            print(f"   • {step.title()}")
            
        print("\n💡 Next Steps:")
        print("   1. Review the generated artifacts")
        print("   2. Combine them into a complete solution")
        print("   3. Run tests to validate functionality")
        print("   4. Use a full workflow for production code")
        
        self._save_artifacts()
        
    def _save_artifacts(self) -> None:
        """Save all artifacts to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/prototypes") / f"prototype_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for step, content in self.generated_artifacts.items():
            file_path = output_dir / f"{step}.txt"
            with open(file_path, 'w') as f:
                f.write(content)
                
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "steps_executed": list(self.generated_artifacts.keys()),
            "files": [f"{step}.txt" for step in self.generated_artifacts.keys()]
        }
        
        import json
        with open(output_dir / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Artifacts saved to: {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Quick prototyping using individual agent steps"
    )
    parser.add_argument(
        "prototype_type",
        nargs="?",
        choices=["algorithm", "api-endpoint"],
        help="Type of prototype to create (optional, interactive if not specified)"
    )
    
    args = parser.parse_args()
    
    prototyper = QuickPrototyper()
    asyncio.run(prototyper.run_prototype(args.prototype_type))


if __name__ == "__main__":
    main()