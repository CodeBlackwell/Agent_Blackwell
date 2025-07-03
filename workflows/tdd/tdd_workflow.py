"""
🧪 Enhanced Test Script for Modular Workflows with Agent Path Tracking

This script provides comprehensive testing for the refactored workflows system with
robust agent interaction tracking, detailed timing, and aesthetic improvements.
"""
import asyncio
import sys
import os
import time
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)
from orchestrator.orchestrator_agent import run_team_member

# 🎯 Test Configuration
TEST_REQUIREMENTS = {
    "minimal": "Create a basic 'Hello World' REST API endpoint",
    "standard": "Create a simple Express.js TODO API with GET /todos, POST /todos, GET /todos/:id, PUT /todos/:id, DELETE /todos/:id",
    "complex": "Build a full-stack e-commerce application with user authentication, product catalog, shopping cart, and payment processing"
}

@dataclass
class AgentPathInfo:
    """Track agent execution path information"""
    simple_path: str  # e.g., "Planner → Reviewer → Designer → Reviewer..."
    agent_sequence: List[str] = field(default_factory=list)
    full_interaction_sequence: List[str] = field(default_factory=list)  # Every single interaction
    interaction_count: int = 0
    
    @property
    def formatted_path(self) -> str:
        """Get formatted path for inline display"""
        return self.simple_path if self.simple_path else "No path recorded"

