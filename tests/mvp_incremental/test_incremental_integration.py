#!/usr/bin/env python3
"""
Integration test for incremental coding following ACP patterns
"""
import sys
import os
import asyncio
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


def test_imports():
    """Test that all new modules can be imported"""
    try:
        # Test feature parser
        from shared.utils.feature_parser import FeatureParser, Feature, ComplexityLevel
        print("✅ Feature parser imports successfully")
        
        # Test incremental executor
        from orchestrator.utils.incremental_executor import IncrementalExecutor, ValidationResult
        print("✅ Incremental executor imports successfully")
        
        # Test feature orchestrator
        from workflows.incremental.feature_orchestrator import FeatureOrchestrator
        print("✅ Feature orchestrator imports successfully")
        
        assert True  # Use assert instead of return
    except ImportError as e:
        print(f"❌ Import error: {e}")
        pytest.fail(f"Import error: {e}")


def test_feature_parser():
    """Test basic feature parsing"""
    from shared.utils.feature_parser import FeatureParser
    
    test_output = """
    IMPLEMENTATION PLAN:
    ===================
    
    FEATURE[1]: Project Setup
    Description: Initialize project structure
    Files: app.py, config.py
    Validation: App starts without errors
    Dependencies: None
    Estimated Complexity: Low
    """
    
    parser = FeatureParser()
    features = parser.parse(test_output)
    
    assert features is not None, "Features should not be None"
    assert len(features) == 1, f"Expected 1 feature, got {len(features)}"
    print("✅ Feature parser works correctly")


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator can be initialized"""
    try:
        from workflows.incremental.feature_orchestrator import FeatureOrchestrator
        from workflows.monitoring import WorkflowExecutionTracer  # Updated import path
        
        # Create mock tracer
        tracer = WorkflowExecutionTracer(workflow_type="incremental", execution_id="test_123")
        
        # Initialize orchestrator
        orchestrator = FeatureOrchestrator(tracer)
        
        print("✅ Orchestrator initialization successful")
        assert True  # Test passed
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        pytest.fail(f"Orchestrator initialization failed: {e}")


async def main():
    """Run all tests"""
    print("🧪 Testing ACP incremental coding integration...\n")
    
    all_passed = True
    
    # Run sync tests
    if not test_imports():
        all_passed = False
    
    if not test_feature_parser():
        all_passed = False
    
    # Run async tests
    if not await test_orchestrator_initialization():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All tests passed! Integration ready.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
