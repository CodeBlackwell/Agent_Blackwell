#!/usr/bin/env python3
"""Debug API test to see what's happening"""

import asyncio
import aiohttp
import json


async def test_api():
    """Test the API and debug errors"""
    base_url = "http://localhost:8100"
    
    async with aiohttp.ClientSession() as session:
        # Start workflow
        print("Starting workflow...")
        async with session.post(
            f"{base_url}/tdd/start",
            json={
                "requirements": "Create a function that returns 'Hello, World!'",
                "config_type": "quick"
            }
        ) as response:
            data = await response.json()
            session_id = data["session_id"]
            print(f"Started workflow: {session_id}")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Check status
        print("\nChecking status...")
        async with session.get(f"{base_url}/tdd/status/{session_id}") as response:
            status = await response.json()
            print(f"Status: {json.dumps(status, indent=2)}")
        
        # Get output
        print("\nGetting output stream...")
        async with session.get(f"{base_url}/tdd/stream/{session_id}") as response:
            # Read first few lines
            count = 0
            async for line in response.content:
                if line and count < 10:
                    try:
                        event = json.loads(line.decode())
                        print(f"Event: {event.get('text', '')[:100]}")
                        count += 1
                    except:
                        pass


if __name__ == "__main__":
    asyncio.run(test_api())