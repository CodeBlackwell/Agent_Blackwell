import asyncio
import os
import json
import re
from collections.abc import AsyncGenerator
from acp_sdk.models import Message
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Import configuration
from config import MODEL_CONFIG, PROMPTS, SERVER_CONFIG, FALLBACKS

# Load environment variables
load_dotenv()

server = Server()

# Initialize OpenAI client
# First check .env file, then fall back to global environment if needed
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in .env file, using global environment")

client = AsyncOpenAI()
# No need to explicitly set api_key as OpenAI client will check environment variables

@server.agent()
async def coder(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Generates code from a simple plan"""
    # Get the plan
    plan = input[0].parts[0].content
    
    yield {"thought": "Analyzing the plan and generating code using OpenAI..."}
    
    # Generate code using OpenAI with config settings
    try:
        response = await client.chat.completions.create(
            model=MODEL_CONFIG["coder"]["model"],
            messages=[
                {"role": "system", "content": PROMPTS["coder"]["system"]}, 
                {"role": "user", "content": PROMPTS["coder"]["user_multifile"].format(plan=plan)}
            ],
            temperature=MODEL_CONFIG["coder"]["temperature"],
            max_tokens=MODEL_CONFIG["coder"]["max_tokens"]
        )
        
        # Extract the generated code and parse into file structures
        generated_content = response.choices[0].message.content
        
        # Parse the content to extract files
        files = parse_files_from_content(generated_content)
        
        if not files:
            # Fallback if no files were parsed
            files = [
                {
                    "filename": "solution.py",
                    "content": generated_content
                }
            ]
        
        # Generate a project name from the plan
        project_name = generate_project_name(plan)
        
        # Convert files to JSON for transport
        code = json.dumps({
            "plan": plan.strip(),
            "files": files,
            "project_name": project_name,
            "raw_response": generated_content
        })
        
    except Exception as e:
        # Fallback if API call fails
        code = json.dumps({
            "plan": plan.strip(),
            "files": [
                {
                    "filename": "error_solution.py",
                    "content": f"# Error occurred: {str(e)}\n\ndef main():\n    print(\"This is a fallback implementation due to API error\")\n    return \"Error occurred during code generation\"\n\nif __name__ == \"__main__\":\n    main()"
                }
            ],
            "project_name": "error_project",
            "error": str(e)
        })
    
    # Return the code
    yield {"thought": "Generating code structure from plan"}
    await asyncio.sleep(0.5)  # Simulate thinking
    yield code

def parse_files_from_content(content):
    """Parse content from LLM to extract filenames and code"""
    # Regular expression to match ```filename: [filename]\n[content]```
    pattern = r"```filename:\s*(.+?)\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    
    files = []
    for filename, file_content in matches:
        files.append({
            "filename": filename.strip(),
            "content": file_content.strip()
        })
    
    return files

def generate_project_name(plan):
    """Generate a project name from the plan"""
    # Extract the first line which typically contains the purpose
    first_line = plan.strip().split('\n')[0]
    
    # Try to extract a meaningful name from the plan description
    if ":" in first_line:
        description = first_line.split(':', 1)[1].strip()
    else:
        description = first_line.strip()
    
    # Clean up the description to create a suitable directory name
    project_name = re.sub(r'[^a-zA-Z0-9_-]', '_', description.lower())
    project_name = re.sub(r'_+', '_', project_name)  # Replace multiple underscores with one
    project_name = project_name.strip('_')
    
    # If the name is too long, truncate it
    if len(project_name) > 30:
        project_name = project_name[:30].rstrip('_')
    
    return project_name if project_name else "code_project"

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the coder agent server")
    parser.add_argument("--reload", action="store_true", help="Enable hot reloading for development")
    args = parser.parse_args()
    
    # Start the server with optional hot reloading
    server.run(
        port=SERVER_CONFIG["coder"]["port"], 
        host=SERVER_CONFIG["coder"]["host"],
        reload=args.reload
    )
