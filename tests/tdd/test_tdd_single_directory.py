#!/usr/bin/env python3
"""
Test script to verify TDD workflow creates only one directory per run
"""
import asyncio
import sys
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.workflow_config import GENERATED_CODE_PATH


async def test_single_directory_generation():
    """Test that TDD workflow creates only one directory"""
    
    # Simple calculator requirements for testing
    requirements = """
Create a Calculator class with the following methods:
1. add(a, b) - returns sum of two numbers
2. subtract(a, b) - returns difference
3. multiply(a, b) - returns product
4. divide(a, b) - returns quotient, raises ValueError for division by zero

Use strict Test-Driven Development. All methods should handle edge cases.
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
    
    print("🧪 TDD Single Directory Test")
    print("=" * 60)
    print("Testing that TDD workflow creates only ONE directory")
    print("Requirements: Calculator with TDD")
    print("=" * 60)
    
    # Get initial directory count
    generated_path = Path(GENERATED_CODE_PATH)
    if generated_path.exists():
        initial_dirs = set(p.name for p in generated_path.iterdir() if p.is_dir())
        initial_count = len(initial_dirs)
    else:
        initial_dirs = set()
        initial_count = 0
        
    print(f"\n📁 Initial directories in {GENERATED_CODE_PATH}: {initial_count}")
    
    try:
        # Execute workflow
        results, report = await execute_tdd_workflow(input_data)
        
        print("\n✅ Workflow completed!")
        print(f"Total steps: {len(report.steps)}")
        
        # Check new directories created
        if generated_path.exists():
            final_dirs = set(p.name for p in generated_path.iterdir() if p.is_dir())
            new_dirs = final_dirs - initial_dirs
            
            print(f"\n📊 Directory Analysis:")
            print(f"  - Directories before: {initial_count}")
            print(f"  - Directories after: {len(final_dirs)}")
            print(f"  - New directories created: {len(new_dirs)}")
            
            if new_dirs:
                print(f"\n📁 New directories:")
                for dir_name in sorted(new_dirs):
                    dir_path = generated_path / dir_name
                    file_count = len(list(dir_path.rglob('*')))
                    print(f"  - {dir_name} ({file_count} files)")
                    
                    # Check if it's a TDD session directory
                    if 'tdd' in dir_name or 'calculator' in dir_name:
                        print(f"    ✓ TDD session directory")
                        
                        # List some files
                        files = list(dir_path.rglob('*.py'))[:5]
                        if files:
                            print("    Files:")
                            for f in files:
                                print(f"      - {f.relative_to(dir_path)}")
            
            # Check for success
            if len(new_dirs) == 1:
                print("\n✅ SUCCESS: Only ONE directory was created!")
                
                # Check if project_path is in the report
                if hasattr(report, 'final_output') and report.final_output:
                    project_path = report.final_output.get('project_path')
                    if project_path:
                        print(f"📍 Project path from report: {project_path}")
                        
            elif len(new_dirs) == 0:
                print("\n⚠️  WARNING: No new directories were created")
            else:
                print(f"\n❌ FAILURE: {len(new_dirs)} directories were created (expected 1)")
                
        # Check TDD cycle execution
        tdd_cycle_step = None
        for step in report.steps:
            if step.step_name == "tdd_cycle":
                tdd_cycle_step = step
                break
                
        if tdd_cycle_step:
            print("\n📊 TDD Cycle Results:")
            print(f"  - Step status: {tdd_cycle_step.status}")
            if hasattr(tdd_cycle_step, 'output_data') and isinstance(tdd_cycle_step.output_data, dict):
                data = tdd_cycle_step.output_data
                print(f"  - Iterations: {data.get('iterations', 'N/A')}")
                print(f"  - Initial failures: {data.get('initial_failures', 'N/A')}")
                print(f"  - Final passes: {data.get('final_passes', 'N/A')}")
                print(f"  - All tests passing: {data.get('all_tests_passing', 'N/A')}")
                
                # Check iterations - more iterations might mean more directories in old version
                iterations = data.get('iterations', 0)
                if iterations > 1:
                    print(f"\n📝 Note: TDD ran {iterations} iterations but still created only {len(new_dirs)} directory!")
                    
        print("\n✅ Test completed!")
        return len(new_dirs) == 1
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_old_projects():
    """Clean up old test projects"""
    generated_path = Path(GENERATED_CODE_PATH)
    if generated_path.exists():
        # Keep only the 3 most recent projects
        projects = sorted(
            [p for p in generated_path.iterdir() if p.is_dir() and ('calculator' in p.name or 'tdd' in p.name)],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for project in projects[3:]:
            print(f"🗑️  Cleaning up old project: {project.name}")
            shutil.rmtree(project)


if __name__ == "__main__":
    print("TDD Single Directory Generation Test")
    print("This test verifies that the TDD workflow creates only ONE directory per run")
    print("-" * 60)
    
    # Clean up old projects first
    asyncio.run(cleanup_old_projects())
    
    # Check if orchestrator is running
    print("\n⚠️  Note: Make sure the orchestrator is running:")
    print("  python orchestrator/orchestrator_agent.py")
    print("")
    
    # Run the test
    success = asyncio.run(test_single_directory_generation())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)