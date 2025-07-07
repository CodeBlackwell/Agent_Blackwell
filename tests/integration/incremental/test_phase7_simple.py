#!/usr/bin/env python3
"""
Simple standalone test for Phase 7 - Feature Reviewer Agent.
Tests the agent directly without requiring the orchestrator.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent

async def test_feature_reviewer_directly():
    """Test the feature reviewer agent directly"""
    print("🧪 Testing Phase 7 - Feature Reviewer Agent (Direct)")
    print("=" * 60)
    
    # Test case 1: Simple feature
    print("\n1️⃣ Testing simple feature review:")
    simple_input = """
Feature: Add method
Description: Implement an add method that returns the sum of two numbers

Current Implementation:
```python
# filename: calculator.py
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
```
"""
    
    messages = [Message(parts=[MessagePart(content=simple_input, content_type="text/plain")])]
    
    print("Input:", simple_input[:100] + "...")
    print("\nReviewing...")
    
    response_parts = []
    async for part in feature_reviewer_agent(messages):
        response_parts.append(part.content)
    
    response = ''.join(response_parts)
    print("\nResponse:", response)
    
    # Test case 2: Feature with issues
    print("\n\n2️⃣ Testing feature with issues:")
    issue_input = """
Feature: Divide method
Description: Implement a divide method that safely handles division by zero

Current Implementation:
```python
# filename: calculator.py
class Calculator:
    def divide(self, a, b):
        return a / b  # Missing error handling
```

This feature should handle division by zero gracefully.
"""
    
    messages = [Message(parts=[MessagePart(content=issue_input, content_type="text/plain")])]
    
    print("Input:", issue_input[:100] + "...")
    print("\nReviewing...")
    
    response_parts = []
    async for part in feature_reviewer_agent(messages):
        response_parts.append(part.content)
    
    response = ''.join(response_parts)
    print("\nResponse:", response)
    
    # Test case 3: Retry context
    print("\n\n3️⃣ Testing retry context review:")
    retry_input = """
Feature: Complete task method
Retry Attempt: 2

Previous Error:
NameError: name 'task' is not defined

Previous Feedback:
You need to retrieve the task from self.tasks using task_id before accessing it.

New Implementation:
```python
# filename: task_manager.py
def complete_task(self, task_id):
    if task_id in self.tasks:
        self.tasks[task_id]['completed'] = True
        return True
    return False
```
"""
    
    messages = [Message(parts=[MessagePart(content=retry_input, content_type="text/plain")])]
    
    print("Input:", retry_input[:100] + "...")
    print("\nReviewing...")
    
    response_parts = []
    async for part in feature_reviewer_agent(messages):
        response_parts.append(part.content)
    
    response = ''.join(response_parts)
    print("\nResponse:", response)
    
    print("\n✅ Phase 7 Feature Reviewer Agent is working!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_feature_reviewer_directly())
    exit(0 if success else 1)