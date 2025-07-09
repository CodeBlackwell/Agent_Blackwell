"""
Live Test: Simple Calculator Implementation
Tests the system's ability to create a basic calculator using TDD
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.live.test_fixtures import workflow_helper, docker_env, perf_monitor
from workflows.workflow_manager import execute_workflow


async def test_calculator_implementation():
    """Test creating a calculator with TDD workflow"""
    
    # Test requirements
    requirements = """Create a simple calculator class using TDD that supports:
- Addition of two numbers
- Subtraction of two numbers  
- Multiplication of two numbers
- Division of two numbers (with proper error handling for division by zero)

The calculator should be implemented as a Python class with methods for each operation.
Use the RED-YELLOW-GREEN TDD cycle for each feature."""
    
    # Create test session
    session_dir = await workflow_helper.create_test_session()
    print(f"📁 Test session: {session_dir}")
    
    # Start performance monitoring
    perf_monitor.start()
    perf_monitor.checkpoint("test_start")
    
    try:
        # Execute workflow
        print("🚀 Starting TDD workflow for calculator...")
        result = await execute_workflow(
            requirements=requirements,
            workflow_type="mvp_incremental",
            session_id="test_calculator",
            output_dir=str(session_dir / "generated")
        )
        
        perf_monitor.checkpoint("workflow_complete")
        
        # Validate generated files
        print("\n📋 Validating generated files...")
        expected_files = [
            "calculator.py",
            "test_calculator.py"
        ]
        
        validation = workflow_helper.validate_generated_code(
            session_dir / "generated",
            expected_files
        )
        
        assert validation["all_files_exist"], f"Missing files: {validation['missing_files']}"
        print(f"✅ All expected files generated")
        print(f"📊 Total lines of code: {validation['total_lines']}")
        
        # Run tests in Docker
        print("\n🐳 Running tests in Docker container...")
        perf_monitor.checkpoint("docker_start")
        
        container = await docker_env.create_python_container(
            session_dir / "generated",
            requirements=["pytest"]
        )
        
        exit_code, output = await docker_env.run_test_command(
            container,
            "python -m pytest test_calculator.py -v"
        )
        
        perf_monitor.checkpoint("docker_tests_complete")
        
        print("\n📤 Test output:")
        print(output)
        
        assert exit_code == 0, "Tests failed in Docker container"
        print("\n✅ All tests passed in Docker!")
        
        # Test the calculator functionality
        print("\n🧮 Testing calculator operations...")
        exit_code, output = await docker_env.run_test_command(
            container,
            "python -c \"from calculator import Calculator; calc = Calculator(); print('2+3 =', calc.add(2, 3)); print('10-4 =', calc.subtract(10, 4)); print('6*7 =', calc.multiply(6, 7)); print('15/3 =', calc.divide(15, 3))\""
        )
        
        print(output)
        assert exit_code == 0, "Calculator execution failed"
        
        # Test division by zero
        exit_code, output = await docker_env.run_test_command(
            container,
            "python -c \"from calculator import Calculator; calc = Calculator(); try: calc.divide(10, 0); except (ValueError, ZeroDivisionError): print('✅ Division by zero handled correctly')\""
        )
        
        print(output)
        assert exit_code == 0, "Division by zero handling failed"
        
        perf_monitor.checkpoint("test_complete")
        
        # Clean up
        await docker_env.cleanup()
        
        # Performance summary
        perf_metrics = perf_monitor.stop()
        summary = perf_monitor.get_summary()
        
        print("\n📊 Performance Summary:")
        print(f"Total duration: {summary['duration']:.2f} seconds")
        print(f"Checkpoints: {summary['total_checkpoints']}")
        
        print("\n✅ Calculator test completed successfully!")
        
        return {
            "success": True,
            "session_dir": str(session_dir),
            "validation": validation,
            "performance": summary
        }
        
    except Exception as e:
        await docker_env.cleanup()
        perf_monitor.stop()
        
        print(f"\n❌ Test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_dir": str(session_dir)
        }


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_calculator_implementation())
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)