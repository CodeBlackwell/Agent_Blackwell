#!/usr/bin/env python3
"""Test the Flagship TDD orchestrator with custom requirements"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from Flagship.flagship_orchestrator import FlagshipOrchestrator
from Flagship.configs.flagship_config import get_config


async def test_custom_requirement():
    """Test with a custom requirement"""
    
    # Define your own requirements here
    requirements = """
    Create a function called 'reverse_string' that:
    - Takes a string as input
    - Returns the string reversed
    - Handles empty strings
    - Preserves spaces and special characters
    """
    
    # Choose configuration
    config = get_config("quick")  # or "default", "comprehensive"
    
    # Create orchestrator
    orchestrator = FlagshipOrchestrator(config)
    
    print("🚀 Testing Custom Requirement")
    print("=" * 80)
    
    try:
        # Run the TDD workflow
        state = await orchestrator.run_tdd_workflow(requirements)
        
        # Save the results
        orchestrator.save_workflow_state()
        
        print("\n✅ Workflow completed!")
        print(f"Check the generated files in: {config.code_directory}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_custom_requirement())