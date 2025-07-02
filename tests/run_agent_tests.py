#!/usr/bin/env python
"""
Agent Test Runner

This script runs tests for all agents in the system or a specific agent if specified.
It checks if an orchestrator server is running, and if not, starts one automatically.
Test outputs are saved to log files in the tests/outputs/ directory.

Usage:
  python tests/run_agent_tests.py              # Run all agent tests
  python tests/run_agent_tests.py --list       # List available tests
  python tests/run_agent_tests.py planner      # Run only planner agent tests
  python tests/run_agent_tests.py --help       # Show help
"""

import os
import sys
import time
import socket
import argparse
import importlib
import subprocess
import signal
import glob
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import json

# Add the project root to the Python path
# Since we're now in the tests directory, parent is the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup output directory
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Generate timestamp for the current run
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_LOG_DIR = OUTPUT_DIR / f"run_{TIMESTAMP}"
RUN_LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler(RUN_LOG_DIR / "runner.log")  # Log to file
    ]
)
logger = logging.getLogger('agent_tests')

# Import dotenv for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv not installed, skipping environment variable loading")

# Constants
PORT = 8080
SERVER_START_TIMEOUT = 10
SERVER_SCRIPT = os.path.join(project_root, "orchestrator", "orchestrator_agent.py")

# Agent directories
AGENT_DIRS = [
    "planner",
    "designer", 
    "coder", 
    "test_writer", 
    "reviewer"
]

