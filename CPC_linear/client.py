import asyncio
import sys
import os
import json
import datetime
from pathlib import Path
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

# Import configuration
from config import CLIENT_CONFIG, OUTPUT_CONFIG

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py 'your code description'")
        return
        
    code_description = sys.argv[1]
    print(f"Generating code for: {code_description}")
    
    # Step 1: Call planner agent
    async with Client(base_url=CLIENT_CONFIG["planner_url"]) as planner_client:
        print("Calling planner agent...")
        planner_response = await planner_client.run_sync(
            agent="planner",
            input=[Message(parts=[MessagePart(content=code_description)])],
        )
        
        plan = planner_response.output[0].parts[0].content
        print("\n=== PLAN ===")
        print(plan)
    
    # Step 2: Call coder agent with plan
    async with Client(base_url=CLIENT_CONFIG["coder_url"]) as coder_client:
        print("\nCalling coder agent...")
        coder_response = await coder_client.run_sync(
            agent="coder",
            input=[Message(parts=[MessagePart(content=plan)])],
        )
        
        code_json = coder_response.output[0].parts[0].content
        
        try:
            # Parse the JSON response
            code_data = json.loads(code_json)
            
            # Create output directory
            output_dir = await create_output_directory()
            
            # Save the generated files
            saved_files = await save_generated_files(code_data, output_dir, plan)
            
            print(f"\n=== GENERATED FILES ===")
            print(f"Files saved to: {output_dir}")
            for filename in saved_files:
                print(f"- {filename}")
                
        except json.JSONDecodeError:
            print("\n=== ERROR ===")
            print("Failed to parse JSON response from coder agent.")
            print("\n=== RAW RESPONSE ===")
            print(code_json)


async def create_output_directory():
    """Create a directory for the generated code"""
    base_dir = Path(OUTPUT_CONFIG["base_dir"])
    base_dir.mkdir(exist_ok=True)
    
    if OUTPUT_CONFIG["create_timestamp_dirs"]:
        # Create a timestamped subdirectory with user-friendly format
        timestamp = datetime.datetime.now().strftime("%b_%d_%Y_%I-%M-%S%p")
        output_dir = base_dir / timestamp
    else:
        output_dir = base_dir
    
    output_dir.mkdir(exist_ok=True)
    return output_dir


async def save_generated_files(code_data, output_dir, plan):
    """Save the generated files to disk"""
    saved_files = []
    
    # Save each file
    for file_info in code_data.get("files", []):
        filename = file_info.get("filename", "solution.py")
        content = file_info.get("content", "")
        
        # Ensure the filename has an extension
        if not os.path.splitext(filename)[1]:
            filename = f"{filename}{OUTPUT_CONFIG['default_extension']}"
            
        # Save the file
        file_path = output_dir / filename
        with open(file_path, "w") as f:
            f.write(content)
        
        saved_files.append(filename)
    
    # Generate README if configured
    if OUTPUT_CONFIG["include_readme"]:
        readme_path = output_dir / "README.md"
        with open(readme_path, "w") as f:
            f.write(f"# Generated Code\n\n## Plan\n\n{plan}\n\n## Files\n\n")
            for filename in saved_files:
                f.write(f"- {filename}\n")
        saved_files.append("README.md")
    
    return saved_files


if __name__ == "__main__":
    asyncio.run(main())
