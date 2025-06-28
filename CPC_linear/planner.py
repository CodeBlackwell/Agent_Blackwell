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
async def planner(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Creates a simple plan based on code description"""
    # Get user request
    request = input[0].parts[0].content
    
    yield {"thought": "Analyzing request and creating implementation plan..."}
    
    # Generate plan using OpenAI
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a planning assistant that creates programming plans. Return only steps for implementation in a numbered list format. Be concise and direct."}, 
                {"role": "user", "content": f"Create a step-by-step plan for implementing: {request}. Keep it under 5 steps."}
            ],
            temperature=0.2,
            max_tokens=250
        )
        
        # Extract the plan
        generated_plan = response.choices[0].message.content
        plan = f"""PLAN FOR: {request}

{generated_plan}"""
    except Exception as e:
        # Fallback if API call fails
        plan = f"""
        PLAN FOR: {request}
        
        1. Define the main function
        2. Implement core logic
        3. Add basic error handling
        4. Return results
        
        Note: Error occurred during plan generation: {str(e)}
        """
    
    # Return the plan
    yield {"thought": "Creating a simple plan"}
    await asyncio.sleep(0.5)  # Simulate thinking
    yield plan

if __name__ == "__main__":
    server.run(port=8100)
