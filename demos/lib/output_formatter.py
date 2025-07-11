"""
Output formatter for displaying workflow results.
"""
from typing import Dict, Any, List
import json
from datetime import datetime


class OutputFormatter:
    """Formats and displays workflow output."""
    
    def __init__(self):
        self.width = 80
        
    def format_workflow_result(self, result: Dict[str, Any]):
        """Format and display workflow execution result."""
        print("\n" + "=" * self.width)
        print("WORKFLOW EXECUTION COMPLETE".center(self.width))
        print("=" * self.width)
        
        # Basic info
        if 'session_id' in result:
            print(f"\n📋 Session ID: {result['session_id']}")
        if 'workflow_type' in result:
            print(f"🔄 Workflow Type: {result['workflow_type']}")
        if 'duration' in result:
            print(f"⏱️  Duration: {result['duration']:.2f} seconds")
            
        # Files generated
        if 'files_generated' in result:
            print(f"\n📁 Files Generated: {len(result['files_generated'])}")
            for file in result['files_generated'][:5]:  # Show first 5
                print(f"   - {file}")
            if len(result['files_generated']) > 5:
                print(f"   ... and {len(result['files_generated']) - 5} more")
                
        # Test results
        if 'test_results' in result:
            self._format_test_results(result['test_results'])
            
        # Errors
        if 'errors' in result and result['errors']:
            print(f"\n❌ Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Show first 3
                print(f"   - {error}")
                
        print("\n" + "=" * self.width)
        
    def _format_test_results(self, test_results: Dict[str, Any]):
        """Format test results section."""
        print("\n🧪 Test Results:")
        
        if 'total' in test_results:
            print(f"   Total Tests: {test_results['total']}")
        if 'passed' in test_results:
            print(f"   ✅ Passed: {test_results['passed']}")
        if 'failed' in test_results:
            print(f"   ❌ Failed: {test_results['failed']}")
        if 'coverage' in test_results:
            print(f"   📊 Coverage: {test_results['coverage']}%")
            
    def format_error(self, error: Exception):
        """Format error message."""
        print("\n" + "=" * self.width)
        print("❌ ERROR OCCURRED".center(self.width))
        print("=" * self.width)
        print(f"\nError Type: {type(error).__name__}")
        print(f"Message: {str(error)}")
        print("\n" + "=" * self.width)
        
    def format_test_output(self, output: str, passed: bool):
        """Format test execution output."""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\n{status}")
        print("-" * 40)
        print(output)
        print("-" * 40)