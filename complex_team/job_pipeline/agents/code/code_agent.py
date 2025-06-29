"""
Code Agent that implements code generation and file operations.

Based on ACP MCP integration patterns from ACPxMCP.py and smolagents integration.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Dict, List, Any

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server, RunYield, RunYieldResume
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.backend import UserMessage
from mcp import StdioServerParameters

import sys
import os
# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import LLM_CONFIG, BEEAI_CONFIG, MCP_CONFIG, PROMPT_TEMPLATES

server = Server()

@server.agent()
async def code_agent(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Code Agent that generates and manages code files using MCP tools.
    
    This agent implements code generation, file operations, and Git integration
    through MCP (Model Context Protocol) servers.
    """
    try:
        # Extract the coding request
        if not inputs or not inputs[0].parts:
            yield MessagePart(content="Error: No coding request provided")
            return
            
        coding_request = inputs[0].parts[0].content
        
        # Yield initial processing message
        yield MessagePart(content="💻 Starting code generation and file operations...")
        
        # Initialize LLM for code generation
        llm = ChatModel.from_name(LLM_CONFIG["model_id"])
        memory = TokenMemory(llm)
        
        # Setup MCP server for file operations
        filesystem_server_params = StdioServerParameters(
            command=MCP_CONFIG["filesystem_server"]["command"],
            args=MCP_CONFIG["filesystem_server"]["args"],
            env=MCP_CONFIG["filesystem_server"]["env"],
        )
        
        # Setup MCP server for Git operations
        git_server_params = StdioServerParameters(
            command=MCP_CONFIG["git_server"]["command"],
            args=MCP_CONFIG["git_server"]["args"], 
            env=MCP_CONFIG["git_server"]["env"],
        )
        
        # Create agent with MCP tools (following ACPxMCP pattern)
        from smolagents import ToolCallingAgent, ToolCollection
        
        # Combine multiple MCP tool collections
        with ToolCollection.from_mcp(filesystem_server_params, trust_remote_code=True) as fs_tools, \
             ToolCollection.from_mcp(git_server_params, trust_remote_code=True) as git_tools:
            
            # Combine all tools
            all_tools = [*fs_tools.tools, *git_tools.tools]
            
            # Create ReAct agent with combined tools
            agent = ReActAgent(
                llm=llm,
                tools=all_tools,
                templates={
                    "system": lambda template: template.update(
                        defaults={
                            "instructions": PROMPT_TEMPLATES.get("code", {}).get("system", "You are a code generation agent."),
                            "role": "system",
                        }
                    )
                },
                memory=memory,
            )
            
            # Add coding request to memory
            await memory.add(UserMessage(coding_request))
            
            # Generate code and perform file operations
            yield MessagePart(content="🔧 Generating code with tool integration...")
            
            response = await agent.run()
            
            # Yield the code generation result
            yield MessagePart(content=f"✅ Code generation completed:\n\n{response.result.text}")
        
    except Exception as e:
        yield MessagePart(content=f"❌ Error in code generation: {str(e)}")

# Alternative implementation using BeeAI Framework directly
@server.agent()
async def simple_code_agent(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Simplified code agent using BeeAI Framework without MCP tools.
    
    This is a fallback implementation that works without external MCP servers.
    """
    try:
        if not inputs or not inputs[0].parts:
            yield MessagePart(content="Error: No coding request provided")
            return
            
        coding_request = inputs[0].parts[0].content
        
        yield MessagePart(content="💻 Generating code using LLM...")
        
        # Simple BeeAI Framework integration
        llm = ChatModel.from_name(LLM_CONFIG["model_id"])
        memory = TokenMemory(llm)
        
        agent = ReActAgent(
            llm=llm,
            tools=[],  # No external tools in simple version
            templates={
                "system": lambda template: template.update(
                    defaults={
                        "instructions": """You are a code generation agent. Generate clean, well-documented code based on user requests. 
                        Include appropriate imports, error handling, and follow best practices for the requested language.""",
                        "role": "system",
                    }
                )
            },
            memory=memory,
        )
        
        await memory.add(UserMessage(coding_request))
        response = await agent.run()
        
        yield MessagePart(content=f"✅ Code generated successfully:\n\n```\n{response.result.text}\n```")
        
    except Exception as e:
        yield MessagePart(content=f"❌ Error generating code: {str(e)}")

# Add server runner for standalone execution
if __name__ == "__main__":
    from config.config import AGENT_PORTS
    print(f"Starting Code Agent on port {AGENT_PORTS['code']}...")
    server.run(port=AGENT_PORTS["code"])
