"""
Test the incremental workflow with various scenarios.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_incremental_workflow():
    """Test the incremental workflow with a simple calculator example."""
    print("\n🧪 Testing Incremental Workflow")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Simple Calculator",
            "requirements": """Create a simple calculator class with the following features:
            1. Add two numbers
            2. Subtract two numbers
            3. Multiply two numbers
            4. Divide two numbers (with error handling for division by zero)
            
            Each operation should be implemented as a separate method."""
        },
        {
            "name": "TODO API",
            "requirements": """Create a REST API for managing TODO items with these features:
            1. Create a new TODO item with title and description
            2. List all TODO items
            3. Get a specific TODO item by ID
            4. Update a TODO item's status (pending/completed)
            5. Delete a TODO item
            
            Use FastAPI and include proper error handling for each endpoint."""
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test Case: {test_case['name']}")
        print("-" * 40)
        
        # Create input data
        input_data = CodingTeamInput(
            requirements=test_case["requirements"],
            workflow_type="incremental"
        )
        
        # Create tracer
        tracer = WorkflowExecutionTracer("incremental")
        
        try:
            # Execute workflow
            print("⏳ Executing incremental workflow...")
            results, report = await execute_workflow(input_data, tracer)
            
            print(f"✅ Workflow completed successfully!")
            print(f"   - Total agents involved: {len(results)}")
            print(f"   - Total duration: {report.overall_duration:.2f}s")
            
            # Print feature implementation summary
            if hasattr(report, 'metadata') and 'incremental_execution_metrics' in report.metadata:
                metrics = report.metadata['incremental_execution_metrics']
                print(f"\n📊 Feature Implementation Summary:")
                print(f"   - Features implemented: {metrics.get('features_implemented', 'N/A')}")
                print(f"   - Total features: {metrics.get('total_features', 'N/A')}")
                if 'feature_details' in metrics:
                    print(f"\n   Feature Details:")
                    for feature in metrics['feature_details']:
                        print(f"   - {feature['id']}: {feature['status']} (complexity: {feature['complexity']})")
            
            # Save outputs
            output_dir = Path("tests/outputs/incremental_workflow_test")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save each agent's output
            for i, result in enumerate(results):
                agent_name = result.name or result.team_member.value
                output_file = output_dir / f"{test_case['name'].lower().replace(' ', '_')}_{agent_name}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"Agent: {agent_name}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(result.output)
                
            # Save the execution report
            report_file = output_dir / f"{test_case['name'].lower().replace(' ', '_')}_report.json"
            with open(report_file, 'w') as f:
                f.write(report.to_json())
                
            print(f"\n💾 Outputs saved to: {output_dir}")
            
        except Exception as e:
            print(f"❌ Error executing incremental workflow: {str(e)}")
            import traceback
            traceback.print_exc()
            
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_incremental_workflow())