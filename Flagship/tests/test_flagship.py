#!/usr/bin/env python3
"""Quick test of the Flagship TDD orchestrator"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from Flagship.flagship_orchestrator import FlagshipOrchestrator
from Flagship.configs.flagship_config import get_config


async def test_basic_tdd():
    """Test basic TDD functionality"""
    print("Testing Flagship TDD Orchestrator")
    print("=" * 80)
    
    # Use quick config for testing
    config = get_config("quick")
    config.max_iterations = 1  # Just one iteration for testing
    
    orchestrator = FlagshipOrchestrator(config)
    
    # Simple requirements
    requirements = "Create a function called 'greet' that takes a name and returns 'Hello, {name}!'"
    
    try:
        state = await orchestrator.run_tdd_workflow(requirements)
        
        print("\nTest Results:")
        print(f"- Workflow completed: ✓")
        print(f"- Phases executed: {len(state.phase_results)}")
        print(f"- Tests generated: {len(state.generated_tests) > 0}")
        print(f"- Code generated: {len(state.generated_code) > 0}")
        print(f"- Current phase: {state.current_phase.value}")
        
        return True
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_basic_tdd())
    sys.exit(0 if success else 1)