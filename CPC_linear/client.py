import asyncio
import sys
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

# Import configuration
from config import CLIENT_CONFIG

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py 'your code description'")
        return
        
    code_description = sys.argv[1]
    print(f"Generating code for: {code_description}")
    
    # Step 1: Call planner agent
    async with Client(base_url=CLIENT_CONFIG["planner_url"]) as planner_client:
        print("Calling planner agent...")
        planner_response = await planner_client.run_sync(
            agent="planner",
            input=[Message(parts=[MessagePart(content=code_description)])],
        )
        
        plan = planner_response.output[0].parts[0].content
        print("\n=== PLAN ===")
        print(plan)
    
    # Step 2: Call coder agent with plan
    async with Client(base_url=CLIENT_CONFIG["coder_url"]) as coder_client:
        print("\nCalling coder agent...")
        coder_response = await coder_client.run_sync(
            agent="coder",
            input=[Message(parts=[MessagePart(content=plan)])],
        )
        
        code = coder_response.output[0].parts[0].content
        print("\n=== CODE ===")
        print(code)

if __name__ == "__main__":
    asyncio.run(main())
