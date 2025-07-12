from collections.abc import AsyncGenerator
from functools import reduce
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import time
import json
import re
import subprocess
import platform

# Add the project root to the Python path so we can import from the agents module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import shared data models
from shared.data_models import (
    TeamMember, WorkflowStep, TeamMemberResult, 
    CodingTeamInput, CodingTeamResult
)

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
from agents.feature_coder.feature_coder_agent import feature_coder_agent
from agents.validator.validator_agent import validator_agent
from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent

# Import the modular tools
from orchestrator.regression_test_runner_tool import TestRunnerTool

# Import the enhanced orchestrator config
from orchestrator.orchestrator_configs import orchestrator_config, OUTPUT_DISPLAY_CONFIG

# Import monitoring system
from workflows.monitoring import WorkflowExecutionTracer, StepStatus, ReviewDecision

# Import real-time output handler
from workflows.agent_output_handler import RealTimeOutputHandler, get_output_handler, set_output_handler

# Load environment variables from .env file
load_dotenv()

# Configure logging
import logging

# Check if debug mode is enabled
debug_mode = os.environ.get('ORCHESTRATOR_DEBUG', '').lower() in ['1', 'true', 'yes']
log_level = logging.DEBUG if debug_mode else logging.WARNING

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if debug_mode else '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create orchestrator logger
logger = logging.getLogger("orchestrator")
logger.setLevel(log_level)

# Suppress noisy loggers unless in debug mode
if not debug_mode:
    # Suppress HTTP client logs
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('aiohttp').setLevel(logging.ERROR)
    logging.getLogger('acp_sdk').setLevel(logging.ERROR)
    logging.getLogger('beeai_framework').setLevel(logging.ERROR)

server = Server()

# ============================================================================
# ENHANCED PROGRESS TRACKING
# ============================================================================

@dataclass
class ObjectiveStatus:
    """Track individual objective completion"""
    name: str
    description: str
    agent: str
    status: str  # "pending", "in_progress", "completed", "failed"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    output_length: int = 0
    challenges: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def status_emoji(self) -> str:
        return {
            "pending": "⏳", 
            "in_progress": "🔄", 
            "completed": "✅", 
            "failed": "❌"
        }.get(self.status, "❓")

@dataclass
class TestResults:
    """Track test execution results"""
    tests_written: int = 0
    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    coverage_info: Optional[str] = None
    
    @property
    def pass_rate(self) -> float:
        if self.tests_executed == 0:
            return 0.0
        return (self.tests_passed / self.tests_executed) * 100

