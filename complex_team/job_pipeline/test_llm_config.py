#!/usr/bin/env python
"""
Test script to verify LLM configurations.
Tests both Ollama and OpenAI configurations to identify which is working.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the configuration
from config.config import LLM_CONFIG, BEEAI_CONFIG

# Import BeeAI Framework components
from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend import UserMessage, SystemMessage
from beeai_framework.memory import TokenMemory


async def test_ollama_config():
    """Test the Ollama configuration from LLM_CONFIG."""
    print("\n=== Testing Ollama Configuration ===")
    print(f"Model: {LLM_CONFIG['model_id']}")
    print(f"API Base: {LLM_CONFIG['api_base']}")
    
    try:
        print("Initializing Ollama ChatModel...")
        llm = ChatModel.from_name(
            LLM_CONFIG["model_id"],
            api_base=LLM_CONFIG["api_base"]
        )
        
        print("Creating memory...")
        memory = TokenMemory(llm)
        
        print("Adding test message...")
        await memory.add(UserMessage("Hello, this is a test message."))
        
        print("Running simple generation...")
        # Use the updated API - create messages and use async call
        messages = [
            SystemMessage("You are a helpful assistant."),
            UserMessage("Say hello!")
        ]
        
        # Use the correct method - either invoke() or call() depending on your BeeAI version
        try:
            # Try the newer invoke method first
            response = await llm.invoke(messages)
        except AttributeError:
            # Fall back to call method if invoke doesn't exist
            response = await llm.call(messages)
        
        # Handle response based on BeeAI response format
        if hasattr(response, 'content'):
            print(f"Response: {response.content}")
        elif hasattr(response, 'message'):
            print(f"Response: {response.message}")
        else:
            print(f"Response: {response}")
            
        print("✅ Ollama configuration is working!")
        return True
    except Exception as e:
        print(f"❌ Ollama configuration error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


async def test_openai_config():
    """Test the OpenAI configuration from BEEAI_CONFIG."""
    print("\n=== Testing OpenAI Configuration ===")
    print(f"Model: {BEEAI_CONFIG['chat_model']['model']}")
    print(f"API Base: {BEEAI_CONFIG['chat_model']['base_url']}")
    print(f"API Key: {'Set' if BEEAI_CONFIG['chat_model']['api_key'] else 'Not set'}")
    
    try:
        print("Initializing OpenAI ChatModel...")
        llm = ChatModel.from_name(
            BEEAI_CONFIG["chat_model"]["model"],
            api_base=BEEAI_CONFIG["chat_model"]["base_url"],
            api_key=BEEAI_CONFIG["chat_model"]["api_key"]
        )
        
        print("Creating memory...")
        memory = TokenMemory(llm)
        
        print("Adding test message...")
        await memory.add(UserMessage("Hello, this is a test message."))
        
        print("Running simple generation...")
        # Use the updated API - create messages and use async call
        messages = [
            SystemMessage("You are a helpful assistant."),
            UserMessage("Say hello!")
        ]
        
        # Use the correct method - either invoke() or call() depending on your BeeAI version
        try:
            # Try the newer invoke method first
            response = await llm.invoke(messages)
        except AttributeError:
            # Fall back to call method if invoke doesn't exist
            response = await llm.call(messages)
        
        # Handle response based on BeeAI response format
        if hasattr(response, 'content'):
            print(f"Response: {response.content}")
        elif hasattr(response, 'message'):
            print(f"Response: {response.message}")
        else:
            print(f"Response: {response}")
            
        print("✅ OpenAI configuration is working!")
        return True
    except Exception as e:
        print(f"❌ OpenAI configuration error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


async def test_simple_generation():
    """Test with a more basic approach if the above methods fail."""
    print("\n=== Testing Simple Generation ===")
    
    try:
        # Try Ollama first
        print("Testing simple Ollama call...")
        llm = ChatModel.from_name(
            LLM_CONFIG["model_id"],
            api_base=LLM_CONFIG["api_base"]
        )
        
        # Try different possible method names
        test_message = "Hello, respond with 'Test successful'"
        
        for method_name in ['invoke', 'call', 'generate', 'agenerate', 'chat']:
            if hasattr(llm, method_name):
                print(f"Found method: {method_name}")
                try:
                    if method_name in ['invoke', 'call']:
                        result = await getattr(llm, method_name)([UserMessage(test_message)])
                    else:
                        result = await getattr(llm, method_name)(test_message)
                    print(f"✅ {method_name} works! Result: {result}")
                    return True
                except Exception as e:
                    print(f"❌ {method_name} failed: {e}")
                    
        print("No working method found for LLM")
        return False
        
    except Exception as e:
        print(f"❌ Simple generation test failed: {e}")
        return False


async def main():
    """Run all tests and provide recommendations."""
    print("Testing LLM configurations...")
    
    ollama_works = await test_ollama_config()
    openai_works = await test_openai_config()
    
    # If both fail, try the simple generation test
    if not ollama_works and not openai_works:
        print("\n=== Trying Alternative Methods ===")
        simple_works = await test_simple_generation()
    
    print("\n=== Results ===")
    if ollama_works:
        print("✅ Ollama configuration is working")
    else:
        print("❌ Ollama configuration is NOT working")
        
    if openai_works:
        print("✅ OpenAI configuration is working")
    else:
        print("❌ OpenAI configuration is NOT working")
    
    print("\n=== Recommendations ===")
    if ollama_works:
        print("1. Update planning_agent.py to use LLM_CONFIG with the correct method:")
        print("   llm = ChatModel.from_name(LLM_CONFIG['model_id'], api_base=LLM_CONFIG['api_base'])")
        print("   response = await llm.invoke([SystemMessage(...), UserMessage(...)])")
    elif openai_works:
        print("1. Update planning_agent.py to use BEEAI_CONFIG instead of LLM_CONFIG:")
        print("   llm = ChatModel.from_name(")
        print("       BEEAI_CONFIG['chat_model']['model'],")
        print("       api_base=BEEAI_CONFIG['chat_model']['base_url'],")
        print("       api_key=BEEAI_CONFIG['chat_model']['api_key']")
        print("   )")
        print("   response = await llm.invoke([SystemMessage(...), UserMessage(...)])")
    else:
        print("Both configurations are not working. Please check:")
        print("1. For Ollama: Is Ollama running locally? Try 'ollama run qwen2.5:7b'")
        print("2. For OpenAI: Is your API key set in the environment?")
        print("3. Check your BeeAI Framework version - the API might have changed")
        print("4. Try running: pip install --upgrade beeai-framework")


if __name__ == "__main__":
    asyncio.run(main())