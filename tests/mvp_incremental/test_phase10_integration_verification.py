#!/usr/bin/env python3
"""
Test script for Phase 10: Integration Verification functionality
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.mvp_incremental.integration_verification import (
    IntegrationVerifier, IntegrationTestResult, CompletionReport,
    perform_integration_verification
)
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.test_execution import TestResult


async def test_basic_integration_verification():
    """Test basic integration verification functionality."""
    print("🔍 Testing basic integration verification...")
    
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create sample project files
        main_file = project_path / "main.py"
        main_file.write_text('''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == "__main__":
    print("Calculator ready!")
    print(f"2 + 3 = {add(2, 3)}")
''')
        
        # Create validator and verifier
        validator = CodeValidator(working_dir=project_path)
        verifier = IntegrationVerifier(validator)
        
        # Mock features
        features = [
            {"name": "Add function", "id": "feature_1", "status": "completed"},
            {"name": "Subtract function", "id": "feature_2", "status": "completed"}
        ]
        
        # Mock workflow report
        class MockWorkflowReport:
            output_path = str(project_path)
            total_duration = "45 seconds"
        
        workflow_report = MockWorkflowReport()
        
        # Run verification
        result = await verifier.verify_integration(
            project_path,
            features,
            workflow_report
        )
        
        print(f"✅ Integration verification completed")
        print(f"   All tests pass: {result.all_tests_pass}")
        print(f"   Build successful: {result.build_successful}")
        print(f"   Smoke test passed: {result.smoke_test_passed}")
        print(f"   Issues found: {len(result.issues_found)}")
        
        assert result.all_tests_pass, "Expected tests to pass (no tests = success)"
        assert result.build_successful, "Expected build to succeed"
        

async def test_smoke_test_execution():
    """Test smoke test functionality."""
    print("\n💨 Testing smoke test execution...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create a simple main.py that runs successfully
        main_file = project_path / "main.py"
        main_file.write_text('''
print("Application started successfully!")
''')
        
        validator = CodeValidator(working_dir=project_path)
        verifier = IntegrationVerifier(validator)
        
        # Run smoke test
        passed, output = await verifier._run_smoke_test(project_path)
        
        print(f"✅ Smoke test completed")
        print(f"   Passed: {passed}")
        print(f"   Output preview: {output[:100]}...")
        
        assert passed, "Smoke test should pass for simple script"
        assert "SUCCESS" in output, "Should contain success message"
        

async def test_completion_report_generation():
    """Test completion report generation."""
    print("\n📄 Testing completion report generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        validator = CodeValidator(working_dir=project_path)
        verifier = IntegrationVerifier(validator)
        
        # Mock data
        features = [
            {"name": "Feature A", "id": "f1", "status": "completed", "retries": 0},
            {"name": "Feature B", "id": "f2", "status": "completed", "retries": 1},
            {"name": "Feature C", "id": "f3", "status": "failed", "retries": 3}
        ]
        
        integration_result = IntegrationTestResult(
            all_tests_pass=True,
            unit_test_results=TestResult(True, 10, 2, [], "test output", ["test_file.py"]),
            integration_test_results=None,
            smoke_test_passed=True,
            smoke_test_output="App started",
            build_successful=True,
            build_output="Build ok",
            feature_interactions={"f1 <-> f2": True},
            issues_found=["Feature C failed after 3 retries"]
        )
        
        class MockWorkflowReport:
            output_path = str(project_path)
            total_duration = "2 minutes"
        
        # Generate report
        report = await verifier.generate_completion_report(
            "Test Project",
            features,
            integration_result,
            MockWorkflowReport(),
            project_path
        )
        
        print(f"✅ Completion report generated")
        print(f"   Project: {report.project_name}")
        print(f"   Features: {len(report.features_implemented)}")
        print(f"   Known issues: {len(report.known_issues)}")
        print(f"   Recommendations: {len(report.recommendations)}")
        
        assert report.project_name == "Test Project"
        assert len(report.features_implemented) == 3
        assert len(report.known_issues) == 1
        assert len(report.recommendations) > 0
        
        # Save and verify report file
        report_path = verifier.save_completion_report(report, project_path)
        assert report_path.exists(), "Report file should be created"
        assert (project_path / "completion_report.json").exists(), "JSON report should be created"
        

async def test_build_verification():
    """Test build verification functionality."""
    print("\n🔨 Testing build verification...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create setup.py
        setup_file = project_path / "setup.py"
        setup_file.write_text('''
from setuptools import setup

setup(
    name="test-project",
    version="0.1.0",
    py_modules=["main"],
)
''')
        
        validator = CodeValidator(working_dir=project_path)
        verifier = IntegrationVerifier(validator)
        
        # Verify build
        success, output = await verifier._verify_build(project_path)
        
        print(f"✅ Build verification completed")
        print(f"   Success: {success}")
        print(f"   Output: {output[:100]}...")
        
        # Note: May fail if setuptools not available, but should not crash
        assert isinstance(success, bool), "Should return boolean"
        assert isinstance(output, str), "Should return string output"
        

async def test_metrics_calculation():
    """Test metrics calculation."""
    print("\n📊 Testing metrics calculation...")
    
    validator = CodeValidator()
    verifier = IntegrationVerifier(validator)
    
    features = [
        {"name": "F1", "status": "completed", "retries": 0},
        {"name": "F2", "status": "completed", "retries": 2},
        {"name": "F3", "status": "failed", "retries": 3},
    ]
    
    integration_result = IntegrationTestResult(
        all_tests_pass=True,
        unit_test_results=TestResult(True, 8, 2, [], "", []),
        integration_test_results=None,
        smoke_test_passed=True,
        smoke_test_output="",
        build_successful=True,
        build_output="",
        feature_interactions={},
        issues_found=[]
    )
    
    class MockReport:
        total_duration = "120 seconds"
        output_path = "/tmp/test"
    
    metrics = verifier._calculate_metrics(features, integration_result, MockReport())
    
    print(f"✅ Metrics calculated")
    print(f"   Total features: {metrics['total_features']}")
    print(f"   Completed: {metrics['completed_features']}")
    print(f"   Completion rate: {metrics['completion_rate']}")
    print(f"   Total retries: {metrics['total_retries']}")
    print(f"   Test success rate: {metrics['test_success_rate']}")
    
    assert metrics['total_features'] == 3
    assert metrics['completed_features'] == 2
    assert metrics['total_retries'] == 5
    assert "80.0%" in metrics['test_success_rate']
    

async def test_full_integration_flow():
    """Test the complete integration verification flow."""
    print("\n🚀 Testing full integration flow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create a simple project
        (project_path / "calculator.py").write_text('''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
''')
        
        features = [
            {"name": "Calculator class", "id": "f1", "status": "completed"},
            {"name": "Add method", "id": "f2", "status": "completed"},
            {"name": "Multiply method", "id": "f3", "status": "completed"}
        ]
        
        class MockReport:
            output_path = str(project_path)
            total_duration = "30 seconds"
        
        # Run full integration verification
        integration_result, completion_report = await perform_integration_verification(
            project_path,
            features,
            MockReport(),
            "Calculator Project"
        )
        
        print(f"✅ Full integration completed")
        print(f"   Project: {completion_report.project_name}")
        print(f"   Build status: {completion_report.build_status}")
        print(f"   Metrics: {completion_report.metrics}")
        
        assert completion_report.project_name == "Calculator Project"
        assert len(completion_report.features_implemented) == 3
        assert completion_report.build_status in ["SUCCESS", "FAILED"]
        assert "total_features" in completion_report.metrics
        

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 10: Integration Verification - Test Suite")
    print("=" * 60)
    
    try:
        await test_basic_integration_verification()
        await test_smoke_test_execution()
        await test_completion_report_generation()
        await test_build_verification()
        await test_metrics_calculation()
        await test_full_integration_flow()
        
        print("\n✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())