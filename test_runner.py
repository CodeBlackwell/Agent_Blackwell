#!/usr/bin/env python3
"""
🧪 Comprehensive Test Runner for Multi-Agent System

A unified, user-friendly CLI for running all tests in the codebase.
Supports pytest tests, standalone scripts, and custom test runners.
"""

import asyncio
import argparse
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Test categories with emojis
TEST_CATEGORIES = {
    "unit": {
        "emoji": "🔬",
        "name": "Unit Tests",
        "description": "Fast, isolated tests for individual components",
        "runner": "pytest",
        "path": "tests/unit/",
        "args": ["-v"]
    },
    "integration": {
        "emoji": "🔗",
        "name": "Integration Tests",
        "description": "Tests for component interactions",
        "runner": "pytest",
        "path": "tests/integration/",
        "args": ["-v"]
    },
    "workflow": {
        "emoji": "🔄",
        "name": "Workflow Tests",
        "description": "End-to-end workflow validation",
        "runner": "python",
        "files": [
            "tests/test_workflows.py",
            "tests/test_incremental_workflow.py",
            "tests/test_incremental_simple.py"
        ]
    },
    "agent": {
        "emoji": "🤖",
        "name": "Agent Tests",
        "description": "Individual agent functionality tests",
        "runner": "python",
        "script": "tests/run_agent_tests.py"
    },
    "executor": {
        "emoji": "⚡",
        "name": "Executor Tests",
        "description": "Code execution and validation tests",
        "runner": "python",
        "files": [
            "tests/test_executor_direct.py",
            "tests/test_executor_docker.py",
            "tests/run_executor_tests.py"
        ]
    },
    "api": {
        "emoji": "🌐",
        "name": "API Tests",
        "description": "REST API endpoint tests",
        "runner": "mixed",
        "pytest_files": ["api/test_orchestrator_api.py"],
        "python_files": [
            "api/test_api_simple.py",
            "api/test_api_client.py"
        ]
    },
    "realtime": {
        "emoji": "📺",
        "name": "Real-time Output Tests",
        "description": "Real-time output display tests",
        "runner": "python",
        "files": ["tests/integration/test_realtime_output.py"]
    },
    "naming": {
        "emoji": "🏷️",
        "name": "Naming & Proof Tests",
        "description": "Dynamic naming and proof of execution tests",
        "runner": "python",
        "files": [
            "tests/integration/test_proof_integration.py",
            "tests/integration/test_dynamic_naming.py",
            "tests/integration/test_naming_integration.py"
        ]
    },
    "frontend": {
        "emoji": "🖥️",
        "name": "Frontend Tests",
        "description": "Web frontend functionality tests",
        "runner": "python",
        "script": "tests/frontend/test_frontend.py"
    },
    "orchestrator": {
        "emoji": "🎭",
        "name": "Orchestrator Client Tests",
        "description": "Orchestrator client functionality tests",
        "runner": "python",
        "script": "tests/orchestrator/test_orchestrator_client.py"
    }
}

