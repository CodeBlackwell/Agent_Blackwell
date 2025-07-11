"""Flagship Orchestrator - Manages RED-YELLOW-GREEN TDD phases"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from agents.test_writer_flagship import TestWriterFlagship
from agents.coder_flagship import CoderFlagship
from agents.test_runner_flagship import TestRunnerFlagship
from models.flagship_models import (
    TDDPhase, TDDWorkflowState, PhaseTransition, PhaseResult,
    TDDWorkflowConfig, TestStatus, TestResult, AgentType
)
from models.execution_tracer import ExecutionTracer, EventType
from utils.enhanced_file_manager import EnhancedFileManager


class FlagshipOrchestrator:
    """Orchestrates the TDD workflow through RED-YELLOW-GREEN phases"""
    
    def __init__(self, config: TDDWorkflowConfig = None, session_id: str = None, project_root: Path = None):
        self.config = config or TDDWorkflowConfig()
        self.session_id = session_id or f"tdd_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.tracer = ExecutionTracer(self.session_id)
        
        # Initialize file manager
        if project_root is None:
            project_root = Path(__file__).parent
        self.file_manager = EnhancedFileManager(self.session_id, project_root)
        
        # Initialize agents with tracer and file manager
        self.test_writer = TestWriterFlagship(file_manager=self.file_manager)
        self.coder = CoderFlagship(file_manager=self.file_manager)
        self.test_runner = TestRunnerFlagship(tracer=self.tracer, file_manager=self.file_manager)
        self.state: Optional[TDDWorkflowState] = None
        
    async def run_tdd_workflow(self, requirements: str) -> TDDWorkflowState:
        """
        Run the complete TDD workflow for given requirements
        
        Args:
            requirements: The requirements to implement
            
        Returns:
            The final workflow state
        """
        # Initialize workflow state
        self.state = TDDWorkflowState(
            current_phase=TDDPhase.RED,
            requirements=requirements
        )
        
        # Trace workflow start
        self.tracer.trace_event(
            EventType.WORKFLOW_START,
            data={
                "requirements": requirements,
                "config": {
                    "max_iterations": self.config.max_iterations,
                    "timeout_seconds": self.config.timeout_seconds,
                    "auto_refactor": self.config.auto_refactor
                }
            }
        )
        
        print(f"\n{'='*80}")
        print(f"🚀 Starting TDD Workflow")
        print(f"{'='*80}\n")
        print(f"Requirements: {requirements}\n")
        
        try:
            # Run the TDD cycle
            iteration = 0
            while iteration < self.config.max_iterations:
                iteration += 1
                self.state.iteration_count = iteration
                
                print(f"\n{'='*80}")
                print(f"📍 Iteration {iteration}")
                print(f"{'='*80}\n")
                
                # RED Phase - Write failing tests
                await self._run_red_phase()
                
                # Check if we should continue (tests were written)
                if not self.state.generated_tests:
                    print("⚠️  No tests generated. Ending workflow.")
                    break
                
                # YELLOW Phase - Write minimal code
                await self._run_yellow_phase()
                
                # GREEN Phase - Run tests
                await self._run_green_phase()
                
                # Check if all tests pass
                if self.state.all_tests_passing:
                    print("\n✅ All tests passing! TDD cycle complete.")
                    break
                else:
                    print("\n⚠️  Some tests still failing. Starting next iteration...")
                    
                    # Transition back to YELLOW for fixes
                    self._transition_phase(TDDPhase.GREEN, TDDPhase.YELLOW, 
                                         False, "Tests failing, need code revision")
            
            # Mark workflow as complete
            self.state.end_time = datetime.now()
            
            # Trace workflow end
            self.tracer.trace_event(
                EventType.WORKFLOW_END,
                data={
                    "success": self.state.all_tests_passing,
                    "iterations": self.state.iteration_count,
                    "duration_seconds": (self.state.end_time - self.state.start_time).total_seconds()
                }
            )
            
            # Print final summary
            self._print_workflow_summary()
            
        except Exception as e:
            print(f"\n❌ Error in TDD workflow: {str(e)}")
            self.state.end_time = datetime.now()
            
            # Trace error
            self.tracer.trace_event(
                EventType.ERROR,
                data={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "phase": self.state.current_phase.value if self.state else "UNKNOWN"
                }
            )
            
            raise
        
        return self.state
    
    async def _run_red_phase(self):
        """Run the RED phase - write failing tests"""
        print("🔴 Entering RED Phase: Writing failing tests...")
        
        # Trace phase start
        self.tracer.trace_event(
            EventType.PHASE_START,
            phase=TDDPhase.RED.value,
            iteration=self.state.iteration_count
        )
        
        # Start agent exchange
        exchange_id = self.tracer.start_agent_exchange(
            agent_name="TestWriterFlagship",
            phase=TDDPhase.RED.value,
            iteration=self.state.iteration_count,
            request_data={"requirements": self.state.requirements}
        )
        
        # Run test writer agent
        test_code = ""
        async for chunk in self.test_writer.write_tests(self.state.requirements):
            print(chunk, end='', flush=True)
            test_code += chunk
            self.tracer.add_streaming_chunk(exchange_id, chunk)
        
        # Get the actual test code
        test_code = self.test_writer.get_test_code()
        if test_code:
            self.state.generated_tests.append(test_code)
            # Trace file operation
            self.tracer.trace_file_operation("create", "test_generated.py", len(test_code))
        
        # Complete agent exchange
        self.tracer.complete_agent_exchange(
            exchange_id,
            response_data={
                "test_code_generated": bool(test_code),
                "test_code_length": len(test_code) if test_code else 0
            },
            success=bool(test_code),
            error=None if test_code else "No test code generated"
        )
        
        # Create phase result
        result = self.test_writer.create_phase_result(
            success=bool(test_code),
            error=None if test_code else "No test code generated"
        )
        self.state.add_phase_result(result)
        
        # Trace phase end
        self.tracer.trace_event(
            EventType.PHASE_END,
            phase=TDDPhase.RED.value,
            iteration=self.state.iteration_count,
            data={"success": bool(test_code)}
        )
        
        # Transition to YELLOW phase
        if test_code:
            self._transition_phase(TDDPhase.RED, TDDPhase.YELLOW, True, 
                                 "Tests written successfully")
        else:
            self._transition_phase(TDDPhase.RED, TDDPhase.RED, False, 
                                 "Failed to generate tests")
    
    async def _run_yellow_phase(self):
        """Run the YELLOW phase - write minimal implementation"""
        print("\n🟡 Entering YELLOW Phase: Writing minimal implementation...")
        
        # Trace phase start
        self.tracer.trace_event(
            EventType.PHASE_START,
            phase=TDDPhase.YELLOW.value,
            iteration=self.state.iteration_count
        )
        
        # Get latest test code and results
        test_code = self.state.generated_tests[-1] if self.state.generated_tests else ""
        
        # Get test results from last GREEN phase (if any)
        last_green = self.state.get_latest_phase_result(TDDPhase.GREEN)
        test_results = last_green.test_results if last_green else []
        
        # If no test results yet, create "NOT_RUN" results
        if not test_results:
            # Create NOT_RUN results for all tests
            test_results = []
            for line in test_code.split('\n'):
                if line.strip().startswith('def test_'):
                    test_name = line.strip().split('(')[0].replace('def ', '')
                    test_results.append(TestResult(
                        test_name=test_name,
                        status=TestStatus.NOT_RUN,
                        error_message="Test not yet executed"
                    ))
        
        # Start agent exchange
        exchange_id = self.tracer.start_agent_exchange(
            agent_name="CoderFlagship",
            phase=TDDPhase.YELLOW.value,
            iteration=self.state.iteration_count,
            request_data={
                "test_code": test_code[:500],  # Truncate for logging
                "test_results_count": len(test_results)
            }
        )
        
        # Run coder agent
        implementation_code = ""
        async for chunk in self.coder.write_code(test_code, test_results):
            print(chunk, end='', flush=True)
            implementation_code += chunk
            self.tracer.add_streaming_chunk(exchange_id, chunk)
        
        # Get the actual implementation code
        implementation_code = self.coder.get_implementation_code()
        if implementation_code:
            self.state.generated_code.append(implementation_code)
            # Trace file operation
            self.tracer.trace_file_operation("create", "implementation_generated.py", len(implementation_code))
        
        # Complete agent exchange
        self.tracer.complete_agent_exchange(
            exchange_id,
            response_data={
                "implementation_generated": bool(implementation_code),
                "implementation_length": len(implementation_code) if implementation_code else 0
            },
            success=bool(implementation_code),
            error=None if implementation_code else "No implementation generated"
        )
        
        # Create phase result
        result = self.coder.create_phase_result(
            success=bool(implementation_code),
            error=None if implementation_code else "No implementation generated"
        )
        self.state.add_phase_result(result)
        
        # Trace phase end
        self.tracer.trace_event(
            EventType.PHASE_END,
            phase=TDDPhase.YELLOW.value,
            iteration=self.state.iteration_count,
            data={"success": bool(implementation_code)}
        )
        
        # Transition to GREEN phase
        if implementation_code:
            self._transition_phase(TDDPhase.YELLOW, TDDPhase.GREEN, True,
                                 "Implementation written successfully")
        else:
            self._transition_phase(TDDPhase.YELLOW, TDDPhase.YELLOW, False,
                                 "Failed to generate implementation")
    
    async def _run_green_phase(self):
        """Run the GREEN phase - execute tests"""
        print("\n🟢 Entering GREEN Phase: Running tests...")
        
        # Trace phase start
        self.tracer.trace_event(
            EventType.PHASE_START,
            phase=TDDPhase.GREEN.value,
            iteration=self.state.iteration_count
        )
        
        # Get latest test and implementation code
        test_code = self.state.generated_tests[-1] if self.state.generated_tests else ""
        impl_code = self.state.generated_code[-1] if self.state.generated_code else ""
        
        if not test_code or not impl_code:
            print("❌ Missing test or implementation code!")
            return
        
        # Start agent exchange
        exchange_id = self.tracer.start_agent_exchange(
            agent_name="TestRunnerFlagship",
            phase=TDDPhase.GREEN.value,
            iteration=self.state.iteration_count,
            request_data={
                "test_code_length": len(test_code),
                "implementation_length": len(impl_code)
            }
        )
        
        # Track test execution start time
        test_start_time = datetime.now()
        
        # Run test runner agent
        async for chunk in self.test_runner.run_tests(test_code, impl_code):
            print(chunk, end='', flush=True)
            self.tracer.add_streaming_chunk(exchange_id, chunk)
        
        # Get test results
        test_results = self.test_runner.get_test_results()
        all_passed = self.test_runner.all_tests_passed()
        
        # Calculate test execution duration
        test_duration = (datetime.now() - test_start_time).total_seconds() * 1000
        
        # Trace test execution
        test_results_data = [
            {
                "test_name": tr.test_name,
                "status": tr.status.value,
                "error_message": tr.error_message
            }
            for tr in test_results
        ]
        self.tracer.trace_test_execution(
            "test_generated.py",
            test_results_data,
            test_duration
        )
        
        # Complete agent exchange
        self.tracer.complete_agent_exchange(
            exchange_id,
            response_data={
                "all_tests_passed": all_passed,
                "test_count": len(test_results),
                "passed_count": sum(1 for t in test_results if t.status == TestStatus.PASSED),
                "failed_count": sum(1 for t in test_results if t.status != TestStatus.PASSED)
            },
            success=True
        )
        
        # Update state
        self.state.all_tests_passing = all_passed
        
        # Create phase result
        result = self.test_runner.create_phase_result()
        self.state.add_phase_result(result)
        
        # Trace phase end
        self.tracer.trace_event(
            EventType.PHASE_END,
            phase=TDDPhase.GREEN.value,
            iteration=self.state.iteration_count,
            data={
                "success": all_passed,
                "test_results": len(test_results)
            }
        )
        
        # Determine next phase
        if all_passed:
            # All tests pass - workflow complete!
            self._transition_phase(TDDPhase.GREEN, TDDPhase.GREEN, True,
                                 "All tests passing - TDD cycle complete")
        else:
            # Tests failing - need to go back to YELLOW
            failed_count = sum(1 for t in test_results if t.status != TestStatus.PASSED)
            self._transition_phase(TDDPhase.GREEN, TDDPhase.YELLOW, False,
                                 f"{failed_count} tests still failing")
    
    def _transition_phase(self, from_phase: TDDPhase, to_phase: TDDPhase, 
                         success: bool, reason: str):
        """Record a phase transition"""
        transition = PhaseTransition(
            from_phase=from_phase,
            to_phase=to_phase,
            validation_passed=success,
            reason=reason
        )
        self.state.add_transition(transition)
        
        # Trace transition
        self.tracer.trace_event(
            EventType.TRANSITION,
            data={
                "from_phase": from_phase.value,
                "to_phase": to_phase.value,
                "success": success,
                "reason": reason
            }
        )
        
        # Print transition
        if from_phase != to_phase:
            print(f"\n{'→'*20}")
            print(f"Phase Transition: {from_phase.value} → {to_phase.value}")
            print(f"Reason: {reason}")
            print(f"{'→'*20}\n")
    
    def _print_workflow_summary(self):
        """Print a summary of the workflow execution"""
        print(f"\n{'='*80}")
        print("📊 TDD Workflow Summary")
        print(f"{'='*80}\n")
        
        # Basic info
        duration = (self.state.end_time - self.state.start_time).total_seconds()
        print(f"Total Duration: {duration:.1f} seconds")
        print(f"Iterations: {self.state.iteration_count}")
        print(f"Final Status: {'✅ SUCCESS' if self.state.all_tests_passing else '❌ INCOMPLETE'}")
        
        # Test summary
        test_summary = self.state.get_test_summary()
        print(f"\nTest Results:")
        print(f"  Total: {test_summary['total']}")
        print(f"  ✅ Passed: {test_summary['passed']}")
        print(f"  ❌ Failed: {test_summary['failed']}")
        print(f"  💥 Errors: {test_summary['error']}")
        
        # Phase summary
        print(f"\nPhase Executions:")
        for phase in TDDPhase:
            results = self.state.get_phase_results(phase)
            if results:
                successful = sum(1 for r in results if r.success)
                print(f"  {phase.value}: {len(results)} executions ({successful} successful)")
        
        # Generated artifacts
        print(f"\nGenerated Artifacts:")
        print(f"  Test Files: {len(self.state.generated_tests)}")
        print(f"  Implementation Files: {len(self.state.generated_code)}")
        
        print(f"\n{'='*80}\n")
    
    def save_workflow_state(self, output_dir: str = "generated"):
        """Save the workflow state to disk"""
        if not self.state:
            return
        
        # Use the file manager's session directory instead of creating a new one
        output_path = self.file_manager.session_dir
        
        # Save execution report
        execution_report_file = self.tracer.save_report(output_path)
        print(f"Execution report saved to: {execution_report_file}")
        
        # Save state as JSON
        state_file = output_path / f"tdd_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert state to dict (simplified for JSON serialization)
        state_dict = {
            "requirements": self.state.requirements,
            "iterations": self.state.iteration_count,
            "all_tests_passing": self.state.all_tests_passing,
            "duration_seconds": (self.state.end_time - self.state.start_time).total_seconds() if self.state.end_time else 0,
            "test_summary": self.state.get_test_summary(),
            "phases": [
                {
                    "phase": result.phase.value,
                    "success": result.success,
                    "agent": result.agent.value,
                    "error": result.error
                }
                for result in self.state.phase_results
            ]
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_dict, f, indent=2)
        
        print(f"Workflow state saved to: {state_file}")
        
        # Files are already saved by the file manager during agent execution
        # No need to save them again here
        
        # Save file manager session metadata
        self.file_manager.save_session_metadata()
        print(f"Session metadata saved to: {self.file_manager.session_dir}")


async def main():
    """Example usage of the flagship orchestrator"""
    # Create orchestrator with default config
    orchestrator = FlagshipOrchestrator()
    
    # Run TDD workflow for a calculator
    requirements = "Create a simple calculator with add, subtract, multiply, and divide operations"
    
    try:
        state = await orchestrator.run_tdd_workflow(requirements)
        
        # Save results
        orchestrator.save_workflow_state()
        
    except Exception as e:
        print(f"Error running TDD workflow: {e}")


if __name__ == "__main__":
    asyncio.run(main())