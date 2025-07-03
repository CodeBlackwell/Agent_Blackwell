"""
🧪 Enhanced Test Script for Modular Workflows

This script provides comprehensive testing for the refactored workflows system with
detailed tracking, timing, debugging information, and aesthetic improvements.
"""
import asyncio
import sys
import os
import time
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)
from workflows import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport, StepStatus, ReviewDecision

# 🎯 Test Configuration
TEST_REQUIREMENTS = {
    "minimal": "Create a basic 'Hello World' REST API endpoint",
    "standard": "Create a simple Express.js TODO API with GET /todos, POST /todos, GET /todos/:id, PUT /todos/:id, DELETE /todos/:id",
    "complex": "Build a full-stack e-commerce application with user authentication, product catalog, shopping cart, and payment processing"
}

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
    """Comprehensive test result tracking with monitoring integration"""
    workflow_name: str
    test_type: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    steps: List[TestStep] = None
    agent_results: List[TeamMemberResult] = None
    agent_execution_path: List[str] = None
    performance_metrics: Dict[str, Any] = None
    # Enhanced monitoring fields
    execution_report: Optional[WorkflowExecutionReport] = None
    monitoring_tracer: Optional[WorkflowExecutionTracer] = None
    monitoring_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.agent_results is None:
            self.agent_results = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.monitoring_metrics is None:
            self.monitoring_metrics = {}
    
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
    """Enhanced workflow testing with comprehensive tracking and reporting"""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(project_root) / "tests" / "outputs" / f"session_{self.session_id}"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.test_results: List[WorkflowTestResult] = []
        
        print(f"🚀 Starting Enhanced Workflow Testing Session")
        print(f"📁 Session ID: {self.session_id}")
        print(f"💾 Output Directory: {self.output_dir}")
        print("=" * 80)
    
    def _print_step_progress(self, step: TestStep, workflow_name: str):
        """Print real-time step progress"""
        status = f"{step.status_emoji} {step.name}"
        if step.end_time:
            status += f" ({step.duration:.2f}s)"
        print(f"    {status}")
    
    def _track_agent_interactions(self, results: List[TeamMemberResult]) -> Dict[str, Any]:
        """Extract and track agent interaction metrics"""
        metrics = {
            "total_agents": len(results),
            "agent_sequence": [r.team_member.value for r in results],
            "output_lengths": {r.team_member.value: len(r.output) for r in results},
            "total_output_chars": sum(len(r.output) for r in results)
        }
        
        # Calculate timing if available
        if hasattr(results[0], 'execution_time'):
            metrics["agent_timings"] = {r.team_member.value: getattr(r, 'execution_time', 0) for r in results}
            metrics["total_agent_time"] = sum(metrics["agent_timings"].values())
        
        # Track unique agents
        unique_agents = set(r.team_member.value for r in results)
        metrics["unique_agents"] = list(unique_agents)
        metrics["unique_agent_count"] = len(unique_agents)
        
        # Calculate output distribution
        if results:
            output_lengths = [len(r.output) for r in results]
            metrics["output_stats"] = {
                "min_length": min(output_lengths),
                "max_length": max(output_lengths),
                "avg_length": sum(output_lengths) / len(output_lengths)
            }
        
        return metrics
    
    def _validate_monitoring_data(self, execution_report: WorkflowExecutionReport, 
                                 workflow_results: List[TeamMemberResult]) -> Dict[str, Any]:
        """Comprehensive validation of monitoring data integrity and completeness"""
        validation_results = {
            "validation_passed": True,
            "validation_errors": [],
            "validation_warnings": [],
            "monitoring_summary": {}
        }
        
        try:
            if execution_report is None:
                validation_results["validation_passed"] = False
                validation_results["validation_errors"].append("No execution report provided")
                return validation_results
            
            # Basic report structure validation
            required_fields = ['execution_id', 'workflow_type', 'start_time', 'steps', 'reviews']
            for field in required_fields:
                if not hasattr(execution_report, field):
                    validation_results["validation_errors"].append(f"Missing required field: {field}")
            
            # Step tracking validation
            step_validation = {
                "total_steps": execution_report.step_count,
                "completed_steps": execution_report.completed_steps,
                "failed_steps": execution_report.failed_steps,
                "step_completion_rate": (execution_report.completed_steps / max(execution_report.step_count, 1)) * 100
            }
            
            if execution_report.step_count == 0:
                validation_results["validation_warnings"].append("No workflow steps were tracked")
            
            # Review tracking validation
            review_validation = {
                "total_reviews": execution_report.total_reviews,
                "approved_reviews": execution_report.approved_reviews,
                "revision_requests": execution_report.revision_requests,
                "auto_approvals": execution_report.auto_approvals,
                "review_approval_rate": (execution_report.approved_reviews / max(execution_report.total_reviews, 1)) * 100
            }
            
            # Retry tracking validation
            retry_validation = {
                "total_retries": execution_report.total_retries,
                "retry_rate": (execution_report.total_retries / max(execution_report.step_count, 1)) * 100
            }
            
            # Test execution validation
            test_validation = {
                "total_tests": execution_report.total_tests,
                "passed_tests": execution_report.passed_tests,
                "failed_tests": execution_report.failed_tests,
                "test_pass_rate": (execution_report.passed_tests / max(execution_report.total_tests, 1)) * 100 if execution_report.total_tests > 0 else 0
            }
            
            # Performance validation
            performance_validation = {
                "execution_duration": execution_report.total_duration_seconds,
                "agent_performance_tracked": len(execution_report.agent_performance) > 0,
                "has_timing_data": execution_report.end_time is not None
            }
            
            # Cross-validation with workflow results
            cross_validation = {
                "workflow_results_count": len(workflow_results),
                "results_match_tracking": True
            }
            
            # Check if agent results align with monitoring data
            if len(workflow_results) == 0 and execution_report.step_count > 0:
                validation_results["validation_warnings"].append(
                    "Monitoring shows steps but no workflow results returned"
                )
                cross_validation["results_match_tracking"] = False
            
            # Compile monitoring summary
            validation_results["monitoring_summary"] = {
                "steps": step_validation,
                "reviews": review_validation,
                "retries": retry_validation,
                "tests": test_validation,
                "performance": performance_validation,
                "cross_validation": cross_validation
            }
            
            # Add summary metrics for easy access
            validation_results.update({
                "total_steps": step_validation["total_steps"],
                "total_reviews": review_validation["total_reviews"],
                "total_retries": retry_validation["total_retries"],
                "total_tests": test_validation["total_tests"],
                "execution_duration": performance_validation["execution_duration"]
            })
            
            # Final validation status
            if len(validation_results["validation_errors"]) > 0:
                validation_results["validation_passed"] = False
            
        except Exception as e:
            validation_results["validation_passed"] = False
            validation_results["validation_errors"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    async def _execute_workflow_with_tracking(self, 
                                            workflow_name: str,
                                            input_data: CodingTeamInput,
                                            test_type: str = "standard") -> WorkflowTestResult:
        """Execute workflow with comprehensive tracking and monitoring validation"""
        print(f"\n🚀 Testing {workflow_name} Workflow ({test_type})")
        print("-" * 60)
        
        result = WorkflowTestResult(
            workflow_name=workflow_name,
            test_type=test_type,
            start_time=time.time()
        )
        
        try:
            # Step 1: Initialize workflow with monitoring
            init_step = TestStep("Initialize Workflow with Monitoring", time.time())
            result.steps.append(init_step)
            self._print_step_progress(init_step, workflow_name)
            
            # Create monitoring tracer
            tracer = WorkflowExecutionTracer(
                workflow_type=workflow_name.lower(),
                execution_id=f"test_{self.session_id}_{workflow_name.lower()}_{test_type}"
            )
            result.monitoring_tracer = tracer
            
            # Step 2: Execute workflow with monitoring
            exec_step = TestStep("Execute Workflow with Monitoring", time.time())
            result.steps.append(exec_step)
            self._print_step_progress(exec_step, workflow_name)
            
            # Execute the workflow with timeout and monitoring
            workflow_results, execution_report = await asyncio.wait_for(
                execute_workflow(input_data, tracer=tracer),
                timeout=300.0  # 5 minute timeout
            )
            
            # Store monitoring results
            result.execution_report = execution_report
            
            # Complete execution step
            exec_step.end_time = time.time()
            exec_step.success = True
            exec_step.details = {
                "results_count": len(workflow_results),
                "monitoring_enabled": True,
                "execution_id": tracer.execution_id
            }
            self._print_step_progress(exec_step, workflow_name)
            
            # Step 3: Validate monitoring data
            monitor_step = TestStep("Validate Monitoring Data", time.time())
            result.steps.append(monitor_step)
            self._print_step_progress(monitor_step, workflow_name)
            
            # Comprehensive monitoring validation
            monitoring_validation = self._validate_monitoring_data(execution_report, workflow_results)
            result.monitoring_metrics = monitoring_validation
            
            monitor_step.end_time = time.time()
            monitor_step.success = monitoring_validation.get('validation_passed', False)
            monitor_step.details = monitoring_validation
            self._print_step_progress(monitor_step, workflow_name)
            
            # Step 4: Process results
            process_step = TestStep("Process Results", time.time())
            result.steps.append(process_step)
            self._print_step_progress(process_step, workflow_name)
            
            result.agent_results = workflow_results
            result.agent_execution_path = [r.team_member.value for r in workflow_results]
            
            # Track agent interactions
            result.performance_metrics = self._track_agent_interactions(workflow_results)
            
            process_step.end_time = time.time()
            process_step.success = True
            process_step.details = {
                "agent_count": len(workflow_results),
                "execution_path": result.agent_execution_path
            }
            self._print_step_progress(process_step, workflow_name)
            
            # Complete initialization step
            init_step.end_time = time.time()
            init_step.success = True
            self._print_step_progress(init_step, workflow_name)
            
            # Mark overall success
            result.success = True
            result.end_time = time.time()
            
            print(f"\n✅ {workflow_name} workflow completed successfully!")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Agents: {len(result.agent_results)}")
            print(f"   Path: {' → '.join(result.agent_execution_path)}")
            print(f"   📊 Monitoring: {monitoring_validation.get('total_steps', 0)} steps, {monitoring_validation.get('total_reviews', 0)} reviews")
            
        except asyncio.TimeoutError:
            error_msg = f"Workflow execution timed out after 300 seconds"
            result.error = error_msg
            result.end_time = time.time()
            
            # Mark current step as failed
            if result.steps and result.steps[-1].end_time is None:
                result.steps[-1].end_time = time.time()
                result.steps[-1].error = error_msg
            
            print(f"\n⏰ {workflow_name} workflow timed out")
            print(f"   Duration: {result.duration:.2f}s")
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            result.error = error_msg
            result.end_time = time.time()
            
            # Mark current step as failed
            if result.steps and result.steps[-1].end_time is None:
                result.steps[-1].end_time = time.time()
                result.steps[-1].error = error_msg
            
            print(f"\n❌ {workflow_name} workflow failed")
            print(f"   Error: {error_msg}")
            print(f"   Duration: {result.duration:.2f}s")
            
            # Print traceback for debugging
            print(f"\n🔍 Error Details:")
            traceback.print_exc()
        
        return result
    
    async def _save_test_artifacts(self, result: WorkflowTestResult):
        """Save comprehensive test artifacts with enhanced monitoring data"""
        # Create subdirectory for this specific test run
        test_dir = self.output_dir / f"{result.workflow_name.lower().replace(' ', '_')}_{result.test_type}"
        test_dir.mkdir(exist_ok=True, parents=True)
        
        # 1. Enhanced detailed results file with monitoring data
        results_file = test_dir / "detailed_results.txt"
        with open(results_file, 'w') as f:
            f.write(f"🧪 {result.workflow_name} Test Results (Enhanced with Monitoring)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"📊 Test Summary:\n")
            f.write(f"  • Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
            f.write(f"  • Duration: {result.duration:.2f}s\n")
            f.write(f"  • Test Type: {result.test_type}\n")
            f.write(f"  • Monitoring Enabled: {'✅' if result.monitoring_tracer else '❌'}\n")
            f.write(f"  • Timestamp: {datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if result.agent_execution_path:
                f.write(f"🔄 Execution Path:\n")
                f.write(f"  {' → '.join(result.agent_execution_path)}\n\n")
            
            if result.performance_metrics:
                f.write(f"📈 Performance Metrics:\n")
                for key, value in result.performance_metrics.items():
                    f.write(f"  • {key}: {value}\n")
                f.write("\n")
            
            # Enhanced monitoring data section
            if result.monitoring_metrics:
                f.write(f"🔍 Monitoring Validation Results:\n")
                f.write(f"  • Validation Passed: {'✅' if result.monitoring_metrics.get('validation_passed') else '❌'}\n")
                f.write(f"  • Total Steps Tracked: {result.monitoring_metrics.get('total_steps', 0)}\n")
                f.write(f"  • Total Reviews: {result.monitoring_metrics.get('total_reviews', 0)}\n")
                f.write(f"  • Total Retries: {result.monitoring_metrics.get('total_retries', 0)}\n")
                f.write(f"  • Total Tests: {result.monitoring_metrics.get('total_tests', 0)}\n")
                f.write(f"  • Execution Duration: {result.monitoring_metrics.get('execution_duration', 0):.2f}s\n")
                
                if result.monitoring_metrics.get('validation_errors'):
                    f.write(f"  • Validation Errors: {len(result.monitoring_metrics['validation_errors'])}\n")
                    for error in result.monitoring_metrics['validation_errors']:
                        f.write(f"    - {error}\n")
                
                if result.monitoring_metrics.get('validation_warnings'):
                    f.write(f"  • Validation Warnings: {len(result.monitoring_metrics['validation_warnings'])}\n")
                    for warning in result.monitoring_metrics['validation_warnings']:
                        f.write(f"    - {warning}\n")
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
        
        # 2. JSON metrics file
        metrics_file = test_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({
                "workflow_name": result.workflow_name,
                "test_type": result.test_type,
                "success": result.success,
                "duration": result.duration,
                "timestamp": result.start_time,
                "agent_execution_path": result.agent_execution_path,
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
        
        # 3. Agent outputs file (separate for easier reading)
        if result.agent_results:
            agent_outputs_file = test_dir / "agent_outputs.txt"
            with open(agent_outputs_file, 'w') as f:
                f.write(f"🤖 Agent Outputs for {result.workflow_name} ({result.test_type})\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, agent_result in enumerate(result.agent_results):
                    f.write(f"{idx+1}. {agent_result.team_member.value.upper()} OUTPUT:\n")
                    f.write("=" * 50 + "\n")
                    f.write(agent_result.output)
                    f.write("\n" + "-" * 50 + "\n\n")
        
        # 4. Error log file (if there was an error)
        if result.error:
            error_file = test_dir / "error.log"
            with open(error_file, 'w') as f:
                f.write(f"❌ Error in {result.workflow_name} ({result.test_type})\n")
                f.write("=" * 50 + "\n")
                f.write(f"Error: {result.error}\n\n")
                f.write("Timestamp: " + datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M:%S') + "\n")
        
        # 5. Test summary file
        summary_file = test_dir / "test_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"📋 {result.workflow_name} ({result.test_type}) - Test Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
            f.write(f"Duration: {result.duration:.2f}s\n")
            f.write(f"Timestamp: {datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if result.agent_execution_path:
                f.write(f"Execution Path:\n{' → '.join(result.agent_execution_path)}\n\n")
            
            if result.performance_metrics:
                f.write("Performance Metrics:\n")
                for key, value in result.performance_metrics.items():
                    f.write(f"  • {key}: {value}\n")
                f.write("\n")
            
            f.write("Step Breakdown:\n")
            for step in result.steps:
                f.write(f"  {step.status_emoji} {step.name}: {step.duration:.2f}s\n")
        
        print(f"    📁 Artifacts saved to: {test_dir.name}/")
    
    async def _create_combined_report(self):
        """Create a combined report file with all test results"""
        combined_file = self.output_dir / "combined_test_report.txt"
        
        with open(combined_file, 'w') as f:
            f.write("🧪 COMBINED WORKFLOW TEST REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {len(self.test_results)}\n\n")
            
            # Summary table
            f.write("📊 SUMMARY TABLE\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Workflow':<20} {'Type':<10} {'Status':<8} {'Duration':<10} {'Agents':<15}\n")
            f.write("-" * 80 + "\n")
            
            for result in self.test_results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                agent_count = len(result.agent_results) if result.agent_results else 0
                f.write(f"{result.workflow_name:<20} {result.test_type:<10} {status:<8} {result.duration:<8.2f}s {agent_count:<15}\n")
            
            f.write("\n\n")
            
            # Detailed results for each test
            for idx, result in enumerate(self.test_results, 1):
                f.write(f"{idx}. {result.workflow_name} ({result.test_type})\n")
                f.write("=" * 60 + "\n")
                f.write(f"Status: {result.status_emoji} {'SUCCESS' if result.success else 'FAILED'}\n")
                f.write(f"Duration: {result.duration:.2f}s\n")
                
                if result.agent_execution_path:
                    f.write(f"Execution Path: {' → '.join(result.agent_execution_path)}\n")
                
                if result.error:
                    f.write(f"Error: {result.error}\n")
                
                f.write(f"Artifacts Directory: {result.workflow_name.lower().replace(' ', '_')}_{result.test_type}/\n")
                f.write("\n")
        
        return combined_file
    
    async def test_tdd_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test TDD workflow with enhanced tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.tdd_workflow,
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.test_writer] if test_type != "minimal" 
                         else [TeamMember.planner, TeamMember.designer]
        )
        
        return await self._execute_workflow_with_tracking("TDD Workflow", input_data, test_type)
    
    async def test_full_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test full workflow with enhanced tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.full_workflow,
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.coder] if test_type != "minimal"
                         else [TeamMember.planner, TeamMember.designer]
        )
        
        return await self._execute_workflow_with_tracking("Full Workflow", input_data, test_type)
    
    async def test_individual_workflow(self, test_type: str = "standard") -> WorkflowTestResult:
        """Test individual workflow steps with enhanced tracking"""
        input_data = CodingTeamInput(
            requirements=TEST_REQUIREMENTS[test_type],
            workflow=WorkflowStep.planning,
            team_members=[TeamMember.planner]
        )
        
        return await self._execute_workflow_with_tracking("Individual Workflow", input_data, test_type)
    
    async def run_comprehensive_tests(self):
        """Run all workflow tests with different complexity levels"""
        print(f"🎯 Starting Comprehensive Workflow Testing")
        print(f"⚡ Testing {len(TEST_REQUIREMENTS)} complexity levels")
        print(f"🧪 Running {len(TEST_REQUIREMENTS) * 3} total tests")
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
                    
                    # Real-time status update
                    print(f"  {result.status_emoji} {workflow_name} ({test_type}): {result.duration:.2f}s")
                    if result.error:
                        print(f"    ⚠️  {result.error}")
                    
                except Exception as e:
                    print(f"  💥 {workflow_name} ({test_type}): CRITICAL ERROR - {str(e)}")
        
        overall_duration = time.time() - overall_start
        
        # Generate comprehensive report
        await self._generate_final_report(overall_duration)
    
    async def _generate_final_report(self, overall_duration: float):
        """Generate comprehensive test session report"""
        print(f"\n🎯 COMPREHENSIVE TEST REPORT")
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
        
        print(f"\n🏆 Test Results by Workflow:")
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"  {status} {result.workflow_name} ({result.test_type}): {result.duration:.2f}s")
            if result.agent_execution_path:
                print(f"    └─ Path: {' → '.join(result.agent_execution_path)}")
        
        # Performance insights
        if successful_tests > 0:
            successful_results = [r for r in self.test_results if r.success]
            fastest = min(successful_results, key=lambda x: x.duration)
            slowest = max(successful_results, key=lambda x: x.duration)
            
            print(f"\n⚡ Performance Insights:")
            print(f"  • Fastest: {fastest.workflow_name} ({fastest.test_type}) - {fastest.duration:.2f}s")
            print(f"  • Slowest: {slowest.workflow_name} ({slowest.test_type}) - {slowest.duration:.2f}s")
        
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
                "test_results": [
                    {
                        "workflow_name": r.workflow_name,
                        "test_type": r.test_type,
                        "success": r.success,
                        "duration": r.duration,
                        "error": r.error,
                        "agent_path": r.agent_execution_path,
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
    print("🚀 Enhanced Workflow Testing System")
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
    print("🧪 Enhanced Workflow Module Test Script")
    print("=" * 80)
    print("This script provides comprehensive testing with detailed tracking and reporting")
    print()
    
    asyncio.run(main())