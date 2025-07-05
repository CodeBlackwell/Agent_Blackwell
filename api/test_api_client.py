#!/usr/bin/env python3
"""
Simple test client to demonstrate Orchestrator API usage
"""

import requests
import json
import time
import sys
from typing import Optional, Dict, Any

class OrchestratorClient:
    """Simple client for interacting with the Orchestrator API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_workflow_types(self) -> list:
        """Get available workflow types"""
        response = self.session.get(f"{self.base_url}/workflow-types")
        response.raise_for_status()
        return response.json()
    
    def execute_workflow(
        self,
        requirements: str,
        workflow_type: str = "full",
        step_type: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        data = {
            "requirements": requirements,
            "workflow_type": workflow_type,
            "max_retries": max_retries,
            "timeout_seconds": timeout_seconds
        }
        
        if step_type:
            data["step_type"] = step_type
        
        response = self.session.post(
            f"{self.base_url}/execute-workflow",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a workflow execution"""
        response = self.session.get(f"{self.base_url}/workflow-status/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        session_id: str,
        poll_interval: int = 2,
        max_wait: int = 600
    ) -> Dict[str, Any]:
        """Wait for a workflow to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.get_workflow_status(session_id)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            # Print progress if available
            if status.get("progress"):
                progress = status["progress"]
                print(f"Progress: Step {progress['current_step']}/{progress['total_steps']} - {progress['status']}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Workflow {session_id} did not complete within {max_wait} seconds")

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def main():
    """Demonstrate API usage"""
    # Create client
    client = OrchestratorClient()
    
    try:
        # 1. Health Check
        print_section("Health Check")
        health = client.health_check()
        print(f"API Status: {health['status']}")
        print(f"Orchestrator Initialized: {health['orchestrator_initialized']}")
        
        # 2. Get Workflow Types
        print_section("Available Workflow Types")
        workflow_types = client.get_workflow_types()
        for wf in workflow_types:
            print(f"- {wf['name']}: {wf['description']}")
            if wf['requires_step_type']:
                print(f"  (Requires step_type parameter)")
        
        # 3. Execute a Simple Workflow
        print_section("Execute Full Workflow")
        print("Requirements: Create a Python function that calculates factorial")
        
        # Start workflow
        execution = client.execute_workflow(
            requirements="Create a Python function called factorial that calculates the factorial of a number. Include input validation and docstring.",
            workflow_type="full"
        )
        
        session_id = execution["session_id"]
        print(f"Workflow started with session ID: {session_id}")
        print(f"Status: {execution['status']}")
        print(f"Message: {execution['message']}")
        
        # 4. Monitor Progress
        print_section("Monitoring Workflow Progress")
        print("Polling for status updates...")
        
        try:
            final_status = client.wait_for_completion(
                session_id,
                poll_interval=3,
                max_wait=120  # Wait up to 2 minutes for demo
            )
            
            print(f"\nWorkflow completed!")
            print(f"Final status: {final_status['status']}")
            
            if final_status['status'] == 'completed' and final_status.get('result'):
                print("\nWorkflow Result:")
                print(json.dumps(final_status['result'], indent=2))
            elif final_status['status'] == 'failed':
                print(f"\nWorkflow failed with error: {final_status.get('error', 'Unknown error')}")
                
        except TimeoutError as e:
            print(f"\nTimeout: {e}")
        
        # 5. Execute Individual Step
        print_section("Execute Individual Step (Planning Only)")
        
        planning_execution = client.execute_workflow(
            requirements="Design a REST API for a todo list application",
            workflow_type="individual",
            step_type="planning"
        )
        
        planning_session_id = planning_execution["session_id"]
        print(f"Planning workflow started with session ID: {planning_session_id}")
        
        # Wait for completion
        print("\nWaiting for planning to complete...")
        planning_status = client.wait_for_completion(planning_session_id, max_wait=60)
        
        if planning_status['status'] == 'completed':
            print("\nPlanning completed successfully!")
        
        # 6. Demonstrate Error Handling
        print_section("Error Handling Demo")
        
        try:
            # Try to execute individual workflow without step_type
            print("Attempting to execute individual workflow without step_type...")
            client.execute_workflow(
                requirements="Test error handling",
                workflow_type="individual"
            )
        except requests.HTTPError as e:
            print(f"Expected error occurred: {e.response.status_code} - {e.response.json()['detail']}")
        
        # 7. Check Non-existent Workflow
        try:
            print("\nAttempting to check non-existent workflow...")
            client.get_workflow_status("non-existent-id")
        except requests.HTTPError as e:
            print(f"Expected error occurred: {e.response.status_code} - {e.response.json()['detail']}")
        
    except requests.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the API is running with: python api/orchestrator_api.py")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    
    print_section("Demo Complete!")

if __name__ == "__main__":
    # Print usage instructions
    print("\n" + "="*60)
    print(" Orchestrator API Test Client")
    print("="*60)
    print("\nThis script demonstrates how to use the Orchestrator API.")
    print("Make sure the API server is running first:")
    print("  python api/orchestrator_api.py")
    print("\nPress Ctrl+C to stop at any time.")
    print("="*60)
    
    input("\nPress Enter to start the demo...")
    
    main()