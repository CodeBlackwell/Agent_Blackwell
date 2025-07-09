#!/usr/bin/env python3
"""
Simple Hello World Builder Demo for debugging workflows.
This demo creates a minimal project that builds a hello world API with a single feature.
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput


class HelloWorldBuilder:
    """Demo script for building a simple hello world API."""
    
    def __init__(self, workflow_type: str = "mvp_incremental", output_dir: Optional[str] = None):
        self.workflow_type = workflow_type
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir or f"demo_outputs/hello_world_{self.timestamp}"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    async def build_hello_world(self) -> Dict[str, Any]:
        """Build a hello world API with a single feature."""
        
        # Simple requirements for a hello world API with one feature
        requirements = """
Create a simple REST API with the following single feature:

Feature: Hello World Endpoint
- Create a GET endpoint at /hello that returns {"message": "Hello, World!"}
- The API should run on port 8000
- Include proper error handling
- Use FastAPI framework
- Include a simple test to verify the endpoint works

Project Structure:
- main.py (API implementation)
- test_main.py (Tests)
- requirements.txt (Dependencies)
"""
        
        print(f"\n🚀 Starting Hello World Builder Demo")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🔄 Workflow type: {self.workflow_type}")
        print(f"📋 Requirements: Single feature - Hello World endpoint\n")
        
        # Create workflow request
        request = CodingTeamInput(
            requirements=requirements,
            workflow_type=self.workflow_type,
            output_path=self.output_dir
        )
        
        # Save request for debugging
        request_file = Path(self.output_dir) / "workflow_request.json"
        with open(request_file, 'w') as f:
            json.dump({
                "requirements": requirements,
                "workflow_type": self.workflow_type,
                "language": "python",
                "framework": "fastapi",
                "output_dir": self.output_dir,
                "timestamp": self.timestamp
            }, f, indent=2)
        
        print(f"💾 Saved workflow request to: {request_file}")
        
        try:
            # Execute the workflow
            print(f"\n🔧 Executing {self.workflow_type} workflow...")
            team_results, execution_report = await execute_workflow(request)
            
            # Convert results to a serializable format
            result_data = {
                "success": True,
                "workflow_type": self.workflow_type,
                "team_results": [
                    {
                        "team_member": result.team_member.value,
                        "output": result.output,
                        "metadata": result.metadata
                    }
                    for result in team_results
                ],
                "execution_report": execution_report.to_json() if hasattr(execution_report, 'to_json') else str(execution_report)
            }
            
            # Save result for debugging
            result_file = Path(self.output_dir) / "workflow_result.json"
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            print(f"\n✅ Workflow completed successfully!")
            print(f"💾 Saved workflow result to: {result_file}")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"   - Status: SUCCESS")
            print(f"   - Team members involved: {len(team_results)}")
            print(f"   - Output directory: {self.output_dir}")
            
            if team_results:
                print(f"\n📄 Team member results:")
                for result in team_results:
                    print(f"   - {result.team_member.value}: {len(result.output)} characters output")
            
            # Display generated files
            print(f"\n📂 Checking for generated files...")
            output_path = Path(self.output_dir)
            if output_path.exists():
                files = list(output_path.glob("*.py")) + list(output_path.glob("*.txt")) + list(output_path.glob("*.md"))
                if files:
                    print(f"   Found {len(files)} code files:")
                    for file in sorted(files):
                        print(f"   - {file.name}")
                else:
                    print("   ⚠️  No code files found in output directory")
                    # Check the generated directory as fallback
                    print("\n   Checking default generated directory...")
                    gen_path = Path("generated/app_generated_latest")
                    if gen_path.exists():
                        gen_files = list(gen_path.glob("*"))
                        if gen_files:
                            print(f"   Found {len(gen_files)} files in {gen_path}:")
                            for file in sorted(gen_files)[:10]:
                                print(f"   - {file.name}")
            
            return result_data
            
        except Exception as e:
            error_msg = f"Error executing workflow: {str(e)}"
            print(f"\n❌ {error_msg}")
            
            # Save error for debugging
            error_file = Path(self.output_dir) / "error.json"
            with open(error_file, 'w') as f:
                json.dump({
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": self.timestamp
                }, f, indent=2)
            
            return {"success": False, "error": error_msg}


def main():
    """Main entry point for the demo."""
    parser = argparse.ArgumentParser(
        description="Hello World Builder - Debug workflows with a simple single-feature project"
    )
    
    parser.add_argument(
        "--workflow",
        "-w",
        type=str,
        default="mvp_incremental",
        choices=["full", "tdd", "mvp_incremental", "planning", "design", "implementation", "review"],
        help="Workflow type to use (default: mvp_incremental)"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output directory (default: demo_outputs/hello_world_TIMESTAMP)"
    )
    
    args = parser.parse_args()
    
    # Create and run the builder
    builder = HelloWorldBuilder(
        workflow_type=args.workflow,
        output_dir=args.output
    )
    
    # Run the async function
    result = asyncio.run(builder.build_hello_world())
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()