"""
Test the MVP Incremental TDD workflow with vague requirements
This tests the full end-to-end behavior with enhanced prompts
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor


async def test_vague_api_requirement():
    """Test that vague API requirement expands to multiple features"""
    print("\n" + "="*60)
    print("TEST: Vague API Requirement")
    print("="*60)
    
    # Very vague requirement
    input_data = CodingTeamInput(
        requirements="Create a REST API",
        workflow_type="mvp_incremental_tdd",
        run_tests=False  # Skip execution for this test
    )
    
    try:
        # Execute workflow
        print("\nExecuting workflow with vague requirement...")
        results, report = await execute_workflow(input_data)
        
        # Check results
        print(f"\nWorkflow completed with {len(results)} results")
        
        # Find designer output
        designer_output = None
        for result in results:
            if result.team_member.value == "designer":
                designer_output = result.output
                break
        
        assert designer_output, "Designer output not found"
        
        # Count features in designer output
        feature_count = designer_output.count("FEATURE[")
        print(f"\nDesigner created {feature_count} features")
        
        # Should have expanded to multiple features
        assert feature_count >= 5, f"Expected at least 5 features, got {feature_count}"
        
        # Verify essential API features are included
        essential_keywords = ["setup", "model", "auth", "endpoint", "validation", "test", "doc"]
        found_keywords = []
        
        for keyword in essential_keywords:
            if keyword.lower() in designer_output.lower():
                found_keywords.append(keyword)
        
        print(f"Found essential components: {found_keywords}")
        assert len(found_keywords) >= 5, f"Missing essential API components, only found: {found_keywords}"
        
        print("\n✅ Vague API requirement test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


async def test_vague_web_app_requirement():
    """Test that vague web app requirement expands appropriately"""
    print("\n" + "="*60)
    print("TEST: Vague Web App Requirement")
    print("="*60)
    
    input_data = CodingTeamInput(
        requirements="Build a web application",
        workflow_type="mvp_incremental_tdd",
        run_tests=False
    )
    
    try:
        print("\nExecuting workflow with vague web app requirement...")
        results, report = await execute_workflow(input_data)
        
        # Find designer output
        designer_output = None
        for result in results:
            if result.team_member.value == "designer":
                designer_output = result.output
                break
        
        assert designer_output, "Designer output not found"
        
        # Count features
        feature_count = designer_output.count("FEATURE[")
        print(f"\nDesigner created {feature_count} features")
        
        # Should have multiple features for web app
        assert feature_count >= 4, f"Expected at least 4 features for web app, got {feature_count}"
        
        # Check for web app components
        web_keywords = ["frontend", "backend", "component", "ui", "state", "api"]
        found_keywords = []
        
        for keyword in web_keywords:
            if keyword.lower() in designer_output.lower():
                found_keywords.append(keyword)
        
        print(f"Found web app components: {found_keywords}")
        assert len(found_keywords) >= 3, f"Missing web app components, only found: {found_keywords}"
        
        print("\n✅ Vague web app requirement test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


async def test_specific_requirement_not_overexpanded():
    """Test that specific requirements are not over-expanded"""
    print("\n" + "="*60)
    print("TEST: Specific Requirement Not Over-expanded")
    print("="*60)
    
    input_data = CodingTeamInput(
        requirements="""Create a simple calculator with only these functions:
        1. add(a, b) - returns a + b
        2. subtract(a, b) - returns a - b
        No other features needed.""",
        workflow_type="mvp_incremental_tdd",
        run_tests=False
    )
    
    try:
        print("\nExecuting workflow with specific requirement...")
        results, report = await execute_workflow(input_data)
        
        # Find designer output
        designer_output = None
        for result in results:
            if result.team_member.value == "designer":
                designer_output = result.output
                break
        
        assert designer_output, "Designer output not found"
        
        # Count features
        feature_count = designer_output.count("FEATURE[")
        print(f"\nDesigner created {feature_count} features")
        
        # Should not over-expand specific requirements
        assert feature_count <= 4, f"Over-expanded specific requirement to {feature_count} features"
        
        # Should have calculator functions
        assert "add" in designer_output.lower(), "Missing add function"
        assert "subtract" in designer_output.lower(), "Missing subtract function"
        
        # Should NOT have unnecessary features
        unwanted = ["authentication", "database", "api", "endpoint"]
        found_unwanted = [kw for kw in unwanted if kw in designer_output.lower()]
        
        assert len(found_unwanted) == 0, f"Added unnecessary features: {found_unwanted}"
        
        print("\n✅ Specific requirement test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


async def test_intelligent_extractor_with_real_workflow():
    """Test that the intelligent extractor properly handles real workflow output"""
    print("\n" + "="*60)
    print("TEST: Intelligent Extractor Integration")
    print("="*60)
    
    # Simulate minimal design output
    minimal_design = """
Technical Design for REST API:

FEATURE[1]: Complete API Implementation
Description: Build the entire REST API system
Validation: API works correctly
Dependencies: None
"""
    
    # Test intelligent extraction
    features = IntelligentFeatureExtractor.extract_features(
        plan="Build a REST API",
        design=minimal_design,
        requirements="Create a REST API"
    )
    
    print(f"\nIntelligent extractor found {len(features)} features")
    for i, feature in enumerate(features):
        print(f"  {i+1}. {feature['title']}")
    
    # Should expand to full feature set
    assert len(features) >= 7, f"Expected at least 7 features, got {len(features)}"
    
    print("\n✅ Intelligent extractor test PASSED")
    return True


async def main():
    """Run all vague requirement tests"""
    print("\n" + "="*80)
    print("Running Vague Requirements Tests for MVP Incremental TDD")
    print("="*80)
    
    # Check if orchestrator is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/health") as resp:
                if resp.status != 200:
                    print("\n⚠️  WARNING: Orchestrator server not responding on port 8080")
                    print("Please start the orchestrator: python orchestrator/orchestrator_agent.py")
                    return
    except:
        print("\n⚠️  WARNING: Cannot connect to orchestrator server on port 8080")
        print("Please start the orchestrator: python orchestrator/orchestrator_agent.py")
        return
    
    # Run tests
    tests = [
        test_intelligent_extractor_with_real_workflow,
        test_vague_api_requirement,
        test_vague_web_app_requirement,
        test_specific_requirement_not_overexpanded
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test {test.__name__} crashed: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 All tests passed! The vague requirements handling is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())