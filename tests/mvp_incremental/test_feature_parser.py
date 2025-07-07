#!/usr/bin/env python3
"""
Test script to verify the feature parser fixes work correctly.
Tests with the exact designer output that was failing.
"""
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.utils.feature_parser import FeatureParser

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Test with the exact designer output from the incremental calculator test
test_designer_output = """
# System Architecture Overview
The scientific calculator API will be built using FastAPI, structured in a modular architecture to separate concerns. Each module will handle specific functionalities, ensuring maintainability and testability. The API will support basic and advanced mathematical operations, memory functions, and history tracking.

## Components:
1. **Basic Operations Module**
2. **Advanced Operations Module**
3. **Memory Management Module**
4. **History Tracking Module**
5. **API Endpoints**
6. **Documentation**
7. **Testing**

# IMPLEMENTATION PLAN
===================

FEATURE[1]: Project Setup
Description: Set up FastAPI application structure with configuration management.
Files: main.py, requirements.txt
Validation: Application starts without errors.
Dependencies: None
Estimated Complexity: Low

FEATURE[2]: Basic Operations Module
Description: Implement basic mathematical operations with error handling.
Files: operations/basic.py
Validation: Each operation returns correct results and handles division by zero.
Dependencies: FEATURE[1]
Estimated Complexity: Medium

FEATURE[3]: Advanced Operations Module
Description: Implement advanced mathematical operations.
Files: operations/advanced.py
Validation: Each advanced operation returns correct results.
Dependencies: FEATURE[2]
Estimated Complexity: Medium

FEATURE[4]: Memory Management Module
Description: Implement memory functions for storing and recalling values.
Files: memory/memory_manager.py
Validation: Memory functions work as expected (store, recall, clear).
Dependencies: FEATURE[1]
Estimated Complexity: Medium

FEATURE[5]: History Tracking Module
Description: Implement functionality to track and manage calculation history.
Files: history/history_manager.py
Validation: History functions work as expected (add, get, clear).
Dependencies: FEATURE[1]
Estimated Complexity: Medium

FEATURE[6]: API Endpoints
Description: Create RESTful API endpoints for all operations and features.
Files: api/routes.py
Validation: All endpoints return correct responses and handle errors.
Dependencies: FEATURE[2], FEATURE[3], FEATURE[4], FEATURE[5]
Estimated Complexity: High

FEATURE[7]: Documentation
Description: Generate Swagger documentation for the API.
Files: api/docs.py
Validation: Documentation is accessible and correctly describes the API.
Dependencies: FEATURE[6]
Estimated Complexity: Low

FEATURE[8]: Testing
Description: Write unit tests for each module and perform integration testing.
Files: tests/test_operations.py, tests/test_memory.py, tests/test_history.py
Validation: All tests pass successfully.
Dependencies: FEATURE[2], FEATURE[3], FEATURE[4], FEATURE[5], FEATURE[6]
Estimated Complexity: Medium
"""

def test_feature_parser():
    """Test the feature parser with the designer output"""
    print("\n" + "="*80)
    print("Testing Feature Parser Fix")
    print("="*80)
    
    parser = FeatureParser()
    features = parser.parse(test_designer_output)
    
    print(f"\n✅ Parsed {len(features)} features")
    
    # Display parsed features
    for i, feature in enumerate(features):
        print(f"\n{'-'*60}")
        print(f"Feature {i+1}: {feature.id} - {feature.title}")
        print(f"  Description: {feature.description[:100]}{'...' if len(feature.description) > 100 else ''}")
        print(f"  Files: {', '.join(feature.files)}")
        print(f"  Dependencies: {', '.join(feature.dependencies) if feature.dependencies else 'None'}")
        print(f"  Complexity: {feature.complexity.value}")
        print(f"  Validation: {feature.validation_criteria[:100]}{'...' if len(feature.validation_criteria) > 100 else ''}")
    
    # Verify we got all 8 features
    assert len(features) == 8, f"Expected 8 features, got {len(features)}"
    
    # Verify feature IDs
    expected_ids = [f"FEATURE[{i}]" for i in range(1, 9)]
    actual_ids = [f.id for f in features]
    assert set(actual_ids) == set(expected_ids), f"Feature IDs don't match. Expected: {expected_ids}, Got: {actual_ids}"
    
    # Verify some specific features
    project_setup = next(f for f in features if f.id == "FEATURE[1]")
    assert project_setup.title == "Project Setup"
    assert project_setup.files == ["main.py", "requirements.txt"]
    assert project_setup.dependencies == []
    
    api_endpoints = next(f for f in features if f.id == "FEATURE[6]")
    assert api_endpoints.title == "API Endpoints"
    assert set(api_endpoints.dependencies) == {"FEATURE[2]", "FEATURE[3]", "FEATURE[4]", "FEATURE[5]"}
    
    print("\n✅ All assertions passed!")
    print("\n🎉 Feature parser is working correctly!")
    
    return features


def test_edge_cases():
    """Test various edge cases"""
    print("\n" + "="*80)
    print("Testing Edge Cases")
    print("="*80)
    
    parser = FeatureParser()
    
    # Test 1: No implementation plan
    print("\nTest 1: No implementation plan")
    output1 = "Some design without implementation plan"
    features1 = parser.parse(output1)
    print(f"  Result: {len(features1)} default features generated")
    
    # Test 2: Markdown format
    print("\nTest 2: Markdown format")
    output2 = """
### Feature 1: Setup
**ID**: FEATURE[1]
**Description**: Setup the project
**Files**: main.py
**Dependencies**: None
**Complexity**: Low
**Validation**: Works correctly
"""
    features2 = parser.parse(output2)
    print(f"  Result: {len(features2)} features parsed from markdown")
    
    print("\n✅ Edge case tests completed")


if __name__ == "__main__":
    try:
        # Run main test
        features = test_feature_parser()
        
        # Run edge case tests
        test_edge_cases()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED! The feature parser fix is working correctly!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)