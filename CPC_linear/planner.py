import asyncio
import os
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
async def planner(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Creates a simple plan based on code description"""
    # Get user request
    request = input[0].parts[0].content
    
    yield {"thought": "Analyzing request and creating implementation plan..."}
    
    # Generate plan using OpenAI with config settings
    try:
        response = await client.chat.completions.create(
            model=MODEL_CONFIG["planner"]["model"],
            messages=[
                {"role": "system", "content": PROMPTS["planner"]["system"]}, 
                {"role": "user", "content": PROMPTS["planner"]["user"].format(request=request)}
            ],
            temperature=MODEL_CONFIG["planner"]["temperature"],
            max_tokens=MODEL_CONFIG["planner"]["max_tokens"]
        )
        
        # Extract the plan
        generated_plan = response.choices[0].message.content
        plan = f"""PLAN FOR: {request}

{generated_plan}"""
    except Exception as e:
        # Fallback if API call fails
        plan = FALLBACKS["planner"].format(request=request, error=str(e))
    
    # Return the plan
    yield {"thought": "Creating a simple plan"}
    await asyncio.sleep(0.5)  # Simulate thinking
    yield plan

if __name__ == "__main__":
    server.run(port=SERVER_CONFIG["planner"]["port"], host=SERVER_CONFIG["planner"]["host"])