@dataclass
class ProgressReport:
    """Comprehensive progress tracking"""
    session_id: str
    workflow_type: str
    start_time: float
    end_time: Optional[float] = None
    objectives: List[ObjectiveStatus] = field(default_factory=list)
    test_results: TestResults = field(default_factory=TestResults)
    challenges: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    proof_of_execution_path: Optional[str] = None
    execution_verified: bool = False
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        completed = sum(1 for obj in self.objectives if obj.status == "completed")
        total = len(self.objectives)
        return (completed / total * 100) if total > 0 else 0.0
    
    def generate_report(self) -> str:
        """Generate aesthetic progress report"""
        report = []
        
        # Header
        report.append("🎯 WORKFLOW PROGRESS REPORT")
        report.append("=" * 80)
        report.append(f"📋 Workflow: {self.workflow_type}")
        report.append(f"⏱️  Duration: {self.duration:.2f}s")
        report.append(f"📊 Success Rate: {self.success_rate:.1f}%")
        report.append("")
        
        # Objectives Summary
        completed = sum(1 for obj in self.objectives if obj.status == "completed")
        failed = sum(1 for obj in self.objectives if obj.status == "failed")
        in_progress = sum(1 for obj in self.objectives if obj.status == "in_progress")
        pending = sum(1 for obj in self.objectives if obj.status == "pending")
        
        report.append("📈 OBJECTIVES SUMMARY")
        report.append("-" * 40)
        report.append(f"✅ Completed: {completed}/{len(self.objectives)}")
        report.append(f"❌ Failed: {failed}")
        report.append(f"🔄 In Progress: {in_progress}")
        report.append(f"⏳ Pending: {pending}")
        report.append("")
        
        # Detailed Objectives Checklist
        report.append("📋 OBJECTIVES CHECKLIST")
        report.append("-" * 40)
        for i, obj in enumerate(self.objectives, 1):
            status_line = f"{obj.status_emoji} {i}. {obj.name} ({obj.agent})"
            if obj.status == "completed":
                status_line += f" - {obj.duration:.2f}s"
            report.append(status_line)
            
            if obj.description:
                report.append(f"   └─ {obj.description}")
            
            if obj.challenges:
                for challenge in obj.challenges:
                    report.append(f"   ⚠️  Challenge: {challenge}")
        report.append("")
        
        # Test Results
        if self.test_results.tests_written > 0:
            report.append("🧪 TEST RESULTS")
            report.append("-" * 40)
            report.append(f"📝 Tests Written: {self.test_results.tests_written}")
            report.append(f"▶️  Tests Executed: {self.test_results.tests_executed}")
            report.append(f"✅ Tests Passed: {self.test_results.tests_passed}")
            report.append(f"❌ Tests Failed: {self.test_results.tests_failed}")
            report.append(f"📊 Pass Rate: {self.test_results.pass_rate:.1f}%")
            
            if self.test_results.test_details:
                report.append("\n📋 Test Details:")
                for test in self.test_results.test_details:
                    status = "✅" if test.get("passed", False) else "❌"
                    report.append(f"  {status} {test.get('name', 'Unknown Test')}")
            report.append("")
        
        # Development Challenges
        if self.challenges:
            report.append("⚠️  DEVELOPMENT CHALLENGES")
            report.append("-" * 40)
            for i, challenge in enumerate(self.challenges, 1):
                report.append(f"{i}. {challenge}")
            report.append("")
        
        # Performance Metrics
        if self.performance_metrics:
            report.append("📊 PERFORMANCE METRICS")
            report.append("-" * 40)
            for key, value in self.performance_metrics.items():
                report.append(f"• {key}: {value}")
            report.append("")
        
        # Proof of Execution
        if self.proof_of_execution_path:
            report.append("🔐 PROOF OF EXECUTION")
            report.append("-" * 40)
            report.append(f"📄 Document Path: {self.proof_of_execution_path}")
            report.append(f"✅ Execution Verified: {'Yes' if self.execution_verified else 'No'}")
            report.append("")
        
        # Footer
        status = "🎉 SUCCESS" if self.success_rate == 100 else "⚠️  PARTIAL SUCCESS" if self.success_rate > 0 else "❌ FAILED"
        report.append(f"🎯 FINAL STATUS: {status}")
        report.append("=" * 80)
        
        return "\n".join(report)

# Global progress tracking
current_progress_report: Optional[ProgressReport] = None

# ============================================================================
# INDIVIDUAL TEAM MEMBER AGENTS (Enhanced with Progress Tracking)
# ============================================================================

async def run_team_member_with_tracking(agent: str, input: str, objective_name: str) -> List[Message]:
    """Enhanced team member execution with progress tracking and real-time output"""
    global current_progress_report
    
    # Get the output handler
    output_handler = get_output_handler()
    
    # Determine step number based on completed objectives
    step_number = 1
    if current_progress_report:
        completed_count = sum(1 for obj in current_progress_report.objectives if obj.status in ["completed", "failed"])
        step_number = completed_count + 1
    
    if current_progress_report:
        # Find or create objective
        objective = None
        for obj in current_progress_report.objectives:
            if obj.name == objective_name:
                objective = obj
                break
        
        if not objective:
            objective = ObjectiveStatus(
                name=objective_name,
                description=f"Execute {agent} for {objective_name}",
                agent=agent,
                status="pending"
            )
            current_progress_report.objectives.append(objective)
        
        # Update status to in_progress
        objective.status = "in_progress"
        objective.start_time = time.time()
    
    try:
        # Display agent start in real-time
        start_time = output_handler.on_agent_start(agent, input, step_number)
        
        # Execute the agent
        result = await run_team_member(agent, input)
        
        # Extract output text
        output_text = ""
        if result and len(result) > 0:
            if hasattr(result[0], 'parts') and len(result[0].parts) > 0:
                output_text = result[0].parts[0].content
            else:
                output_text = str(result[0])
        
        # Display agent completion in real-time
        metadata = {"objective": objective_name}
        if current_progress_report and objective:
            metadata["duration"] = time.time() - objective.start_time
        
        output_handler.on_agent_complete(
            agent_name=agent,
            input_text=input,
            output_text=output_text,
            start_time=start_time,
            step_number=step_number,
            metadata=metadata
        )
        
        if current_progress_report and objective:
            # Update status to completed
            objective.status = "completed"
            objective.end_time = time.time()
            objective.output_length = len(output_text)
            
            # Analyze output for challenges
            output_text_lower = output_text.lower()
            if any(keyword in output_text_lower for keyword in ["error", "issue", "problem", "challenge"]):
                objective.challenges.append("Potential issues detected in output")
        
        return result
        
    except Exception as e:
        if current_progress_report and objective:
            objective.status = "failed"
            objective.end_time = time.time()
            objective.challenges.append(f"Execution failed: {str(e)}")
            
            # Add to global challenges
            current_progress_report.challenges.append(f"{agent} failed: {str(e)}")
        
        # Display error in output handler
        output_handler.on_agent_complete(
            agent_name=agent,
            input_text=input,
            output_text=f"ERROR: {str(e)}",
            start_time=start_time if 'start_time' in locals() else time.time(),
            step_number=step_number,
            metadata={"error": str(e), "objective": objective_name}
        )
        
        raise e

