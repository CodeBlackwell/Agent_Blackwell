#!/usr/bin/env python3
"""
Test client for interacting with the agent servers.
"""

import asyncio
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

async def test_planning_agent():
    print("\n===== TESTING PLANNING AGENT =====\n")
    
    user_request = "Create a web application with user authentication, REST API, and database integration"
    print(f"Sending request to Planning Agent: \n'{user_request}'\n")
    
    print("Streaming responses from Planning Agent:")
    print("-" * 50)
    
    async with Client(base_url="http://localhost:8001") as client:
        try:
            async for event in client.run_stream(
                agent="planner",
                input=[Message(parts=[MessagePart(content=user_request)])]
            ):
                print(f"type='{event.type}' run={event}")
                if hasattr(event, "content"):
                    print(event.content)
        except Exception as e:
            print(f"Error during planning agent streaming: {e}")

async def test_orchestrator_agent():
    print("\n===== TESTING ORCHESTRATOR AGENT =====\n")
    
    # Sample job plan that would typically come from the planning agent
    job_plan = {
        "title": "Web Application with Authentication",
        "description": "Create a web application with user authentication, REST API, and database integration",
        "features": [
            {
                "name": "User Authentication",
                "priority": "high",
                "description": "Implement secure login/signup functionality"
            }
        ]
    }
    
    print(f"Sending job plan to Orchestrator Agent")
    print("-" * 50)
    
    async with Client(base_url="http://localhost:8002") as client:
        try:
            async for event in client.run_stream(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(content=str(job_plan))])]
            ):
                if hasattr(event, "content"):
                    print(event.content)
        except Exception as e:
            print(f"Error during orchestrator agent streaming: {e}")

async def main():
    try:
        await test_planning_agent()
        # Uncomment to also test the orchestrator
        # await test_orchestrator_agent()
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure both agent servers are running:")
        print("1. Planning Agent on port 8001")
        print("2. Orchestrator Agent on port 8002")
        print("\nCheck that the virtual environment is activated and all dependencies are installed.")

if __name__ == "__main__":
    asyncio.run(main())