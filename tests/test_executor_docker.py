#!/usr/bin/env python3
"""
Test script for the Docker-based executor agent.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message, MessagePart

# Test cases
TEST_CASES = {
    "python_hello": {
        "name": "Simple Python Hello World",
        "input": """
SESSION_ID: test_session_001

Execute this Python code:

FILENAME: hello.py
```python
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("Docker"))
    print("Python execution in Docker successful!")
```
"""
    },
    
    "python_with_tests": {
        "name": "Python with Unit Tests",
        "input": """
SESSION_ID: test_session_002

Execute this Python code with tests:

FILENAME: calculator.py
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

FILENAME: test_calculator.py
```python
import unittest
from calculator import add, subtract, multiply, divide

class TestCalculator(unittest.TestCase):
    
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
    
    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(0, 5), -5)
    
    def test_multiply(self):
        self.assertEqual(multiply(3, 4), 12)
        self.assertEqual(multiply(-2, 3), -6)
    
    def test_divide(self):
        self.assertEqual(divide(10, 2), 5)
        self.assertAlmostEqual(divide(7, 3), 2.333, places=2)
        
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(5, 0)

if __name__ == "__main__":
    unittest.main()
```
"""
    }
}

async def test_executor_agent():
    """Test the Docker-based executor agent"""
    print("🧪 Testing Docker Executor Agent")
    print("=" * 60)
    
    try:
        # Import executor agent
        from agents.executor.executor_agent import executor_agent
        
        for test_id, test_case in TEST_CASES.items():
            print(f"\n📋 Test: {test_case['name']}")
            print("-" * 40)
            
            # Create test input
            test_input = [Message(parts=[MessagePart(content=test_case['input'])])]
            
            # Call executor agent
            print("🐳 Calling executor agent...")
            response_parts = []
            async for part in executor_agent(test_input):
                response_parts.append(part)
            
            if response_parts:
                response = response_parts[0].content
                print("\n📊 Response:")
                print(response[:500] + "..." if len(response) > 500 else response)
            else:
                print("❌ No response received")
            
            # Small delay between tests
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def cleanup_containers():
    """Clean up any remaining test containers"""
    print("\n🧹 Cleaning up test containers...")
    try:
        from agents.executor.docker_manager import DockerEnvironmentManager
        await DockerEnvironmentManager.cleanup_all_sessions()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

async def main():
    """Main test function"""
    try:
        # Run tests
        await test_executor_agent()
    finally:
        # Always cleanup
        await cleanup_containers()

if __name__ == "__main__":
    print("🐳 Docker Executor Agent Test Suite")
    print("Make sure Docker is installed and running!")
    print()
    
    asyncio.run(main())
