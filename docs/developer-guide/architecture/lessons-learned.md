# Anatomy of an ACP SDK Agent

This document outlines the essential structure and patterns for building robust ACP SDK agents based on our development and debugging experience.

## Core Components

### 1. File Structure
```python
"""
Agent description docstring
"""

# 1. Standard imports
import asyncio
from collections.abc import AsyncGenerator
from typing import Dict, List, Any

# 2. ACP SDK imports
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server, RunYield, RunYieldResume

# 3. LLM Framework imports (if applicable)
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.backend import UserMessage

# 4. Project imports
from config.config import AGENT_PORTS, PROMPT_TEMPLATES, BEEAI_CONFIG

# 5. Server instantiation
server = Server()

# 6. Agent definition
@server.agent()
async def agent_name(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Agent function implementation"""
    # Code here...
    
# 7. Helper functions
def helper_function():
    """Helper function documentation"""
    # Code here...

# 8. Server startup (MUST be in the same file as agent definition)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    port = AGENT_PORTS.get("agent_key", 8001)
    print(f"Starting Agent on port {port}...")
    server.run(port=port)
```

### 2. Agent Function Signature

```python
@server.agent()
async def agent_name(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Agent docstring with purpose and description.
    
    This agent does X and handles Y scenarios.
    """
    try:
        # Extract user request from input
        if not inputs or not inputs[0].parts:
            yield MessagePart(content="Error: No input provided")
            return
            
        user_request = inputs[0].parts[0].content
        
        # Yield initial response
        yield MessagePart(content="Processing your request...")
        
        # Process with LLM if applicable
        result = await process_with_llm(user_request)
        
        # Yield final result
        yield MessagePart(content=f"Result: {result}")
    
    except Exception as e:
        yield MessagePart(content=f"Error: {str(e)}")
```

## Critical Best Practices

### 1. Server and Agent Co-Location
**CRITICAL**: The `server.run()` call **MUST** be in the same file as the agent definition with the `@server.agent()` decorator.

❌ **Incorrect Pattern**
- Agent defined in `agent.py`
- Server run in `server.py`

✅ **Correct Pattern**
- Both agent definition and `server.run()` in same file
- Use `if __name__ == "__main__":` to allow imports without starting server

### 2. LLM Integration
For LLM-powered agents using BeeAI Framework:

```python
# Initialize LLM with full configuration
llm = ChatModel.from_name(
    BEEAI_CONFIG["chat_model"]["model"],
    api_base=BEEAI_CONFIG["chat_model"]["base_url"],
    api_key=BEEAI_CONFIG["chat_model"]["api_key"]
)
memory = TokenMemory(llm)

# Create agent with proper memory
agent = ReActAgent(
    llm=llm,
    tools=[],  # Add tools if needed
    templates={
        "system": lambda template: template.update(
            defaults={
                "instructions": PROMPT_TEMPLATES["agent_name"]["system"],
                "role": "system",
            }
        )
    },
    memory=memory,
)

# Add user message to memory using current API
await memory.add(UserMessage(user_request))
```

### 3. Error Handling
Every agent should implement comprehensive error handling:

```python
try:
    # Agent logic here
except Exception as e:
    yield MessagePart(content=f"❌ Error: {str(e)}")
    # Log error for debugging
    import logging
    logging.error(f"Agent error: {str(e)}", exc_info=True)
```

## Message Handling Patterns

### 1. Extracting Input
```python
# Basic text extraction from first message
user_request = inputs[0].parts[0].content

# Handling multiple messages
all_messages = []
for message in inputs:
    for part in message.parts:
        all_messages.append(part.content)
```

### 2. Streaming Response Pattern
```python
# Initial acknowledgment
yield MessagePart(content="Starting processing...")

# Progress updates
for step in range(3):
    await asyncio.sleep(0.5)  # Simulate processing
    yield MessagePart(content=f"Step {step+1} complete...\n")

# Final result with formatting
yield MessagePart(content=f"""
✅ Process complete!
Results:
```json
{json.dumps(result, indent=2)}
```
""")
```

## Common Debugging Issues

### 1. 404 Not Found Errors
If you encounter 404 errors when accessing `/api/v1/agents/{agent_name}/run`:

- **Check**: Is `server.run()` in the same file as your `@server.agent()` decorator?
- **Check**: Does the function name match the agent name in the URL?
- **Check**: Are you running the correct file with `python -m agents.path.to.file`?

### 2. LLM Integration Issues
If your LLM integration isn't working:

- **Check**: Have you provided all required parameters (model, api_base, api_key)?
- **Check**: Are you using the current memory API: `await memory.add(UserMessage(text))`?
- **Check**: Do you have the correct API keys in your environment variables?

### 3. Message Format Issues
If your messages aren't being processed correctly:

- **Check**: Are you using the correct message extraction: `inputs[0].parts[0].content`?
- **Check**: Are you yielding responses with `yield MessagePart(content="text")`?
- **Check**: For structured data, are you properly JSON encoding/decoding?

## Testing Your Agent

### Command Line Testing
```bash
# Run the agent server
python -m agents.agent_directory.agent_file

# Test with curl
curl -X POST http://localhost:8001/api/v1/agents/agent_name/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {
        "parts": [
          {
            "content": "Your test request"
          }
        ]
      }
    ]
  }'
```

### Python Client Testing
```python
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

async with Client(base_url="http://localhost:8001") as client:
    run = await client.run_sync(
        agent="agent_name",
        input=[Message(parts=[MessagePart(content="Your test request")])]
    )
    print(run.output[0].parts[0].content)
```

## Lessons from Debugging

1. **Route Registration**: ACP SDK requires agent definition and server run to be in the same file
2. **Path Structure**: The URL path must match `/api/v1/agents/{agent_name}/run`
3. **Configuration Completeness**: All LLM parameters must be provided explicitly
4. **API Evolution**: Keep up with API changes (e.g., memory handling)
5. **Error Information**: Log detailed errors during development for faster debugging

---

[← Back to Architecture](../architecture/) | [← Back to Developer Guide](../../developer-guide/) | [← Back to Docs](../../../)
