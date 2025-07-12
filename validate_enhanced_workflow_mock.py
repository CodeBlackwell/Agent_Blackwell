#!/usr/bin/env python3
"""
Mock validation of the enhanced full workflow - demonstrates the workflow structure without requiring running agents.
"""
import asyncio
import time
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput, TeamMember, TeamMemberResult
from workflows.full.enhanced_full_workflow import (
    EnhancedFullWorkflowConfig,
    WorkflowStateManager,
    AgentCommunicationEnhancer,
    execute_enhanced_full_workflow
)
from workflows.full.phase_transition_manager import PhaseTransitionManager
from workflows.full.workflow_cache_manager import WorkflowCacheManager
from workflows.full.performance_monitor import PerformanceMonitor
from workflows.monitoring import WorkflowExecutionTracer
from unittest.mock import patch, AsyncMock


async def mock_agent_responses(agent_name: str, input_data: str, context: str):
    """Mock agent responses for testing."""
    
    # Simulate some processing time
    await asyncio.sleep(0.5)
    
    if "planner" in agent_name:
        return """Plan for Hello World REST API:

1. **Project Setup**
   - Initialize Flask application
   - Set up project structure
   - Configure requirements.txt

2. **API Implementation**
   - Create main application file (app.py)
   - Implement /hello endpoint returning JSON
   - Implement /health endpoint for health checks
   
3. **Error Handling**
   - Add 404 error handler
   - Return appropriate JSON error responses
   
4. **Configuration**
   - Add configuration file for settings
   - Support environment variables

Estimated time: 30 minutes
Technologies: Python 3.9+, Flask 2.0+"""
    
    elif "designer" in agent_name:
        return """Technical Design for Hello World REST API:

## Architecture
- Single Flask application
- RESTful design principles
- JSON response format

## File Structure:
```
hello-api/
├── app.py          # Main application
├── config.py       # Configuration
├── requirements.txt # Dependencies
└── __init__.py     # Package init
```

## API Endpoints:
1. GET /hello
   - Returns: {"message": "Hello, World!"}
   - Status: 200 OK
   
2. GET /health
   - Returns: {"status": "healthy", "timestamp": "<ISO-8601>"}
   - Status: 200 OK

## Error Handling:
- 404 errors return: {"error": "Not found", "status": 404}
- Content-Type: application/json for all responses"""
    
    elif "coder" in agent_name:
        return '''"""Hello World REST API Implementation"""
from flask import Flask, jsonify
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/hello')
def hello_world():
    """Return Hello World message."""
    return jsonify({"message": "Hello, World!"})

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "hello-api"
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found", "status": 404}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

# config.py
import os

class Config:
    """Application configuration."""
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    JSON_SORT_KEYS = False
    
# requirements.txt
Flask==2.3.3
python-dotenv==1.0.0'''
    
    elif "reviewer" in agent_name:
        return """Code Review for Hello World REST API:

## Overall Assessment: ✅ APPROVED

### Strengths:
1. **Clean Implementation**: Code is well-structured and follows Flask best practices
2. **Complete Requirements**: All specified endpoints are implemented correctly
3. **Error Handling**: Proper 404 handling with JSON responses
4. **Configuration**: Good separation of config from code
5. **Security**: No obvious security issues for this simple API

### Code Quality:
- ✅ PEP 8 compliant
- ✅ Clear function names and docstrings
- ✅ Appropriate use of Flask patterns
- ✅ JSON responses are consistent

### Suggestions for Future Enhancement:
1. Add logging for debugging
2. Consider adding CORS headers if needed
3. Add input validation for future endpoints
4. Consider rate limiting for production

### Testing Recommendations:
- Unit tests for each endpoint
- Integration tests for error handling
- Load testing if expecting high traffic

**Verdict**: Code is production-ready for the given requirements."""
    
    else:
        return f"Mock response from {agent_name}"