class TestRunner:
    def __init__(self, verbose: bool = False, no_emoji: bool = False):
        self.verbose = verbose
        self.no_emoji = no_emoji
        self.results = {}
        self.start_time = None
        self.python_cmd = self._get_python_command()
        
    def _get_python_command(self) -> str:
        """Get the appropriate Python command."""
        venv_python = Path(".venv/bin/python")
        if venv_python.exists():
            return str(venv_python)
        return sys.executable
        
    def _print(self, message: str, color: str = "", emoji: str = ""):
        """Print with optional color and emoji."""
        if self.no_emoji:
            emoji = ""
        if color:
            print(f"{color}{emoji} {message}{Colors.END}")
        else:
            print(f"{emoji} {message}")
            
    def _print_header(self, message: str, emoji: str = ""):
        """Print a section header."""
        self._print(f"\n{'='*80}", Colors.BOLD)
        self._print(message, Colors.BOLD + Colors.HEADER, emoji)
        self._print(f"{'='*80}\n", Colors.BOLD)
        
    def _print_subheader(self, message: str, emoji: str = ""):
        """Print a subsection header."""
        self._print(f"\n{'-'*60}", Colors.CYAN)
        self._print(message, Colors.CYAN, emoji)
        self._print(f"{'-'*60}", Colors.CYAN)
        
    def _check_services(self) -> Dict[str, bool]:
        """Check if required services are running."""
        services = {
            "orchestrator": {"port": 8080, "name": "Orchestrator Server"},
            "api": {"port": 8000, "name": "REST API Server"}
        }
        
        results = {}
        for key, info in services.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', info['port']))
                sock.close()
                results[key] = result == 0
            except:
                results[key] = False
                
        return results
        
    def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, and stderr."""
        try:
            if self.verbose:
                self._print(f"Running: {' '.join(command)}", Colors.BLUE, "🔧")
                
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
            
        except Exception as e:
            return 1, "", str(e)
            
    def run_pytest_tests(self, path: str, args: List[str] = None) -> Dict:
        """Run pytest tests for a given path."""
        args = args or ["-v"]
        command = [self.python_cmd, "-m", "pytest", path] + args
        
        start_time = time.time()
        exit_code, stdout, stderr = self._run_command(command)
        duration = time.time() - start_time
        
        # Parse pytest output
        passed = stdout.count(" PASSED")
        failed = stdout.count(" FAILED")
        skipped = stdout.count(" SKIPPED")
        
        return {
            "success": exit_code == 0,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "output": stdout if self.verbose else "",
            "error": stderr if stderr else ""
        }
        
    def run_python_script(self, script: str, args: List[str] = None) -> Dict:
        """Run a standalone Python script."""
        args = args or []
        command = [self.python_cmd, script] + args
        
        start_time = time.time()
        exit_code, stdout, stderr = self._run_command(command)
        duration = time.time() - start_time
        
        return {
            "success": exit_code == 0,
            "duration": duration,
            "output": stdout if self.verbose else stdout[:500],
            "error": stderr if stderr else ""
        }
        
    def run_category(self, category: str, config: Dict) -> Dict:
        """Run all tests in a category."""
        results = {"tests": {}, "summary": {}}
        
        if config["runner"] == "pytest":
            # Run pytest tests
            self._print(f"Running {config['name']}...", Colors.BLUE, config["emoji"])
            result = self.run_pytest_tests(config["path"], config.get("args", []))
            results["tests"][config["path"]] = result
            results["summary"] = result
            
        elif config["runner"] == "python":
            # Run standalone Python scripts
            if "script" in config:
                self._print(f"Running {config['name']}...", Colors.BLUE, config["emoji"])
                result = self.run_python_script(config["script"])
                results["tests"][config["script"]] = result
                results["summary"] = result
            elif "files" in config:
                for file in config["files"]:
                    if Path(file).exists():
                        self._print(f"Running {Path(file).name}...", Colors.BLUE, "▶️")
                        result = self.run_python_script(file)
                        results["tests"][file] = result
                        
        elif config["runner"] == "mixed":
            # Run both pytest and standalone scripts
            if "pytest_files" in config:
                for file in config["pytest_files"]:
                    if Path(file).exists():
                        self._print(f"Running {Path(file).name} (pytest)...", Colors.BLUE, "🧪")
                        result = self.run_pytest_tests(file)
                        results["tests"][file] = result
                        
            if "python_files" in config:
                for file in config["python_files"]:
                    if Path(file).exists():
                        self._print(f"Running {Path(file).name}...", Colors.BLUE, "▶️")
                        result = self.run_python_script(file)
                        results["tests"][file] = result
                        
        return results
        
    def print_results_summary(self):
        """Print a summary of all test results."""
        self._print_header("TEST RESULTS SUMMARY", "📊")
        
        total_duration = time.time() - self.start_time
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            if not results.get("tests"):
                continue
                
            config = TEST_CATEGORIES[category]
            self._print(f"\n{config['emoji']} {config['name']}:", Colors.BOLD)
            
            for test_file, result in results["tests"].items():
                if result["success"]:
                    status = f"{Colors.GREEN}✅ PASSED{Colors.END}"
                    if "passed" in result:
                        total_passed += result["passed"]
                    else:
                        total_passed += 1
                else:
                    status = f"{Colors.RED}❌ FAILED{Colors.END}"
                    if "failed" in result:
                        total_failed += result["failed"]
                    else:
                        total_failed += 1
                        
                self._print(f"  {Path(test_file).name}: {status} ({result['duration']:.2f}s)")
                
                if result.get("error") and not result["success"]:
                    self._print(f"    Error: {result['error'][:100]}...", Colors.RED)
                    
        self._print(f"\n{'-'*60}", Colors.BOLD)
        self._print(f"Total Tests Passed: {total_passed}", Colors.GREEN, "✅")
        self._print(f"Total Tests Failed: {total_failed}", Colors.RED if total_failed > 0 else Colors.GREEN, "❌" if total_failed > 0 else "✅")
        self._print(f"Total Duration: {total_duration:.2f}s", Colors.BLUE, "⏱️")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        self._print(f"\nDetailed results saved to: {results_file}", Colors.CYAN, "💾")
        
    def run_tests(self, categories: List[str], parallel: bool = False):
        """Run tests for specified categories."""
        self.start_time = time.time()
        
        # Check services
        self._print_header("CHECKING REQUIRED SERVICES", "🔍")
        services = self._check_services()
        
        for service, running in services.items():
            if running:
                self._print(f"{service.title()} is running", Colors.GREEN, "✅")
            else:
                self._print(f"{service.title()} is NOT running", Colors.YELLOW, "⚠️")
                
        # Run tests
        self._print_header("RUNNING TESTS", "🚀")
        
        if parallel and len(categories) > 1:
            # Run categories in parallel
            with ThreadPoolExecutor(max_workers=len(categories)) as executor:
                future_to_category = {
                    executor.submit(self.run_category, cat, TEST_CATEGORIES[cat]): cat
                    for cat in categories
                }
                
                for future in as_completed(future_to_category):
                    category = future_to_category[future]
                    try:
                        self.results[category] = future.result()
                    except Exception as e:
                        self._print(f"Error running {category}: {e}", Colors.RED, "❌")
                        self.results[category] = {"error": str(e)}
        else:
            # Run categories sequentially
            for category in categories:
                if category in TEST_CATEGORIES:
                    self._print_subheader(f"Running {TEST_CATEGORIES[category]['name']}", TEST_CATEGORIES[category]['emoji'])
                    self.results[category] = self.run_category(category, TEST_CATEGORIES[category])
                else:
                    self._print(f"Unknown category: {category}", Colors.RED, "❌")
                    
        # Print summary
        self.print_results_summary()

def main():
    parser = argparse.ArgumentParser(
        description="🧪 Comprehensive Test Runner - Run all tests with style!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s unit              # Run only unit tests
  %(prog)s unit integration  # Run unit and integration tests
  %(prog)s -p                # Run all tests in parallel
  %(prog)s -l                # List all available test categories
  %(prog)s -v                # Run with verbose output
  %(prog)s --no-emoji        # Run without emojis (for CI/CD)
        """
    )
    
    parser.add_argument(
        "categories",
        nargs="*",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        help="Test categories to run (default: all)"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available test categories"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run test categories in parallel"
    )
    
    parser.add_argument(
        "--no-emoji",
        action="store_true",
        help="Disable emojis in output"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only fast tests (unit tests)"
    )
    
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode (no emojis, verbose output)"
    )
    
    args = parser.parse_args()
    
    # Handle CI mode
    if args.ci:
        args.no_emoji = True
        args.verbose = True
    
    runner = TestRunner(verbose=args.verbose, no_emoji=args.no_emoji)
    
    # List categories
    if args.list:
        runner._print_header("AVAILABLE TEST CATEGORIES", "📋")
        for key, config in TEST_CATEGORIES.items():
            runner._print(f"\n{config['emoji']} {key.upper()}: {config['name']}", Colors.BOLD)
            runner._print(f"   {config['description']}", Colors.CYAN)
            if "path" in config:
                runner._print(f"   Path: {config['path']}", Colors.BLUE)
            elif "files" in config:
                runner._print(f"   Files: {', '.join([Path(f).name for f in config['files']])}", Colors.BLUE)
        return
    
    # Determine which categories to run
    if args.quick:
        categories = ["unit"]
    elif not args.categories or "all" in args.categories:
        categories = list(TEST_CATEGORIES.keys())
    else:
        categories = args.categories
    
    # Print welcome message
    runner._print_header("MULTI-AGENT SYSTEM TEST RUNNER", "🧪")
    runner._print(f"Running: {', '.join(categories)}", Colors.CYAN, "📌")
    
    # Run tests
    runner.run_tests(categories, parallel=args.parallel)

if __name__ == "__main__":
    main()