# Original run_team_member function (keeping for compatibility)
async def run_team_member(agent: str, input: str) -> list[Message]:
    """Calls a team member agent using ACP protocol"""
    import logging
    logger = logging.getLogger("orchestrator")
    
    agent_ports = {
        "planner_agent": 8080,
        "designer_agent": 8080,
        "coder_agent": 8080,
        "test_writer_agent": 8080,
        "reviewer_agent": 8080,
        "feature_coder_agent": 8080,
        "executor_agent": 8080,
        "validator_agent": 8080,
        "feature_reviewer_agent": 8080,
    }
    
    agent_name_mapping = {
        "planner_agent": "planner_agent_wrapper",
        "designer_agent": "designer_agent_wrapper",
        "coder_agent": "coder_agent_wrapper",
        "test_writer_agent": "test_writer_agent_wrapper",
        "reviewer_agent": "reviewer_agent_wrapper",
        "executor_agent": "executor_agent_wrapper",
        "feature_coder_agent": "feature_coder_agent_wrapper",
        "validator_agent": "validator_agent_wrapper",
        "feature_reviewer_agent": "feature_reviewer_agent_wrapper"
    }
    
    internal_agent_name = agent_name_mapping.get(agent, agent)
    port = agent_ports.get(agent, 8080)
    base_url = f"http://localhost:{port}"
    
    # Log agent call details
    logger.info(f"🤖 Calling agent: {agent} ({internal_agent_name})")
    logger.info(f"📍 Agent endpoint: {base_url}")
    logger.info(f"📝 Input preview: {input[:200]}..." if len(input) > 200 else f"📝 Input: {input}")
    
    async with Client(base_url=base_url) as client:
        try:
            start_time = time.time()
            run = await client.run_sync(
                agent=internal_agent_name,
                input=[Message(parts=[MessagePart(content=input, content_type="text/plain")])]
            )
            duration = time.time() - start_time
            
            # Log successful completion
            output_preview = ""
            if run.output and len(run.output) > 0 and hasattr(run.output[0], 'parts'):
                output_preview = run.output[0].parts[0].content[:200]
            logger.info(f"✅ Agent {agent} completed in {duration:.2f}s")
            logger.info(f"📤 Output preview: {output_preview}..." if len(output_preview) >= 200 else f"📤 Output: {output_preview}")
            
            return run.output
        except Exception as e:
            logger.error(f"❌ Error calling {agent} on {base_url}: {e}")
            print(f"❌ Error calling {agent} on {base_url}: {e}")
            return [Message(parts=[MessagePart(content=f"Error from {agent}: {e}", content_type="text/plain")])]

# Register agent wrappers
@server.agent()
async def planner_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in planner_agent(input):
        yield part

@server.agent()
async def designer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in designer_agent(input):
        yield part

@server.agent()
async def coder_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in coder_agent(input):
        yield part

@server.agent()
async def feature_coder_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in feature_coder_agent(input):
        yield part

@server.agent()
async def test_writer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in test_writer_agent(input):
        yield part

@server.agent()
async def reviewer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in reviewer_agent(input):
        yield part

@server.agent()
async def executor_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    from agents.executor.executor_agent import executor_agent
    async for part in executor_agent(input):
        yield part

@server.agent()
async def validator_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in validator_agent(input):
        yield part

