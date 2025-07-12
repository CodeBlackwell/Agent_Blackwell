#!/usr/bin/env python3
"""
Simple validation script to test the enhanced full workflow with a Hello World API request.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.workflow_manager import execute_workflow
from workflows.full.enhanced_full_workflow import EnhancedFullWorkflowConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_enhanced_workflow():
    """Validate the enhanced full workflow with a simple Hello World API request."""
    print("\n" + "="*60)
    print("🚀 Enhanced Full Workflow Validation Test")
    print("="*60 + "\n")
    
    # Create the test input
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
        skip_docker_cleanup=True  # Skip Docker for this test
    )
    
    print(f"📋 Test Requirements:\n{test_requirements}\n")
    print(f"👥 Team Members: {[m.value for m in input_data.team_members]}")
    print(f"🔧 Workflow Type: {input_data.workflow_type}\n")
    
    try:
        # Execute the workflow
        print("🏃 Starting workflow execution...\n")
        start_time = asyncio.get_event_loop().time()
        
        results, report = await execute_workflow(input_data)
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        print(f"\n✅ Workflow completed in {execution_time:.2f} seconds")
        print(f"📊 Execution Status: {report.status}")
        
        # Display results from each agent
        print("\n" + "-"*60)
        print("📝 Agent Results:")
        print("-"*60 + "\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name.upper()} ({result.team_member.value}):")
            print("-" * 40)
            # Show first 500 chars of output
            output_preview = result.output[:500] + "..." if len(result.output) > 500 else result.output
            print(output_preview)
            print("\n")
        
        # Check if code was generated
        code_result = next((r for r in results if r.name == "coder"), None)
        if code_result:
            print("💻 Generated Code Preview:")
            print("-" * 60)
            code_lines = code_result.output.split('\n')[:30]  # First 30 lines
            for line in code_lines:
                print(line)
            if len(code_result.output.split('\n')) > 30:
                print("... (truncated)")
            print("-" * 60 + "\n")
        
        # Display performance metrics if available
        if hasattr(report, 'metadata') and 'performance_metrics' in report.metadata:
            perf_metrics = report.metadata['performance_metrics']
            print("📈 Performance Metrics:")
            print("-" * 40)
            print(f"Total Duration: {perf_metrics.get('duration', 0):.2f}s")
            print(f"Phase Count: {perf_metrics.get('phase_count', 0)}")
            print(f"Error Count: {perf_metrics.get('error_count', 0)}")
            print(f"Retry Count: {perf_metrics.get('retry_count', 0)}")
            
            if 'cache_hit_rate' in perf_metrics:
                print(f"Cache Hit Rate: {perf_metrics['cache_hit_rate']}")
                
            if 'phase_breakdown' in perf_metrics:
                print("\nPhase Breakdown:")
                for phase in perf_metrics['phase_breakdown']:
                    status = "✅" if phase['success'] else "❌"
                    cache = "📦" if phase.get('cache_hit') else ""
                    print(f"  {status} {phase['phase']}: {phase.get('duration', 0):.2f}s {cache}")
                    
        # Display optimization suggestions if available
        if hasattr(report, 'metadata') and 'optimization_suggestions' in report.metadata:
            suggestions = report.metadata['optimization_suggestions']
            if suggestions:
                print("\n💡 Optimization Suggestions:")
                print("-" * 40)
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
                    
        # Validation checks
        print("\n" + "="*60)
        print("🔍 Validation Results:")
        print("="*60)
        
        checks = {
            "Workflow completed successfully": report.status == "completed",
            "All agents executed": len(results) == len(input_data.team_members),
            "Plan generated": any("plan" in r.output.lower() for r in results if r.name == "planner"),
            "Design created": any("design" in r.output.lower() or "api" in r.output.lower() for r in results if r.name == "designer"),
            "Code generated": code_result is not None and "flask" in code_result.output.lower(),
            "Hello endpoint created": code_result is not None and "/hello" in code_result.output,
            "JSON response included": code_result is not None and "Hello, World!" in code_result.output,
            "Review completed": any("review" in r.output.lower() or "good" in r.output.lower() for r in results if r.name == "reviewer")
        }
        
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_passed = False
                
        print("\n" + "="*60)
        if all_passed:
            print("🎉 All validation checks passed!")
            print("✅ The enhanced full workflow is working correctly!")
        else:
            print("❌ Some validation checks failed.")
            print("Please review the output above for details.")
        print("="*60 + "\n")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {str(e)}")
        logger.exception("Workflow execution failed")
        return False


async def test_with_custom_config():
    """Test the enhanced workflow with custom configuration."""
    print("\n" + "="*60)
    print("🔧 Testing with Custom Configuration")
    print("="*60 + "\n")
    
    # Create custom config
    config = EnhancedFullWorkflowConfig()
    config.enable_caching = True
    config.max_review_retries = 2
    config.retry_delays = [0.5, 1, 2]
    config.phase_timeout = 60  # 1 minute timeout
    config.skip_phases = []  # Don't skip any phases
    
    print("📋 Custom Configuration:")
    print(f"  • Caching: {'Enabled' if config.enable_caching else 'Disabled'}")
    print(f"  • Max Review Retries: {config.max_review_retries}")
    print(f"  • Retry Delays: {config.retry_delays}")
    print(f"  • Phase Timeout: {config.phase_timeout}s")
    print(f"  • Feedback Loop: {'Enabled' if config.enable_feedback_loop else 'Disabled'}")
    print(f"  • Context Enrichment: {'Enabled' if config.enable_context_enrichment else 'Disabled'}")
    print()
    
    # Note: In a real test, you would pass this config to the workflow
    # For now, we'll just display it
    print("ℹ️  Custom configuration would be applied in production usage")
    

def main():
    """Main entry point."""
    print("🧪 Enhanced Full Workflow Validation Script")
    print("This script tests the enhanced full workflow with a Hello World API request\n")
    
    # Run the validation
    success = asyncio.run(validate_enhanced_workflow())
    
    # Optionally show custom config example
    if success:
        asyncio.run(test_with_custom_config())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()