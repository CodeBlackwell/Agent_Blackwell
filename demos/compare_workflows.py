#!/usr/bin/env python3
"""
⚖️ Compare Workflows - Side-by-Side Workflow Comparison Demo
===========================================================

This script demonstrates running the same requirements through different workflows
to show their unique approaches and outputs.

Usage:
    python compare_workflows.py                    # Use default requirements
    python compare_workflows.py "Your custom req"  # Use custom requirements
    
Workflows Compared:
    - TDD: Test-Driven Development (Red-Yellow-Green)
    - Full: Comprehensive planning to implementation
    - MVP Incremental: 10-phase incremental development
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time
from typing import Dict, List, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker


class WorkflowComparator:
    """Compares different workflows with the same requirements."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.results = {}
        
    async def compare_workflows(self, requirements: str = None) -> None:
        """Compare different workflows."""
        self.formatter.print_banner(
            "⚖️  WORKFLOW COMPARISON",
            "Side-by-Side Analysis Demo"
        )
        
        # Show comparison overview
        print("\n📚 Workflow Comparison Overview:")
        print("   This demo runs the same requirements through different workflows")
        print("   to help you understand their unique characteristics:\n")
        
        workflows_info = {
            "tdd": {
                "name": "🔴🟡🟢 TDD (Test-Driven Development)",
                "description": "Tests first, then implementation",
                "strengths": ["Ensures testability", "Catches bugs early", "Clear validation"],
                "best_for": "Projects where reliability is critical"
            },
            "full": {
                "name": "📋 Full Workflow",
                "description": "Complete planning through implementation",
                "strengths": ["Thorough planning", "Clean architecture", "Comprehensive approach"],
                "best_for": "Complex projects needing upfront design"
            },
            "mvp_incremental": {
                "name": "🔄 MVP Incremental",
                "description": "10-phase incremental development",
                "strengths": ["Gradual complexity", "Continuous validation", "Risk mitigation"],
                "best_for": "Large projects or uncertain requirements"
            }
        }
        
        for wf_id, info in workflows_info.items():
            print(f"\n{info['name']}")
            print(f"   {info['description']}")
            print(f"   Strengths: {', '.join(info['strengths'])}")
            print(f"   Best for: {info['best_for']}")
            
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        # Get or use default requirements
        if not requirements:
            requirements = self._get_default_requirements()
            
        # Show requirements
        self.formatter.print_section("Requirements to Compare")
        print("📝 Requirements:")
        print("-" * 60)
        print(requirements[:300] + "..." if len(requirements) > 300 else requirements)
        print("-" * 60)
        
        # Confirm execution
        print("\n🚀 Ready to compare workflows?")
        print("   Each workflow will process the same requirements.")
        print("   This helps you see the differences in approach.")
        print("\n   Press Enter to continue or Ctrl+C to cancel...")
        input()
        
        # Run comparisons
        workflows = ["tdd", "full", "mvp_incremental"]
        
        print("\n" + "="*80)
        print("🏁 STARTING WORKFLOW COMPARISON")
        print("="*80)
        
        for workflow in workflows:
            await self._run_workflow(workflow, requirements, workflows_info[workflow])
            
        # Show comparison results
        self._show_comparison_results()
        
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
        
    def _get_default_requirements(self) -> str:
        """Get default requirements for comparison."""
        return """Create a simple task manager module with the following features:

1. Core Functionality:
   - Add a task with title and optional description
   - Mark task as complete
   - Delete a task
   - List all tasks
   - Filter tasks by status (pending/completed)

2. Data Storage:
   - Use in-memory storage (dictionary or list)
   - Each task should have: id, title, description, status, created_at

3. Error Handling:
   - Handle invalid task IDs
   - Validate input data

4. Testing:
   - Write unit tests for all functions
   - Test edge cases and error conditions

Create a module named 'task_manager.py' with tests in 'test_task_manager.py'."""
   
    async def _run_workflow(self, workflow_type: str, requirements: str, info: Dict) -> None:
        """Run a single workflow and capture results."""
        print(f"\n{'='*80}")
        print(f"🔄 Running {info['name']}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Create input for workflow
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type=workflow_type
            )
            
            # Show workflow characteristics
            print(f"\n📊 Workflow Characteristics:")
            print(f"   Type: {workflow_type}")
            print(f"   Approach: {info['description']}")
            print(f"   Key Strengths: {', '.join(info['strengths'][:2])}")
            
            print(f"\n⏳ Processing...")
            
            # Run the workflow
            result = await execute_workflow(team_input)
            
            duration = time.time() - start_time
            
            # Store results
            self.results[workflow_type] = {
                "info": info,
                "duration": duration,
                "success": True,
                "result": result,
                "files_generated": self._get_generated_files(workflow_type)
            }
            
            print(f"\n✅ {info['name']} completed in {duration:.2f} seconds")
            
            # Show brief results
            print(f"\n📁 Files Generated:")
            for file in self.results[workflow_type]["files_generated"][:5]:
                print(f"   - {file}")
            if len(self.results[workflow_type]["files_generated"]) > 5:
                print(f"   ... and {len(self.results[workflow_type]['files_generated']) - 5} more")
                
        except Exception as e:
            duration = time.time() - start_time
            self.results[workflow_type] = {
                "info": info,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
            print(f"\n❌ {info['name']} failed: {str(e)}")
            
    def _get_generated_files(self, workflow_type: str) -> List[str]:
        """Get list of generated files."""
        output_dir = Path("generated/app_generated_latest")
        if output_dir.exists():
            return [f.name for f in output_dir.iterdir() if f.is_file()]
        return []
        
    def _show_comparison_results(self) -> None:
        """Show detailed comparison of workflow results."""
        self.formatter.print_banner("📊 WORKFLOW COMPARISON RESULTS", width=80)
        
        # Summary table
        print("\n📈 Execution Summary:")
        print("-" * 80)
        print(f"{'Workflow':<25} {'Status':<10} {'Duration':<15} {'Files':<15}")
        print("-" * 80)
        
        for wf_type, result in self.results.items():
            status = "✅ Success" if result["success"] else "❌ Failed"
            duration = f"{result['duration']:.2f}s"
            files = len(result.get("files_generated", []))
            
            print(f"{result['info']['name'][:24]:<25} {status:<10} {duration:<15} {files:<15}")
            
        # Detailed comparison
        print("\n\n🔍 Detailed Analysis:")
        print("="*80)
        
        # Compare approaches
        print("\n1. APPROACH DIFFERENCES:")
        print("-"*40)
        
        if "tdd" in self.results:
            print("\n🔴🟡🟢 TDD Workflow:")
            print("   • Started with writing tests")
            print("   • Implemented code to pass tests")
            print("   • Ensured 100% test coverage")
            
        if "full" in self.results:
            print("\n📋 Full Workflow:")
            print("   • Created comprehensive plan")
            print("   • Designed system architecture")
            print("   • Implemented complete solution")
            
        if "mvp_incremental" in self.results:
            print("\n🔄 MVP Incremental:")
            print("   • Analyzed requirements in detail")
            print("   • Built features incrementally")
            print("   • Validated at each phase")
            
        # Compare timing
        print("\n\n2. PERFORMANCE COMPARISON:")
        print("-"*40)
        
        sorted_results = sorted(self.results.items(), key=lambda x: x[1]["duration"])
        
        print(f"\n⚡ Fastest: {sorted_results[0][1]['info']['name']} ({sorted_results[0][1]['duration']:.2f}s)")
        print(f"🐢 Slowest: {sorted_results[-1][1]['info']['name']} ({sorted_results[-1][1]['duration']:.2f}s)")
        
        # Compare outputs
        print("\n\n3. OUTPUT DIFFERENCES:")
        print("-"*40)
        
        for wf_type, result in self.results.items():
            if result["success"]:
                print(f"\n{result['info']['name']}:")
                files = result.get("files_generated", [])
                unique_files = [f for f in files if not any(f in self.results[other]["files_generated"] 
                                                           for other in self.results if other != wf_type)]
                if unique_files:
                    print(f"   Unique files: {', '.join(unique_files[:3])}")
                else:
                    print("   No unique files")
                    
        # Recommendations
        print("\n\n📚 WORKFLOW RECOMMENDATIONS:")
        print("="*80)
        
        print("\n✅ Use TDD when:")
        print("   • Testing is critical")
        print("   • Working on algorithms or data processing")
        print("   • Refactoring existing code")
        
        print("\n✅ Use Full when:")
        print("   • Building complex systems")
        print("   • Architecture is important")
        print("   • Working with a team")
        
        print("\n✅ Use MVP Incremental when:")
        print("   • Requirements may change")
        print("   • Building large applications")
        print("   • Need continuous validation")
        
        # Save comparison results
        self._save_comparison_results()
        
    def _save_comparison_results(self) -> None:
        """Save comparison results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/workflow_comparisons")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for JSON
        comparison_data = {
            "timestamp": datetime.now().isoformat(),
            "workflows_compared": list(self.results.keys()),
            "results": {}
        }
        
        for wf_type, result in self.results.items():
            comparison_data["results"][wf_type] = {
                "name": result["info"]["name"],
                "duration": result["duration"],
                "success": result["success"],
                "files_generated": result.get("files_generated", []),
                "error": result.get("error", None)
            }
            
        output_file = output_dir / f"comparison_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
            
        print(f"\n💾 Comparison results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare different workflows with the same requirements"
    )
    parser.add_argument(
        "requirements",
        nargs="?",
        default=None,
        help="Custom requirements to use for comparison (optional)"
    )
    
    args = parser.parse_args()
    
    comparator = WorkflowComparator()
    asyncio.run(comparator.compare_workflows(args.requirements))


if __name__ == "__main__":
    main()