#!/usr/bin/env python3
"""
Final test to verify that only one directory is created per workflow run.
Tests the complete fix including:
1. Orchestrator passing session_id
2. Coder agent using session_id for directory
3. Executor agent not generating new session_id when one is provided
"""

import asyncio
import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.orchestrator_agent import EnhancedCodingTeamTool, CodingTeamInputModel

async def test_single_directory_creation():
    """Test that only one directory is created per workflow"""
    
    print("=" * 80)
    print("🧪 Testing Single Directory Creation Fix")
    print("=" * 80)
    
    # Clean up any existing test directories
    generated_path = Path("./generated")
    if generated_path.exists():
        for item in generated_path.iterdir():
            if item.is_dir() and "test_single_dir" in item.name:
                shutil.rmtree(item)
                print(f"🧹 Cleaned up old test directory: {item.name}")
    
    # Generate a custom session ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    custom_session_id = f"test_single_dir_{timestamp}"
    print(f"\n📋 Test Session ID: {custom_session_id}")
    
    # Create the tool
    tool = EnhancedCodingTeamTool()
    
    # Create input with custom session ID
    input_data = CodingTeamInputModel(
        requirements="Create a simple calculator with add and subtract functions",
        workflow_type="full",
        session_id=custom_session_id,
        max_retries=2,
        timeout_seconds=120
    )
    
    print(f"\n📤 Running orchestrator with session ID: {custom_session_id}")
    print(f"   Requirements: {input_data.requirements}")
    print(f"   Workflow type: {input_data.workflow_type}")
    
    # Track directories before execution
    initial_dirs = set()
    if generated_path.exists():
        initial_dirs = {d.name for d in generated_path.iterdir() if d.is_dir()}
    
    print(f"\n📁 Initial directories: {len(initial_dirs)}")
    
    try:
        # Run the workflow
        start_time = time.time()
        result = await tool._run(input_data, None, None)
        end_time = time.time()
        
        print(f"\n✅ Workflow completed in {end_time - start_time:.2f} seconds")
        
        # Check directories after execution
        final_dirs = set()
        if generated_path.exists():
            final_dirs = {d.name for d in generated_path.iterdir() if d.is_dir()}
        
        new_dirs = final_dirs - initial_dirs
        
        print(f"\n📁 Final directories: {len(final_dirs)}")
        print(f"📁 New directories created: {len(new_dirs)}")
        
        if new_dirs:
            print("\n📋 New directories:")
            for dir_name in sorted(new_dirs):
                print(f"   - {dir_name}")
                # Check if it contains our session ID
                if custom_session_id in dir_name:
                    print(f"     ✅ Contains our session ID")
                else:
                    print(f"     ❌ Does not contain our session ID")
        
        # Analyze the results
        session_related_dirs = [d for d in new_dirs if custom_session_id in d or "test_single_dir" in d]
        other_dirs = [d for d in new_dirs if custom_session_id not in d and "test_single_dir" not in d]
        
        print(f"\n📊 Analysis:")
        print(f"   Session-related directories: {len(session_related_dirs)}")
        print(f"   Other directories: {len(other_dirs)}")
        
        # Success criteria
        if len(session_related_dirs) == 1 and len(other_dirs) == 0:
            print(f"\n✅ SUCCESS: Only one directory created for session!")
            print(f"   Directory name: {session_related_dirs[0]}")
            
            # Check directory contents
            session_dir = generated_path / session_related_dirs[0]
            if session_dir.exists():
                files = list(session_dir.glob("**/*"))
                print(f"\n📄 Directory contains {len(files)} files:")
                for f in files[:10]:  # Show first 10 files
                    if f.is_file():
                        print(f"   - {f.relative_to(session_dir)}")
        else:
            print(f"\n❌ FAILURE: Multiple directories created!")
            print(f"   Expected: 1 session-related directory")
            print(f"   Got: {len(session_related_dirs)} session-related, {len(other_dirs)} other")
            
            # Show all directories for debugging
            print("\n🔍 All new directories:")
            for d in new_dirs:
                print(f"   - {d}")
        
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # Note: Both orchestrator and API servers should be running
    print("⚠️  Make sure the orchestrator server is running on port 8080!")
    print("   Run: python orchestrator/orchestrator_agent.py")
    print()
    
    asyncio.run(test_single_directory_creation())