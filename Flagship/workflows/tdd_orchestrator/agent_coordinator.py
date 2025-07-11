"""Agent Coordinator - manages agent invocations with proper context"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path

from .models import TDDPhase, AgentContext, PhaseResult


class AgentCoordinator:
    """Coordinates agent invocations for TDD workflow"""
    
    def __init__(self, run_team_member_func: Optional[Callable] = None):
        """
        Initialize coordinator
        Args:
            run_team_member_func: Function to run team members (for parent system integration)
                                 If None, will use local Flagship agents directly
        """
        self.run_team_member_func = run_team_member_func
        self.invocation_history: List[Dict[str, Any]] = []
        
        # Map phases to agents
        self.phase_agent_map = {
            TDDPhase.RED: "test_writer",
            TDDPhase.YELLOW: "coder",
            TDDPhase.GREEN: "executor"
        }
        
        # If no external function provided, we'll use local agents
        if not self.run_team_member_func:
            self._setup_local_agents()
    
    def _setup_local_agents(self):
        """Setup references to local Flagship agents"""
        # Import local agents
        import sys
        flagship_path = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(flagship_path))
        
        from agents.test_writer_flagship import TestWriterFlagship
        from agents.coder_flagship import CoderFlagship
        from agents.test_runner_flagship import TestRunnerFlagship
        
        self.local_agents = {
            "test_writer": TestWriterFlagship(),
            "coder": CoderFlagship(),
            "executor": TestRunnerFlagship()
        }
    
    async def invoke_agent(self, agent_name: str, context: AgentContext) -> Any:
        """
        Invoke an agent with proper context
        Returns agent result
        """
        start_time = datetime.now()
        
        # Build agent-specific context
        agent_input = self._build_agent_context(agent_name, context)
        
        # Record invocation
        invocation = {
            "agent": agent_name,
            "phase": context.phase.value,
            "feature_id": context.feature_id,
            "attempt": context.attempt_number,
            "timestamp": start_time.isoformat(),
            "input": agent_input
        }
        
        try:
            if self.run_team_member_func:
                # Use external function (parent system integration)
                result = await self.run_team_member_func(agent_name, agent_input)
            else:
                # Use local agents
                result = await self._invoke_local_agent(agent_name, agent_input, context)
            
            # Record success
            invocation["success"] = True
            invocation["output"] = str(result)
            invocation["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            # Record failure
            invocation["success"] = False
            invocation["error"] = str(e)
            invocation["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            raise
        
        finally:
            self.invocation_history.append(invocation)
    
    async def _invoke_local_agent(self, agent_name: str, agent_input: Dict, context: AgentContext):
        """Invoke a local Flagship agent"""
        if agent_name not in self.local_agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.local_agents[agent_name]
        
        # Handle different agent types
        if agent_name == "test_writer":
            # Extract output from async generator
            output = ""
            async for chunk in agent.write_tests(
                context.feature_description,
                context.phase_context
            ):
                output += chunk
            
            # Get the actual test code
            test_code = agent.get_test_code()
            
            # Create result object similar to parent system
            from models.parent_compatibility import TeamMemberResult, TeamMember
            return TeamMemberResult(
                team_member=TeamMember.test_writer,
                output=test_code
            )
            
        elif agent_name == "coder":
            # Get test code and results from context
            test_code = context.phase_context.get("tests", "")
            test_results = context.phase_context.get("test_results", [])
            
            # Extract output from async generator
            output = ""
            async for chunk in agent.write_code(test_code, test_results):
                output += chunk
            
            # Get the actual implementation code
            impl_code = agent.get_implementation_code()
            
            from models.parent_compatibility import TeamMemberResult, TeamMember
            return TeamMemberResult(
                team_member=TeamMember.coder,
                output=impl_code
            )
            
        elif agent_name == "executor":
            # Get test and implementation code
            test_code = context.phase_context.get("tests", "")
            impl_code = context.phase_context.get("implementation", "")
            
            # Run tests
            output = ""
            async for chunk in agent.run_tests(test_code, impl_code):
                output += chunk
            
            # Get test results
            test_results = agent.get_test_results()
            all_passed = agent.all_tests_passed()
            
            # Format output
            result_output = f"{len([t for t in test_results if t.status.name == 'PASSED'])} passed"
            if not all_passed:
                failed_count = len([t for t in test_results if t.status.name != 'PASSED'])
                result_output += f", {failed_count} failed"
            
            from models.parent_compatibility import TeamMemberResult, TeamMember
            return TeamMemberResult(
                team_member=TeamMember.executor,
                output=result_output
            )
    
    def _build_agent_context(self, agent_name: str, context: AgentContext) -> Dict[str, Any]:
        """Build agent-specific context from generic context"""
        base_context = {
            "requirements": context.feature_description,
            "feature_id": context.feature_id,
            "phase": context.phase.value,
            "attempt_number": context.attempt_number
        }
        
        # Add agent-specific context
        if agent_name == "test_writer":
            return self._build_test_writer_context(context, base_context)
        elif agent_name == "coder":
            return self._build_coder_context(context, base_context)
        elif agent_name == "executor":
            return self._build_executor_context(context, base_context)
        elif agent_name == "reviewer":
            return self._build_reviewer_context(context, base_context)
        else:
            return base_context
    
    def _build_test_writer_context(self, context: AgentContext, base: Dict) -> Dict[str, Any]:
        """Build context for test writer agent"""
        test_context = base.copy()
        test_context.update({
            "test_strategy": "red_phase_failing_tests",
            "test_framework": context.global_context.get("test_framework", "pytest"),
            "previous_attempts": context.previous_attempts
        })
        
        # Add any existing tests if retrying
        if context.phase_context.get("existing_tests"):
            test_context["existing_tests"] = context.phase_context["existing_tests"]
            test_context["revision_reason"] = context.phase_context.get("error", "Tests need revision")
        
        return test_context
    
    def _build_coder_context(self, context: AgentContext, base: Dict) -> Dict[str, Any]:
        """Build context for coder agent"""
        coder_context = base.copy()
        coder_context.update({
            "tests_to_pass": context.phase_context.get("tests", ""),
            "test_results": context.phase_context.get("test_results", []),
            "implementation_phase": "YELLOW",  # Minimal implementation
            "previous_attempts": context.previous_attempts
        })
        
        # Add existing implementation if retrying
        if context.phase_context.get("existing_implementation"):
            coder_context["existing_implementation"] = context.phase_context["existing_implementation"]
            coder_context["revision_reason"] = context.phase_context.get("error", "Implementation needs revision")
        
        # Add specific failure info
        if context.phase_context.get("failed_tests"):
            coder_context["failed_tests"] = context.phase_context["failed_tests"]
        
        return coder_context
    
    def _build_executor_context(self, context: AgentContext, base: Dict) -> Dict[str, Any]:
        """Build context for executor agent"""
        executor_context = base.copy()
        executor_context.update({
            "execution_type": "test_execution",
            "test_code": context.phase_context.get("tests", ""),
            "implementation_code": context.phase_context.get("implementation", ""),
            "test_framework": context.global_context.get("test_framework", "pytest"),
            "phase": context.phase.value,
            "expect_failure": context.phase == TDDPhase.RED  # Tests should fail in RED phase
        })
        
        return executor_context
    
    def _build_reviewer_context(self, context: AgentContext, base: Dict) -> Dict[str, Any]:
        """Build context for reviewer agent"""
        reviewer_context = base.copy()
        reviewer_context.update({
            "review_type": f"tdd_phase_{context.phase.value.lower()}",
            "artifacts": {
                "tests": context.phase_context.get("tests", ""),
                "implementation": context.phase_context.get("implementation", ""),
                "test_results": context.phase_context.get("test_results", {})
            },
            "review_criteria": self._get_review_criteria(context.phase)
        })
        
        return reviewer_context
    
    def _get_review_criteria(self, phase: TDDPhase) -> List[str]:
        """Get review criteria for a specific phase"""
        criteria_map = {
            TDDPhase.RED: [
                "Tests are well-structured and clear",
                "Tests cover the requirements",
                "Tests follow best practices",
                "Tests should fail (no implementation yet)"
            ],
            TDDPhase.YELLOW: [
                "Implementation is minimal but correct",
                "Code follows best practices",
                "No over-engineering",
                "All tests should pass"
            ],
            TDDPhase.GREEN: [
                "All tests pass",
                "Code is clean and maintainable",
                "No unnecessary complexity",
                "Ready for next iteration or completion"
            ]
        }
        
        return criteria_map.get(phase, [])
    
    def get_agent_for_phase(self, phase: TDDPhase) -> str:
        """Get the appropriate agent for a TDD phase"""
        return self.phase_agent_map.get(phase, "reviewer")
    
    def get_invocation_summary(self) -> Dict[str, Any]:
        """Get summary of all agent invocations"""
        summary = {
            "total_invocations": len(self.invocation_history),
            "by_agent": {},
            "by_phase": {},
            "success_rate": 0.0,
            "total_duration_seconds": 0.0
        }
        
        if not self.invocation_history:
            return summary
        
        # Calculate statistics
        successful = 0
        for inv in self.invocation_history:
            agent = inv["agent"]
            phase = inv["phase"]
            
            # Count by agent
            if agent not in summary["by_agent"]:
                summary["by_agent"][agent] = {"count": 0, "success": 0, "duration": 0.0}
            summary["by_agent"][agent]["count"] += 1
            
            # Count by phase
            if phase not in summary["by_phase"]:
                summary["by_phase"][phase] = {"count": 0, "success": 0, "duration": 0.0}
            summary["by_phase"][phase]["count"] += 1
            
            # Track success and duration
            if inv.get("success", False):
                successful += 1
                summary["by_agent"][agent]["success"] += 1
                summary["by_phase"][phase]["success"] += 1
            
            duration = inv.get("duration_seconds", 0.0)
            summary["total_duration_seconds"] += duration
            summary["by_agent"][agent]["duration"] += duration
            summary["by_phase"][phase]["duration"] += duration
        
        summary["success_rate"] = successful / len(self.invocation_history)
        
        return summary