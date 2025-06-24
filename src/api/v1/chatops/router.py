"""
ChatOps API router.

This module implements the FastAPI router for ChatOps functionality, allowing chat-based
interaction with the Agent Blackwell system through various chat platforms.
"""

import logging
import os
import re
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from src.api.v1.chatops.models import (
    ChatCommandRequest,
    ChatCommandResponse,
    CommandType,
    TaskCreationResponse,
    TaskStatusResponse,
)
from src.orchestrator.main import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create router
router = APIRouter(prefix="/api/v1/chatops", tags=["ChatOps"])


# Command parser regex patterns
COMMAND_PATTERN = re.compile(r"^!(\w+)\s*(.*)?$")
PARAM_PATTERN = re.compile(r"--(\w+)=([^\s]+)")


# Create a dependency for getting the orchestrator
async def get_orchestrator() -> Orchestrator:
    """
    Dependency to get the Orchestrator instance.

    This ensures we have a single Orchestrator instance for handling tasks.
    """
    # In a real-world scenario, you might want to use a more robust
    # dependency injection system or a global state manager
    orchestrator = Orchestrator(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    )

    # Initialize agents
    orchestrator.initialize_agents()

    return orchestrator


@router.post("/command", response_model=ChatCommandResponse)
async def process_command(
    request: ChatCommandRequest,
    background_tasks: BackgroundTasks,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> ChatCommandResponse:
    """
    Process a chat command and return an appropriate response.

    This endpoint handles commands sent from chat platforms. It parses the command,
    dispatches it to the appropriate handler, and returns a response.
    """
    logger.info(
        f"Received command: {request.command} from {request.platform} user {request.user_id}"
    )

    # Parse the command
    command_match = COMMAND_PATTERN.match(request.command)
    if not command_match:
        return ChatCommandResponse(
            message="Invalid command format. Commands should start with '!' (e.g., '!deploy')"
        )

    command_type = command_match.group(1).lower()
    command_args = command_match.group(2) or ""

    # Parse any named parameters
    params = {}
    for param_match in PARAM_PATTERN.finditer(command_args):
        param_name = param_match.group(1)
        param_value = param_match.group(2)
        params[param_name] = param_value
        # Remove the parameter from the args
        command_args = command_args.replace(param_match.group(0), "").strip()

    # Clean up remaining command args
    command_args = command_args.strip()

    try:
        # Handle different command types
        if command_type == CommandType.HELP:
            return await handle_help_command()
        elif command_type == CommandType.STATUS:
            task_id = params.get("id") or command_args
            if not task_id:
                return ChatCommandResponse(
                    message="Error: Missing task ID. Usage: !status <task_id> or !status --id=<task_id>"
                )
            return await handle_status_command(orchestrator, task_id)
        elif command_type == CommandType.DEPLOY:
            # Handle deploy command
            return await handle_deploy_command(orchestrator, command_args, params)
        elif command_type in [
            CommandType.SPEC,
            CommandType.DESIGN,
            CommandType.CODE,
            CommandType.REVIEW,
            CommandType.TEST,
        ]:
            # Handle agent commands (spec, design, code, review, test)
            if not command_args:
                return ChatCommandResponse(
                    message=f"Error: The !{command_type} command requires a description. "
                    f"Usage: !{command_type} <description>"
                )

            # Schedule the task in the background
            background_tasks.add_task(
                enqueue_agent_task,
                orchestrator=orchestrator,
                agent_type=command_type,
                description=command_args,
                params=params,
            )

            return ChatCommandResponse(
                message=f"✅ Your {command_type} request has been queued. "
                f"I'll notify you when it's complete."
            )
        else:
            return ChatCommandResponse(
                message=f"Unknown command: {command_type}. Try !help for a list of commands."
            )
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return ChatCommandResponse(
            message=f"An error occurred while processing your command: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str, orchestrator: Orchestrator = Depends(get_orchestrator)
) -> TaskStatusResponse:
    """
    Get the status of a task by its ID.

    This endpoint provides detailed information about a task's status, progress, and results.
    """
    logger.info(f"Getting status for task: {task_id}")

    status = await orchestrator.get_task_status(task_id)

    # If status is None, raise a 404 not found error
    if not status:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found"
        )

    return TaskStatusResponse(
        task_id=task_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", 0),
        result=status.get("result", {}),
        created_at=status.get("created_at"),
        updated_at=status.get("updated_at"),
    )


