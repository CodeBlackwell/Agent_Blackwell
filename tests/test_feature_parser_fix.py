#!/usr/bin/env python3
"""
Test the feature parser fix for the bug where all features were parsed as one.
This test ensures that designer output wrapped in a dictionary is properly handled.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.feature_parser import FeatureParser
from workflows.incremental.feature_orchestrator import extract_content_from_message


def test_dictionary_wrapped_output():
    """Test that dictionary-wrapped designer output is correctly parsed"""
    
    # Sample designer output wrapped in dictionary (as returned by agents)
    designer_result = {
        'content': '''# System Design

## IMPLEMENTATION PLAN

FEATURE[1]: Project Foundation
Description: Set up FastAPI application structure with configuration management.
Files: main.py, requirements.txt, Dockerfile
Validation: Application starts without errors and responds to requests.
Dependencies: None
Estimated Complexity: Low

FEATURE[2]: Hello World Endpoint
Description: Create a GET endpoint that returns a greeting message.
Files: main.py
Validation: Endpoint returns `{"message": "Hello, World!"}` on GET request.
Dependencies: FEATURE[1]
Estimated Complexity: Low

FEATURE[3]: Testing Suite
Description: Write unit tests for the Hello World endpoint using pytest.
Files: tests/test_main.py
Validation: All tests pass with expected output.
Dependencies: FEATURE[1], FEATURE[2]
Estimated Complexity: Medium

FEATURE[4]: API Documentation
Description: Generate OpenAPI documentation for the API.
Files: main.py (using FastAPI's built-in documentation)
Validation: Documentation is accessible and accurately describes the API.
Dependencies: FEATURE[1], FEATURE[2]
Estimated Complexity: Low

FEATURE[5]: Docker Containerization
Description: Create a Dockerfile to containerize the FastAPI application.
Files: Dockerfile
Validation: Docker image builds successfully and runs the application.
Dependencies: FEATURE[1]
Estimated Complexity: Medium
''',
        'messages': [],
        'success': True,
        'metadata': {'agent': 'designer_agent', 'context': 'enhanced_design'}
    }
    
    # Extract content
    content = extract_content_from_message(designer_result)
    
    # Verify content extraction
    assert isinstance(content, str), "Extracted content should be a string"
    assert content.startswith("# System Design"), "Content should start with the actual text"
    assert "{'content':" not in content, "Content should not contain dictionary string representation"
    
    # Parse features
    parser = FeatureParser()
    features = parser.parse(content)
    
    # Verify correct number of features
    assert len(features) == 5, f"Expected 5 features, got {len(features)}"
    
    # Verify each feature
    expected_features = [
        ("FEATURE[1]", "Foundation", "Project Foundation"),
        ("FEATURE[2]", "Hello API", "Hello World Endpoint"),
        ("FEATURE[3]", "Tests", "Testing Suite"),
        ("FEATURE[4]", "Docs", "API Documentation"),
        ("FEATURE[5]", "Docker", "Docker Containerization")
    ]
    
    for i, (expected_id, expected_short_name, expected_title) in enumerate(expected_features):
        feature = features[i]
        assert feature.id == expected_id, f"Feature {i}: expected id {expected_id}, got {feature.id}"
        assert feature.short_name == expected_short_name, f"Feature {i}: expected short_name {expected_short_name}, got {feature.short_name}"
        assert feature.title == expected_title, f"Feature {i}: expected title {expected_title}, got {feature.title}"
        
        # Ensure title doesn't contain multiple features (the bug)
        assert "FEATURE[2]" not in feature.title or feature.id == "FEATURE[2]", \
            f"Feature {feature.id} title contains another feature's content"
    
    print("✅ All tests passed!")
    return True


def test_string_output():
    """Test that plain string designer output still works"""
    
    designer_output = """
FEATURE[1]: User Authentication
Description: Implement user registration and login functionality.
Files: auth/user_model.py, auth/auth_service.py, auth/routes.py
Validation: Users can register and log in successfully.
Dependencies: None
Estimated Complexity: High

FEATURE[2]: Profile Management
Description: Allow users to view and update their profiles.
Files: profile/views.py, profile/serializers.py
Validation: Users can view and update profile information.
Dependencies: FEATURE[1]
Estimated Complexity: Medium
"""
    
    # Extract content (should return as-is for strings)
    content = extract_content_from_message(designer_output)
    assert content == designer_output, "String input should be returned as-is"
    
    # Parse features
    parser = FeatureParser()
    features = parser.parse(content)
    
    assert len(features) == 2, f"Expected 2 features, got {len(features)}"
    assert features[0].short_name == "Auth", "First feature should have 'Auth' as short name"
    assert features[1].short_name == "Profile Management", "Second feature should have 'Profile Management' as short name"
    
    print("✅ String output test passed!")
    return True


def test_message_object_format():
    """Test extraction from message object format"""
    
    # Simulate a message object with parts
    class MessagePart:
        def __init__(self, content):
            self.content = content
    
    class Message:
        def __init__(self, content):
            self.parts = [MessagePart(content)]
    
    message_result = [Message("""
FEATURE[1]: Basic Setup
Description: Initialize project structure.
Files: main.py
Validation: Project runs without errors.
Dependencies: None
Estimated Complexity: Low
""")]
    
    content = extract_content_from_message(message_result)
    assert "FEATURE[1]: Basic Setup" in content, "Should extract content from message parts"
    
    print("✅ Message object format test passed!")
    return True


if __name__ == "__main__":
    print("Testing feature parser bug fix...\n")
    
    try:
        test_dictionary_wrapped_output()
        test_string_output()
        test_message_object_format()
        
        print("\n🎉 All tests passed! The feature parser bug has been fixed.")
        print("\nThe fix ensures that:")
        print("1. Dictionary-wrapped designer output is properly extracted")
        print("2. Each feature is parsed individually with its own short name")
        print("3. Features are no longer concatenated into a single feature")
        print("4. The execution report will show proper feature-by-feature progress")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)