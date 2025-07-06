#!/usr/bin/env python3
"""Debug script to test the validator agent directly"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.validator.validator_agent import validator_agent


async def test_validator():
    """Test the validator agent with different scenarios"""
    
    # Test 1: Initial validation (creates new session)
    print("🧪 Test 1: Initial validation (new session)")
    print("-" * 60)
    
    test_input_1 = """
Please validate this code:

```python
# filename: calculator.py
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input_1, content_type="text/plain")])]
    
    print("📤 Sending request to validator agent...")
    session_id = None
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")
        
        # Extract session ID for next test
        if "SESSION_ID:" in response:
            session_id = response.split("SESSION_ID:")[1].split("\n")[0].strip()
    
    # Test 2: Reuse session with updated code
    print("\n\n🧪 Test 2: Validation with existing session")
    print("-" * 60)
    
    test_input_2 = f"""
SESSION_ID: {session_id}

Please validate this updated code:

```python
# filename: calculator.py
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
```
"""
    
    messages_2 = [Message(parts=[MessagePart(content=test_input_2, content_type="text/plain")])]
    
    print("📤 Sending request to validator agent with session ID...")
    async for message in validator_agent(messages_2):
        print(f"\n📥 Response:\n{message.parts[0].content}")
    
    # Test 3: Invalid code
    print("\n\n🧪 Test 3: Invalid code validation")
    print("-" * 60)
    
    test_input_3 = f"""
SESSION_ID: {session_id}

Please validate this code with syntax error:

```python
# filename: broken.py
def broken_function(
    print("This won't work"
```
"""
    
    messages_3 = [Message(parts=[MessagePart(content=test_input_3, content_type="text/plain")])]
    
    print("📤 Sending invalid code to validator...")
    async for message in validator_agent(messages_3):
        print(f"\n📥 Response:\n{message.parts[0].content}")
    
    # Cleanup
    print("\n🧹 Cleaning up containers...")
    from agents.validator.container_manager import get_container_manager
    container_manager = get_container_manager()
    container_manager.cleanup_all()


if __name__ == "__main__":
    print("🚀 Testing Validator Agent")
    print("=" * 60)
    asyncio.run(test_validator())
    print("\n✅ Test completed!")