#!/usr/bin/env python3
"""
Test script for incremental workflow with a moderate calculator project.
This creates a calculator with multiple features to test incremental development.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow


async def test_incremental_calculator():
    """Test the incremental workflow with a moderate calculator project"""
    
    # Define a moderate complexity calculator project
    requirements = """
    Create a scientific calculator API with the following features:
    
    1. Basic Operations:
       - Addition, subtraction, multiplication, division
       - Support for decimal numbers
       - Error handling for division by zero
    
    2. Advanced Operations:
       - Power (x^y)
       - Square root
       - Factorial
       - Percentage calculations
    
    3. Memory Functions:
       - Store value in memory
       - Recall from memory
       - Clear memory
       - Add to memory
    
    4. History Feature:
       - Keep track of last 10 calculations
       - Clear history
       - Get calculation history
    
    5. API Requirements:
       - RESTful API using FastAPI
       - Proper input validation
       - Clear error messages
       - Swagger documentation
    
    The calculator should be modular, with separate modules for:
    - Basic operations
    - Advanced operations
    - Memory management
    - History tracking
    - API endpoints
    
    Include comprehensive error handling and edge case management.
    """
    
    # Create test input
    test_input = CodingTeamInput(
        requirements=requirements,
        workflow_type="incremental"
    )
    
    print("\n🧪 Testing Incremental Workflow with Moderate Calculator Project")
    print("=" * 70)
    print(f"Requirements: Scientific Calculator API with multiple features")
    print(f"Workflow Type: {test_input.workflow_type}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Execute the incremental workflow
        results = await execute_workflow(test_input)
        
        print("\n✅ Workflow completed successfully!")
        print("\n📊 Results Summary:")
        print("-" * 50)
        
        # Display results summary
        if isinstance(results, list) and len(results) > 0:
            # Check if results is a list of lists (workflow manager sometimes returns nested structure)
            if isinstance(results[0], list):
                results = results[0]
            
            for i, result in enumerate(results, 1):
                if hasattr(result, 'name') and hasattr(result, 'output'):
                    print(f"\n{i}. {result.name.upper()}")
                    print(f"   Output length: {len(result.output)} characters")
                    if len(result.output) > 200:
                        print(f"   Preview: {result.output[:200]}...")
                    else:
                        print(f"   Output: {result.output}")
                else:
                    print(f"\n{i}. Result type: {type(result)}")
                    print(f"   Result: {str(result)[:200]}...")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path("tests/outputs/incremental_calculator")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the full results
        results_file = output_dir / f"results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "requirements": requirements,
                "workflow_type": "incremental",
                "results": [
                    {
                        "agent": result.name if hasattr(result, 'name') else str(type(result)),
                        "output": result.output if hasattr(result, 'output') else str(result),
                        "length": len(result.output) if hasattr(result, 'output') else len(str(result))
                    }
                    for result in results
                ]
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Check if generated code exists
        generated_dir = Path("generated")
        if generated_dir.exists():
            latest_generated = max(generated_dir.glob("app_generated_*"), 
                                 key=lambda p: p.stat().st_mtime,
                                 default=None)
            if latest_generated:
                print(f"\n📁 Generated code location: {latest_generated}")
                
                # List generated files
                print("\n📄 Generated files:")
                for file_path in latest_generated.rglob("*.py"):
                    relative_path = file_path.relative_to(latest_generated)
                    print(f"   - {relative_path}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point"""
    print("\n🚀 Incremental Workflow Calculator Test")
    print("This test will create a scientific calculator using incremental development")
    
    # Check if orchestrator is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8080/status') as response:
                if response.status == 200:
                    print("✅ Orchestrator is running")
                else:
                    print("⚠️  Orchestrator returned unexpected status")
    except:
        print("⚠️  Warning: Could not connect to orchestrator on port 8080")
        print("   Make sure to run: python orchestrator/orchestrator_agent.py")
        print("   Continuing anyway...")
    
    # Run the test
    results = await test_incremental_calculator()
    
    if results:
        print("\n✨ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())