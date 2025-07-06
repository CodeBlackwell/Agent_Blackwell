#!/usr/bin/env python3
"""
👋 HELLO AGENTS - The simplest possible example

This is the absolute minimal example to test the multi-agent system.
It will create a simple "Hello World" program using the TDD workflow.

Prerequisites:
1. Make sure you have the orchestrator running:
   python orchestrator/orchestrator_agent.py

2. Run this script:
   python hello_agents.py
"""

import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput, TeamMember


async def main():
    print("👋 Hello! Let's create a simple program using AI agents!\n")
    
    # Define our simple task
    task = "Create a Python function that prints 'Hello from the AI agents!' and include a test for it"
    
    # Create the input for our agents
    input_data = CodingTeamInput(
        requirements=task,
        workflow_type="tdd",  # Use Test-Driven Development
        team_members=[
            TeamMember.planner,    # Plans the approach
            TeamMember.designer,   # Designs the architecture
            TeamMember.test_writer,# Writes tests first (TDD)
            TeamMember.coder,      # Implements the code
            TeamMember.executor,   # Runs the code
            TeamMember.reviewer    # Reviews everything
        ]
    )
    
    print(f"🎯 Task: {task}")
    print(f"👥 Agents working: {len(input_data.team_members)}")
    print("\n🚀 Starting...\n")
    
    try:
        # Run the workflow
        results, report = await execute_workflow(input_data)
        
        print("\n✅ Success! The agents have completed your task.")
        print(f"⏱️  Time taken: {report.total_duration_seconds:.1f} seconds")
        print(f"\n📁 Check the './generated/' folder for your new code!")
        
    except Exception as e:
        print(f"\n❌ Oops! Something went wrong: {e}")
        print("\n💡 Tip: Make sure the orchestrator is running first:")
        print("   python orchestrator/orchestrator_agent.py")


if __name__ == "__main__":
    asyncio.run(main())