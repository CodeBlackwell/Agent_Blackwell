#!/usr/bin/env python3
"""Simple test to debug the workflow"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flagship_orchestrator import FlagshipOrchestrator

async def test_simple():
    print("Testing simple workflow execution...")
    try:
        orchestrator = FlagshipOrchestrator()
        state = await orchestrator.run_tdd_workflow("Create a greeting function")
        print(f"Workflow completed: {state.all_tests_passing}")
        orchestrator.save_workflow_state()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())