def check_server_running(port: int = PORT) -> bool:
    """Check if a server is running on the specified port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def start_server() -> subprocess.Popen:
    """Start the orchestrator server as a background process."""
    logger.info(f"Starting orchestrator server from {SERVER_SCRIPT}...")
    
    # Create the Python command with the correct virtual environment
    venv_python = os.path.join(project_root, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable  # Fall back to current Python
        logger.warning("Virtual environment Python not found, using current Python interpreter")
    
    # Start the server as a background process
    server_process = subprocess.Popen(
        [venv_python, SERVER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    start_time = time.time()
    while not check_server_running() and time.time() - start_time < SERVER_START_TIMEOUT:
        time.sleep(0.5)
        
        # Check if process has crashed
        if server_process.poll() is not None:
            out, err = server_process.communicate()
            logger.error(f"Server failed to start!\nOutput: {out}\nError: {err}")
            sys.exit(1)
    
    if not check_server_running():
        logger.error(f"Server did not start within {SERVER_START_TIMEOUT} seconds")
        server_process.terminate()
        sys.exit(1)
        
    logger.info("Orchestrator server started successfully")
    return server_process

def find_test_modules() -> Dict[str, str]:
    """Find all test modules for the agents."""
    test_modules = {}
    
    for agent in AGENT_DIRS:
        # Update path to look in agents directory
        agent_dir = project_root / "agents" / agent
        
        # Skip if directory doesn't exist
        if not agent_dir.exists() or not agent_dir.is_dir():
            logger.warning(f"Agent directory not found: {agent_dir}")
            continue
            
        # Look for test files
        test_files = list(agent_dir.glob("test_*.py"))
        
        if not test_files:
            logger.warning(f"No test files found for agent: {agent}")
            continue
            
        # Use the first test file found
        test_modules[agent] = str(test_files[0])
    
    return test_modules

def run_test(test_path: str) -> Dict:
    """Run a single test and return the results."""
    logger.info(f"Running test: {test_path}")
    
    # Get the agent name from the path (updated to handle the new path structure)
    agent_name = Path(test_path).parent.name
    
    # Extract test file name without extension for more descriptive logging
    test_file_name = Path(test_path).stem
    
    # Get Python from virtual environment
    venv_python = os.path.join(project_root, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    
    start_time = time.time()
    process = subprocess.run(
        [venv_python, test_path, "--automated"],  # Run in automated mode
        capture_output=True,
        text=True
    )
    execution_time = time.time() - start_time
    
    # Default result structure
    result = {
        "agent": agent_name,
        "test_name": test_file_name,
        "test_path": test_path,
        "success": process.returncode == 0,
        "execution_time": round(execution_time, 2),
        "output": process.stdout.strip(),
        "error": process.stderr.strip() if process.stderr else None,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Try to extract test description from the file
    try:
        with open(test_path, 'r') as f:
            content = f.read(1000)  # Read first 1000 chars
            if '"""' in content:
                docstring = content.split('"""')[1].strip()
                description = docstring.split('\n')[0].strip()
                result["description"] = description
    except Exception:
        result["description"] = ""  # Default empty description if extraction fails
    
    # Try to parse JSON output if available
    try:
        if process.stdout.strip().startswith("{") and process.stdout.strip().endswith("}"):
            result.update(json.loads(process.stdout.strip()))
    except:
        pass
    
    # Save test output to log file with more descriptive name
    log_file = RUN_LOG_DIR / f"{agent_name}_{test_file_name}_test_output.log"
    with open(log_file, 'w') as f:
        f.write(f"TEST RESULTS: {agent_name.upper()} - {test_file_name}\n")
        f.write(f"Test path: {test_path}\n")
        if result.get('description'):
            f.write(f"Description: {result['description']}\n")
        f.write(f"Status: {'PASSED' if result['success'] else 'FAILED'}\n")
        f.write(f"Execution time: {result['execution_time']:.2f}s\n")
        f.write(f"Timestamp: {result['timestamp']}\n")
        f.write("\n=== STDOUT ===\n")
        f.write(result['output'] or "No output")
        f.write("\n\n=== STDERR ===\n")
        f.write(result['error'] or "No errors")
    
    # If we have detailed output, save it separately
    try:
        if result.get('detailed_output'):
            detail_file = RUN_LOG_DIR / f"{agent_name}_{test_file_name}_detailed_output.json"
            with open(detail_file, 'w') as f:
                json.dump(result['detailed_output'], f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save detailed output for {agent_name} ({test_file_name}): {e}")
        
    return result

def print_results(results: List[Dict]) -> None:
    """Print test results in a nicely formatted way."""
    print("\n" + "=" * 80)
    print(f"🧪 AGENT TEST RESULTS ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r["success"])
    
    for i, result in enumerate(results, 1):
        agent = result["agent"].upper()
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        time_taken = f"{result['execution_time']:.2f}s"
        
        test_name = result.get("test_name", "")
        description = result.get("description", "")
        print(f"\n{i}. {agent} TESTS: {status} ({time_taken})")
        print(f"   Test: {test_name}{' - ' + description if description else ''}")
        
        if not result["success"]:
            print("\nERROR OUTPUT:")
            print("-" * 50)
            print(result["error"] if result["error"] else "No error output")
            print("-" * 50)
            
        # Print a more comprehensive output preview
        if result["output"]:
            lines = result["output"].split('\n')
            # Show more lines for better context
            preview_lines = 10
            preview = '\n'.join(lines[:preview_lines])
            if len(lines) > preview_lines:
                preview += f"\n... ({len(lines) - preview_lines} more lines)"
            print("\nOUTPUT PREVIEW:")
            print("-" * 50)
            print(preview)
            print("-" * 50)
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {success_count}/{len(results)} tests passed")
    print(f"Detailed logs saved to: {RUN_LOG_DIR}")
    print("=" * 80 + "\n")
    
    if success_count < len(results):
        print("❗ Some tests failed. Check the output above for details.")
    else:
        print("🎉 All tests passed successfully!")
    
    # Save summary to a file
    summary_file = RUN_LOG_DIR / "test_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"TEST SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write("="*50 + "\n")
        f.write(f"Total tests: {len(results)}\n")
        f.write(f"Passed: {success_count}\n")
        f.write(f"Failed: {len(results) - success_count}\n\n")
        
        for i, result in enumerate(results, 1):
            agent = result["agent"].upper()
            test_name = result.get("test_name", "")
            description = result.get("description", "")
            status = "PASSED" if result["success"] else "FAILED"
            time_taken = f"{result['execution_time']:.2f}s"
            f.write(f"{i}. {agent} ({test_name}): {status} ({time_taken})\n")
            if description:
                f.write(f"   Description: {description}\n")

def list_available_tests() -> None:
    """List all available tests."""
    test_modules = find_test_modules()
    
    print("\nAVAILABLE AGENT TESTS:\n")
    
    if not test_modules:
        print("No agent tests found.")
        return
        
    for i, (agent, path) in enumerate(test_modules.items(), 1):
        print(f"{i}. {agent.upper()} - {path}")
        
    print("\nRun specific test with: python tests/run_agent_tests.py [agent_name]")
    print("Run all tests with: python tests/run_agent_tests.py\n")

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Run agent tests")
    parser.add_argument("agent", nargs="?", help="Specific agent to test (e.g., planner, designer)")
    parser.add_argument("--list", action="store_true", help="List available tests")
    parser.add_argument("--no-server", action="store_true", help="Don't start server automatically")
    parser.add_argument("--no-logs", action="store_true", help="Don't save logs to files")
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
        return
    
    # Find test modules
    test_modules = find_test_modules()
    
    if not test_modules:
        logger.error("No agent test modules found")
        sys.exit(1)
    
    # Filter by agent name if specified
    if args.agent:
        if args.agent not in test_modules:
            logger.error(f"No test module found for agent: {args.agent}")
            print("\nAvailable agents:")
            for agent in test_modules:
                print(f"- {agent}")
            sys.exit(1)
        test_modules = {args.agent: test_modules[args.agent]}
    
    # Check if server is running, start if not
    server_process = None
    if not check_server_running():
        if args.no_server:
            logger.error("No server running and --no-server flag is set")
            sys.exit(1)
        else:
            server_process = start_server()
    else:
        logger.info("Orchestrator server is already running")
    
    # Run the tests
    try:
        logger.info(f"Running tests for {len(test_modules)} agents")
        
        results = []
        for agent, test_path in test_modules.items():
            result = run_test(test_path)
            results.append(result)
        
        # Print the results
        print_results(results)
        
        # Set exit code based on test results
        if not all(r["success"] for r in results):
            sys.exit(1)
            
    finally:
        # Clean up server process if we started it
        if server_process is not None:
            logger.info("Stopping orchestrator server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

if __name__ == "__main__":
    main()
