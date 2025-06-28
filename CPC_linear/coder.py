import asyncio
import os
from collections.abc import AsyncGenerator
from acp_sdk.models import Message
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from openai import AsyncOpenAI
from dotenv import load_dotenv

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
    
    # Generate code using OpenAI
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Python code based on plans. Generate only code, no explanations."}, 
                {"role": "user", "content": f"Generate Python code based on this plan: {plan}"}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        # Extract the generated code
        code = f"""# Implementation based on plan: 
# {plan.strip()}

{response.choices[0].message.content}"""
    except Exception as e:
        # Fallback if API call fails
        code = f"""# Implementation based on plan: 
# {plan.strip()}

# Error occurred: {str(e)}

def main():
    print("This is a fallback implementation due to API error")
    return "Error occurred during code generation"

if __name__ == "__main__":
    main()
"""
    
    # Return the code
    yield {"thought": "Generating code from plan"}
    await asyncio.sleep(0.5)  # Simulate thinking
    yield code

if __name__ == "__main__":
    server.run(port=8200)
