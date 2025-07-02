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

# Import the modular planner agent
from agents.planner.planner_agent import planner_agent
from agents.designer.designer_agent import designer_agent
from agents.coder.coder_agent import coder_agent

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
async def test_writer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for writing business-value focused tests for TDD"""
    llm = ChatModel.from_name("openai:gpt-3.5-turbo")
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior test engineer specializing in Test-Driven Development (TDD) with a focus on business value.
                    Your role is to:
                    1. Write tests that validate business requirements and user stories
                    2. Create acceptance criteria that define "done" from a business perspective
                    3. Focus on behavior and outcomes rather than implementation details
                    4. Write tests that guide development by defining what success looks like
                    5. Ensure tests capture the WHY (business purpose) not just the WHAT (technical details)
                    6. Create tests that remain valuable even when implementation changes
                    
                    IMPORTANT: Always create concrete test scenarios based on the provided plan and design.
                    Never ask for more details - work with what you have and make reasonable assumptions.
                    Extract business requirements from the plan and create comprehensive test scenarios.
                    
                    Write tests that:
                    - Validate end-to-end user workflows and business processes
                    - Test integration points and system behavior
                    - Focus on user outcomes and business value delivery
                    - Are readable by non-technical stakeholders
                    - Guide implementation rather than constrain it
                    - Test the contract/interface, not internal mechanics
                    
                    Provide:
                    - Business-focused test scenarios
                    - Acceptance criteria in Given-When-Then format
                    - Integration and end-to-end tests
                    - User story validation tests
                    - Performance/scalability tests where business-critical
                    - Clear test descriptions explaining business value
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Write business-value focused tests for TDD approach: " + str(input))
    yield MessagePart(content=response.result.text)


@server.agent()
async def reviewer_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for code review and quality assurance"""
    llm = ChatModel.from_name("openai:gpt-3.5-turbo")
    
    agent = ReActAgent(
        llm=llm, 
        tools=[], 
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are a senior code reviewer and quality assurance engineer. Your role is to:
                    1. Review code for bugs, security issues, and performance problems
                    2. Check adherence to coding standards and best practices
                    3. Verify that implementations match the design specifications
                    4. Identify potential improvements and optimizations
                    5. Ensure proper testing coverage and documentation
                    6. Provide constructive feedback and suggestions
                    
                    Provide comprehensive review feedback including:
                    - Code Quality Assessment
                    - Security Analysis
                    - Performance Considerations
                    - Best Practice Compliance
                    - Improvement Suggestions
                    - Test Coverage Analysis
                    - Final Approval/Rejection with reasoning
                    """,
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm)
    )
    
    response = await agent.run(prompt="Review the following work: " + str(input))
    yield MessagePart(content=response.result.text)


# ============================================================================
# CODING TEAM COORDINATION TOOL
# ============================================================================

async def run_team_member(agent: str, input: str) -> list[Message]:
    """
    Calls a team member agent using ACP protocol
    
    Args:
        agent: The agent name to call (planner_agent, designer_agent, etc.)
        input: The input to send to the agent
        
    Returns:
        The agent's response messages
    """
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
        "coder_agent": "coder_agent_wrapper"
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


class CodingTeamOutput(ToolOutput):
    """Output from the coding team tool"""
    result: CodingTeamResult = Field(description="Coding team result")

    def get_text_content(self) -> str:
        return to_json(self.result)

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
        results = []
        
        if input.workflow == WorkflowStep.tdd_workflow:
            # Run TDD workflow: planner -> designer -> test_writer -> coder -> reviewer
            print(f"🧪 Starting TDD workflow for: {input.requirements[:50]}...")
            
            # Step 1: Planning
            if TeamMember.planner in input.team_members:
                print("📋 Planning phase...")
                planning_result = await run_team_member("planner_agent", input.requirements)
                plan_output = str(planning_result[0])
                results.append(TeamMemberResult(team_member=TeamMember.planner, output=plan_output))
                
                # Step 2: Design (using plan as input)
                if TeamMember.designer in input.team_members:
                    print("🎨 Design phase...")
                    design_input = f"""You are the designer for this project. Here is the detailed plan:

{plan_output}

Based on this plan, create a comprehensive technical design. Do NOT ask for more details - use the plan above to extract all technical requirements and create concrete designs.

Original requirements: {input.requirements}

Create the technical architecture, database schemas, API endpoints, and component designs."""
                    design_result = await run_team_member("designer_agent", design_input)
                    design_output = str(design_result[0])
                    results.append(TeamMemberResult(team_member=TeamMember.designer, output=design_output))
                    
                    # Step 3: Test Writing (using plan and design as input)
                    if TeamMember.test_writer in input.team_members:
                        print("🧪 Test writing phase...")
                        test_input = f"""You are the test writer for this project. Here is the plan and design:

PLAN:
{plan_output}

DESIGN:
{design_output}

Based on this plan and design, write comprehensive business-value focused tests. Do NOT ask for more details - extract the business requirements from the above information and create test scenarios.

Original requirements: {input.requirements}

Write Given-When-Then test scenarios that validate business outcomes."""
                        test_result = await run_team_member("test_writer_agent", test_input)
                        test_output = str(test_result[0])
                        results.append(TeamMemberResult(team_member=TeamMember.test_writer, output=test_output))
                        
                        # Step 4: Implementation (using tests to guide development)
                        if TeamMember.coder in input.team_members:
                            print("💻 Implementation phase (TDD-guided)...")
                            code_input = f"""You are the developer for this project. Here are the specifications:

PLAN:
{plan_output}

DESIGN:
{design_output}

TESTS TO SATISFY:
{test_output}

Based on these specifications, implement working code that satisfies the tests and follows the design. Do NOT ask for more details - use the above information to create a complete implementation.

Original requirements: {input.requirements}

Write complete, working code with proper documentation."""
                            code_result = await run_team_member("coder_agent", code_input)
                            code_output = str(code_result[0])
                            results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                            
                            # Step 5: Review (using implementation as input)
                            if TeamMember.reviewer in input.team_members:
                                print("🔍 Review phase...")
                                review_input = f"""You are reviewing this TDD implementation. Here is the complete context:

ORIGINAL REQUIREMENTS: {input.requirements}

TESTS THAT SHOULD BE SATISFIED:
{test_output}

IMPLEMENTATION TO REVIEW:
{code_output}

Review this implementation for code quality, security, performance, and adherence to the tests. Provide specific feedback and recommendations."""
                                review_result = await run_team_member("reviewer_agent", review_input)
                                review_output = str(review_result[0])
                                results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_output))
            
        elif input.workflow == WorkflowStep.full_workflow:
                # Step 2: Design (using plan as input)
                if TeamMember.designer in input.team_members:
                    print("🎨 Design phase...")
                    design_input = f"""You are the designer for this project. Here is the detailed plan:

{plan_output}

Based on this plan, create a comprehensive technical design. Do NOT ask for more details - use the plan above to extract all technical requirements and create concrete designs.

Original requirements: {input.requirements}

Create the technical architecture, database schemas, API endpoints, and component designs."""
                    design_result = await run_team_member("designer_agent", design_input)
                    design_output = str(design_result[0])
                    results.append(TeamMemberResult(team_member=TeamMember.designer, output=design_output))
                    
                    # Step 3: Implementation (using plan and design as input)
                    if TeamMember.coder in input.team_members:
                        print("💻 Implementation phase...")
                        code_input = f"""You are the developer for this project. Here are the specifications:

PLAN:
{plan_output}

DESIGN:
{design_output}

Based on these specifications, implement working code that follows the design. Do NOT ask for more details - use the above information to create a complete implementation.

Original requirements: {input.requirements}

Write complete, working code with proper documentation."""
                        code_result = await run_team_member("coder_agent", code_input)
                        code_output = str(code_result[0])
                        results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                        
                        # Step 4: Review (using implementation as input)
                        if TeamMember.reviewer in input.team_members:
                            print("🔍 Review phase...")
                            review_input = f"""You are reviewing this implementation. Here is the complete context:

ORIGINAL REQUIREMENTS: {input.requirements}

PLAN:
{plan_output}

DESIGN:
{design_output}

IMPLEMENTATION TO REVIEW:
{code_output}

Review this implementation for code quality, security, performance, and adherence to the design. Provide specific feedback and recommendations."""
                            review_result = await run_team_member("reviewer_agent", review_input)
                            review_output = str(review_result[0])
                            results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_output))
            
        else:
            # Run specific workflow step
            agent_map = {
                WorkflowStep.planning: "planner_agent",
                WorkflowStep.design: "designer_agent",
                WorkflowStep.test_writing: "test_writer_agent",
                WorkflowStep.implementation: "coder_agent",
                WorkflowStep.review: "reviewer_agent"
            }
            
            if input.workflow in agent_map:
                print(f"🔄 Running {input.workflow.value} phase...")
                result = await run_team_member(agent_map[input.workflow], input.requirements)
                output = str(result[0])
                
                # Map workflow steps to team members
                step_to_member = {
                    WorkflowStep.planning: TeamMember.planner,
                    WorkflowStep.design: TeamMember.designer,
                    WorkflowStep.test_writing: TeamMember.test_writer,
                    WorkflowStep.implementation: TeamMember.coder,
                    WorkflowStep.review: TeamMember.reviewer
                }
                
                team_member = step_to_member[input.workflow]
                results.append(TeamMemberResult(team_member=team_member, output=output))

        print("✅ Coding team workflow completed")
        
        # Create final summary
        summary = f"Coding team workflow completed with {len(results)} team members involved."
        if results:
            summary += f"\nTeam members: {', '.join([r.team_member.value for r in results])}"

        return CodingTeamOutput(
            result=CodingTeamResult(results=results, final_summary=summary)
        )


# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

@server.agent(name="orchestrator", metadata={"ui": {"type": "handsoff"}})
async def main_orchestrator(input: list[Message], context: Context) -> AsyncGenerator:
    """Main orchestrator that manages the coding team workflow"""
    llm = ChatModel.from_name("openai:gpt-3.5-turbo")

    agent = ReActAgent(
        llm=llm,
        tools=[CodingTeamTool()],
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": """
                    You are the orchestrator of a coding team consisting of:
                    - Planner: Creates project plans and breaks down requirements
                    - Designer: Creates system architecture and technical designs
                    - Test Writer: Creates business-value focused tests for TDD approach
                    - Coder: Implements the code based on plans, designs, and tests
                    - Reviewer: Reviews code for quality, security, and best practices
                    
                    Based on user requests, coordinate the appropriate team members using the CodingTeam tool.
                    
                    WORKFLOW SELECTION RULES:
                    1. Look for explicit workflow keywords in user input:
                       - "tdd workflow" or "test-driven" → use tdd_workflow
                       - "full workflow" or "complete cycle" → use full_workflow
                       - "just planning" or "only plan" → use planning
                       - "just design" or "only design" → use design
                       - "write tests" or "only tests" → use test_writing
                       - "just code" or "only implement" → use implementation
                       - "just review" or "only review" → use review
                    
                    2. Default behavior when no explicit workflow is specified:
                       - For new features/projects → use tdd_workflow (recommended)
                       - For code review requests → use review
                       - For architectural questions → use design
                       - For project planning → use planning
                    
                    3. Available workflows:
                       - tdd_workflow: Full TDD cycle (planner → designer → test_writer → coder → reviewer)
                       - full_workflow: Traditional cycle (planner → designer → coder → reviewer)
                       - Individual steps: planning, design, test_writing, implementation, review
                    
                    4. Team member selection:
                       - Default: include all relevant team members for the workflow
                       - If user specifies "without X" or "skip X", exclude that team member
                    
                    Examples:
                    - "Use TDD workflow to build a REST API" → tdd_workflow
                    - "Just do planning for a mobile app" → planning only
                    - "Full workflow but skip tests" → full_workflow, exclude test_writer
                    - "Write tests for user authentication" → test_writing only
                    
                    Always use the CodingTeam tool to coordinate team members.
                    Present results in a clear, organized manner.
                    """,
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