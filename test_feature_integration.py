#!/usr/bin/env python3
"""
Test script to verify Feature Orchestrator integration in run.py
"""
import subprocess
import sys
import os

def test_feature_command():
    """Test the new feature command in run.py"""
    print("🧪 Testing Feature Orchestrator Integration\n")
    
    # Test 1: Check if feature command is recognized
    print("Test 1: Checking if 'feature' command is recognized...")
    result = subprocess.run(
        [sys.executable, "run.py", "feature", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "Feature Orchestrator" in result.stdout:
        print("✅ Feature command recognized\n")
    else:
        print("❌ Feature command not recognized")
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return False
    
    # Test 2: Dry run test
    print("Test 2: Testing dry run mode...")
    result = subprocess.run(
        [sys.executable, "run.py", "feature", "--task", "Build a simple calculator API", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "Would run incremental workflow" in result.stdout:
        print("✅ Dry run mode works\n")
    else:
        print("❌ Dry run mode failed")
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return False
    
    # Test 3: Check workflow type option
    print("Test 3: Testing workflow type option...")
    result = subprocess.run(
        [sys.executable, "run.py", "feature", "--task", "Test task", "--workflow-type", "mvp_incremental", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "mvp_incremental" in result.stdout:
        print("✅ Workflow type option works\n")
    else:
        print("❌ Workflow type option failed")
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return False
    
    # Test 4: Check complexity filter
    print("Test 4: Testing complexity filter...")
    result = subprocess.run(
        [sys.executable, "run.py", "feature", "--task", "Test task", "--complexity", "medium", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Complexity filter accepted\n")
    else:
        print("❌ Complexity filter failed")
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return False
    
    print("🎉 All tests passed!")
    return True

def test_interactive_menu():
    """Test interactive menu integration (manual verification needed)"""
    print("\n📋 Manual Test Instructions:")
    print("1. Run: python run.py")
    print("2. Select option 4: '🏗️ Feature Orchestrator Mode'")
    print("3. Verify the Feature Orchestrator menu appears")
    print("4. Test each submenu option")
    print("\nThis requires manual verification as it's interactive.")

if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("="*60)
    print("Feature Orchestrator Integration Test")
    print("="*60)
    
    # Run automated tests
    if test_feature_command():
        print("\n✅ Automated tests completed successfully!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
    
    # Show manual test instructions
    test_interactive_menu()
    
    print("\n" + "="*60)
    print("Example commands to try:")
    print('  python run.py feature --task "Build a REST API with CRUD operations"')
    print('  python run.py feature --task "Create a todo list app" --show-progress')
    print('  python run.py feature --task "Build a CLI tool" --workflow-type mvp_incremental')
    print("="*60)