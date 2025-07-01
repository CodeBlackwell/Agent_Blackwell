"""
Planning Agent that analyzes user requests and creates structured job plans.

Based on ACP SDK patterns from basic/servers/echo.py and beeai-orchestrator/agent.py
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Dict, List, Any

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server, RunYield, RunYieldResume
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.backend import UserMessage

import sys
import os
# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import LLM_CONFIG, AGENT_PORTS, PROMPT_TEMPLATES, BEEAI_CONFIG

server = Server()

@server.agent(name="planning")
async def planner(inputs: List[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Planning agent that analyzes user requests and creates structured job plans.
    
    This agent breaks down complex user requests into actionable feature sets,
    identifies dependencies, and creates milestone-driven development roadmaps.
    """
    try:
        # Extract user request from input
        if not inputs or not inputs[0].parts:
            yield MessagePart(content="Error: No user request provided")
            return
            
        user_request = inputs[0].parts[0].content
        
        # Yield initial processing message
        yield MessagePart(content="🔍 Analyzing user request and creating structured job plan...")
        
        # Initialize LLM for planning
        llm = ChatModel.from_name(
            BEEAI_CONFIG["chat_model"]["model"],
            api_base=BEEAI_CONFIG["chat_model"]["base_url"],
            api_key=BEEAI_CONFIG["chat_model"]["api_key"]
        )
        memory = TokenMemory(llm)
        
        # Create ReAct agent with planning-specific configuration
        agent = ReActAgent(
            llm=llm,
            tools=[],  # Planning doesn't need external tools
            templates={
                "system": lambda template: template.update(
                    defaults={
                        "instructions": PROMPT_TEMPLATES["planner"]["system"],
                        "role": "system",
                    }
                )
            },
            memory=memory,
        )
        
        # Add user request to memory
        await memory.add(UserMessage(user_request))
        
        # Generate structured plan using LLM
        response = await agent.run()
        
        # Yield the structured job plan
        yield MessagePart(content=f"✅ Job plan created successfully:\n\n{response.result.text}")
        
    except Exception as e:
        yield MessagePart(content=f"❌ Error creating job plan: {str(e)}")

