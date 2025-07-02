#!/usr/bin/env python3
"""Quick test for server integration of test_writer_agent_wrapper"""

import asyncio
import os
from dotenv import load_dotenv
from acp_sdk import Message, MessagePart
from acp_sdk.client import Client

# Load environment variables
load_dotenv()

async def test_server():
    """Test server connection to test_writer_agent_wrapper"""
    print("Testing server connection to test_writer_agent_wrapper...")
    
    try:
        # Create ACP client
        async with Client(base_url="http://localhost:8080") as client:
            print("✅ Connected to server")
            
            # Create test input
            message = Message(parts=[MessagePart(content="Write a simple test for a login feature")])
            
            # Call the agent
            print("Calling test_writer_agent_wrapper...")
            try:
                response = await client.run_sync(
                    agent="test_writer_agent_wrapper",
                    input=[message]
                )
                
                print("✅ Agent call successful!")
                print(f"\nAgent response:\n{response.output[0].parts[0].content[:500]}...\n(truncated)")
                return True
            except Exception as agent_error:
                print(f"❌ Error calling agent: {agent_error}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_server())
