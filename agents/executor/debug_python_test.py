#!/usr/bin/env python3
"""
Debug script for Python test execution in the executor agent.
This script will help diagnose the issue with the failing Python test.
"""

import os
import sys
import tempfile
import subprocess
import asyncio
from pathlib import Path

# Test case content
CALCULATOR_PY = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

TEST_CALCULATOR_PY = """
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
"""

async def run_test_with_pytest(temp_dir):
    """Try to run tests with pytest"""
    print("\n=== PYTEST EXECUTION ===")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pytest", "-v", ".",
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        print(f"Exit code: {process.returncode}")
        print(f"STDOUT:\n{stdout_str}")
        print(f"STDERR:\n{stderr_str}")
        
        return process.returncode == 0
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

async def run_test_with_unittest(temp_dir):
    """Try to run tests with unittest"""
    print("\n=== UNITTEST EXECUTION ===")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "unittest", "discover", "-v",
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        print(f"Exit code: {process.returncode}")
        print(f"STDOUT:\n{stdout_str}")
        print(f"STDERR:\n{stderr_str}")
        
        return process.returncode == 0
    except Exception as e:
        print(f"Error running unittest: {e}")
        return False

async def run_test_directly(temp_dir):
    """Run the test file directly"""
    print("\n=== DIRECT PYTHON EXECUTION ===")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "test_calculator.py",
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        print(f"Exit code: {process.returncode}")
        print(f"STDOUT:\n{stdout_str}")
        print(f"STDERR:\n{stderr_str}")
        
        return process.returncode == 0
    except Exception as e:
        print(f"Error running direct execution: {e}")
        return False

async def main():
    """Main function to run the tests"""
    print("🔍 Python Test Execution Debugger")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory(prefix="executor_debug_") as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Write the test files
        calculator_path = os.path.join(temp_dir, "calculator.py")
        test_calculator_path = os.path.join(temp_dir, "test_calculator.py")
        
        with open(calculator_path, "w") as f:
            f.write(CALCULATOR_PY)
        
        with open(test_calculator_path, "w") as f:
            f.write(TEST_CALCULATOR_PY)
        
        print(f"Created test files: calculator.py, test_calculator.py")
        
        # Try all test execution methods
        pytest_success = await run_test_with_pytest(temp_dir)
        unittest_success = await run_test_with_unittest(temp_dir)
        direct_success = await run_test_directly(temp_dir)
        
        # Summary
        print("\n=== SUMMARY ===")
        print(f"Pytest execution: {'✅ SUCCESS' if pytest_success else '❌ FAILED'}")
        print(f"Unittest execution: {'✅ SUCCESS' if unittest_success else '❌ FAILED'}")
        print(f"Direct execution: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
        
        # Check if any method succeeded
        if pytest_success or unittest_success or direct_success:
            print("\n✅ At least one test method succeeded!")
            print("Recommendation: Update executor agent to use the successful method.")
        else:
            print("\n❌ All test methods failed!")
            print("Recommendation: Check Python environment and dependencies.")

if __name__ == "__main__":
    asyncio.run(main())
