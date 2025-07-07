#!/usr/bin/env python3
"""
Integration test for the enhanced TDD workflow with file management
Tests the complete flow from test writing through implementation
"""
import asyncio
import sys
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.workflow_config import GENERATED_CODE_PATH


async def test_tdd_integration():
    """Test the complete TDD workflow with integrated file management"""
    
    # Simple string utilities requirements for testing
    requirements = """
Create a StringUtils class with the following methods:
1. reverse(text) - returns reversed string
2. is_palindrome(text) - returns True if text is palindrome
3. count_vowels(text) - returns count of vowels (a,e,i,o,u)
4. capitalize_words(text) - capitalizes first letter of each word

Use strict Test-Driven Development. All methods should handle empty strings.
"""
    
    # Create input
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="TDD",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.test_writer,
            TeamMember.coder,
            TeamMember.reviewer
        ],
        max_retries=3,
        timeout_seconds=600
    )
    
    print("🧪 TDD Integration Test")
    print("=" * 60)
    print("Testing complete TDD flow with file management")
    print("Requirements: String utilities with TDD")
    print("=" * 60)
    
    try:
        # Execute workflow
        results, report = await execute_tdd_workflow(input_data)
        
        print("\n✅ Workflow completed!")
        print(f"Total steps: {len(report.steps)}")
        
        # Check if TDD cycle was executed
        tdd_cycle_step = None
        for step in report.steps:
            if step.step_name == "tdd_cycle":
                tdd_cycle_step = step
                break
                
        if tdd_cycle_step:
            print("\n📊 TDD Cycle Results:")
            # Check the actual structure of the step
            print(f"  - Step name: {tdd_cycle_step.step_name}")
            print(f"  - Status: {tdd_cycle_step.status}")
            if hasattr(tdd_cycle_step, 'output_data') and isinstance(tdd_cycle_step.output_data, dict):
                print(f"  - Success: {tdd_cycle_step.output_data.get('success', 'N/A')}")
                print(f"  - Iterations: {tdd_cycle_step.output_data.get('iterations', 'N/A')}")
                print(f"  - Initial failures: {tdd_cycle_step.output_data.get('initial_failures', 'N/A')}")
                print(f"  - Final passes: {tdd_cycle_step.output_data.get('final_passes', 'N/A')}")
                print(f"  - All tests passing: {tdd_cycle_step.output_data.get('all_tests_passing', 'N/A')}")
            else:
                print("  - No TDD cycle data available (used fallback coding)")
            
        # Check for generated files
        generated_path = Path(GENERATED_CODE_PATH)
        if generated_path.exists():
            projects = list(generated_path.glob("*_generated_*"))
            if projects:
                latest_project = max(projects, key=lambda p: p.stat().st_mtime)
                print(f"\n📁 Generated project: {latest_project}")
                
                # List files in the project
                print("\n📄 Project files:")
                for file_path in latest_project.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith("."):
                        relative = file_path.relative_to(latest_project)
                        print(f"  - {relative}")
                        
                # Check if tests exist and can be run
                test_files = list(latest_project.glob("**/test_*.py"))
                if test_files:
                    print(f"\n🧪 Found {len(test_files)} test file(s)")
                    
                    # Try to run the tests
                    print("\n🏃 Running generated tests...")
                    import subprocess
                    try:
                        result = subprocess.run(
                            ["python", "-m", "pytest", str(latest_project), "-v"],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            print("✅ All tests passed!")
                        else:
                            print(f"❌ Tests failed with code {result.returncode}")
                            if result.stdout:
                                print("STDOUT:", result.stdout[-500:])
                            if result.stderr:
                                print("STDERR:", result.stderr[-500:])
                                
                    except subprocess.TimeoutExpired:
                        print("⏱️  Test execution timed out")
                    except Exception as e:
                        print(f"❌ Error running tests: {e}")
                        
        # Check for failed steps
        failed_steps = [s for s in report.steps if s.status.name == "FAILED"]
        if failed_steps:
            print("\n⚠️  Failed steps:")
            for step in failed_steps:
                print(f"  - {step.step_name}: {step.error if hasattr(step, 'error') else 'Unknown error'}")
                
        print("\n✅ Integration test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_test_projects():
    """Clean up old test projects"""
    generated_path = Path(GENERATED_CODE_PATH)
    if generated_path.exists():
        # Keep only the 5 most recent projects
        projects = sorted(
            generated_path.glob("*_generated_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for project in projects[5:]:
            print(f"🗑️  Cleaning up old project: {project.name}")
            shutil.rmtree(project)


if __name__ == "__main__":
    print("TDD Workflow Integration Test")
    print("This test verifies the complete TDD flow with file management")
    print("-" * 60)
    
    # Clean up old projects first
    asyncio.run(cleanup_test_projects())
    
    # Check if orchestrator is running
    print("\n⚠️  Note: Make sure the orchestrator is running:")
    print("  python orchestrator/orchestrator_agent.py")
    print("")
    
    # Run the test
    success = asyncio.run(test_tdd_integration())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)