@server.agent()
async def feature_reviewer_agent_wrapper(input: list[Message]) -> AsyncGenerator:
    async for part in feature_reviewer_agent(input):
        yield part

# ============================================================================
# ENHANCED CODING TEAM COORDINATION TOOL
# ============================================================================

# Using shared data models from shared.data_models
# TeamMember, WorkflowStep, CodingTeamInput, TeamMemberResult, CodingTeamResult are imported above

# Pydantic models for tool interface (keeping separate from dataclasses)
class CodingTeamInputModel(BaseModel):
    requirements: str = Field(description="The project requirements or task description")
    workflow_type: str = Field(description="The workflow type to execute (tdd, full, individual)")
    step_type: Optional[str] = Field(default=None, description="For individual workflows, the specific step")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=300, description="Timeout in seconds")

class TeamMemberResultModel(BaseModel):
    team_member: str = Field(description="The team member who produced this result")
    output: str = Field(description="The output from the team member")

class CodingTeamResultModel(BaseModel):
    results: list[TeamMemberResultModel] = Field(description="Results from each team member")
    final_summary: str = Field(description="Summary of the complete workflow")
    progress_report: str = Field(description="Detailed progress report")
    success_metrics: Dict[str, Any] = Field(default_factory=dict, description="Success metrics and statistics")
    monitoring_report: Optional[str] = Field(default=None, description="Comprehensive monitoring report in JSON format")
    execution_tracer: Optional[Any] = Field(default=None, description="WorkflowExecutionTracer instance for detailed analysis")

class CodingTeamOutput(ToolOutput):
    result: CodingTeamResultModel = Field(description="Enhanced coding team result")

    def get_text_content(self) -> str:
        return self.result.progress_report

    def is_empty(self) -> bool:
        return False

    def __init__(self, result: CodingTeamResultModel) -> None:
        super().__init__()
        self.result = result

