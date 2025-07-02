#!/usr/bin/env python3
"""Debug test for test_writer agent import and functionality"""

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
    
    from test_writer_agent import test_writer_agent
    print("✅ test_writer_agent imported successfully")
    
    from acp_sdk import Message, MessagePart
    print("✅ ACP types imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_test_writer_agent_direct():
    """Test calling the test_writer agent directly"""
    print("\n--- Testing Test Writer Agent Direct Call ---")
    
    try:
        # Create test input
        test_input = [Message(parts=[MessagePart(content="Write tests for a Todo API with CRUD operations")])]
        
        print(f"Input: {test_input}")
        
        # Call test_writer agent directly
        print("Calling test_writer_agent...")
        response_parts = []
        async for part in test_writer_agent(test_input):
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
                agent="test_writer_agent_wrapper", 
                input=[Message(parts=[MessagePart(content="Test connection - write tests for a simple login feature")])]
            )
            print(f"✅ Server connection successful! Response: {run.output}")
            return True
            
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 50)
    print("TEST WRITER AGENT DEBUG TEST")
    print("=" * 50)
    
    # Test 1: Direct function call
    direct_success = await test_test_writer_agent_direct()
    
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
        print("Fix the test_writer_agent direct call first before testing server integration")
    
    return direct_success

if __name__ == "__main__":
    asyncio.run(main())
