#!/usr/bin/env python3
"""Debug test for coder agent import and functionality"""

import asyncio
import sys
import os
from pathlib import Path

# Add the orchestrator directory to path
orchestrator_dir = Path(__file__).parent
sys.path.insert(0, str(orchestrator_dir))

# Test imports
print("Testing imports...")
try:
    from dotenv import load_dotenv
    print("✅ dotenv imported successfully")
    
    load_dotenv()
    print("✅ Environment variables loaded")
    
    from coder_agent import coder_agent
    print("✅ coder_agent imported successfully")
    
    from acp_sdk import Message, MessagePart
    print("✅ ACP types imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_coder_agent_direct():
    """Test calling the coder agent directly"""
    print("\n--- Testing Coder Agent Direct Call ---")
    
    try:
        # Create test input
        test_input = [Message(parts=[MessagePart(content="Create a simple hello world Express.js API")])]
        
        print(f"Input: {test_input}")
        
        # Call coder agent directly
        print("Calling coder_agent...")
        response_parts = []
        async for part in coder_agent(test_input):
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
            # Test if server is running
            run = await client.run_sync(
                agent="coder_agent_wrapper", 
                input=[Message(parts=[MessagePart(content="Test connection - create a simple hello world HTML file")])]
            )
            print(f"✅ Server connection successful! Response: {run.output}")
            return True
            
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 50)
    print("CODER AGENT DEBUG TEST")
    print("=" * 50)
    
    # Test 1: Direct function call
    direct_success = await test_coder_agent_direct()
    
    # Test 2: Server connection (if direct call works)
    if direct_success:
        server_success = await test_server_connection()
    else:
        print("\n⚠️ Skipping server test due to direct call failure")
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Direct call: {'✅ PASS' if direct_success else '❌ FAIL'}")
    
    if not direct_success:
        print("\n💡 RECOMMENDATION:")
        print("Fix the coder_agent direct call first before testing server integration")
    
    return direct_success

if __name__ == "__main__":
    asyncio.run(main())
