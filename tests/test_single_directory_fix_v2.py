#!/usr/bin/env python3
"""
Test script to verify that workflows now create a single directory per session.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
import requests

# API endpoint
API_URL = "http://localhost:8000"

async def test_single_directory_fix():
    """Test that a workflow creates only one directory"""
    
    print("=" * 80)
    print("🧪 Testing Single Directory Fix")
    print("=" * 80)
    
    # Clear the generated directory
    generated_path = Path("./generated")
    
    # List current directories
    print(f"\n📁 Current directories in {generated_path}:")
    if generated_path.exists():
        before_dirs = list(generated_path.iterdir())
        for d in before_dirs:
            print(f"  - {d.name}")
    else:
        before_dirs = []
    
    # Submit a workflow request
    request_data = {
        "requirements": "Create a simple hello world API with FastAPI",
        "workflow_type": "full",
        "max_retries": 2,
        "timeout_seconds": 300
    }
    
    print(f"\n📤 Submitting workflow request...")
    print(f"   Requirements: {request_data['requirements']}")
    print(f"   Workflow type: {request_data['workflow_type']}")
    
    try:
        response = requests.post(f"{API_URL}/execute-workflow", json=request_data)
        response.raise_for_status()
        result = response.json()
        session_id = result["session_id"]
        print(f"✅ Workflow submitted with session ID: {session_id}")
    except Exception as e:
        print(f"❌ Failed to submit workflow: {e}")
        return
    
    # Poll for completion (max 30 seconds)
    print(f"\n⏳ Waiting for workflow to complete (max 30 seconds)...")
    start_time = time.time()
    timeout = 30
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"⏱️  Timeout reached after {timeout} seconds")
            break
        
        try:
            status_response = requests.get(f"{API_URL}/workflow-status/{session_id}")
            status_response.raise_for_status()
            status = status_response.json()
            
            print(f"\r   Status: {status['status']} ({elapsed:.1f}s)", end="", flush=True)
            
            if status['status'] in ['completed', 'failed']:
                print()  # New line
                if status['status'] == 'failed':
                    print(f"❌ Workflow failed: {status.get('error', 'Unknown error')}")
                else:
                    print(f"✅ Workflow completed successfully")
                break
        except Exception as e:
            print(f"\n❌ Error checking status: {e}")
            break
        
        await asyncio.sleep(1)
    
    # Check directories created
    print(f"\n📁 Checking directories created...")
    if generated_path.exists():
        after_dirs = list(generated_path.iterdir())
        new_dirs = [d for d in after_dirs if d not in before_dirs]
        
        print(f"   New directories created: {len(new_dirs)}")
        for d in new_dirs:
            print(f"   - {d.name}")
            # Check if it contains the session ID
            if session_id in d.name:
                print(f"     ✅ Contains session ID")
            else:
                print(f"     ⚠️  Does not contain session ID")
        
        # Check for the expected single directory pattern
        if len(new_dirs) == 1:
            print(f"\n✅ SUCCESS: Only one directory created!")
            print(f"   Directory: {new_dirs[0].name}")
            
            # List subdirectories
            subdirs = list(new_dirs[0].iterdir())
            if subdirs:
                print(f"   Subdirectories: {len(subdirs)}")
                for s in subdirs[:5]:  # Show first 5
                    print(f"     - {s.name}")
        else:
            print(f"\n❌ FAILURE: Multiple directories created ({len(new_dirs)})")
            print("   This indicates the fix is not working properly")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_single_directory_fix())