#!/usr/bin/env python3
"""
🚀 SIMPLE EXAMPLE - Multi-Agent Coding System

This is the simplest way to use the multi-agent coding system.
Make sure the orchestrator is running first:
    python orchestrator/orchestrator_agent.py

Then run this script:
    python simple_example.py

You can also specify parameters:
    python simple_example.py --workflow tdd --task "Create a calculator"
    python simple_example.py --workflow full --task "Build a REST API"
    python simple_example.py --workflow plan --task "Design a chat system"
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput, TeamMember


# Example tasks for different workflows
EXAMPLE_TASKS = {
    "tdd": "Create a Python class for a bank account with deposit, withdraw, and balance methods",
    "full": "Build a simple REST API for a todo list with CRUD operations",
    "plan": "Design an architecture for a real-time chat application",
    "design": "Create the database schema for an e-commerce platform",
    "implement": "Write a function to validate email addresses using regex"
}


async def run_example(workflow_type: str = "tdd", task: str = None):
    """
    Run a simple example workflow
    
    Args:
        workflow_type: One of 'tdd', 'full', 'plan', 'design', 'implement'
        task: The coding task to accomplish
    """
    # Use default task if none provided
    if not task:
        task = EXAMPLE_TASKS.get(workflow_type, EXAMPLE_TASKS["tdd"])
    
    print("="*60)
    print("🤖 MULTI-AGENT CODING SYSTEM - SIMPLE EXAMPLE")
    print("="*60)
    print(f"\n📋 Task: {task}")
    print(f"🔄 Workflow: {workflow_type}")
    print("-"*60)
    
    # Configure the team based on workflow
    if workflow_type == "tdd":
        # Test-Driven Development: Full team with test writer
        team_members = [
            TeamMember.planner,
            TeamMember.designer, 
            TeamMember.test_writer,
            TeamMember.coder,
            TeamMember.executor,
            TeamMember.reviewer
        ]
        workflow = "tdd"
        step_type = None
    elif workflow_type == "full":
        # Full workflow: Complete team without test writer
        team_members = [
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.executor,
            TeamMember.reviewer
        ]
        workflow = "full"
        step_type = None
    elif workflow_type == "plan":
        # Planning only
        team_members = [TeamMember.planner]
        workflow = "individual"
        step_type = "planning"
    elif workflow_type == "design":
        # Design only
        team_members = [TeamMember.designer]
        workflow = "individual"
        step_type = "design"
    elif workflow_type == "implement":
        # Implementation only
        team_members = [TeamMember.coder]
        workflow = "individual"
        step_type = "implementation"
    else:
        print(f"❌ Unknown workflow: {workflow_type}")
        print("   Valid options: tdd, full, plan, design, implement")
        return
    
    # Create input
    input_data = CodingTeamInput(
        requirements=task,
        workflow_type=workflow,
        step_type=step_type,
        team_members=team_members
    )
    
    print(f"\n👥 Team members: {[member.value for member in team_members]}")
    print("\n🚀 Starting workflow...\n")
    
    try:
        # Execute the workflow
        results, execution_report = await execute_workflow(input_data)
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETED!")
        print("="*60)
        
        # Show summary
        print(f"\n📊 Execution Summary:")
        print(f"   • Total steps: {execution_report.step_count}")
        print(f"   • Completed steps: {execution_report.completed_steps}")
        print(f"   • Duration: {execution_report.total_duration_seconds:.2f} seconds")
        
        # Show proof of execution if available
        if execution_report.proof_of_execution_path:
            print(f"\n🔐 Proof of Execution:")
            print(f"   • Document: {execution_report.proof_of_execution_path}")
            print(f"   • Verified: {'✅ Yes' if execution_report.proof_of_execution_data else '❌ No'}")
        
        # Show where to find generated code
        print(f"\n📁 Generated Files:")
        print(f"   Check the ./generated/ directory for your code")
        
        # Show sample output from each agent
        print(f"\n📝 Agent Outputs (preview):")
        for result in results[:3]:  # Show first 3 agents
            print(f"\n{result.name.upper()}:")
            preview = result.output[:200] + "..." if len(result.output) > 200 else result.output
            print(f"{preview}")
        
        if len(results) > 3:
            print(f"\n... and {len(results) - 3} more agents")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Make sure the orchestrator is running:")
        print("   python orchestrator/orchestrator_agent.py")


def main():
    """Main entry point with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Simple example of the Multi-Agent Coding System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_example.py
  python simple_example.py --workflow full
  python simple_example.py --task "Create a password generator"
  python simple_example.py --workflow tdd --task "Build a calculator class"
        """
    )
    
    parser.add_argument(
        "--workflow",
        choices=["tdd", "full", "plan", "design", "implement"],
        default="tdd",
        help="Workflow type to use (default: tdd)"
    )
    
    parser.add_argument(
        "--task",
        type=str,
        help="The coding task to accomplish"
    )
    
    args = parser.parse_args()
    
    # Run the example
    asyncio.run(run_example(args.workflow, args.task))
    
    print("\n✨ Example complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)