class EnhancedCodingTeamTool(Tool[CodingTeamInputModel, ToolRunOptions, CodingTeamOutput]):
    """Enhanced tool with comprehensive progress tracking and parallel execution"""
    name = "CodingTeam"
    description = "Coordinate a coding team with detailed progress tracking and parallel execution capabilities"
    input_schema = CodingTeamInputModel

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "enhanced_coding_team"],
            creator=self,
        )

    async def _run(
        self, input: CodingTeamInputModel, options: ToolRunOptions | None, context: RunContext
    ) -> CodingTeamOutput:
        """Enhanced workflow execution with comprehensive tracking"""
        global current_progress_report
        
        # Initialize progress tracking
        session_id = f"session_{int(time.time())}"
        current_progress_report = ProgressReport(
            session_id=session_id,
            workflow_type=input.workflow_type,
            start_time=time.time()
        )
        
        # Initialize real-time output handler with configuration
        display_mode = OUTPUT_DISPLAY_CONFIG.get("mode", "detailed")
        max_input_chars = OUTPUT_DISPLAY_CONFIG.get("max_input_chars", 1000)
        max_output_chars = OUTPUT_DISPLAY_CONFIG.get("max_output_chars", 2000)
        output_handler = RealTimeOutputHandler(
            display_mode=display_mode,
            max_input_chars=max_input_chars,
            max_output_chars=max_output_chars
        )
        set_output_handler(output_handler)
        
        import logging
        logger = logging.getLogger("orchestrator")
        
        logger.info(f"🚀 Starting Enhanced Workflow: {input.workflow_type}")
        logger.info(f"📋 Session ID: {session_id}")
        logger.info(f"📝 Requirements: {input.requirements[:200]}..." if len(input.requirements) > 200 else f"📝 Requirements: {input.requirements}")
        logger.info(f"⚙️ Max retries: {input.max_retries}, Timeout: {input.timeout_seconds}s")
        logger.info(f"📺 Output Mode: {display_mode}")
        
        print(f"🚀 Starting Enhanced Workflow: {input.workflow_type}")
        print(f"📋 Session ID: {session_id}")
        print(f"📺 Output Mode: {display_mode}")
        print()
        
        try:
            # Import here to avoid circular imports
            from workflows import execute_workflow
            
            # Create comprehensive monitoring tracer
            tracer = WorkflowExecutionTracer(
                workflow_type=input.workflow_type,
                execution_id=session_id
            )
            
            # Convert Pydantic model to dataclass for workflow execution
            workflow_input = CodingTeamInput(
                requirements=input.requirements,
                workflow_type=input.workflow_type,
                step_type=input.step_type,
                max_retries=input.max_retries,
                timeout_seconds=input.timeout_seconds
            )
            
            # Execute the workflow with comprehensive monitoring
            logger.info(f"🔄 Executing workflow via workflow_manager...")
            results, execution_report = await execute_workflow(workflow_input, tracer=tracer)
            logger.info(f"✅ Workflow execution completed with {len(results)} results")
            
            # Analyze test results from outputs
            await self._analyze_test_results(results)
            
            # Generate performance metrics
            await self._calculate_performance_metrics(results)
            
            # Extract proof of execution data from execution report
            if execution_report and hasattr(execution_report, 'proof_of_execution_path'):
                current_progress_report.proof_of_execution_path = execution_report.proof_of_execution_path
                if hasattr(execution_report, 'proof_of_execution_data') and execution_report.proof_of_execution_data:
                    current_progress_report.execution_verified = execution_report.proof_of_execution_data.get('execution_success', False)
            
            # Complete progress tracking
            current_progress_report.end_time = time.time()
            tracer.complete_execution(
                final_output={
                    "results_count": len(results),
                    "session_id": session_id,
                    "workflow_type": input.workflow_type
                }
            )
            
            # Generate comprehensive reports
            progress_report = current_progress_report.generate_report()
            monitoring_report = execution_report.to_json() if execution_report else None
            
            # Add output handler summary
            handler_summary = output_handler.generate_summary()
            print(handler_summary)
            
            # Optionally export interactions
            export_path = f"logs/{session_id}_interactions.json"
            try:
                import os
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                output_handler.export_interactions(export_path)
            except Exception as e:
                print(f"Failed to export interactions: {e}")
            
            # Create enhanced success metrics with monitoring data
            success_metrics = {
                "total_objectives": len(current_progress_report.objectives),
                "completed_objectives": sum(1 for obj in current_progress_report.objectives if obj.status == "completed"),
                "success_rate": current_progress_report.success_rate,
                "total_duration": current_progress_report.duration,
                "tests_pass_rate": current_progress_report.test_results.pass_rate,
                "challenges_encountered": len(current_progress_report.challenges),
                # Enhanced monitoring metrics
                "monitoring_enabled": True,
                "execution_id": session_id,
                "total_steps": execution_report.step_count if execution_report else 0,
                "completed_steps": execution_report.completed_steps if execution_report else 0,
                "total_reviews": execution_report.total_reviews if execution_report else 0,
                "approved_reviews": execution_report.approved_reviews if execution_report else 0,
                "total_retries": execution_report.total_retries if execution_report else 0,
                "test_executions": execution_report.total_tests if execution_report else 0
            }
            
            # Create final summary
            summary = f"""
🎯 Workflow Completed: {input.workflow.value}
📊 Success Rate: {current_progress_report.success_rate:.1f}%
⏱️  Duration: {current_progress_report.duration:.2f}s
👥 Team Members: {len(results)} agents
🧪 Test Pass Rate: {current_progress_report.test_results.pass_rate:.1f}%
⚠️  Challenges: {len(current_progress_report.challenges)}
            """.strip()
            
            result = CodingTeamResult(
                results=results,
                final_summary=summary,
                progress_report=progress_report,
                success_metrics=success_metrics,
                monitoring_report=monitoring_report,
                execution_tracer=tracer
            )
            
            return CodingTeamOutput(result=result)
            
        except Exception as e:
            if current_progress_report:
                current_progress_report.challenges.append(f"Critical workflow error: {str(e)}")
                current_progress_report.end_time = time.time()
                
                error_report = current_progress_report.generate_report()
                error_report += f"\n\n❌ CRITICAL ERROR: {str(e)}"
                
                result = CodingTeamResult(
                    results=[],
                    final_summary=f"Workflow failed: {str(e)}",
                    progress_report=error_report,
                    success_metrics={"error": str(e)},
                    monitoring_report=None,
                    execution_tracer=None
                )
                
                return CodingTeamOutput(result=result)
            
            raise e
    
    async def _analyze_test_results(self, results: List[TeamMemberResult]):
        """Analyze test results from agent outputs"""
        global current_progress_report
        
        if not current_progress_report:
            return
        
        for result in results:
            if result.team_member == TeamMember.test_writer:
                # Count tests written
                output = result.output.lower()
                test_keywords = ["test", "describe", "it(", "def test_", "assert", "expect"]
                tests_written = sum(output.count(keyword) for keyword in test_keywords)
                current_progress_report.test_results.tests_written = max(
                    current_progress_report.test_results.tests_written, 
                    tests_written
                )
            
            elif result.team_member == TeamMember.coder:
                # Analyze for test execution results
                output = result.output
                if "test" in output.lower():
                    # Simple heuristic for test results
                    passed_matches = re.findall(r'(\d+)\s*(?:test|spec)s?\s*passed', output, re.IGNORECASE)
                    failed_matches = re.findall(r'(\d+)\s*(?:test|spec)s?\s*failed', output, re.IGNORECASE)
                    
                    if passed_matches:
                        current_progress_report.test_results.tests_passed = int(passed_matches[0])
                    if failed_matches:
                        current_progress_report.test_results.tests_failed = int(failed_matches[0])
                    
                    current_progress_report.test_results.tests_executed = (
                        current_progress_report.test_results.tests_passed + 
                        current_progress_report.test_results.tests_failed
                    )
    
    async def _calculate_performance_metrics(self, results: List[TeamMemberResult]):
        """Calculate performance metrics"""
        global current_progress_report
        
        if not current_progress_report:
            return
        
        # Agent output analysis
        total_chars = sum(len(result.output) for result in results)
        avg_chars = total_chars / len(results) if results else 0
        
        # Objective timing analysis
        completed_objectives = [obj for obj in current_progress_report.objectives if obj.status == "completed"]
        avg_objective_time = sum(obj.duration for obj in completed_objectives) / len(completed_objectives) if completed_objectives else 0
        
        current_progress_report.performance_metrics.update({
            "total_output_chars": total_chars,
            "avg_output_chars": int(avg_chars),
            "avg_objective_duration": round(avg_objective_time, 2),
            "fastest_objective": min(obj.duration for obj in completed_objectives) if completed_objectives else 0,
            "slowest_objective": max(obj.duration for obj in completed_objectives) if completed_objectives else 0,
            "agents_executed": len(results)
        })

