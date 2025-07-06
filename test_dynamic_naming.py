#!/usr/bin/env python3
"""Test script to verify the new dynamic naming convention"""

from agents.executor.session_utils import generate_session_id, generate_dynamic_name

def test_dynamic_naming():
    """Test various requirements to see the generated names"""
    
    test_cases = [
        "Create a calculator API with add, subtract, multiply and divide functions",
        "Build a todo list application with CRUD operations",
        "Implement a weather forecast service using external APIs", 
        "Make a simple hello world program",
        "Develop an e-commerce shopping cart system with payment integration",
        "Write a Python script to analyze CSV files and generate reports",
        "Create REST API endpoints for user authentication and authorization",
        "Build a real-time chat application using websockets",
        "The quick brown fox jumps over the lazy dog",
        "",  # Empty requirements
        "A simple app",  # Short requirements
    ]
    
    print("Testing Dynamic Naming Convention")
    print("=" * 80)
    print("Format: YYYYMMDD_HHMMSS_<dynamic_name>_<hash>")
    print("=" * 80)
    print()
    
    for i, requirements in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Requirements: {requirements[:60]}..." if len(requirements) > 60 else f"Requirements: {requirements}")
        
        # Generate dynamic name component
        dynamic_name = generate_dynamic_name(requirements) if requirements else "app"
        print(f"Dynamic Name: {dynamic_name}")
        
        # Generate full session ID
        session_id = generate_session_id(requirements)
        print(f"Full Session ID: {session_id}")
        
        # Show what the directory would look like (with a sample container key)
        sample_container_key = "python39"
        dir_name = f"{session_id}_{sample_container_key}"
        print(f"Directory Name: generated/{dir_name}/")
        print("-" * 80)
        print()

if __name__ == "__main__":
    test_dynamic_naming()