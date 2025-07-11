#!/usr/bin/env python3
"""Test that the execution report serialization fix works"""

import subprocess
import time
import json
from pathlib import Path

print("🧪 Testing execution report serialization fix")
print("=" * 60)

# Start the server
print("🚀 Starting Flagship server...")
server_process = subprocess.Popen(
    ["python", "flagship_server_simple.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
time.sleep(3)

try:
    # Send a test request
    print("📤 Sending test request...")
    result = subprocess.run(
        ["curl", "-X", "POST", "http://localhost:8100/tdd/start",
         "-H", "Content-Type: application/json",
         "-d", '{"requirements": "create a simple counter that increments and decrements"}'],
        capture_output=True,
        text=True
    )
    
    # Parse response to get session ID
    if result.returncode == 0:
        response = json.loads(result.stdout)
        session_id = response.get("session_id")
        print(f"📋 Session ID: {session_id}")
        
        # Wait for workflow to complete
        print("⏳ Waiting for workflow to complete...")
        time.sleep(5)
        
        # Check execution report
        report_path = Path(f"generated/{session_id}/execution_report.json")
        if report_path.exists():
            print(f"✅ Execution report generated successfully!")
            
            # Load and analyze
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            print(f"\n📊 Report Summary:")
            print(f"  - Original Command: ✓" if "original_command" in report else "  - Original Command: ✗")
            print(f"  - Agent Exchanges: {len(report.get('agent_exchanges', []))}")
            print(f"  - Total Events: {report['summary'].get('total_events', 0)}")
            print(f"  - Files Created: {report['metrics'].get('files_created', 0)}")
            
            # Check for serialization errors
            print(f"\n🔍 Checking for serialization issues...")
            issues = []
            
            # Check agent exchanges for TestableFeature objects
            for exchange in report.get('agent_exchanges', []):
                request_str = json.dumps(exchange.get('request_data', {}))
                if 'TestableFeature' in request_str:
                    issues.append("Found non-serialized TestableFeature in request data")
                response_str = json.dumps(exchange.get('response_data', {}))
                if 'TestableFeature' in response_str:
                    issues.append("Found non-serialized TestableFeature in response data")
            
            if issues:
                print(f"❌ Serialization issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print(f"✅ No serialization issues found!")
            
        else:
            print(f"❌ Execution report not found at {report_path}")
            # List what files were created
            session_dir = Path(f"generated/{session_id}")
            if session_dir.exists():
                print(f"\n📁 Files in session directory:")
                for file in session_dir.iterdir():
                    print(f"  - {file.name}")
    else:
        print(f"❌ Request failed: {result.stderr}")
        
finally:
    # Stop the server
    print("\n🛑 Stopping server...")
    server_process.terminate()
    server_process.wait()
    print("✅ Test complete!")