async def validate_enhanced_workflow_with_mocks():
    """Validate the enhanced full workflow using mocked agent responses."""
    
    print("\n" + "="*80)
    print("🧪 Enhanced Full Workflow Validation (Mock Mode)")
    print("="*80 + "\n")
    
    # Create test input
    test_requirements = """Build a Hello World REST API with the following requirements:
1. Use Python with Flask framework
2. Create a single endpoint GET /hello
3. Return JSON response: {"message": "Hello, World!"}
4. Include error handling for 404 routes
5. Add a health check endpoint at GET /health"""
    
    input_data = CodingTeamInput(
        requirements=test_requirements,
        workflow_type="enhanced_full",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ],
        skip_docker_cleanup=True
    )
    
    # Create configuration
    config = EnhancedFullWorkflowConfig()
    config.phase_timeout = 30  # Shorter timeout for testing
    config.enable_caching = True
    config.retry_delays = [1, 2]  # Shorter delays for testing
    
    print("📋 Configuration:")
    print(f"  • Caching: {'Enabled' if config.enable_caching else 'Disabled'}")
    print(f"  • Rollback: {'Enabled' if config.enable_rollback else 'Disabled'}")
    print(f"  • Context Enrichment: {'Enabled' if config.enable_context_enrichment else 'Disabled'}")
    print(f"  • Performance Monitoring: Enabled")
    print()
    
    # Mock the agent calls
    with patch('core.orchestrator_client.call_agent_via_orchestrator', side_effect=mock_agent_responses):
        with patch('workflows.incremental.feature_orchestrator.run_incremental_coding_phase') as mock_incremental:
            # Mock the incremental coding phase to return the code directly
            mock_incremental.return_value = (
                await mock_agent_responses("coder", "", ""),
                {
                    "total_features": 1,
                    "completed_features": 1,
                    "success_rate": 100.0,
                    "execution_time": 2.5
                }
            )
            
            try:
                print("🚀 Starting enhanced workflow execution...\n")
                start_time = time.time()
                
                # Execute the enhanced workflow
                results, report = await execute_enhanced_full_workflow(input_data, config)
                
                execution_time = time.time() - start_time
                
                print(f"\n✅ Workflow completed in {execution_time:.2f} seconds")
                print(f"📊 Status: {report.status}")
                print(f"🆔 Execution ID: {report.execution_id}")
                
                # Display results
                print("\n" + "-"*80)
                print("📝 Phase Results:")
                print("-"*80 + "\n")
                
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.name.upper()} Phase:")
                    print("-" * 40)
                    # Show preview of output
                    lines = result.output.split('\n')[:10]
                    for line in lines:
                        print(f"   {line}")
                    if len(result.output.split('\n')) > 10:
                        print("   ... (truncated)")
                    print()
                
                # Display performance metrics
                if hasattr(report, 'metadata') and 'performance_metrics' in report.metadata:
                    metrics = report.metadata['performance_metrics']
                    print("\n📈 Performance Metrics:")
                    print("-" * 40)
                    print(f"  • Total Duration: {metrics.get('duration', 0):.2f}s")
                    print(f"  • Phase Count: {metrics.get('phase_count', 0)}")
                    print(f"  • Error Count: {metrics.get('error_count', 0)}")
                    print(f"  • Cache Hit Rate: {metrics.get('cache_hit_rate', 'N/A')}")
                    
                    if 'phase_breakdown' in metrics:
                        print("\n  Phase Timing:")
                        for phase in metrics['phase_breakdown']:
                            cache_indicator = " 📦" if phase.get('cache_hit') else ""
                            print(f"    - {phase['phase']}: {phase.get('duration', 0):.3f}s{cache_indicator}")
                
                # Display cache statistics
                print("\n💾 Cache Statistics:")
                print("-" * 40)
                if 'cache_stats' in metrics:
                    stats = metrics['cache_stats']
                    print(f"  • Cache Enabled: {stats.get('enabled', False)}")
                    print(f"  • Cache Size: {stats.get('size', 0)}")
                    print(f"  • Hits: {stats.get('hits', 0)}")
                    print(f"  • Misses: {stats.get('misses', 0)}")
                
                # Test caching by running again
                print("\n🔄 Testing cache effectiveness (running workflow again)...")
                start_time2 = time.time()
                results2, report2 = await execute_enhanced_full_workflow(input_data, config)
                execution_time2 = time.time() - start_time2
                
                print(f"✅ Second run completed in {execution_time2:.2f} seconds")
                print(f"⚡ Speed improvement: {(execution_time - execution_time2) / execution_time * 100:.1f}%")
                
                # Validate generated code
                print("\n" + "="*80)
                print("🔍 Validation Checks:")
                print("="*80)
                
                code_result = next((r for r in results if r.name == "coder"), None)
                
                checks = {
                    "Workflow completed successfully": report.status == "completed",
                    "All phases executed": len(results) == 4,
                    "Planning phase completed": any("plan" in r.output.lower() for r in results if r.name == "planner"),
                    "Design phase completed": any("design" in r.output.lower() for r in results if r.name == "designer"),
                    "Code generation completed": code_result is not None,
                    "Flask import present": code_result and "from flask import" in code_result.output,
                    "Hello endpoint implemented": code_result and "@app.route('/hello')" in code_result.output,
                    "Health endpoint implemented": code_result and "@app.route('/health')" in code_result.output,
                    "404 handler implemented": code_result and "@app.errorhandler(404)" in code_result.output,
                    "JSON response correct": code_result and '"Hello, World!"' in code_result.output,
                    "Review completed": any("approved" in r.output.lower() for r in results if r.name == "reviewer"),
                    "Performance monitoring active": 'performance_metrics' in report.metadata,
                    "Cache utilized on second run": execution_time2 < execution_time * 0.8
                }
                
                all_passed = True
                for check, passed in checks.items():
                    status = "✅" if passed else "❌"
                    print(f"{status} {check}")
                    if not passed:
                        all_passed = False
                
                print("\n" + "="*80)
                if all_passed:
                    print("🎉 All validation checks passed!")
                    print("✅ The enhanced full workflow is working correctly!")
                    print("\nKey Features Demonstrated:")
                    print("  • Phased execution with smooth transitions")
                    print("  • Performance monitoring and metrics")
                    print("  • Caching for improved performance")
                    print("  • Context enrichment between phases")
                    print("  • Comprehensive error handling")
                    print("  • Rollback capabilities (not triggered in this test)")
                else:
                    print("❌ Some validation checks failed")
                print("="*80 + "\n")
                
                return all_passed
                
            except Exception as e:
                print(f"\n❌ Error during workflow execution: {str(e)}")
                import traceback
                traceback.print_exc()
                return False


def main():
    """Main entry point."""
    print("🚀 Enhanced Full Workflow Validation (Mock Mode)")
    print("This demonstrates the enhanced workflow features without requiring running agents\n")
    
    success = asyncio.run(validate_enhanced_workflow_with_mocks())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()