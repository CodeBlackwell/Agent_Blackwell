#!/usr/bin/env python3
"""
Executor Agent Module - Responsible for executing code and tests in Docker environments

This agent handles:
1. Analysis of code to determine minimal Docker environment
2. Building custom Docker images for each session
3. Executing code and tests in isolated containers
4. Persisting containers throughout workflow sessions
5. Intelligent interpretation of execution results

File: agents/executor/executor_agent.py
"""

from collections.abc import AsyncGenerator
import os
import sys
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.utils.dicts import exclude_none

# Import from agents package
from agents.agent_configs import executor_config
from agents.executor.docker_manager import DockerEnvironmentManager, EnvironmentSpec
from agents.executor.environment_analyzer import parse_environment_spec
from workflows.workflow_config import GENERATED_CODE_PATH

load_dotenv()

# Environment Analysis Instructions
ENVIRONMENT_ANALYSIS_INSTRUCTIONS = """
You are a Docker environment specialist. Analyze code to determine the minimal required environment.

For each code submission, identify:

1. **Language & Version**: Be specific (e.g., python:3.9, node:16)
2. **Base Image**: Choose minimal secure images (alpine preferred when possible)
3. **Dependencies**: Only what's actually imported/required
4. **System Packages**: Any system-level dependencies
5. **Build Commands**: Compilation or setup steps needed
6. **Execution Commands**: How to run tests and main application

Output as structured data:
- Language: [detected language]
- Version: [specific version or 'latest']
- Base Image: [docker image name]
- Dependencies: [list of packages]
- System Packages: [list of system deps]
- Build Commands: [list of build steps]
- Execution Commands: [list of commands to run]

Be minimal - only include what's necessary for the code to run.
"""

RESULT_ANALYSIS_INSTRUCTIONS = """
You are a test execution analyst. Interpret Docker execution results and provide actionable feedback.

Analyze:
1. Which tests passed or failed
2. Root causes of any failures
3. Performance characteristics
4. Security or resource concerns
5. Whether requirements are met

Provide:
- Clear summary of results
- Specific fixes for failures
- Performance insights
- Next steps for improvement

Be constructive and specific in feedback.
"""

def extract_session_id(input_text: str) -> Optional[str]:
    """Extract session ID from input text if present"""
    lines = input_text.split('\n')
    for line in lines:
        if 'SESSION_ID:' in line:
            return line.split('SESSION_ID:')[1].strip()
    return None

def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(os.urandom(16)).hexdigest()[:8]
    return f"exec_{timestamp}_{random_hash}"

def format_docker_execution_response(session_id: str, env_spec: Dict, 
                                   container_info: Dict, execution_result: Dict, 
                                   analysis: str) -> str:
    """Format the execution response"""
    response = []
    
    # Header
    status = "✅" if execution_result.get("overall_success", False) else "❌"
    response.append(f"{status} DOCKER EXECUTION RESULT")
    response.append("=" * 60)
    response.append(f"🔗 Session ID: {session_id}")
    response.append(f"🐳 Container: {container_info['container_name']}")
    response.append(f"📦 Environment: {env_spec.get('language', 'unknown')}:{env_spec.get('version', 'latest')}")
    response.append("")
    
    # Execution Details
    response.append("📊 EXECUTION DETAILS")
    response.append("-" * 40)
    for execution in execution_result.get("executions", []):
        cmd_status = "✅" if execution["success"] else "❌"
        response.append(f"{cmd_status} Command: {execution['command']}")
        response.append(f"   Exit Code: {execution['exit_code']}")
        
        if execution["stdout"]:
            response.append("   Output:")
            for line in execution["stdout"].split('\n')[:10]:  # First 10 lines
                if line.strip():
                    response.append(f"      {line}")
        
        if execution["stderr"]:
            response.append("   Errors:")
            for line in execution["stderr"].split('\n')[:5]:  # First 5 error lines
                if line.strip():
                    response.append(f"      {line}")
        response.append("")
    
    # Analysis
    response.append("🔍 ANALYSIS")
    response.append("-" * 40)
    response.append(analysis)
    
    return "\n".join(response)

