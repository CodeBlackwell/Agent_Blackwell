#!/usr/bin/env python3
"""Debug test for reviewer agent import and functionality"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to path for proper imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test imports
print("Testing imports...")
try:
    from dotenv import load_dotenv
    print("✅ dotenv imported successfully")
    
    load_dotenv()
    print("✅ Environment variables loaded")
    
    from agents.reviewer.reviewer_agent import reviewer_agent
    print("✅ reviewer_agent imported successfully")
    
    from acp_sdk import Message, MessagePart
    print("✅ ACP types imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_reviewer_agent_direct():
    """Test calling the reviewer agent directly"""
    print("\n--- Testing Reviewer Agent Direct Call ---")
    
    try:
        # Create test input
        test_input = [Message(parts=[MessagePart(content="""
        Review this code:
        ```python
        def calculate_total(items):
            total = 0
            for item in items:
                total += item['price']
            return total
        ```
        """)])]
        
        print(f"Input: {test_input}")
        
        # Call reviewer agent directly
        print("Calling reviewer_agent...")
        response_parts = []
        async for part in reviewer_agent(test_input):
            response_parts.append(part)
            print(f"Received part: {part}")
        
        print(f"✅ Direct call successful! Received {len(response_parts)} parts")
        return True
        
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_connection():
    """Test connecting to orchestrator server"""
    print("\n--- Testing Server Connection ---")
    
    try:
        from acp_sdk.client import Client
        
        async with Client(base_url="http://localhost:8080") as client:
            # Create test input
            message = Message(parts=[MessagePart(content="""
            Review this code:
            ```python
            def calculate_total(items):
                total = 0
                for item in items:
                    total += item['price']
                return total
            ```
            """)])
            
            # Call the agent
            print("Calling reviewer_agent_wrapper through server...")
            try:
                response = await client.run_sync(
                    agent="reviewer_agent_wrapper",
                    input=[message]
                )
                
                print("✅ Agent call successful!")
                print(f"\nAgent response preview:\n{response.output[0].parts[0].content[:200]}...\n(truncated)")
                return True
            except Exception as agent_error:
                print(f"❌ Error calling agent: {agent_error}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 50)
    print("REVIEWER AGENT DEBUG TEST")
    print("=" * 50)
    
    # Test 1: Direct function call
    direct_success = await test_reviewer_agent_direct()
    
    # Test 2: Server connection (if direct call works)
    if direct_success:
        server_success = await test_server_connection()
    else:
        print("\n⚠️ Skipping server test due to direct call failure")
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Direct call: {'✅ PASS' if direct_success else '❌ FAIL'}")
    if direct_success:
        print(f"Server integration: {'✅ PASS' if server_success else '❌ FAIL'}")
    
    if not direct_success:
        print("\n💡 RECOMMENDATION:")
        print("Fix the reviewer_agent direct call first before testing server integration")
    elif not server_success:
        print("\n💡 RECOMMENDATION:")
        print("1. Check that orchestrator server is running")
        print("2. Verify that reviewer_agent_wrapper is registered correctly")
        print("3. Make sure agent_name_mapping includes reviewer_agent")
    
    return direct_success and server_success

if __name__ == "__main__":
    asyncio.run(main())
