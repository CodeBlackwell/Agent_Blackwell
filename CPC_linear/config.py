"""
Unified configuration file for ACP agents.
This centralizes all configurable parameters including model settings, prompts, and server configurations.
"""

# ===== MODEL CONFIGURATIONS =====
MODEL_CONFIG = {
    "default_model": "gpt-3.5-turbo",
    "planner": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.2,
        "max_tokens": 250,
    },
    "coder": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.2,
        "max_tokens": 500,
    }
}

# ===== PROMPT TEMPLATES =====
PROMPTS = {
    "planner": {
        "system": "You are a planning assistant that creates programming plans. Return only steps for implementation in a numbered list format. Be concise and direct.",
        "user": "Create a step-by-step plan for implementing: {request}. Keep it under 5 steps."
    },
    "coder": {
        "system": "You are a helpful assistant that generates Python code based on plans. Generate only code, no explanations.",
        "user": "Generate Python code based on this plan: {plan}"
    }
}

# ===== SERVER CONFIGURATIONS =====
SERVER_CONFIG = {
    "planner": {
        "port": 8100,
        "host": "127.0.0.1"
    },
    "coder": {
        "port": 8200,
        "host": "127.0.0.1"
    }
}

# ===== CLIENT CONFIGURATIONS =====
CLIENT_CONFIG = {
    "planner_url": "http://localhost:8100",
    "coder_url": "http://localhost:8200"
}

# ===== FALLBACK TEMPLATES =====
FALLBACKS = {
    "planner": """
        PLAN FOR: {request}
        
        1. Define the main function
        2. Implement core logic
        3. Add basic error handling
        4. Return results
        
        Note: Error occurred during plan generation: {error}
        """,
    "coder": """# Implementation based on plan: 
# {plan}

# Error occurred: {error}

def main():
    print("This is a fallback implementation due to API error")
    return "Error occurred during code generation"

if __name__ == "__main__":
    main()
"""
}
