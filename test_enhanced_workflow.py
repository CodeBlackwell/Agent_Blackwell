#!/usr/bin/env python3
"""
Test script for the Enhanced Full Workflow.
Run this after starting the orchestrator service.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.workflow_manager import execute_workflow
from workflows.full.enhanced_full_workflow import EnhancedFullWorkflowConfig


async def test_enhanced_workflow():
    """Test the enhanced full workflow with a simple example."""
    
    print("\n" + "="*60)
    print("🧪 Testing Enhanced Full Workflow")
    print("="*60 + "\n")
    
    # Define your test requirements
    requirements = """
Create a simple Python calculator with the following features:
1. Basic operations: add, subtract, multiply, divide
2. Handle division by zero gracefully
3. Include a command-line interface
4. Add unit tests for all operations
"""
    
    # Create workflow input
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="enhanced_full",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ],
        skip_docker_cleanup=True  # Skip Docker for testing
    )
    
    # Optional: Configure the enhanced features
    # (If you don't create a config, it will use defaults)
    config = EnhancedFullWorkflowConfig()
    config.enable_caching = True          # Enable caching
    config.retry_delays = [2, 5, 10]      # Retry delays in seconds
    config.phase_timeout = 120            # 2 minute timeout per phase
    
    print("📋 Requirements:")
    print(requirements)
    print("\n🔧 Configuration:")
    print(f"  - Caching: {'Enabled' if config.enable_caching else 'Disabled'}")
    print(f"  - Retry delays: {config.retry_delays}")
    print(f"  - Phase timeout: {config.phase_timeout}s")
    print(f"  - Rollback: {'Enabled' if config.enable_rollback else 'Disabled'}")
    print(f"  - Context enrichment: {'Enabled' if config.enable_context_enrichment else 'Disabled'}")
    
    try:
        print("\n🚀 Starting workflow execution...\n")
        
        # Execute the workflow
        results, report = await execute_workflow(input_data)
        
        print(f"\n✅ Workflow completed!")
        print(f"📊 Status: {report.status}")
        print(f"🆔 Execution ID: {report.execution_id}")
        
        # Display results from each agent
        print("\n" + "-"*60)
        print("📝 Agent Results:")
        print("-"*60)
        
        for result in results:
            print(f"\n{result.name.upper()}:")
            # Show first 300 chars of output
            preview = result.output[:300] + "..." if len(result.output) > 300 else result.output
            print(preview)
        
        # Display performance metrics
        if hasattr(report, 'metadata') and 'performance_metrics' in report.metadata:
            metrics = report.metadata['performance_metrics']
            print("\n" + "-"*60)
            print("📈 Performance Metrics:")
            print("-"*60)
            print(f"  Total duration: {metrics.get('duration', 0):.2f}s")
            print(f"  Phase count: {metrics.get('phase_count', 0)}")
            print(f"  Error count: {metrics.get('error_count', 0)}")
            print(f"  Retry count: {metrics.get('retry_count', 0)}")
            print(f"  Cache hit rate: {metrics.get('cache_hit_rate', 'N/A')}")
            
            # Show optimization suggestions if any
            if 'optimization_suggestions' in report.metadata:
                suggestions = report.metadata['optimization_suggestions']
                if suggestions:
                    print("\n💡 Optimization Suggestions:")
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")
        
        # Test caching by running again
        print("\n" + "="*60)
        print("🔄 Testing cache (running same workflow again)...")
        print("="*60)
        
        import time
        start = time.time()
        results2, report2 = await execute_workflow(input_data)
        elapsed = time.time() - start
        
        print(f"\n✅ Second run completed in {elapsed:.2f}s")
        
        if hasattr(report2, 'metadata') and 'performance_metrics' in report2.metadata:
            metrics2 = report2.metadata['performance_metrics']
            if 'cache_hit_rate' in metrics2:
                print(f"📦 Cache hit rate: {metrics2['cache_hit_rate']}")
        
        # Find the generated code
        coder_result = next((r for r in results if r.name == "coder"), None)
        if coder_result:
            print("\n" + "="*60)
            print("💻 Generated Code Preview:")
            print("="*60)
            lines = coder_result.output.split('\n')[:50]  # First 50 lines
            for line in lines:
                print(line)
            if len(coder_result.output.split('\n')) > 50:
                print("\n... (truncated)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n⚠️  Make sure the orchestrator is running:")
        print("    python orchestrator/orchestrator_agent.py")
        return False


def main():
    """Main entry point."""
    print("Enhanced Full Workflow Test Script")
    print("Make sure the orchestrator is running before proceeding!")
    print("\nTo start the orchestrator in another terminal:")
    print("  python orchestrator/orchestrator_agent.py\n")
    
    input("Press Enter when the orchestrator is running...")
    
    success = asyncio.run(test_enhanced_workflow())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()