async def executor_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for analyzing, building, and executing code in Docker environments"""
    print("🐳 Docker Executor Agent Starting...")
    
    # Ensure the generated code directory exists
    generated_path = Path(GENERATED_CODE_PATH)
    generated_path.mkdir(parents=True, exist_ok=True)
    print(f"📂 Generated code will be saved to: {generated_path.absolute()}")
    
    # Initialize OpenAI client
    llm = ChatModel.from_name(executor_config["model"])
    
    # Extract input
    input_text = ""
    for message in input:
        for part in message.parts:
            input_text += part.content + "\n"
    
    # Extract or generate session ID
    session_id = extract_session_id(input_text) or generate_session_id()
    print(f"📋 Session ID: {session_id}")
    
    try:
        # Step 1: Analyze environment requirements using LLM
        print("🔍 Analyzing environment requirements...")
        agent = ReActAgent(
            llm=llm,
            tools=[],
            templates={
                "system": lambda template: template.update(
                    defaults=exclude_none({
                        "instructions": ENVIRONMENT_ANALYSIS_INSTRUCTIONS,
                        "role": "system",
                    })
                )
            },
            memory=TokenMemory(llm)
        )
        
        analysis_prompt = f"""
        Analyze this code submission and determine:
        1. Programming language and version needed
        2. Required dependencies and packages
        3. System dependencies (databases, tools, etc.)
        4. Optimal base Docker image
        5. Build and execution commands
        
        Code submission:
        {input_text}
        """
        
        analysis_response = await agent.run(prompt=analysis_prompt)
        environment_spec = parse_environment_spec(analysis_response.result.text)
        
        # Step 2: Build or retrieve Docker environment
        print("🔨 Setting up Docker environment...")
        docker_manager = DockerEnvironmentManager(session_id)
        await docker_manager.initialize()
        
        # Check if we already have an environment for this session
        container_info = await docker_manager.get_or_create_environment(
            environment_spec,
            input_text
        )
        
        # Step 3: Execute code in the container
        print("▶️  Executing code in container...")
        execution_result = await docker_manager.execute_in_container(
            container_info['container_id'],
            environment_spec.execution_commands
        )
        
        # Step 4: Analyze results with LLM
        print("📊 Analyzing execution results...")
        result_agent = ReActAgent(
            llm=llm,
            tools=[],
            templates={
                "system": lambda template: template.update(
                    defaults=exclude_none({
                        "instructions": RESULT_ANALYSIS_INSTRUCTIONS,
                        "role": "system",
                    })
                )
            },
            memory=TokenMemory(llm)
        )
        
        result_prompt = f"""
        Analyze these execution results:
        
        Environment: {json.dumps(environment_spec.__dict__ if hasattr(environment_spec, '__dict__') else environment_spec, indent=2)}
        Container: {container_info['container_id'][:12]}
        Execution Results: {json.dumps(execution_result, indent=2)}
        
        Original Requirements Context:
        {input_text[:1000]}...
        
        Provide comprehensive analysis including:
        - Test results summary
        - Any failures and their causes
        - Performance observations
        - Recommendations for improvement
        - Whether the implementation meets requirements
        """
        
        final_analysis = await result_agent.run(prompt=result_prompt)
        
        # Format response
        response = format_docker_execution_response(
            session_id,
            environment_spec.__dict__ if hasattr(environment_spec, '__dict__') else environment_spec,
            container_info,
            execution_result,
            final_analysis.result.text
        )
        
        yield MessagePart(content=response)
        
    except Exception as e:
        print(f"❌ Executor error: {e}")
        error_response = f"""
❌ DOCKER EXECUTION ERROR

Session ID: {session_id}
Error: {str(e)}

Please check:
1. Docker is installed and running
2. The code format is correct
3. Dependencies are properly specified

Technical details:
{str(e)}
"""
        yield MessagePart(content=error_response)
