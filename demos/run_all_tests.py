#!/usr/bin/env python3
"""
🧪 Run All Tests - Comprehensive Test Execution Demo
==================================================

This script demonstrates how to run all test categories in the system,
providing a complete overview of the codebase health.

Usage:
    python run_all_tests.py              # Run all test categories
    python run_all_tests.py unit         # Run only unit tests
    python run_all_tests.py integration  # Run only integration tests
    
Test Categories:
    - Unit Tests: Fast, isolated component tests
    - Integration Tests: Component interaction tests
    - Workflow Tests: End-to-end workflow validation
    - Agent Tests: Individual agent functionality
    - Executor Tests: Code execution validation
    - API Tests: REST endpoint validation
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import json
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker


class TestRunner:
    """Manages execution of all test categories."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.test_results = {}
        self.start_time = None
        
    def run_all_tests(self, category: str = "all") -> None:
        """Run all test categories or a specific category."""
        self.formatter.print_banner(
            "🧪 COMPREHENSIVE TEST RUNNER",
            "Executing System Test Suite"
        )
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        self.start_time = time.time()
        
        # Define test categories
        test_categories = {
            "unit": {
                "name": "🔬 Unit Tests",
                "command": ["pytest", "tests/unit/", "-v"],
                "description": "Fast, isolated component tests"
            },
            "integration": {
                "name": "🔗 Integration Tests", 
                "command": ["pytest", "tests/integration/", "-v"],
                "description": "Component interaction tests"
            },
            "workflow": {
                "name": "🔄 Workflow Tests",
                "command": ["python", "tests/test_workflows.py"],
                "description": "End-to-end workflow validation"
            },
            "agent": {
                "name": "🤖 Agent Tests",
                "command": ["python", "tests/run_agent_tests.py"],
                "description": "Individual agent functionality"
            },
            "executor": {
                "name": "⚡ Executor Tests",
                "command": ["python", "tests/test_executor_basic.py"],
                "description": "Code execution validation"
            },
            "api": {
                "name": "🌐 API Tests",
                "command": ["python", "api/test_api_integration.py"],
                "description": "REST endpoint validation"
            }
        }
        
        # Filter categories based on argument
        if category != "all":
            if category in test_categories:
                test_categories = {category: test_categories[category]}
            else:
                self.formatter.show_error(
                    f"Unknown test category: {category}",
                    ["Available categories: " + ", ".join(test_categories.keys())]
                )
                return
                
        # Run each test category
        for cat_id, cat_info in test_categories.items():
            self._run_test_category(cat_id, cat_info)
            
        # Show final summary
        self._show_summary()
        
    def _check_prerequisites(self) -> bool:
        """Check if system is ready for testing."""
        self.formatter.print_section("Checking Prerequisites")
        
        # Check virtual environment
        if not self.checker.check_virtual_env():
            self.formatter.show_error(
                "Virtual environment not activated",
                ["Run: source .venv/bin/activate"]
            )
            return False
            
        # Check orchestrator
        print("🔍 Checking orchestrator status...")
        if not self.checker.is_orchestrator_running():
            print("⚠️  Orchestrator not running (some tests may fail)")
            print("   Start it with: python orchestrator/orchestrator_agent.py")
            
        # Check API server
        print("🔍 Checking API server status...")
        api_running = self._check_api_server()
        if not api_running:
            print("⚠️  API server not running (API tests will fail)")
            print("   Start it with: python api/orchestrator_api.py")
            
        print("✅ Prerequisites check complete\n")
        return True
        
    def _check_api_server(self) -> bool:
        """Check if API server is running."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _run_test_category(self, category: str, info: Dict) -> None:
        """Run a single test category."""
        self.formatter.print_section(f"{info['name']} - {info['description']}")
        
        start_time = time.time()
        result = {
            "name": info['name'],
            "description": info['description'],
            "status": "pending",
            "duration": 0,
            "output": "",
            "errors": ""
        }
        
        try:
            # Run the test command
            print(f"🏃 Running: {' '.join(info['command'])}")
            process = subprocess.run(
                info['command'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            result["output"] = process.stdout
            result["errors"] = process.stderr
            result["status"] = "passed" if process.returncode == 0 else "failed"
            
            # Show brief result
            if result["status"] == "passed":
                print(f"✅ {info['name']} passed!")
            else:
                print(f"❌ {info['name']} failed!")
                if result["errors"]:
                    print(f"   Error: {result['errors'][:200]}...")
                    
        except Exception as e:
            result["status"] = "error"
            result["errors"] = str(e)
            print(f"💥 {info['name']} encountered an error: {e}")
            
        result["duration"] = time.time() - start_time
        self.test_results[category] = result
        print(f"⏱️  Duration: {result['duration']:.2f} seconds\n")
        
    def _show_summary(self) -> None:
        """Show test execution summary."""
        self.formatter.print_banner("📊 TEST EXECUTION SUMMARY", width=80)
        
        total_duration = time.time() - self.start_time
        passed = sum(1 for r in self.test_results.values() if r["status"] == "passed")
        failed = sum(1 for r in self.test_results.values() if r["status"] == "failed")
        errors = sum(1 for r in self.test_results.values() if r["status"] == "error")
        
        # Status overview
        print(f"\n📈 Results Overview:")
        print(f"   Total Categories: {len(self.test_results)}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   💥 Errors: {errors}")
        print(f"   ⏱️  Total Duration: {total_duration:.2f} seconds")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        print("-" * 80)
        print(f"{'Category':<30} {'Status':<15} {'Duration':<15}")
        print("-" * 80)
        
        for category, result in self.test_results.items():
            status_icon = {
                "passed": "✅",
                "failed": "❌", 
                "error": "💥",
                "pending": "⏳"
            }.get(result["status"], "❓")
            
            print(f"{result['name']:<30} {status_icon} {result['status']:<12} {result['duration']:>6.2f}s")
            
        # Save results to file
        self._save_results()
        
        # Final status
        print("\n" + "=" * 80)
        if failed == 0 and errors == 0:
            print("🎉 All tests passed successfully!")
        else:
            print("⚠️  Some tests failed. Check the detailed output above.")
            
    def _save_results(self) -> None:
        """Save test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path("demo_outputs/test_results") / f"all_tests_{timestamp}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": time.time() - self.start_time,
            "results": self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run all test categories for the Multi-Agent Coding System"
    )
    parser.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "workflow", "agent", "executor", "api"],
        help="Test category to run (default: all)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    runner.run_all_tests(args.category)


if __name__ == "__main__":
    main()