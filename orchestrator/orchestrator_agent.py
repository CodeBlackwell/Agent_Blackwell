from collections.abc import AsyncGenerator
from functools import reduce
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from enum import Enum

# Add the project root to the Python path so we can import from the agents module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from acp_sdk.client import Client
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.utils.dicts import exclude_none
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.tools import ToolOutput
from beeai_framework.tools.tool import Tool
from beeai_framework.tools.types import ToolRunOptions
from beeai_framework.utils.strings import to_json
from pydantic import BaseModel, Field

# Import the modular agents
from agents.planner.planner_agent import planner_agent
from agents.designer.designer_agent import designer_agent
from agents.coder.coder_agent import coder_agent
from agents.test_writer.test_writer_agent import test_writer_agent
from agents.reviewer.reviewer_agent import reviewer_agent

# Import the modular tools
from orchestrator.regression_test_runner_tool import TestRunnerTool
from orchestrator.orchestrator_configs import orchestrator_config

# Load environment variables from .env file
load_dotenv()

# Ensure OPENAI_API_KEY is set in your environment or .env file
server = Server()


# ============================================================================
# INDIVIDUAL TEAM MEMBER AGENTS
# ============================================================================

# Register the imported planner agent
@server.agent()
async def planner_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    """Wrapper to register the modular planner agent with the server"""
    async for part in planner_agent(input):
        yield part


@server.agent()
async def designer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    """Wrapper to register the modular designer agent with the server"""
    async for part in designer_agent(input):
        yield part


@server.agent()
async def coder_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    """Wrapper to register the modular coder agent with the server"""
    async for part in coder_agent(input):
        yield part


@server.agent()
async def test_writer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    """Wrapper to register the modular test_writer agent with the server"""
    async for part in test_writer_agent(input):
        yield part


@server.agent()
async def reviewer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    """Wrapper to register the modular reviewer agent with the server"""
    async for part in reviewer_agent(input):
        yield part


# ============================================================================
# CODING TEAM COORDINATION TOOL
# ============================================================================

# Global variable to track agent execution path
agent_execution_path = []

async def run_team_member(agent: str, input: str) -> list[Message]:
    """
    Calls a team member agent using ACP protocol
    
    Args:
        agent: The agent name to call (planner_agent, designer_agent, etc.)
        input: The input to send to the agent
        
    Returns:
        The agent's response messages
    """
    # Track agent execution path
    global agent_execution_path
    # Convert agent name to readable format (remove _agent suffix if present)
    readable_agent = agent.replace("_agent", "").capitalize()
    agent_execution_path.append(readable_agent)
    # Map agent names to their respective ports
    agent_ports = {
        "planner_agent": 8080,
        "designer_agent": 8080,
        "coder_agent": 8080,
        "test_writer_agent": 8080,
        "reviewer_agent": 8080,
    }
    
    # Map external agent names to internal registered names
    agent_name_mapping = {
        "planner_agent": "planner_agent_wrapper",
        "designer_agent": "designer_agent_wrapper",
        "coder_agent": "coder_agent_wrapper",
        "test_writer_agent": "test_writer_agent_wrapper",
        "reviewer_agent": "reviewer_agent_wrapper"
    }
    
    # Get the internal agent name (use mapping if available, otherwise use original name)
    internal_agent_name = agent_name_mapping.get(agent, agent)
    port = agent_ports.get(agent, 8080)
    base_url = f"http://localhost:{port}"
    
    async with Client(base_url=base_url) as client:
        try:
            run = await client.run_sync(
                agent=internal_agent_name,  # Use mapped internal name
                input=[Message(parts=[MessagePart(content=input, content_type="text/plain")])]
            )
            return run.output
        except Exception as e:
            print(f"❌ Error calling {agent} on {base_url}: {e}")
            return [Message(parts=[MessagePart(content=f"Error from {agent}: {e}", content_type="text/plain")])]


class TeamMember(str, Enum):
    """Team members available for the coding team"""
    planner = "planner"
    designer = "designer"
    test_writer = "test_writer"
    coder = "coder"
    reviewer = "reviewer"


class WorkflowStep(str, Enum):
    """Workflow steps in the development process"""
    planning = "planning"
    design = "design"
    test_writing = "test_writing"
    implementation = "implementation"
    review = "review"
    tdd_workflow = "tdd_workflow"
    full_workflow = "full_workflow"


