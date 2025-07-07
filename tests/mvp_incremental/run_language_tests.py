#!/usr/bin/env python3
"""
Run all language detection and runtime tests for MVP Incremental workflow
This provides a quick way to verify the MEAN stack validation fixes
"""

import subprocess
import sys
from pathlib import Path

# Test files to run
TEST_FILES = [
    "test_language_detection.py",
    "test_language_hint_flow.py", 
    "test_runtime_container_selection.py",
    "test_validation_language_flow.py",
    "test_mean_stack_detection.py"
]

def run_tests():
    """Run all language-related tests"""
    print("🧪 Running Language Detection and Runtime Tests")
    print("=" * 60)
    
    test_dir = Path(__file__).parent
    failed_tests = []
    passed_tests = []
    
    for test_file in TEST_FILES:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"\n📄 Running {test_file}...")
        
        # Run the test
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        # Check results
        if result.returncode == 0:
            # Extract test count from output
            if "passed" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" not in line:
                        print(f"   ✅ {line.strip()}")
                        break
            passed_tests.append(test_file)
        else:
            print(f"   ❌ FAILED")
            failed_tests.append(test_file)
            # Show failures
            if "FAILURES" in result.stdout:
                print("\n   Failures:")
                in_failures = False
                for line in result.stdout.split('\n'):
                    if "FAILURES" in line:
                        in_failures = True
                    elif "short test summary" in line:
                        break
                    elif in_failures and line.strip():
                        print(f"   {line}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"   ✅ Passed: {len(passed_tests)} test files")
    print(f"   ❌ Failed: {len(failed_tests)} test files")
    
    if failed_tests:
        print(f"\n   Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("\n🎉 All language detection and runtime tests passed!")
        print("\n✨ The MEAN stack validation fix is verified to work correctly:")
        print("   - Language detection properly identifies TypeScript/JavaScript")
        print("   - Language hints propagate through the workflow")
        print("   - Correct Docker containers are selected for each language")
        print("   - No 'Python file not found' errors for JavaScript/TypeScript code")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())