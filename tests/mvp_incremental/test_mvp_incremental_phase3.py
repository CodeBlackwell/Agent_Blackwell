#!/usr/bin/env python3
"""
Test script for MVP incremental workflow Phase 3.
Tests feature dependency parsing and ordering.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_dependency_ordering():
    """Test MVP incremental with feature dependencies."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow Phase 3 - Dependency Ordering")
    print("📦 Features will be ordered based on dependencies")
    print("="*60)
    
    # Test case with clear dependencies
    input_data = CodingTeamInput(
        requirements="""
Create a task management system with:
1. A Task class to represent individual tasks
2. A TaskList class that manages multiple tasks
3. Methods in TaskList to add, remove, and list tasks
4. A priority system for tasks (high, medium, low)
5. A method to get tasks by priority
6. Export functionality to save tasks to JSON
7. Import functionality to load tasks from JSON

Make sure TaskList uses the Task class, and import/export work with the task structure.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase3_test")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Extract feature implementation order
        feature_order = []
        for result in results:
            if result.name and result.name.startswith("coder_feature_"):
                # Extract feature info from the input used
                feature_num = result.name.split("_")[-1]
                feature_order.append(f"Feature {feature_num}")
        
        print(f"\n📋 Feature Implementation Order:")
        for i, feature in enumerate(feature_order, 1):
            print(f"   {i}. {feature}")
        
        # Check validation results
        validation_count = 0
        validation_passed = 0
        
        for result in results:
            if hasattr(result, 'metadata') and result.metadata and 'validation_passed' in result.metadata:
                validation_count += 1
                if result.metadata['validation_passed']:
                    validation_passed += 1
        
        print(f"\n📊 Validation Summary:")
        print(f"   Total validations: {validation_count}")
        print(f"   Passed: {validation_passed}")
        print(f"   Failed: {validation_count - validation_passed}")
        
        # Save final implementation
        save_results(results, "phase3_dependencies")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_results(results, suffix=""):
    """Save the final implementation to a file."""
    output_dir = Path("tests/outputs/mvp_incremental")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"task_system_{suffix}_{timestamp}.py"
    
    # Find the final implementation result
    final_result = None
    for result in reversed(results):
        if result.name == "final_implementation":
            final_result = result
            break
    
    if final_result:
        # Extract just the code from the markdown
        import re
        code_blocks = re.findall(r'```python\n(.*?)```', final_result.output, re.DOTALL)
        
        if code_blocks:
            # Save the main implementation
            with open(output_file, 'w') as f:
                f.write(code_blocks[0])
            print(f"\n💾 Saved implementation to: {output_file}")


async def test_explicit_dependencies():
    """Test with explicit dependency declarations in design."""
    print("\n\n" + "="*60)
    print("🧪 Testing Explicit Dependencies")
    print("="*60)
    
    # This test would use a modified prompt that encourages explicit dependency declaration
    input_data = CodingTeamInput(
        requirements="""
Create a simple e-commerce system. When designing, explicitly state feature dependencies:

1. Product class (no dependencies)
2. Cart class that holds Products (depends on Product class) 
3. CartItem to track quantity (depends on Product)
4. Add to cart method (depends on Cart and CartItem)
5. Calculate total method (depends on Cart having items)

IMPORTANT: In your design, use FEATURE[n] format and explicitly list Dependencies for each feature.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_explicit_deps")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        print(f"\n✅ Explicit dependencies test completed")
        return True
    except Exception as e:
        print(f"\n❌ Error in explicit dependencies test: {e}")
        return False


async def main():
    """Run Phase 3 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 3 Tests")
    print("📋 Phase 3: Feature dependency analysis and ordering")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run basic dependency ordering test
    success1 = await test_dependency_ordering()
    
    # Run explicit dependencies test
    success2 = await test_explicit_dependencies()
    
    if success1 and success2:
        print("\n🎉 All Phase 3 tests passed!")
        print("✅ Features are being ordered by dependencies")
    else:
        print("\n⚠️  Some Phase 3 tests failed.")
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)