@router.get("/help", response_model=Dict[str, Any])
async def get_command_help() -> Dict[str, Any]:
    """
    Get help information about available chat commands.

    This endpoint provides documentation about the commands available through ChatOps.
    """
    return {
        "commands": {
            "help": "Show this help message",
            "status": "Check status of a task: !status <task_id>",
            "deploy": "Deploy an application: !deploy <app_name> [--env=prod|staging]",
            "spec": "Create a specification: !spec <description>",
            "design": "Create a design: !design <description>",
            "code": "Generate code: !code <description>",
            "review": "Review code: !review <description>",
            "test": "Generate tests: !test <description>",
        },
        "examples": [
            "!help",
            "!status abc123",
            "!deploy auth-service --env=staging",
            "!spec Create a user authentication API with JWT support",
            "!code Implement a Redis-based rate limiting middleware",
        ],
    }


# Command handlers
async def handle_help_command() -> ChatCommandResponse:
    """Handle the !help command."""
    help_info = await get_command_help()

    # Format the help message
    message = "**Available Commands:**\n\n"

    for cmd, desc in help_info["commands"].items():
        message += f"• **!{cmd}**: {desc}\n"

    message += "\n**Examples:**\n\n"

    for example in help_info["examples"]:
        message += f"• `{example}`\n"

    return ChatCommandResponse(message=message)


async def handle_status_command(
    orchestrator: Orchestrator, task_id: str
) -> ChatCommandResponse:
    """Handle the !status command."""
    status = await orchestrator.get_task_status(task_id)

    if not status:
        return ChatCommandResponse(message=f"❌ Task with ID {task_id} not found.")

    # Format the status message
    message = f"**Status for Task {task_id}:**\n\n"
    message += f"• **Status:** {status.get('status', 'unknown')}\n"

    if status.get("progress") is not None:
        message += f"• **Progress:** {status.get('progress')}%\n"

    message += f"• **Created:** {status.get('created_at', 'unknown')}\n"
    message += f"• **Updated:** {status.get('updated_at', 'unknown')}\n"

    if status.get("error"):
        message += f"\n**Error:** {status.get('error')}\n"

    if status.get("result"):
        message += f"\n**Result Summary:**\n{summarize_result(status.get('result'))}\n"

    return ChatCommandResponse(message=message)


async def handle_deploy_command(
    orchestrator: Orchestrator, app_name: str, params: Dict[str, str]
) -> ChatCommandResponse:
    """Handle the !deploy command."""
    if not app_name:
        return ChatCommandResponse(
            message="Error: Missing application name. Usage: !deploy <app_name> [--env=prod|staging]"
        )

    # Get the environment
    env = params.get("env", "staging").lower()
    if env not in ["prod", "staging", "dev"]:
        return ChatCommandResponse(
            message=f"Error: Invalid environment '{env}'. Valid options are: prod, staging, dev"
        )

    # Create a deploy task
    task_data = {
        "app_name": app_name,
        "environment": env,
    }

    task_id = await orchestrator.enqueue_task("deploy", task_data)

    return ChatCommandResponse(
        message=f"🚀 Deployment of {app_name} to {env} environment has been queued. "
        f"Track status with: !status {task_id}"
    )


async def enqueue_agent_task(
    orchestrator: Orchestrator,
    agent_type: str,
    description: str,
    params: Dict[str, str],
) -> str:
    """Enqueue a task for an agent."""
    # Map command type to agent name
    agent_map = {
        "spec": "spec",
        "design": "design",
        "code": "coding",
        "review": "review",
        "test": "test",
    }

    agent_name = agent_map.get(agent_type, agent_type)

    task_data = {
        "description": description,
        **params,  # Include any additional parameters from the command
    }

    return await orchestrator.enqueue_task(agent_name, task_data)


def summarize_result(result: Any) -> str:
    """Summarize a result for display in chat."""
    if isinstance(result, str):
        # If result is a string, return the first 200 chars
        if len(result) > 200:
            return result[:200] + "..."
        return result

    if isinstance(result, dict):
        # For dictionaries, format as key-value pairs
        return "\n".join(f"• **{k}**: {summarize_result(v)}" for k, v in result.items())

    if isinstance(result, list):
        # For lists, format as bullet points
        if len(result) > 3:
            items = [f"• {summarize_result(item)}" for item in result[:3]]
            items.append(f"• ... ({len(result) - 3} more items)")
            return "\n".join(items)
        return "\n".join(f"• {summarize_result(item)}" for item in result)

    # For other types, convert to string
    return str(result)
