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
import json

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

# Import session utilities
from agents.executor.session_utils import extract_session_id, generate_session_id

def create_proof_of_execution_entry(session_id: str, stage: str, details: Dict, status: str = "started") -> Dict:
    """Create a proof of execution entry"""
    return {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "stage": stage,
        "status": status,
        "details": details
    }

def write_proof_of_execution(session_id: str, entry: Dict, build_path: Optional[Path] = None):
    """Write proof of execution entry to file"""
    # Determine the path for the proof document
    if build_path:
        proof_path = build_path / "proof_of_execution.json"
    else:
        # Fallback to generated code path
        generated_path = Path(GENERATED_CODE_PATH)
        session_dir = generated_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        proof_path = session_dir / "proof_of_execution.json"
    
    # Read existing entries or create new list
    entries = []
    if proof_path.exists():
        try:
            with open(proof_path, 'r') as f:
                entries = json.load(f)
        except:
            entries = []
    
    # Append new entry
    entries.append(entry)
    
    # Write back to file
    with open(proof_path, 'w') as f:
        json.dump(entries, f, indent=2)
    
    print(f"📝 Proof of execution updated: {proof_path}")

def format_docker_execution_response(session_id: str, env_spec: Dict, 
                                   container_info: Dict, execution_result: Dict, 
                                   analysis: str, build_path: Optional[Path] = None) -> str:
    """Format the execution response"""
    response = []
    
    # Header
    status = "✅" if execution_result.get("overall_success", False) else "❌"
    response.append(f"{status} DOCKER EXECUTION RESULT")
    response.append("=" * 60)
    response.append(f"🔗 Session ID: {session_id}")
    response.append(f"🐳 Container: {container_info['container_name']}")
    response.append(f"📦 Environment: {env_spec.get('language', 'unknown')}:{env_spec.get('version', 'latest')}")
    
    # Add proof of execution document path
    if build_path:
        proof_path = build_path / "proof_of_execution.json"
    else:
        proof_path = Path(GENERATED_CODE_PATH) / session_id / "proof_of_execution.json"
    response.append(f"📄 Proof of Execution: {proof_path}")
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
    
    # Initialize variables for tracking execution
    session_id = None
    build_path = None
    
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
    
    # Write initial proof of execution entry
    initial_entry = create_proof_of_execution_entry(
        session_id,
        "executor_initialization",
        {
            "input_length": len(input_text),
            "timestamp_start": datetime.now().isoformat(),
            "generated_path": str(generated_path.absolute())
        },
        "started"
    )
    write_proof_of_execution(session_id, initial_entry)
    
    try:
        # Step 1: Analyze environment requirements using LLM
        print("🔍 Analyzing environment requirements...")
        
        # Log environment analysis start
        env_analysis_entry = create_proof_of_execution_entry(
            session_id,
            "environment_analysis",
            {"action": "Starting environment analysis"},
            "started"
        )
        write_proof_of_execution(session_id, env_analysis_entry)
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
        
        # Log environment analysis completion
        env_complete_entry = create_proof_of_execution_entry(
            session_id,
            "environment_analysis",
            {
                "language": getattr(environment_spec, 'language', 'unknown'),
                "version": getattr(environment_spec, 'version', 'unknown'),
                "base_image": getattr(environment_spec, 'base_image', 'unknown'),
                "dependencies_count": len(getattr(environment_spec, 'dependencies', [])),
                "execution_commands": getattr(environment_spec, 'execution_commands', [])
            },
            "completed"
        )
        write_proof_of_execution(session_id, env_complete_entry)
        
        # Step 2: Build or retrieve Docker environment
        print("🔨 Setting up Docker environment...")
        
        # Log Docker setup start
        docker_setup_entry = create_proof_of_execution_entry(
            session_id,
            "docker_setup",
            {"action": "Initializing Docker environment"},
            "started"
        )
        write_proof_of_execution(session_id, docker_setup_entry)
        
        # Import here to avoid circular import
        from agents.executor.docker_manager import DockerEnvironmentManager
        
        docker_manager = DockerEnvironmentManager(session_id)
        await docker_manager.initialize()
        
        # Check if we already have an environment for this session
        container_info = await docker_manager.get_or_create_environment(
            environment_spec,
            input_text
        )
        
        # Store build path for proof of execution
        if 'build_path' in container_info:
            build_path = Path(container_info['build_path'])
        
        # Log Docker container creation
        docker_complete_entry = create_proof_of_execution_entry(
            session_id,
            "docker_setup",
            {
                "container_id": container_info['container_id'][:12],
                "container_name": container_info['container_name'],
                "image_tag": container_info.get('image_tag', 'unknown'),
                "build_path": str(build_path) if build_path else None,
                "reused_existing": 'Reusing existing' in container_info.get('status', '')
            },
            "completed"
        )
        write_proof_of_execution(session_id, docker_complete_entry, build_path)
        
        # Step 3: Execute code in the container
        print("▶️  Executing code in container...")
        
        # Log execution start
        exec_start_entry = create_proof_of_execution_entry(
            session_id,
            "code_execution",
            {
                "container_id": container_info['container_id'][:12],
                "commands_to_execute": environment_spec.execution_commands,
                "commands_count": len(environment_spec.execution_commands)
            },
            "started"
        )
        write_proof_of_execution(session_id, exec_start_entry, build_path)
        
        execution_result = await docker_manager.execute_in_container(
            container_info['container_id'],
            environment_spec.execution_commands
        )
        
        # Log detailed execution results
        exec_complete_entry = create_proof_of_execution_entry(
            session_id,
            "code_execution",
            {
                "overall_success": execution_result.get("overall_success", False),
                "executions": [
                    {
                        "command": exec_data["command"],
                        "exit_code": exec_data["exit_code"],
                        "success": exec_data["success"],
                        "stdout_length": len(exec_data.get("stdout", "")),
                        "stderr_length": len(exec_data.get("stderr", "")),
                        "stdout_preview": exec_data.get("stdout", "")[:500] if exec_data.get("stdout") else "",
                        "stderr_preview": exec_data.get("stderr", "")[:500] if exec_data.get("stderr") else ""
                    }
                    for exec_data in execution_result.get("executions", [])
                ]
            },
            "completed"
        )
        write_proof_of_execution(session_id, exec_complete_entry, build_path)
        
        # Step 4: Analyze results with LLM
        print("📊 Analyzing execution results...")
        
        # Log analysis start
        analysis_start_entry = create_proof_of_execution_entry(
            session_id,
            "result_analysis",
            {"action": "Starting execution result analysis"},
            "started"
        )
        write_proof_of_execution(session_id, analysis_start_entry, build_path)
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
        
        # Log analysis completion
        analysis_complete_entry = create_proof_of_execution_entry(
            session_id,
            "result_analysis",
            {
                "analysis_length": len(final_analysis.result.text),
                "analysis_preview": final_analysis.result.text[:500]
            },
            "completed"
        )
        write_proof_of_execution(session_id, analysis_complete_entry, build_path)
        
        # Format response
        response = format_docker_execution_response(
            session_id,
            environment_spec.__dict__ if hasattr(environment_spec, '__dict__') else environment_spec,
            container_info,
            execution_result,
            final_analysis.result.text,
            build_path
        )
        
        # Final success entry
        final_entry = create_proof_of_execution_entry(
            session_id,
            "executor_completion",
            {
                "status": "success",
                "proof_document_path": str(build_path / "proof_of_execution.json") if build_path else f"{GENERATED_CODE_PATH}/{session_id}/proof_of_execution.json"
            },
            "completed"
        )
        write_proof_of_execution(session_id, final_entry, build_path)
        
        yield MessagePart(content=response)
        
    except Exception as e:
        print(f"❌ Executor error: {e}")
        
        # Log error
        if session_id:
            error_entry = create_proof_of_execution_entry(
                session_id,
                "executor_error",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
                },
                "failed"
            )
            write_proof_of_execution(session_id, error_entry, build_path)
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