class CodingTeamInput(BaseModel):
    """Input schema for the coding team tool"""
    requirements: str = Field(description="The project requirements or task description")
    workflow: WorkflowStep = Field(description="The workflow step to execute")
    team_members: list[TeamMember] = Field(
        default=[TeamMember.planner, TeamMember.designer, TeamMember.test_writer, TeamMember.coder, TeamMember.reviewer],
        description="Team members to involve in the process"
    )


class TeamMemberResult(BaseModel):
    """Result from a single team member"""
    team_member: TeamMember = Field(description="The team member who produced this result")
    output: str = Field(description="The output from the team member")


class CodingTeamResult(BaseModel):
    """Result schema containing all team member outputs"""
    results: list[TeamMemberResult] = Field(description="Results from each team member")
    final_summary: str = Field(description="Summary of the complete workflow")
    agent_path: list[str] = Field(default_factory=list, description="Path of agents executed in sequence")


class CodingTeamOutput(ToolOutput):
    """Output from the coding team tool"""
    result: CodingTeamResult = Field(description="Coding team result")

    def get_text_content(self) -> str:
        # Build a more readable text representation
        output = []
        
        # Add each team member result
        for idx, result in enumerate(self.result.results):
            output.append(f"\n{idx+1}. {result.team_member.value.upper()} OUTPUT:")
            output.append("="*50)
            output.append(result.output)
            output.append("\n" + "-"*50)
            
        # Add the final summary with agent path
        output.append(f"\n📋 SUMMARY:\n{self.result.final_summary}")
        
        # Make sure agent path is visible in the output
        if self.result.agent_path:
            path_str = " → ".join(self.result.agent_path)
            output.append(f"\n📊 EXECUTION PATH: {path_str}")
        
        return "\n".join(output)

    def is_empty(self) -> bool:
        return False

    def __init__(self, result: CodingTeamResult) -> None:
        super().__init__()
        self.result = result


class CodingTeamTool(Tool[CodingTeamInput, ToolRunOptions, CodingTeamOutput]):
    """
    Tool that coordinates a coding team workflow across specialized agents.
    """
    name = "CodingTeam"
    description = "Coordinate a coding team to work on software development tasks"
    input_schema = CodingTeamInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "coding_team"],
            creator=self,
        )

    async def _run(
        self, input: CodingTeamInput, options: ToolRunOptions | None, context: RunContext
    ) -> CodingTeamOutput:
        """
        Run the coding team workflow
        """
        global agent_execution_path
        
        # Import here to avoid circular imports
        from workflows import execute_workflow
        
        # Execute the appropriate workflow based on input
        results = await execute_workflow(input)

        print("✅ Coding team workflow completed")
        
        # Create final summary
        summary = f"Coding team workflow completed with {len(results)} team members involved."
        if results:
            summary += f"\nTeam members: {', '.join([r.team_member.value for r in results])}"
            
        # Add agent execution path to summary
        path_str = " → ".join(agent_execution_path)
        summary += f"\n\n📊 Execution Path: {path_str}"

        # Create result with execution path
        result = CodingTeamResult(
            results=results, 
            final_summary=summary,
            agent_path=agent_execution_path
        )
        
        # Reset the global execution path for next run
        agent_execution_path = []
        
        return CodingTeamOutput(result=result)


# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

@server.agent(name="orchestrator", metadata={"ui": {"type": "handsoff"}})
async def main_orchestrator(input: list[Message], context: Context) -> AsyncGenerator:
    """Main orchestrator that manages the coding team workflow"""
    global agent_execution_path
    # Reset agent execution path at the start of each orchestration
    agent_execution_path = []
    llm = ChatModel.from_name(orchestrator_config["model"])

    agent = ReActAgent(
        llm=llm,
        tools=[CodingTeamTool(), TestRunnerTool()],
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": orchestrator_config["instructions"],
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm),
    )

    prompt = reduce(lambda x, y: x + y, input)
    response = await agent.run(str(prompt)).observe(
        lambda emitter: emitter.on(
            "update", lambda data, event: print(f"Orchestrator({data.update.key}) 🎯 : ", data.update.parsed_value)
        )
    )

    yield MessagePart(content=response.result.text)


# Run the server
if __name__ == "__main__":
    print("🚀 Starting Coding Team Agent System on port 8080...")
    server.run(port=8080)