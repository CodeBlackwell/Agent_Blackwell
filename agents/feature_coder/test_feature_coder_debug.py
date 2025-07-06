#!/usr/bin/env python3
"""Debug script to test the feature coder agent directly"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message


async def test_feature_coder():
    """Test the feature coder agent with a simple example"""
    
    # Test 1: Initial feature implementation
    print("🧪 Test 1: Implementing initial calculator feature")
    print("-" * 60)
    
    test_input = """
You are implementing a specific feature as part of a new project.

ORIGINAL REQUIREMENTS:
Create a simple calculator class that supports basic arithmetic operations.

FEATURE TO IMPLEMENT: Addition of two numbers
Description: Implement a method to add two numbers in a Calculator class

EXISTING CODE:
No existing code yet. This is the first feature.

INSTRUCTIONS:
1. Create the initial Calculator class
2. Implement ONLY the addition feature
3. Create complete, runnable code
"""
    
    from acp_sdk.models import MessagePart
    messages = [Message(parts=[MessagePart(content=test_input, content_type="text/plain")])]
    
    # Import the feature coder agent here to test it
    from agents.feature_coder.feature_coder_agent import feature_coder_agent
    
    print("📤 Sending request to feature coder agent...")
    response_messages = []
    async for message in feature_coder_agent(messages):
        response_messages.append(message)
        print(f"\n📥 Response:\n{message.parts[0].content}")
    
    # Test 2: Adding a feature to existing code
    print("\n\n🧪 Test 2: Adding subtraction to existing calculator")
    print("-" * 60)
    
    test_input_2 = """
You are implementing a specific feature as part of an EXISTING project. DO NOT create a new project.

ORIGINAL REQUIREMENTS:
Create a simple calculator class that supports basic arithmetic operations.

FEATURE TO IMPLEMENT: Subtraction of two numbers
Description: Add a subtract method to the existing Calculator class

EXISTING CODE THAT YOU MUST BUILD UPON:
The following files have been created so far:

--- calculator.py ---
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b

CRITICAL INSTRUCTIONS:
1. DO NOT create a new project
2. MODIFY the existing calculator.py file
3. Add the subtract method to the existing Calculator class
4. Preserve all existing functionality
"""
    
    messages_2 = [Message(parts=[MessagePart(content=test_input_2, content_type="text/plain")])]
    
    print("📤 Sending request to feature coder agent...")
    async for message in feature_coder_agent(messages_2):
        print(f"\n📥 Response:\n{message.parts[0].content}")


if __name__ == "__main__":
    print("🚀 Testing Feature Coder Agent")
    print("=" * 60)
    asyncio.run(test_feature_coder())
    print("\n✅ Test completed!")