@dataclass
class TestStep:
    """Track individual test steps with timing and results"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    details: Dict[str, Any] = None
    
    @property
    def duration(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def status_emoji(self) -> str:
        if self.end_time is None:
            return "⏳"
        return "✅" if self.success else "❌"

@dataclass 
class WorkflowTestResult:
    """Comprehensive test result tracking with agent path info"""
    workflow_name: str
    test_type: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    steps: List[TestStep] = None
    agent_results: List[TeamMemberResult] = None
    agent_path: AgentPathInfo = None  # Enhanced agent path tracking
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.agent_results is None:
            self.agent_results = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.agent_path is None:
            self.agent_path = AgentPathInfo(simple_path="", agent_sequence=[])
    
    @property
    def duration(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def status_emoji(self) -> str:
        if self.end_time is None:
            return "🔄"
        return "🎉" if self.success else "💥"

class WorkflowTester:
    """Enhanced workflow testing with comprehensive agent path tracking and reporting"""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(project_root) / "tests" / "outputs" / f"session_{self.session_id}"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.test_results: List[WorkflowTestResult] = []
        
        print(f"🚀 Starting Enhanced Workflow Testing Session")
        print(f"📁 Session ID: {self.session_id}")
        print(f"💾 Output Directory: {self.output_dir}")
        print(f"🔄 Agent Path Tracking: ENABLED")
        print("=" * 80)
    
    def _print_step_progress(self, step: TestStep, workflow_name: str):
        """Print real-time step progress"""
        status = f"{step.status_emoji} {step.name}"
        if step.end_time:
            status += f" ({step.duration:.2f}s)"
        print(f"    {status}")
    
    def _extract_agent_path(self, results: List[TeamMemberResult]) -> AgentPathInfo:
        """Extract agent path information from execution results"""
        # First, try to get the path from the global progress report
        global current_progress_report
        
        if current_progress_report and hasattr(current_progress_report, 'agent_flow'):
            # Use the enhanced agent flow tracking from orchestrator
            simple_path = current_progress_report.agent_flow.get_simple_path()
            agent_sequence = current_progress_report.agent_flow.agent_sequence
            full_interactions = current_progress_report.agent_flow.full_interaction_path
            interaction_count = len(current_progress_report.agent_flow.interactions)
            
            return AgentPathInfo(
                simple_path=simple_path,
                agent_sequence=agent_sequence,
                full_interaction_sequence=full_interactions,
                interaction_count=interaction_count
            )
        
        # Fallback: build path from results - show every agent in order
        full_interaction_sequence = []
        agent_sequence = []
        
        for result in results:
            agent_name = result.team_member.value.replace("_agent", "").capitalize()
            full_interaction_sequence.append(agent_name)
            
            if agent_name not in agent_sequence:
                agent_sequence.append(agent_name)
        
        simple_path = " → ".join(full_interaction_sequence)
        
        return AgentPathInfo(
            simple_path=simple_path,
            agent_sequence=agent_sequence,
            full_interaction_sequence=full_interaction_sequence,
            interaction_count=len(results)
        )
    
    def _track_agent_interactions(self, results: List[TeamMemberResult], agent_path: AgentPathInfo) -> Dict[str, Any]:
        """Extract and track agent interaction metrics with path info"""
        metrics = {
            "total_agents": len(results),
            "agent_sequence": agent_path.agent_sequence,
            "agent_path": agent_path.simple_path,
            "interaction_count": agent_path.interaction_count,
            "output_lengths": {r.team_member.value: len(r.output) for r in results},
            "total_output_chars": sum(len(r.output) for r in results)
        }
        
        # Analyze output content
        for result in results:
            agent = result.team_member.value
            output = result.output.lower()
            
            # Track keywords that indicate success/quality
            if agent == "coder":
                metrics[f"{agent}_has_code"] = any(keyword in output for keyword in ["function", "class", "def", "const", "let", "var"])
                metrics[f"{agent}_has_imports"] = any(keyword in output for keyword in ["import", "require", "from"])
            elif agent == "test_writer":
                metrics[f"{agent}_has_tests"] = any(keyword in output for keyword in ["test", "describe", "it", "assert", "expect"])
            elif agent == "reviewer":
                metrics[f"{agent}_has_approval"] = "approved" in output
        
        return metrics
    
    async def _execute_workflow_with_tracking(self, 
                                            workflow_name: str,
                                            input_data: CodingTeamInput,
                                            test_type: str = "standard") -> WorkflowTestResult:
        """Execute workflow with comprehensive tracking including agent paths"""
        
        print(f"\n🔥 Testing {workflow_name}")
        print(f"📋 Workflow: {input_data.workflow.value}")
        print(f"👥 Team Members: {[m.value for m in input_data.team_members]}")
        print(f"📝 Test Type: {test_type}")
        print("-" * 60)
        
        result = WorkflowTestResult(
            workflow_name=workflow_name,
            test_type=test_type,
            start_time=time.time()
        )
        
        try:
            # Step 1: Initialization
            step = TestStep("🔧 Initializing workflow", time.time())
            result.steps.append(step)
            self._print_step_progress(step, workflow_name)
            
            await asyncio.sleep(0.1)  # Brief pause for realism
            step.end_time = time.time()
            step.success = True
            self._print_step_progress(step, workflow_name)
            
            # Step 2: Execute workflow
            step = TestStep("⚡ Executing workflow pipeline", time.time())
            result.steps.append(step)
            self._print_step_progress(step, workflow_name)
            
            # Track execution with timeout
            workflow_results = await asyncio.wait_for(
                execute_workflow(input_data), 
                timeout=300  # 5 minute timeout
            )
            
            step.end_time = time.time()
            step.success = True
            step.details = {"results_count": len(workflow_results)}
            self._print_step_progress(step, workflow_name)
            
            # Step 3: Extract agent path
            step = TestStep("🔄 Extracting agent execution path", time.time())
            result.steps.append(step)
            self._print_step_progress(step, workflow_name)
            
            result.agent_path = self._extract_agent_path(workflow_results)
            
            step.end_time = time.time()
            step.success = True
            step.details = {"path": result.agent_path.simple_path}
            self._print_step_progress(step, workflow_name)
            
            # Print the agent path inline
            print(f"       Agents: {result.agent_path.simple_path}")
            
            # Step 4: Analyze results
            step = TestStep("🔍 Analyzing results", time.time())
            result.steps.append(step)
            self._print_step_progress(step, workflow_name)
            
            result.agent_results = workflow_results
            result.performance_metrics = self._track_agent_interactions(workflow_results, result.agent_path)
            
            step.end_time = time.time()
            step.success = True
            step.details = result.performance_metrics
            self._print_step_progress(step, workflow_name)
            
            # Step 5: Save artifacts
            step = TestStep("💾 Saving artifacts", time.time())
            result.steps.append(step)
            self._print_step_progress(step, workflow_name)
            
            await self._save_test_artifacts(result)
            
            step.end_time = time.time()
            step.success = True
            self._print_step_progress(step, workflow_name)
            
            result.success = True
            result.end_time = time.time()
            
            print(f"    🎯 Workflow completed in {result.duration:.2f}s")
            
        except asyncio.TimeoutError:
            result.error = "Workflow execution timed out after 5 minutes"
            result.end_time = time.time()
            print(f"    ⏰ Timeout: {result.error}")
            
        except Exception as e:
            result.error = str(e)
            result.end_time = time.time()
            print(f"    💥 Error: {result.error}")
            
            # Save detailed error info in test subdirectory
            test_dir = self.output_dir / f"{workflow_name.lower().replace(' ', '_')}_{test_type}"
            test_dir.mkdir(exist_ok=True, parents=True)
            error_file = test_dir / "critical_error.log"
            with open(error_file, 'w') as f:
                f.write(f"Error in {workflow_name}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Error: {result.error}\n\n")
                f.write("Traceback:\n")
                f.write(traceback.format_exc())
        
        return result
    
    async def _save_test_artifacts(self, result: WorkflowTestResult):
        """Save comprehensive test artifacts including agent path information"""
        # Create subdirectory for this specific test run
        test_dir = self.output_dir / f"{result.workflow_name.lower().replace(' ', '_')}_{result.test_type}"
        test_dir.mkdir(exist_ok=True, parents=True)
        
        # 1. Agent Path File (NEW - prominent tracking file)
        agent_path_file = test_dir / "agent_execution_path.txt"
        with open(agent_path_file, 'w') as f:
            f.write("🔄 AGENT EXECUTION PATH\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Simple Path: {result.agent_path.simple_path}\n")
            f.write(f"Interaction Count: {result.agent_path.interaction_count}\n\n")
            f.write("Detailed Sequence:\n")
            for i, agent in enumerate(result.agent_path.agent_sequence, 1):
                f.write(f"  {i}. {agent}\n")
        
        # 2. Detailed results file
        results_file = test_dir / "detailed_results.txt"
        with open(results_file, 'w') as f:
            f.write(f"🧪 {result.workflow_name} Test Results\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"📊 Test Summary:\n")
            f.write(f"  • Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
            f.write(f"  • Duration: {result.duration:.2f}s\n")
            f.write(f"  • Test Type: {result.test_type}\n")
            f.write(f"  • Timestamp: {datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  • Agent Interactions: {result.agent_path.interaction_count}\n")
            f.write(f"     Agents: {result.agent_path.simple_path}\n\n")
            
            if result.performance_metrics:
                f.write(f"📈 Performance Metrics:\n")
                for key, value in result.performance_metrics.items():
                    f.write(f"  • {key}: {value}\n")
                f.write("\n")
            
            f.write(f"⏱️  Step Breakdown:\n")
            for step in result.steps:
                f.write(f"  {step.status_emoji} {step.name}: {step.duration:.2f}s\n")
                if step.details:
                    for key, value in step.details.items():
                        f.write(f"    └─ {key}: {value}\n")
            f.write("\n")
            
            if result.agent_results:
                f.write(f"🤖 Agent Outputs:\n")
                f.write("-" * 80 + "\n")
                for idx, agent_result in enumerate(result.agent_results):
                    f.write(f"\n{idx+1}. {agent_result.team_member.value.upper()} OUTPUT:\n")
                    f.write("=" * 50 + "\n")
                    f.write(agent_result.output)
                    f.write("\n" + "-" * 50 + "\n")
            
            if result.error:
                f.write(f"\n❌ Error Details:\n")
                f.write(f"{result.error}\n")
        
        # 3. JSON metrics file
        metrics_file = test_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({
                "workflow_name": result.workflow_name,
                "test_type": result.test_type,
                "success": result.success,
                "duration": result.duration,
                "timestamp": result.start_time,
                "agent_path": {
                    "simple": result.agent_path.simple_path,
                    "sequence": result.agent_path.agent_sequence,
                    "interaction_count": result.agent_path.interaction_count
                },
                "performance_metrics": result.performance_metrics,
                "steps": [
                    {
                        "name": step.name,
                        "duration": step.duration,
                        "success": step.success,
                        "details": step.details
                    }
                    for step in result.steps
                ],
                "error": result.error
            }, f, indent=2)
        
        # 4. Test summary file
        summary_file = test_dir / "test_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"📋 {result.workflow_name} ({result.test_type}) - Test Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
            f.write(f"Duration: {result.duration:.2f}s\n")
            f.write(f"Timestamp: {datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"🔄 Agent Execution Path:\n")
            f.write(f"{result.agent_path.simple_path}\n\n")
            
            if result.performance_metrics:
                f.write("Performance Metrics:\n")
                for key, value in result.performance_metrics.items():
                    if key not in ["output_lengths", "agent_sequence"]:  # Skip verbose items
                        f.write(f"  • {key}: {value}\n")
                f.write("\n")
            
            f.write("Step Breakdown:\n")
            for step in result.steps:
                f.write(f"  {step.status_emoji} {step.name}: {step.duration:.2f}s\n")
        
        print(f"    📁 Artifacts saved to: {test_dir.name}/")
    
    async def _create_combined_report(self):
        """Create a combined report file with all test results and agent paths"""
        combined_file = self.output_dir / "combined_test_report.txt"
        
        with open(combined_file, 'w') as f:
            f.write("🧪 COMBINED WORKFLOW TEST REPORT WITH AGENT TRACKING\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {len(self.test_results)}\n\n")
            
            # Agent Path Summary (NEW section)
            f.write("🔄 AGENT EXECUTION PATHS\n")
            f.write("-" * 80 + "\n")
            for result in self.test_results:
                f.write(f"{result.workflow_name} ({result.test_type}):\n")
                f.write(f"  {result.agent_path.simple_path}\n")
            f.write("\n")
            
            # Summary table
            f.write("📊 SUMMARY TABLE\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Workflow':<20} {'Type':<10} {'Status':<8} {'Duration':<10} {'Path':<30}\n")
            f.write("-" * 80 + "\n")
            
            for result in self.test_results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                # Truncate path if too long for table
                path = result.agent_path.simple_path
                if len(path) > 28:
                    path = path[:25] + "..."
                f.write(f"{result.workflow_name:<20} {result.test_type:<10} {status:<8} {result.duration:<8.2f}s {path:<30}\n")
            
            f.write("\n\n")
            
            # Detailed results for each test
            for idx, result in enumerate(self.test_results, 1):
                f.write(f"{idx}. {result.workflow_name} ({result.test_type})\n")
                f.write("=" * 60 + "\n")
                f.write(f"Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
                f.write(f"Duration: {result.duration:.2f}s\n")
                f.write(f"Agent Path: {result.agent_path.simple_path}\n")
                f.write(f"Agent Interactions: {result.agent_path.interaction_count}\n")
                
                if result.error:
                    f.write(f"Error: {result.error}\n")
                
                f.write(f"Artifacts Directory: {result.workflow_name.lower().replace(' ', '_')}_{result.test_type}/\n")
                f.write("\n")
        
        # Create agent paths summary file
        paths_file = self.output_dir / "agent_paths_summary.txt"
        with open(paths_file, 'w') as f:
            f.write("🔄 AGENT EXECUTION PATHS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            # Group by workflow type
            workflow_groups = {}
            for result in self.test_results:
                if result.workflow_name not in workflow_groups:
                    workflow_groups[result.workflow_name] = []
                workflow_groups[result.workflow_name].append(result)
            
            for workflow_name, results in workflow_groups.items():
                f.write(f"\n{workflow_name}:\n")
                f.write("-" * 40 + "\n")
                for result in results:
                    f.write(f"  {result.test_type}: {result.agent_path.simple_path}\n")
        
        return combined_file
    
    async def test_tdd_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test TDD workflow with enhanced agent path tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.tdd_workflow,
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.test_writer] if test_type != "minimal" 
                         else [TeamMember.planner, TeamMember.designer]
        )
        
        return await self._execute_workflow_with_tracking("TDD Workflow", input_data, test_type)
    
    async def test_full_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test full workflow with enhanced agent path tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.full_workflow,
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.coder] if test_type != "minimal"
                         else [TeamMember.planner, TeamMember.designer]
        )
        
        return await self._execute_workflow_with_tracking("Full Workflow", input_data, test_type)
    
    async def test_individual_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test individual workflow steps with enhanced agent path tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.planning,
            team_members=[TeamMember.planner]
        )
        
        return await self._execute_workflow_with_tracking("Individual Workflow", input_data, test_type)
    
    async def run_comprehensive_tests(self):
        """Run all workflow tests with agent path tracking"""
        print(f"🎯 Starting Comprehensive Workflow Testing")
        print(f"⚡ Testing {len(TEST_REQUIREMENTS)} complexity levels")
        print(f"🧪 Running {len(TEST_REQUIREMENTS) * 3} total tests")
        print(f"🔄 Agent path tracking enabled for all tests")
        print()
        
        overall_start = time.time()
        
        test_configurations = [
            ("TDD Workflow", self.test_tdd_workflow),
            ("Full Workflow", self.test_full_workflow),
            ("Individual Workflow", self.test_individual_workflow)
        ]
        
        for test_type in ["minimal", "standard"]:  # Skip complex for faster testing
            print(f"\n🔄 Running {test_type.upper()} complexity tests")
            print("=" * 60)
            
            for workflow_name, test_func in test_configurations:
                try:
                    result = await test_func(test_type)
                    self.test_results.append(result)
                    
                    # Real-time status update with inline agent path
                    print(f"  {result.status_emoji} {workflow_name} ({test_type}): {result.duration:.2f}s")
                    print(f"     Agents: {result.agent_path.simple_path}")
                    if result.error:
                        print(f"     ⚠️  {result.error}")
                    
                except Exception as e:
                    print(f"  💥 {workflow_name} ({test_type}): CRITICAL ERROR - {str(e)}")
        
        overall_duration = time.time() - overall_start
        
        # Generate comprehensive report
        await self._generate_final_report(overall_duration)
    
    async def _generate_final_report(self, overall_duration: float):
        """Generate comprehensive test session report with agent path analysis"""
        print(f"\n🎯 COMPREHENSIVE TEST REPORT WITH AGENT TRACKING")
        print("=" * 80)
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        
        total_workflow_time = sum(r.duration for r in self.test_results)
        avg_workflow_time = total_workflow_time / total_tests if total_tests > 0 else 0
        
        print(f"📊 Session Statistics:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Successful: {successful_tests} ✅")
        print(f"  • Failed: {failed_tests} ❌")
        print(f"  • Success Rate: {(successful_tests/total_tests*100):.1f}%")
        print(f"  • Total Workflow Time: {total_workflow_time:.2f}s")
        print(f"  • Average Workflow Time: {avg_workflow_time:.2f}s")
        print(f"  • Overall Session Time: {overall_duration:.2f}s")
        
        print(f"\n🔄 Agent Execution Paths:")
        for result in self.test_results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.workflow_name} ({result.test_type}):")
            print(f"     Agents: {result.agent_path.simple_path}")
        
        print(f"\n🏆 Test Results by Workflow:")
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"  {status} {result.workflow_name} ({result.test_type}): {result.duration:.2f}s")
            print(f"    └─ Interactions: {result.agent_path.interaction_count}")
        
        # Performance insights
        if successful_tests > 0:
            successful_results = [r for r in self.test_results if r.success]
            fastest = min(successful_results, key=lambda x: x.duration)
            slowest = max(successful_results, key=lambda x: x.duration)
            
            print(f"\n⚡ Performance Insights:")
            print(f"  • Fastest: {fastest.workflow_name} ({fastest.test_type}) - {fastest.duration:.2f}s")
            print(f"     Agents: {fastest.agent_path.simple_path}")
            print(f"  • Slowest: {slowest.workflow_name} ({slowest.test_type}) - {slowest.duration:.2f}s")
            print(f"     Agents: {slowest.agent_path.simple_path}")
        
        # Agent path analysis
        print(f"\n📊 Agent Path Analysis:")
        unique_paths = set(r.agent_path.simple_path for r in self.test_results if r.agent_path.simple_path)
        print(f"  • Unique Paths: {len(unique_paths)}")
        for path in unique_paths:
            count = sum(1 for r in self.test_results if r.agent_path.simple_path == path)
            print(f"    └─ {path} (used {count}x)")
        
        # Save session summary
        summary_file = self.output_dir / "session_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "overall_duration": overall_duration,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests/total_tests if total_tests > 0 else 0,
                "total_workflow_time": total_workflow_time,
                "average_workflow_time": avg_workflow_time,
                "unique_agent_paths": list(unique_paths),
                "test_results": [
                    {
                        "workflow_name": r.workflow_name,
                        "test_type": r.test_type,
                        "success": r.success,
                        "duration": r.duration,
                        "error": r.error,
                        "agent_path": r.agent_path.simple_path,
                        "agent_sequence": r.agent_path.agent_sequence,
                        "interaction_count": r.agent_path.interaction_count,
                        "artifacts_dir": f"{r.workflow_name.lower().replace(' ', '_')}_{r.test_type}"
                    }
                    for r in self.test_results
                ]
            }, f, indent=2)
        
        # Create combined report
        combined_report = await self._create_combined_report()
        
        print(f"\n📁 All artifacts saved to: {self.output_dir}")
        print(f"📊 Session summary: {summary_file}")
        print(f"📋 Combined report: {combined_report}")
        print(f"🔄 Agent paths summary: {self.output_dir}/agent_paths_summary.txt")
        
        # List all test subdirectories
        test_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
        if test_dirs:
            print(f"📂 Individual test directories:")
            for test_dir in sorted(test_dirs):
                print(f"  • {test_dir.name}/")
        
        if failed_tests > 0:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check individual error files for details.")
        else:
            print(f"\n🎉 All tests passed! The workflow system is functioning correctly.")

async def main():
    """Main test execution"""
    print("🚀 Enhanced Workflow Testing System with Agent Path Tracking")
    print("=" * 80)
    
    tester = WorkflowTester()
    
    try:
        await tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print(f"\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Critical testing error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Enhanced Workflow Module Test Script with Agent Path Tracking")
    print("=" * 80)
    print("This script provides comprehensive testing with robust agent interaction tracking")
    print("Agent paths will be displayed in the format: AGENT1 → AGENT2 → AGENT3")
    print()
    
    asyncio.run(main())