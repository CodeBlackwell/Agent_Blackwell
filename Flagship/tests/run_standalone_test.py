#!/usr/bin/env python3
"""Standalone test of TDD orchestrator with direct imports"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import without Flagship prefix
from flagship_orchestrator import FlagshipOrchestrator
from configs.flagship_config import QUICK_TEST_CONFIG


async def run_test():
    """Run a simple TDD test"""
    orchestrator = FlagshipOrchestrator(QUICK_TEST_CONFIG)
    
    requirements = "Create a calculator class with add and subtract methods"
    print(f"Testing: {requirements}\n")
    
    try:
        state = await orchestrator.run_tdd_workflow(requirements)
        print(f"\n✅ SUCCESS!")
        print(f"Final phase: {state.current_phase}")
        print(f"All tests passing: {state.all_tests_passing}")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_test())