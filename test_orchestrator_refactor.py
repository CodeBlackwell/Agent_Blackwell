#!/usr/bin/env python3
"""
Test runner for orchestrator job workflow refactor.
Runs comprehensive tests to validate the job-oriented architecture implementation.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run orchestrator refactor tests."""
    print("🧪 Running Orchestrator Job Workflow Tests")
    print("=" * 50)

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Check if we're in a virtual environment
    if not os.environ.get("VIRTUAL_ENV") and not os.environ.get("POETRY_ACTIVE"):
        print("⚠️  Warning: Not in a virtual environment")
        print("   Consider running: poetry shell")
        print()

    # Install test dependencies if needed
    try:
        import pytest

        print("✅ pytest available")
    except ImportError:
        print("📦 Installing pytest...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"],
            check=True,
        )

    # Run the tests
    test_file = "tests/test_orchestrator_job_workflow.py"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return 1

    print(f"🚀 Running tests from {test_file}")
    print()

    # Run pytest with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_file,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
    ]

    result = subprocess.run(cmd, capture_output=False)

    print()
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("🎉 Orchestrator refactor validation successful")
    else:
        print("❌ Some tests failed")
        print("🔍 Check the output above for details")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
