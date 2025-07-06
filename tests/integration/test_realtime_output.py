#!/usr/bin/env python3
"""
Test script to demonstrate real-time agent output display.
Run this to see step-by-step agent interactions.
"""

import asyncio
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from acp_sdk import Message
    from acp_sdk.models import MessagePart
    from acp_sdk.client import Client
except ImportError:
    # Skip tests if acp_sdk is not available
    pytestmark = pytest.mark.skip(reason="acp_sdk not available")

@pytest.mark.asyncio
async def test_realtime_output():
    """Test the real-time output display with a simple workflow"""
    
    print("🧪 Testing Real-Time Agent Output Display")
    print("=" * 80)
    print()
    
    # Simple test request
    test_request = """
    Use the TDD workflow to create a simple calculator API with the following endpoints:
    - POST /add - adds two numbers
    - POST /subtract - subtracts two numbers
    - POST /multiply - multiplies two numbers
    - POST /divide - divides two numbers (handle division by zero)
    
    The API should be built with Python and FastAPI.
    """
    
    try:
        # Connect to the orchestrator
        async with Client(base_url="http://localhost:8080") as client:
            print("📡 Connecting to orchestrator...")
            print()
            
            # Run the orchestrator with the test request
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content=test_request,
                    content_type="text/plain"
                )])]
            )
            
            # The real-time output will be displayed during execution
            # Final result is shown here
            print("\n" + "=" * 80)
            print("📊 FINAL ORCHESTRATOR RESPONSE:")
            print("=" * 80)
            if run.output:
                for message in run.output:
                    if hasattr(message, 'parts'):
                        for part in message.parts:
                            print(part.content)
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure the orchestrator is running on port 8080:")
        print("  python orchestrator/orchestrator_agent.py")
        return 1
    
    return 0

@pytest.mark.asyncio
async def test_summary_mode():
    """Test with summary mode for more condensed output"""
    
    print("\n\n🧪 Testing Summary Mode Output")
    print("=" * 80)
    print()
    
    # First, modify the config to use summary mode
    from orchestrator.orchestrator_configs import OUTPUT_DISPLAY_CONFIG
    OUTPUT_DISPLAY_CONFIG["mode"] = "summary"
    
    # Simple test request
    test_request = "Just do planning for a todo list mobile app"
    
    try:
        async with Client(base_url="http://localhost:8080") as client:
            print("📡 Running in summary mode...")
            print()
            
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content=test_request,
                    content_type="text/plain"
                )])]
            )
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Reset to detailed mode
    OUTPUT_DISPLAY_CONFIG["mode"] = "detailed"

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           Real-Time Agent Output Display Test                 ║
╠═══════════════════════════════════════════════════════════════╣
║ This test demonstrates the new step-by-step agent output      ║
║ feature. You'll see each agent's input and output as they     ║
║ execute, rather than just a final summary.                    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the tests
    exit_code = asyncio.run(test_realtime_output())
    
    if exit_code == 0:
        # Also test summary mode
        asyncio.run(test_summary_mode())
    
    sys.exit(exit_code)