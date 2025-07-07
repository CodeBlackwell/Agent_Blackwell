#!/usr/bin/env python3
"""
🚀 QUICKSTART - Multi-Agent Coding System

This is a simple example script to get you started with the multi-agent coding system.
It automatically starts the orchestrator and executes your chosen workflow.

Usage:
    python quickstart.py                    # Interactive mode (prompts for input)
    python quickstart.py --tdd              # Use TDD workflow (recommended)
    python quickstart.py --full             # Use Full workflow
    python quickstart.py --plan             # Planning only
    python quickstart.py --design           # Design only
    python quickstart.py --implement        # Implementation only

Examples:
    python quickstart.py --tdd --task "Create a calculator with add and subtract functions"
    python quickstart.py --full --task "Build a simple todo list API"
    python quickstart.py --plan --task "Design a weather app architecture"
"""

import asyncio
import argparse
import subprocess
import time
import sys
import os
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.orchestrator_agent import create_orchestrator_tool
from shared.data_models import CodingTeamInput, TeamMember
from mcp import StdioServerTransport


# Default task if none provided
DEFAULT_TASK = "Create a simple Python function that calculates the factorial of a number, with tests"

# Workflow descriptions
WORKFLOW_INFO = {
    "tdd": {
        "name": "Test-Driven Development (TDD)",
        "description": "Planning → Design → Test Writing → Implementation → Execution → Review",
        "team": [TeamMember.planner, TeamMember.designer, TeamMember.test_writer, 
                TeamMember.coder, TeamMember.executor, TeamMember.reviewer],
        "best_for": "Projects where you want tests written before code"
    },
    "full": {
        "name": "Full Workflow", 
        "description": "Planning → Design → Implementation → Review",
        "team": [TeamMember.planner, TeamMember.designer, TeamMember.coder, 
                TeamMember.executor, TeamMember.reviewer],
        "best_for": "Complete projects without test-first approach"
    },
    "plan": {
        "name": "Planning Only",
        "description": "Just the planning phase",
        "team": [TeamMember.planner],
        "workflow_type": "individual",
        "step_type": "planning",
        "best_for": "When you need help planning your approach"
    },
    "design": {
        "name": "Design Only",
        "description": "Just the design phase",
        "team": [TeamMember.designer],
        "workflow_type": "individual", 
        "step_type": "design",
        "best_for": "When you need help with architecture and design"
    },
    "implement": {
        "name": "Implementation Only",
        "description": "Just the coding phase",
        "team": [TeamMember.coder],
        "workflow_type": "individual",
        "step_type": "implementation", 
        "best_for": "When you just need code written"
    }
}


def print_banner():
    """Print a nice banner"""
    print("\n" + "="*60)
    print("🤖 MULTI-AGENT CODING SYSTEM - QUICKSTART")
    print("="*60 + "\n")


def get_user_input() -> tuple[str, str]:
    """Get workflow and task from user interactively"""
    print("Available workflows:")
    print("-" * 40)
    for key, info in WORKFLOW_INFO.items():
        print(f"  {key:<10} - {info['name']}")
        print(f"               {info['best_for']}")
    print()
    
    # Get workflow choice
    while True:
        workflow = input("Choose workflow (tdd/full/plan/design/implement) [tdd]: ").strip().lower()
        if not workflow:
            workflow = "tdd"
        if workflow in WORKFLOW_INFO:
            break
        print("❌ Invalid choice. Please try again.")
    
    print(f"\n✅ Selected: {WORKFLOW_INFO[workflow]['name']}")
    print(f"   {WORKFLOW_INFO[workflow]['description']}")
    
    # Get task
    print("\n" + "-" * 40)
    print("Enter your task/requirements:")
    print(f"(Press Enter for default: '{DEFAULT_TASK[:50]}...')")
    task = input("\n> ").strip()
    if not task:
        task = DEFAULT_TASK
    
    return workflow, task


async def check_orchestrator_health() -> bool:
    """Check if orchestrator is running"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/health", timeout=2) as response:
                return response.status == 200
    except:
        return False


async def start_orchestrator():
    """Start the orchestrator in the background"""
    print("🚀 Starting orchestrator server...")
    
    # Check if already running
    if await check_orchestrator_health():
        print("✅ Orchestrator is already running!")
        return None
    
    # Start orchestrator as a subprocess
    process = subprocess.Popen(
        [sys.executable, "orchestrator/orchestrator_agent.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for it to start
    for i in range(10):
        await asyncio.sleep(1)
        if await check_orchestrator_health():
            print("✅ Orchestrator started successfully!")
            return process
        print(".", end="", flush=True)
    
    print("\n❌ Failed to start orchestrator")
    process.terminate()
    return None


async def run_workflow(workflow: str, task: str):
    """Execute the chosen workflow"""
    print(f"\n🎯 Executing {WORKFLOW_INFO[workflow]['name']}")
    print(f"📋 Task: {task}")
    print("-" * 60)
    
    # Prepare input
    workflow_type = WORKFLOW_INFO[workflow].get("workflow_type", workflow)
    step_type = WORKFLOW_INFO[workflow].get("step_type", None)
    
    input_data = CodingTeamInput(
        requirements=task,
        workflow_type=workflow_type,
        team_members=WORKFLOW_INFO[workflow]["team"],
        step_type=step_type
    )
    
    # Create and run the orchestrator tool
    tool = create_orchestrator_tool()
    
    try:
        # Execute the workflow
        result = await tool.run(input_data)
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Display key results
        if hasattr(result, 'session_id'):
            print(f"\n📁 Generated code location:")
            print(f"   ./generated/{result.session_id}_*/")
        
        print(f"\n📊 Summary:")
        print(f"   • Workflow: {workflow}")
        print(f"   • Agents used: {len(WORKFLOW_INFO[workflow]['team'])}")
        
        # Show where to find outputs
        print(f"\n📄 For detailed results, check:")
        print(f"   • Progress report: Displayed above")
        print(f"   • Generated code: ./generated/*/")
        print(f"   • Execution logs: ./logs/")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Coding System - Quickstart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Workflow options
    parser.add_argument("--tdd", action="store_true", help="Use TDD workflow")
    parser.add_argument("--full", action="store_true", help="Use Full workflow")
    parser.add_argument("--plan", action="store_true", help="Planning only")
    parser.add_argument("--design", action="store_true", help="Design only")
    parser.add_argument("--implement", action="store_true", help="Implementation only")
    
    # Task option
    parser.add_argument("--task", type=str, help="The task/requirements to execute")
    
    # Parse arguments
    args = parser.parse_args()
    
    print_banner()
    
    # Determine workflow and task
    workflow = None
    if args.tdd:
        workflow = "tdd"
    elif args.full:
        workflow = "full"
    elif args.plan:
        workflow = "plan"
    elif args.design:
        workflow = "design"
    elif args.implement:
        workflow = "implement"
    
    # Get task
    task = args.task
    
    # If no command line args, use interactive mode
    if not workflow or not task:
        if workflow and not task:
            print(f"Selected workflow: {WORKFLOW_INFO[workflow]['name']}")
            task = input("\nEnter your task: ").strip() or DEFAULT_TASK
        else:
            workflow, task = get_user_input()
    
    # Start orchestrator
    orchestrator_process = await start_orchestrator()
    
    try:
        # Run the workflow
        await run_workflow(workflow, task)
    finally:
        # Clean up
        if orchestrator_process:
            print("\n🛑 Stopping orchestrator...")
            orchestrator_process.terminate()
            orchestrator_process.wait()
    
    print("\n✨ Done! Thank you for using the Multi-Agent Coding System.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)