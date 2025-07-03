#!/usr/bin/env python3
"""
Test script for the executor agent.
Tests both direct agent calls and server integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to path for proper imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message, MessagePart
from acp_sdk.client import Client

# Test cases for different technology stacks
TEST_CASES = {
    "python_simple": {
        "name": "Simple Python Script",
        "input": """
Execute this Python code:

FILENAME: hello.py
```python
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
    print("Python execution test successful!")
```
""",
        "expected_success": True
    },
    
    "python_with_tests": {
        "name": "Python with Tests",
        "input": """
Execute this Python code with tests:

FILENAME: calculator.py
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
```

FILENAME: test_calculator.py
```python
import unittest
from calculator import add, subtract, multiply

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

if __name__ == "__main__":
    unittest.main()
```
""",
        "expected_success": True
    },
    
    "nodejs_simple": {
        "name": "Simple Node.js Script",
        "input": """
Execute this Node.js code:

FILENAME: package.json
```json
{
  "name": "test-app",
  "version": "1.0.0",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  }
}
```

FILENAME: app.js
```javascript
function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("Node.js"));
console.log("JavaScript execution test successful!");
```
""",
        "expected_success": True
    },
    
    "nodejs_with_tests": {
        "name": "Node.js with Tests",
        "input": """
Execute this Node.js code with tests:

FILENAME: package.json
```json
{
  "name": "calculator-app",
  "version": "1.0.0",
  "main": "calculator.js",
  "scripts": {
    "test": "node test.js"
  }
}
```

FILENAME: calculator.js
```javascript
function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

function multiply(a, b) {
    return a * b;
}

module.exports = { add, subtract, multiply };
```

FILENAME: test.js
```javascript
const { add, subtract, multiply } = require('./calculator');

function test(name, condition) {
    if (condition) {
        console.log(`✓ ${name}`);
        return true;
    } else {
        console.log(`× ${name}`);
        return false;
    }
}

let passed = 0;
let total = 0;

// Test cases
total++; if (test("add(2, 3) should equal 5", add(2, 3) === 5)) passed++;
total++; if (test("add(-1, 1) should equal 0", add(-1, 1) === 0)) passed++;
total++; if (test("subtract(5, 3) should equal 2", subtract(5, 3) === 2)) passed++;
total++; if (test("multiply(3, 4) should equal 12", multiply(3, 4) === 12)) passed++;

console.log(`\\nTest Results: ${passed}/${total} passed`);
process.exit(passed === total ? 0 : 1);
```
""",
        "expected_success": True
    },
    
    "syntax_error": {
        "name": "Python with Syntax Error",
        "input": """
Execute this Python code (contains syntax error):

FILENAME: broken.py
```python
def hello_world(
    print("Missing closing parenthesis")
    return "Hello"
```
""",
        "expected_success": False
    }
}

async def test_executor_agent_direct():
    """Test calling the executor agent directly"""
    print("\n--- Testing Executor Agent Direct Call ---")
    
    try:
        # Import executor agent
        from agents.executor.executor_agent import executor_agent
        
        success_count = 0
        total_tests = len(TEST_CASES)
        
        for test_id, test_case in TEST_CASES.items():
            print(f"\n🧪 Testing: {test_case['name']}")
            print("-" * 50)
            
            try:
                # Create test input
                test_input = [Message(parts=[MessagePart(content=test_case['input'])])]
                
                # Call executor agent directly
                response_parts = []
                async for part in executor_agent(test_input):
                    response_parts.append(part)
                
                if response_parts:
                    response_content = response_parts[0].content
                    print(f"Response length: {len(response_content)} characters")
                    
                    # Check if execution was successful based on response content
                    success_indicators = ["✅ CODE EXECUTION RESULT", "✅ Code executed successfully"]
                    failure_indicators = ["❌ CODE EXECUTION RESULT", "❌ Code execution failed"]
                    
                    was_successful = any(indicator in response_content for indicator in success_indicators)
                    was_failure = any(indicator in response_content for indicator in failure_indicators)
                    
                    # Validate against expected result
                    if test_case['expected_success']:
                        if was_successful:
                            print("✅ Test PASSED - Expected success, got success")
                            success_count += 1
                        else:
                            print("❌ Test FAILED - Expected success, got failure")
                            print(f"Response preview: {response_content[:200]}...")
                    else:
                        if was_failure or not was_successful:
                            print("✅ Test PASSED - Expected failure, got failure/error")
                            success_count += 1
                        else:
                            print("❌ Test FAILED - Expected failure, got success")
                            print(f"Response preview: {response_content[:200]}...")
                else:
                    print("❌ Test FAILED - No response from executor agent")
                    
            except Exception as e:
                print(f"❌ Test FAILED - Exception: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Test Summary: {success_count}/{total_tests} tests passed")
        return success_count == total_tests
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure the executor agent is properly implemented")
        return False
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_connection():
    """Test connecting to orchestrator server"""
    print("\n--- Testing Server Connection ---")
    
    try:
        # Test a simple case through the server
        test_case = TEST_CASES["python_simple"]
        
        async with Client(base_url="http://localhost:8080") as client:
            # Test if server is running and has executor agent
            response = await client.run_sync(
                agent="executor_agent_wrapper", 
                input=[Message(parts=[MessagePart(content=test_case['input'])])]
            )
            
            if response.output:
                response_content = response.output[0].parts[0].content
                print(f"✅ Server connection successful!")
                print(f"Response length: {len(response_content)} characters")
                
                # Check for success indicators
                if "CODE EXECUTION RESULT" in response_content:
                    print("✅ Executor agent is working through server")
                    return True
                else:
                    print("⚠️  Server responded but output format unexpected")
                    print(f"Response preview: {response_content[:300]}...")
                    return False
            else:
                print("❌ Server responded but no output received")
                return False
            
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        print("Make sure the orchestrator server is running with executor agent registered")
        return False

async def main():
    """Run all executor agent tests"""
    print("=" * 80)
    print("🧪 EXECUTOR AGENT TEST SUITE")
    print("=" * 80)
    
    # Test 1: Direct function call
    print("\n🔧 Phase 1: Direct Agent Testing")
    direct_success = await test_executor_agent_direct()
    
    # Test 2: Server connection (if direct call works)
    server_success = False
    if direct_success:
        print("\n🔧 Phase 2: Server Integration Testing")
        server_success = await test_server_connection()
    else:
        print("\n⚠️ Skipping server test due to direct call failures")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"Direct Agent Tests: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"Server Integration: {'✅ PASS' if server_success else '❌ FAIL'}")
    
    if direct_success and server_success:
        print("\n🎉 All tests passed! Executor agent is ready for integration.")
    elif direct_success:
        print("\n⚠️ Direct tests passed but server integration failed.")
        print("Make sure to register the executor agent in the orchestrator.")
    else:
        print("\n❌ Tests failed. Check the implementation and dependencies.")
        print("\n💡 Common issues:")
        print("  • Missing dependencies (ensure Python/Node.js are installed)")
        print("  • Import errors (check project structure)")
        print("  • Environment setup (check .env file)")
    
    return direct_success and server_success

if __name__ == "__main__":
    print("🚀 Starting Executor Agent Tests...")
    print("Make sure Python and Node.js are installed for full testing")
    print()
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)