#!/usr/bin/env python3
"""Simple API test using curl"""

import subprocess
import json
import time

# Start a workflow
print("Starting workflow...")
result = subprocess.run([
    "curl", "-X", "POST", "http://localhost:8100/tdd/start",
    "-H", "Content-Type: application/json",
    "-d", '{"requirements": "Create a hello world function", "config_type": "quick"}'
], capture_output=True, text=True)

response = json.loads(result.stdout)
session_id = response["session_id"]
print(f"Started: {session_id}")

# Wait a bit
print("Waiting for workflow to complete...")
time.sleep(10)

# Check status
print("\nChecking status...")
result = subprocess.run([
    "curl", f"http://localhost:8100/tdd/status/{session_id}"
], capture_output=True, text=True)

status = json.loads(result.stdout)
print(json.dumps(status, indent=2))