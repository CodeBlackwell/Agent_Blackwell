#!/usr/bin/env python3
"""
Simplified orchestrator manager - just ensures it's running.
"""

import subprocess
import time
import requests
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def is_orchestrator_healthy(timeout: int = 2, port: int = 8080) -> bool:
    """Check if the orchestrator is running and healthy."""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False


def start_orchestrator_background():
    """Start orchestrator in background and return immediately."""
    orchestrator_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator",
        "orchestrator_agent.py"
    )
    
    if not os.path.exists(orchestrator_path):
        print(f"❌ Orchestrator not found at: {orchestrator_path}")
        sys.exit(1)
    
    print(f"🚀 Starting orchestrator in background...")
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Start in background, detached from this process
    if sys.platform == 'win32':
        # Windows
        subprocess.Popen(
            [sys.executable, orchestrator_path],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=env
        )
    else:
        # Unix/Linux/macOS
        subprocess.Popen(
            [sys.executable, orchestrator_path],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
    
    print("✅ Orchestrator starting...")
    
    # Wait for it to be ready
    print("⏳ Waiting for orchestrator to be ready...")
    for i in range(30):
        if is_orchestrator_healthy():
            print("✅ Orchestrator is ready!")
            return True
        time.sleep(1)
        if i % 5 == 4:
            print(f"   Still waiting... ({i+1}/30)")
    
    print("❌ Orchestrator didn't start properly")
    return False


def ensure_orchestrator():
    """Ensure orchestrator is running, start if needed."""
    if is_orchestrator_healthy():
        print("✅ Orchestrator is already running")
        return True
    
    print("🔍 Orchestrator not detected, starting it...")
    return start_orchestrator_background()


if __name__ == "__main__":
    print("🧪 Testing simple orchestrator manager...")
    if ensure_orchestrator():
        print("✅ Success! Orchestrator is running")
        print("   Note: The orchestrator will keep running in the background")
        print("   To stop it, use: pkill -f orchestrator_agent.py")
    else:
        print("❌ Failed to start orchestrator")