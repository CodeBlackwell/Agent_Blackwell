"""
Centralized configuration for the ACP job pipeline system.

This module centralizes all LLM configurations, prompts, model parameters,
and other tunable settings according to our project standards.

Following our rules:
- All LLM configurations are centralized here
- Uses dotenv for environment variables
- Supports virtual environment (UV)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# LLM Configuration - centralized as per requirements
LLM_CONFIG = {
    "model_id": os.getenv("LLM_MODEL", "ollama_chat/qwen2:7b"),
    "api_base": os.getenv("LLM_API_BASE", "http://localhost:11434"),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
}

# Agent port configuration
AGENT_PORTS = {
    "planner": int(os.getenv("PLANNER_PORT", "8001")),
    "orchestrator": int(os.getenv("ORCHESTRATOR_PORT", "8002")),
    "specification": int(os.getenv("SPECIFICATION_PORT", "8003")),
    "design": int(os.getenv("DESIGN_PORT", "8004")),
    "code": int(os.getenv("CODE_PORT", "8005")),
    "review": int(os.getenv("REVIEW_PORT", "8006")),
    "test": int(os.getenv("TEST_PORT", "8007")),
    "mcp_git": int(os.getenv("MCP_GIT_PORT", "8100")),
    "streamlit": int(os.getenv("STREAMLIT_PORT", "8501")),
}

# Agent prompt templates - to be expanded as agents are developed
PROMPT_TEMPLATES = {
    "planner": {
        "system": """You are a Planning Agent responsible for analyzing user requests
                   and creating structured job plans. Break down complex tasks into 
                   manageable feature sets that can be implemented in parallel pipelines."""
    },
    "orchestrator": {
        "system": """You are an Orchestrator Agent responsible for managing the entire
                   development workflow. Coordinate between different agent pipelines
                   and ensure milestone reviews are properly handled."""
    },
    # Additional agent prompts will be defined as agents are implemented
}
