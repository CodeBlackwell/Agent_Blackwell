#!/usr/bin/env python3
"""
ACP SDK Test Client

An improved client for testing and debugging ACP SDK agent servers with proper
error handling, endpoint validation, and both streaming and sync client options.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

# Load environment variables
load_dotenv()

# Agent server configurations
AGENT_CONFIGS = {
    "planning": {
        "port": 8001,
        "name": "planner",
        "sample_request": "Create a web application with user authentication, REST API, and database integration"
    },
    "orchestrator": {
        "port": 8002,
        "name": "orchestrator", 
        "sample_request": None  # Uses structured job plan
    }
}

async def test_agent_sync(agent_type: str, custom_request: Optional[str] = None) -> None:
    """Test an agent using the synchronous client API (cleaner output for debugging)"""
    
    config = AGENT_CONFIGS.get(agent_type)
    if not config:
        print(f"Error: Unknown agent type '{agent_type}'. Available types: {', '.join(AGENT_CONFIGS.keys())}")
        return
    
    print(f"\n===== TESTING {agent_type.upper()} AGENT (SYNC) =====\n")
    
    # Determine the request content
    if custom_request:
        request_content = custom_request
    elif config["sample_request"]:
        request_content = config["sample_request"]
    else:
        # For orchestrator, use a sample job plan
        request_content = json.dumps({
            "title": "Web Application with Authentication",
            "description": "Create a web application with user authentication, REST API, and database integration",
            "features": [
                {
                    "name": "User Authentication",
                    "priority": "high",
                    "description": "Implement secure login/signup functionality"
                }
            ]
        })
    
    print(f"Sending request to {agent_type.capitalize()} Agent:\n'{request_content}'\n")
    
    base_url = f"http://localhost:{config['port']}"
    agent_name = config["name"]
    
    try:
        async with Client(base_url=base_url) as client:
            run = await client.run_sync(
                agent=agent_name,
                input=[Message(parts=[MessagePart(content=request_content)])]
            )
            
            if run.output:
                print(f"\nResponse from {agent_type.capitalize()} Agent:")
                print("-" * 50)
                print(run.output[0].parts[0].content)
            else:
                print(f"\nNo content in response from {agent_type.capitalize()} Agent")
    
    except Exception as e:
        print(f"\nError connecting to {agent_type.capitalize()} Agent: {str(e)}")
        print(f"\nDebug information:")
        print(f"- Server URL: {base_url}")
        print(f"- Agent name: {agent_name}")
        print(f"- Expected endpoint: {base_url}/api/v1/agents/{agent_name}/run")
        
        # Display common ACP SDK debugging tips
        print("\nCommon issues:")
        print("1. Is the agent server running?")
        print(f"2. Does the agent name '{agent_name}' match the function name in the agent file?")
        print("3. Is the server.run() call in the same file as the agent definition?")
        print("4. Are all required LLM configuration parameters provided?")
        
        import traceback
        traceback.print_exc()

async def test_agent_stream(agent_type: str, custom_request: Optional[str] = None) -> None:
    """Test an agent using the streaming client API (shows incremental outputs)"""
    
    config = AGENT_CONFIGS.get(agent_type)
    if not config:
        print(f"Error: Unknown agent type '{agent_type}'. Available types: {', '.join(AGENT_CONFIGS.keys())}")
        return
    
    print(f"\n===== TESTING {agent_type.upper()} AGENT (STREAM) =====\n")
    
    # Determine the request content
    if custom_request:
        request_content = custom_request
    elif config["sample_request"]:
        request_content = config["sample_request"]
    else:
        # For orchestrator, use a sample job plan
        request_content = json.dumps({
            "title": "Web Application with Authentication",
            "description": "Create a web application with user authentication, REST API, and database integration",
            "features": [
                {
                    "name": "User Authentication",
                    "priority": "high",
                    "description": "Implement secure login/signup functionality"
                }
            ]
        })
    
    print(f"Sending request to {agent_type.capitalize()} Agent:\n'{request_content}'\n")
    print(f"Streaming responses from {agent_type.capitalize()} Agent:")
    print("-" * 50)
    
    base_url = f"http://localhost:{config['port']}"
    agent_name = config["name"]
    
    try:
        async with Client(base_url=base_url) as client:
            async for event in client.run_stream(
                agent=agent_name,
                input=[Message(parts=[MessagePart(content=request_content)])]
            ):
                if hasattr(event, "content"):
                    print(event.content, end="", flush=True)
                else:
                    # Show event type for debugging
                    print(f"\n[Event: {event.type}]", end="", flush=True)
    
    except Exception as e:
        print(f"\nError connecting to {agent_type.capitalize()} Agent: {str(e)}")
        print(f"\nDebug information:")
        print(f"- Server URL: {base_url}")
        print(f"- Agent name: {agent_name}")
        print(f"- Expected endpoint: {base_url}/api/v1/agents/{agent_name}/run")
        
        # Display common ACP SDK debugging tips
        print("\nCommon issues:")
        print("1. Is the agent server running?")
        print(f"2. Does the agent name '{agent_name}' match the function name in the agent file?")
        print("3. Is the server.run() call in the same file as the agent definition?")
        print("4. Are all required LLM configuration parameters provided?")
        
        import traceback
        traceback.print_exc()

async def main():
    """Main function to run the test client"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ACP SDK agent servers")
    parser.add_argument("agent", choices=["planning", "orchestrator"], 
                        help="The agent to test")
    parser.add_argument("--sync", action="store_true", 
                        help="Use synchronous client instead of streaming")
    parser.add_argument("--request", type=str, 
                        help="Custom request to send to the agent")
    
    args = parser.parse_args()
    
    try:
        if args.sync:
            await test_agent_sync(args.agent, args.request)
        else:
            await test_agent_stream(args.agent, args.request)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure the agent servers are running and properly configured.")
        print("Check that your virtual environment is activated and all dependencies are installed.")

if __name__ == "__main__":
    asyncio.run(main())