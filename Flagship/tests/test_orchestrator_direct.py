#!/usr/bin/env python3
"""Direct test of the flagship orchestrator"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Flagship.flagship_orchestrator import FlagshipOrchestrator
from Flagship.configs.flagship_config import DEFAULT_CONFIG


async def test_orchestrator():
    """Test the orchestrator directly"""
    print("Testing Flagship Orchestrator directly...")
    
    try:
        # Create orchestrator
        orchestrator = FlagshipOrchestrator(DEFAULT_CONFIG)
        
        # Run simple workflow
        requirements = "Create a simple calculator with add and subtract functions"
        print(f"\nRequirements: {requirements}")
        
        # Run the workflow
        final_state = await orchestrator.run_tdd_workflow(requirements)
        
        print(f"\nFinal Phase: {final_state.current_phase}")
        print(f"All tests passing: {final_state.all_tests_passing}")
        print(f"Phase history length: {len(final_state.phase_history)}")
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_orchestrator())