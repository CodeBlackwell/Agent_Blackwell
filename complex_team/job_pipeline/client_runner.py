#!/usr/bin/env python3
"""
ACP SDK Test Client

An improved client for testing and debugging ACP SDK agent servers with proper
error handling, endpoint validation, and both streaming and sync client options.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

from config.config import AGENT_PORTS

# Load environment variables
load_dotenv()

# Agent configurations
AGENT_CONFIGS = {
    "planner": {
        "name": "planner",
        "port": AGENT_PORTS["planner"],
        "sample_request": "Create a web application with user authentication, REST API, and database integration"
    },
    "orchestrator": {
        "name": "orchestrator",
        "port": AGENT_PORTS["orchestrator"],
        "sample_request": "Create a web application with user authentication, REST API, and database integration" # Will use a job plan from the planning agent
    },
    "code": {
        "name": "simple_code_agent",  # Match the actual function name in code_agent.py
        "port": AGENT_PORTS["code"],
        "sample_request": "Create a React login component with form validation and API integration"
    }
}

async def test_agent_sync(agent_type: str, custom_request: Optional[str] = None) -> None:
    """Test an agent using the synchronous client API (no streaming)"""
    
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
            
            print(f"Response from {agent_type.capitalize()} Agent:")
            print("-" * 50)
            
            # Extract and display the message content
            for message in run.output:
                for part in message.parts:
                    print(part.content)
                    
    except Exception as e:
        print(f"\nError connecting to {agent_type.capitalize()} Agent: {str(e)}")
        print(f"\nDebug information:")
        print(f"- Server URL: {base_url}")
        print(f"- Agent name: {agent_name}")

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
                # Extract content from message.part events
                if event.type == "message.part":
                    # Access the content directly from the part attribute
                    if hasattr(event, "part") and hasattr(event.part, "content"):
                        print(event.part.content, end="", flush=True)
                    # Fallback in case structure changes
                    elif hasattr(event, "data") and hasattr(event.data, "content"):
                        print(event.data.content, end="", flush=True)
                # Show minimal event info for other event types (can be turned off in production)
                else:
                    print(f"\n[Event: {event.type}]", flush=True)
            
            print("\n\n✅ Agent run completed")
    
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

async def main():
    """Main function to parse arguments and run the appropriate test"""
    
    if len(sys.argv) < 2:
        print("Usage: python client_runner.py <agent_type> [custom_request] [--sync]")
        print("\nAvailable agent types:")
        for agent_type, config in AGENT_CONFIGS.items():
            print(f"  - {agent_type} (port {config['port']}, agent name '{config['name']}')")
        return
    
    agent_type = sys.argv[1]
    
    # Check for sync flag
    use_sync = "--sync" in sys.argv
    if use_sync:
        sys.argv.remove("--sync")
    
    # Check for custom request (everything after agent_type but before --sync)
    custom_request = None
    if len(sys.argv) > 2:
        custom_request = sys.argv[2]
    
    if use_sync:
        await test_agent_sync(agent_type, custom_request)
    else:
        await test_agent_stream(agent_type, custom_request)

if __name__ == "__main__":
    asyncio.run(main())