async def process_request(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Process a user request and create a structured job plan.
    
    Args:
        input: List of input messages containing the user request
        context: Context for the current request
            
    Returns:
        An async generator yielding the structured job plan
    """
    try:
        # Extract user request from input
        if not input or not input[0].parts:
            yield MessagePart(content="Error: No user request provided")
            return
            
        user_request = input[0].parts[0].content
        
        # Yield initial processing message
        yield MessagePart(content="🔍 Analyzing user request and creating structured job plan...")
        await asyncio.sleep(0.5)
        
        # Create structured job plan based on user request
        job_plan = await _create_job_plan(user_request)
        
        # Yield the structured job plan as JSON
        yield MessagePart(content=f"✅ Job plan created successfully:\n\n```json\n{json.dumps(job_plan, indent=2)}\n```")
            
    except Exception as e:
        yield MessagePart(content=f"❌ Error creating job plan: {str(e)}")

async def _create_job_plan(user_request: str) -> Dict[str, Any]:
    """
    Create a structured job plan from the user request.
    
    Args:
        user_request: The raw user request
            
    Returns:
        A structured job plan dictionary
    """
    # Simulate LLM processing with a structured analysis
    # In a real implementation, this would use the LLM with the planning prompt
        
    # Basic analysis of the request to determine complexity and features
    features = _extract_features(user_request)
    dependencies = _analyze_dependencies(features)
    milestones = _create_milestones(features)
        
    job_plan = {
        "job_id": f"job_{hash(user_request) % 10000:04d}",
        "user_request": user_request,
        "feature_sets": features,
        "dependencies": dependencies,
        "milestones": milestones,
        "estimated_complexity": _estimate_complexity(features),
        "risk_assessment": _assess_risks(user_request, features),
        "created_at": asyncio.get_event_loop().time(),
        "status": "planned"
    }
        
    return job_plan

def _extract_features(user_request: str) -> List[Dict[str, Any]]:
    """
    Extract feature sets from the user request.
    
    Args:
        user_request: The user's request
            
    Returns:
        List of feature dictionaries
    """
    # Simple keyword-based feature extraction
    # In production, this would use LLM analysis
        
    features = []
        
    # Detect common patterns
    if any(word in user_request.lower() for word in ['api', 'endpoint', 'rest', 'service']):
        features.append({
            "name": "API Development",
            "description": "Create REST API endpoints and services",
            "priority": "high",
            "estimated_effort": "medium",
            "parallel_executable": True
        })
        
    if any(word in user_request.lower() for word in ['ui', 'interface', 'frontend', 'web', 'app']):
        features.append({
            "name": "User Interface",
            "description": "Develop user interface components",
            "priority": "high",
            "estimated_effort": "medium",
            "parallel_executable": True
        })
        
    if any(word in user_request.lower() for word in ['database', 'db', 'storage', 'data']):
        features.append({
            "name": "Data Layer",
            "description": "Implement data storage and management",
            "priority": "high",
            "estimated_effort": "medium",
            "parallel_executable": False  # Usually needs to be done first
        })
        
    if any(word in user_request.lower() for word in ['auth', 'login', 'security', 'user']):
        features.append({
            "name": "Authentication",
            "description": "Implement user authentication and authorization",
            "priority": "medium",
            "estimated_effort": "medium",
            "parallel_executable": True
        })
        
    # Default feature if none detected
    if not features:
        features.append({
            "name": "Core Implementation",
            "description": "Implement the main functionality as requested",
            "priority": "high",
            "estimated_effort": "medium",
            "parallel_executable": True
        })
        
    return features

def _analyze_dependencies(features: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Analyze dependencies between features.
    
    Args:
        features: List of feature dictionaries
            
    Returns:
        Dictionary mapping feature names to their dependencies
    """
    dependencies = {}
    feature_names = [f["name"] for f in features]
        
    for feature in features:
        deps = []
            
        # Data Layer usually comes first
        if feature["name"] != "Data Layer" and "Data Layer" in feature_names:
            deps.append("Data Layer")
            
        # Authentication might depend on data layer
        if feature["name"] == "Authentication" and "Data Layer" in feature_names:
            deps.append("Data Layer")
            
        # UI might depend on API
        if feature["name"] == "User Interface" and "API Development" in feature_names:
            deps.append("API Development")
            
        dependencies[feature["name"]] = deps
        
    return dependencies

def _create_milestones(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create milestone definitions for the project.
    
    Args:
        features: List of feature dictionaries
            
    Returns:
        List of milestone dictionaries
    """
    milestones = [
        {
            "name": "Requirements Complete",
            "description": "All specifications and requirements documented",
            "stage": "specification",
            "requires_human_review": True,
            "deliverables": ["Technical specifications", "API documentation", "User stories"]
        },
        {
            "name": "Design Complete",
            "description": "Technical architecture and design finalized",
            "stage": "design",
            "requires_human_review": True,
            "deliverables": ["System architecture", "Database schema", "API design"]
        },
        {
            "name": "Implementation Complete",
            "description": "All features implemented and code reviewed",
            "stage": "coding",
            "requires_human_review": True,
            "deliverables": ["Working code", "Unit tests", "Integration tests"]
        },
        {
            "name": "Testing Complete",
            "description": "All tests passing and quality gates met",
            "stage": "testing",
            "requires_human_review": True,
            "deliverables": ["Test results", "Coverage reports", "Quality metrics"]
        }
    ]
        
    return milestones

def _estimate_complexity(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Estimate the complexity of the project.
    
    Args:
        features: List of feature dictionaries
            
    Returns:
        Complexity assessment dictionary
    """
    total_features = len(features)
    high_effort_features = sum(1 for f in features if f.get("estimated_effort") == "high")
        
    if total_features <= 2:
        overall = "low"
    elif total_features <= 4:
        overall = "medium"
    else:
        overall = "high"
        
    return {
        "overall": overall,
        "total_features": total_features,
        "high_effort_features": high_effort_features,
        "estimated_duration": f"{total_features * 2}-{total_features * 4} days"
    }

def _assess_risks(user_request: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess technical and business risks.
    
    Args:
        user_request: The original user request
        features: List of feature dictionaries
            
    Returns:
        Risk assessment dictionary
    """
    risks = {
        "technical": [],
        "business": [],
        "mitigation": []
    }
        
    # Check for common technical risks
    if any(word in user_request.lower() for word in ['integration', 'external', 'api']):
        risks["technical"].append("External API integration complexity")
        risks["mitigation"].append("Plan for API testing and fallback mechanisms")
        
    if len(features) > 3:
        risks["technical"].append("High feature complexity")
        risks["mitigation"].append("Break into smaller phases with incremental delivery")
        
    if any(word in user_request.lower() for word in ['security', 'auth', 'payment']):
        risks["technical"].append("Security implementation complexity")
        risks["mitigation"].append("Follow security best practices and conduct security review")
        
    # Business risks
    if "unclear" in user_request.lower() or len(user_request.split()) < 10:
        risks["business"].append("Unclear requirements")
        risks["mitigation"].append("Conduct detailed requirements gathering session")
        
    return risks

# Server startup code - consolidated from separate server.py file
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get port from config or use default
    port = AGENT_PORTS.get("planning", 8001)
    print(f"Starting Planning Agent on port {port}...")
    
    # Run the server - this must be in the same file as the agent definition
    server.run(port=port)
