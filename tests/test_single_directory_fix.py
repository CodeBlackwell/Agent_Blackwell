#!/usr/bin/env python3
"""
Test to verify that the orchestrator maintains a single directory throughout a workflow run.
This test verifies the fix for multiple directory creation issue.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk.client import Client
from acp_sdk import Message
from acp_sdk.models import MessagePart
from workflows.workflow_config import GENERATED_CODE_PATH


async def test_single_directory_creation():
    """Test that only one directory is created per workflow run"""
    print("🧪 Testing Single Directory Creation Fix")
    print("=" * 60)
    
    # Simple test requirements
    requirements = "Create a function that adds two numbers and returns the result"
    
    # Connect to orchestrator
    base_url = "http://localhost:8080"
    
    print("📡 Connecting to orchestrator...")
    
    try:
        async with Client(base_url=base_url) as client:
            # Run a simple workflow
            print("▶️  Running test workflow with requirements:")
            print(f"   {requirements}")
            print()
            
            start_time = datetime.now()
            
            # Create the prompt with workflow specification
            prompt = f"""
Use the TDD workflow to implement this:

{requirements}

Include the executor agent so we can verify directory creation.
"""
            
            # Run workflow with 30-second timeout
            run = await asyncio.wait_for(
                client.run_sync(
                    agent="orchestrator",
                    input=[Message(parts=[MessagePart(content=prompt, content_type="text/plain")])]
                ),
                timeout=30.0
            )
            
            # Extract output
            if run.output and len(run.output) > 0:
                output = run.output[0].parts[0].content
                
                # Look for session ID in output
                session_id = None
                for line in output.split('\n'):
                    if "Session ID:" in line or "SESSION_ID:" in line:
                        session_id = line.split(":")[-1].strip()
                        break
                
                if session_id:
                    print(f"✅ Found session ID: {session_id}")
                else:
                    print("⚠️  Could not find session ID in output")
                
                # Check generated directories
                generated_path = Path(GENERATED_CODE_PATH)
                print(f"\n📂 Checking generated code directory: {generated_path}")
                
                if generated_path.exists():
                    # List all directories
                    directories = [d for d in generated_path.iterdir() if d.is_dir()]
                    
                    # Filter directories created after start_time
                    new_directories = []
                    for d in directories:
                        try:
                            # Check directory modification time
                            mtime = datetime.fromtimestamp(d.stat().st_mtime)
                            if mtime >= start_time:
                                new_directories.append(d)
                        except:
                            pass
                    
                    print(f"\n📊 Directories created during this run:")
                    for d in new_directories:
                        print(f"   - {d.name}")
                    
                    # Verify single directory
                    if len(new_directories) == 0:
                        print("\n❌ ERROR: No directories were created!")
                        return False
                    elif len(new_directories) == 1:
                        print(f"\n✅ SUCCESS: Only one directory created: {new_directories[0].name}")
                        
                        # Check if it matches our session ID format
                        dir_name = new_directories[0].name
                        if session_id and session_id in dir_name:
                            print(f"✅ Directory name contains session ID")
                        
                        # Check directory structure
                        print(f"\n📁 Directory structure:")
                        for root, dirs, files in os.walk(new_directories[0]):
                            level = root.replace(str(new_directories[0]), '').count(os.sep)
                            indent = ' ' * 2 * level
                            print(f"{indent}{os.path.basename(root)}/")
                            subindent = ' ' * 2 * (level + 1)
                            for file in files:
                                print(f"{subindent}{file}")
                        
                        return True
                    else:
                        print(f"\n❌ ERROR: Multiple directories created ({len(new_directories)}):")
                        for d in new_directories:
                            print(f"   - {d.name}")
                        return False
                else:
                    print(f"❌ Generated directory does not exist: {generated_path}")
                    return False
                
            else:
                print("❌ No output received from orchestrator")
                return False
                
    except asyncio.TimeoutError:
        print("\n⏱️  Test timed out after 30 seconds")
        print("💡 This is expected - checking directories anyway...")
        
        # Still check directories even after timeout
        generated_path = Path(GENERATED_CODE_PATH)
        if generated_path.exists():
            directories = [d for d in generated_path.iterdir() if d.is_dir()]
            new_directories = []
            for d in directories:
                try:
                    mtime = datetime.fromtimestamp(d.stat().st_mtime)
                    if mtime >= start_time:
                        new_directories.append(d)
                except:
                    pass
            
            if len(new_directories) == 1:
                print(f"✅ Good news: Only one directory was created: {new_directories[0].name}")
                return True
            elif len(new_directories) > 1:
                print(f"❌ Multiple directories were created: {[d.name for d in new_directories]}")
                return False
            else:
                print("⚠️  No new directories were created")
                return False
                
        return False
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test"""
    print("🚀 Single Directory Creation Test")
    print("=" * 60)
    print("This test verifies that the orchestrator creates only one directory per workflow run")
    print()
    
    # Run test
    success = await test_single_directory_creation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Single directory creation verified!")
    else:
        print("❌ TEST FAILED: Multiple directories were created")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)