# ============================================================================
# ENHANCED ORCHESTRATOR CONFIGURATION
# ============================================================================

enhanced_orchestrator_config = {
    "model": orchestrator_config["model"],
    "instructions": orchestrator_config["instructions"] 
}

# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

@server.agent(name="orchestrator", metadata={"ui": {"type": "handsoff"}})
async def enhanced_orchestrator(input: list[Message], context: Context) -> AsyncGenerator:
    """Enhanced orchestrator with comprehensive progress tracking"""
    llm = ChatModel.from_name(enhanced_orchestrator_config["model"])

    agent = ReActAgent(
        llm=llm,
        tools=[EnhancedCodingTeamTool(), TestRunnerTool()],
        templates={
            "system": lambda template: template.update(
                defaults=exclude_none({
                    "instructions": enhanced_orchestrator_config["instructions"],
                    "role": "system",
                })
            )
        },
        memory=TokenMemory(llm),
    )

    prompt = reduce(lambda x, y: x + y, input)
    response = await agent.run(str(prompt)).observe(
        lambda emitter: emitter.on(
            "update", lambda data, event: print(f"Enhanced Orchestrator({data.update.key}) 🎯: ", data.update.parsed_value)
        )
    )

    yield MessagePart(content=response.result.text)

def kill_process_on_port(port: int):
    """Kill any process listening on the specified port."""
    try:
        if platform.system() == "Darwin" or platform.system() == "Linux":
            # Find process using lsof
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(["kill", "-9", pid])
                        print(f"✅ Killed process {pid} on port {port}")
                    except Exception as e:
                        print(f"⚠️  Failed to kill process {pid}: {e}")
        elif platform.system() == "Windows":
            # Windows command to find and kill process
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{port}"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        try:
                            subprocess.run(["taskkill", "/F", "/PID", pid])
                            print(f"✅ Killed process {pid} on port {port}")
                        except Exception as e:
                            print(f"⚠️  Failed to kill process {pid}: {e}")
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")

# Run the server
if __name__ == "__main__":
    print("🚀 Starting Enhanced Coding Team Agent System on port 8080...")
    print("✨ Features: Progress Tracking | Parallel Execution | Comprehensive Reporting")
    
    # Kill any existing process on port 8080
    print("🔍 Checking for existing processes on port 8080...")
    kill_process_on_port(8080)
    
    server.run(port=8080)