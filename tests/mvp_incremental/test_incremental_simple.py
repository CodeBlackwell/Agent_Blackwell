"""
Simple test for incremental workflow debugging.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_simple():
    """Run a very simple test."""
    print("Testing incremental workflow...")
    
    # Simple test case
    input_data = CodingTeamInput(
        requirements="Create a function that adds two numbers",
        workflow_type="incremental"
    )
    
    tracer = WorkflowExecutionTracer("incremental")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        print(f"✅ Success! Got {len(results)} results")
        print(f"Duration: {report.overall_duration:.2f}s")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple())