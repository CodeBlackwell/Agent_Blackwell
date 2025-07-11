"""Main TDD Orchestrator - coordinates the complete TDD workflow"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .models import (
    TDDPhase, TDDFeature, TDDOrchestratorConfig, FeatureResult,
    PhaseResult, AgentContext, TDDCycle
)
from .phase_manager import PhaseManager
from .agent_coordinator import AgentCoordinator
from .retry_coordinator import RetryCoordinator
from .metrics_collector import MetricsCollector


class TDDOrchestrator:
    """Main orchestrator for TDD workflow execution"""
    
    def __init__(self, config: TDDOrchestratorConfig = None, 
                 run_team_member_func: Optional[Callable] = None):
        """
        Initialize TDD Orchestrator
        Args:
            config: Configuration for the orchestrator
            run_team_member_func: Optional function to run team members (for parent system integration)
        """
        self.config = config or TDDOrchestratorConfig()
        self.phase_manager = PhaseManager()
        self.agent_coordinator = AgentCoordinator(run_team_member_func)
        self.retry_coordinator = RetryCoordinator(self.config.__dict__)
        self.metrics_collector = MetricsCollector()
        
        # Output handlers
        self.verbose = self.config.verbose_output
        
    async def execute_feature(self, feature: TDDFeature) -> FeatureResult:
        """
        Execute TDD workflow for a single feature
        Returns: FeatureResult with implementation details
        """
        print(f"\n{'='*80}")
        print(f"🚀 Starting TDD implementation for: {feature.id}")
        print(f"Description: {feature.description}")
        print(f"{'='*80}\n")
        
        # Start metrics collection
        feature_metrics = self.metrics_collector.start_feature(
            feature.id, feature.description
        )
        
        cycles = []
        success = False
        errors = []
        
        try:
            # Execute TDD cycles until complete or max retries
            cycle_count = 0
            while cycle_count < self.config.max_total_retries:
                cycle_count += 1
                
                print(f"\n{'='*60}")
                print(f"📍 TDD Cycle {cycle_count}")
                print(f"{'='*60}\n")
                
                # Execute one complete TDD cycle
                cycle_result = await self._execute_tdd_cycle(feature, cycle_count)
                cycles.append(cycle_result)
                
                if cycle_result.is_complete:
                    success = True
                    print("\n✅ Feature implementation complete!")
                    break
                
                # Check if we should continue
                if not self._should_continue_cycles(cycles):
                    print("\n⚠️ Stopping cycles - too many attempts or stagnation detected")
                    break
                    
            # Complete feature metrics
            self.metrics_collector.complete_feature(feature.id, success)
            
        except Exception as e:
            errors.append(f"Fatal error: {str(e)}")
            print(f"\n❌ Fatal error during execution: {e}")
            self.metrics_collector.complete_feature(feature.id, False)
            
        # Generate final result
        final_tests = cycles[-1].generated_tests if cycles else ""
        final_code = cycles[-1].generated_code if cycles else ""
        
        # Get performance metrics
        feature_perf = self.metrics_collector.get_feature_metrics(feature.id)
        
        return FeatureResult(
            feature_id=feature.id,
            feature_description=feature.description,
            success=success,
            cycles=cycles,
            total_duration_seconds=time.time() if feature_perf else 0,  # Simplified
            phase_metrics=feature_perf.phase_metrics if feature_perf else {},
            errors=errors,
            final_tests=final_tests,
            final_code=final_code
        )
    
    async def _execute_tdd_cycle(self, feature: TDDFeature, cycle_number: int) -> TDDCycle:
        """Execute a complete RED-YELLOW-GREEN cycle"""
        # Start a new cycle
        cycle = self.phase_manager.start_cycle(
            feature.id,
            {"description": feature.description}
        )
        
        # Global context for all phases
        global_context = {
            "feature": feature.__dict__,
            "cycle_number": cycle_number,
            "test_framework": self.config.test_framework
        }
        
        # Execute phases in order
        phases = [TDDPhase.RED, TDDPhase.YELLOW, TDDPhase.GREEN]
        
        for phase in phases:
            print(f"\n{'='*40}")
            print(f"{'🔴' if phase == TDDPhase.RED else '🟡' if phase == TDDPhase.YELLOW else '🟢'} Entering {phase.value} Phase")
            print(f"{'='*40}\n")
            
            # Execute phase with retries
            phase_success = await self._execute_phase_with_retries(
                feature, cycle, phase, global_context
            )
            
            if not phase_success:
                print(f"❌ Failed to complete {phase.value} phase")
                break
            
            # Check phase transition
            next_phase, transition_success = self.phase_manager.transition_phase(
                feature.id,
                self._get_transition_context(cycle, phase)
            )
            
            if not transition_success:
                print(f"❌ Failed to transition from {phase.value}")
                break
                
            if next_phase == TDDPhase.COMPLETE:
                cycle.is_complete = True
                break
        
        # Complete the cycle
        self.phase_manager.complete_cycle(feature.id, cycle.is_complete)
        
        return cycle
    
    async def _execute_phase_with_retries(self, feature: TDDFeature, cycle: TDDCycle,
                                        phase: TDDPhase, global_context: Dict) -> bool:
        """Execute a single phase with retry logic"""
        attempt = 0
        phase_start = time.time()
        
        while attempt < self.config.max_phase_retries:
            attempt += 1
            
            try:
                # Build phase context
                phase_context = self._build_phase_context(cycle, phase)
                
                # Create agent context
                context = AgentContext(
                    phase=phase,
                    feature_id=feature.id,
                    feature_description=feature.description,
                    attempt_number=attempt,
                    previous_attempts=self._get_previous_attempts(feature.id, phase),
                    phase_context=phase_context,
                    global_context=global_context
                )
                
                # Get the appropriate agent
                agent_name = self.agent_coordinator.get_agent_for_phase(phase)
                
                # Invoke agent
                print(f"🤖 Invoking {agent_name} agent (attempt {attempt})...")
                result = await self.agent_coordinator.invoke_agent(agent_name, context)
                
                # Process agent output
                agent_outputs = self._process_agent_output(result, phase)
                
                # Update cycle with results
                self._update_cycle_from_phase(cycle, phase, agent_outputs)
                
                # Validate phase results
                validation_passed = self._validate_phase_results(phase, agent_outputs)
                
                if validation_passed:
                    # Record successful phase
                    phase_result = PhaseResult(
                        phase=phase,
                        success=True,
                        attempts=attempt,
                        duration_seconds=time.time() - phase_start,
                        agent_outputs=agent_outputs,
                        test_results=agent_outputs.get("test_results")
                    )
                    self.phase_manager.record_phase_result(feature.id, phase_result)
                    
                    # Record metrics
                    self.metrics_collector.record_phase_complete(
                        feature.id, phase,
                        phase_result.duration_seconds,
                        attempt, True,
                        agent_invocations=1,
                        test_metrics=agent_outputs.get("test_metrics")
                    )
                    
                    return True
                else:
                    raise ValueError("Phase validation failed")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Phase attempt {attempt} failed: {error_msg}")
                
                # Check if we should retry
                retry_decision = self.retry_coordinator.get_retry_decision(
                    feature.id, phase, attempt, error_msg, phase_context
                )
                
                if not retry_decision.should_retry:
                    print(f"🛑 {retry_decision.reason}")
                    
                    # Record failed phase
                    phase_result = PhaseResult(
                        phase=phase,
                        success=False,
                        attempts=attempt,
                        duration_seconds=time.time() - phase_start,
                        errors=[error_msg]
                    )
                    self.phase_manager.record_phase_result(feature.id, phase_result)
                    return False
                
                # Show retry suggestions
                if retry_decision.suggestions:
                    print("💡 Suggestions for next attempt:")
                    for suggestion in retry_decision.suggestions:
                        print(f"   - {suggestion}")
                
                # Wait before retry
                if retry_decision.delay_seconds > 0:
                    print(f"⏳ Waiting {retry_decision.delay_seconds}s before retry...")
                    await asyncio.sleep(retry_decision.delay_seconds)
        
        # Max retries reached
        print(f"❌ Max retries ({self.config.max_phase_retries}) reached for {phase.value} phase")
        return False
    
    def _build_phase_context(self, cycle: TDDCycle, phase: TDDPhase) -> Dict[str, Any]:
        """Build context for a specific phase"""
        context = {}
        
        if phase == TDDPhase.RED:
            # RED phase needs requirements
            context["requirements"] = cycle.feature_description
            
        elif phase == TDDPhase.YELLOW:
            # YELLOW phase needs tests and any previous results
            context["tests"] = cycle.generated_tests
            
            # Get last GREEN phase results if any
            last_green = cycle.get_phase_result(TDDPhase.GREEN)
            if last_green and last_green.test_results:
                context["test_results"] = last_green.test_results
                
        elif phase == TDDPhase.GREEN:
            # GREEN phase needs tests and implementation
            context["tests"] = cycle.generated_tests
            context["implementation"] = cycle.generated_code
            
        return context
    
    def _get_transition_context(self, cycle: TDDCycle, phase: TDDPhase) -> Dict[str, Any]:
        """Get context for phase transition validation"""
        context = {}
        
        if phase == TDDPhase.RED:
            # Check if tests were written and fail
            context["tests_written"] = bool(cycle.generated_tests)
            context["tests_fail"] = True  # In RED, tests should fail
            
        elif phase == TDDPhase.YELLOW:
            # Check if implementation was written
            context["implementation_written"] = bool(cycle.generated_code)
            
        elif phase == TDDPhase.GREEN:
            # Check test results
            last_result = cycle.get_phase_result(TDDPhase.GREEN)
            if last_result and last_result.test_results:
                test_info = last_result.test_results
                context["all_tests_pass"] = test_info.get("all_passed", False)
                context["test_results"] = test_info
            
        return context
    
    def _process_agent_output(self, result: Any, phase: TDDPhase) -> Dict[str, Any]:
        """Process agent output based on phase"""
        outputs = {}
        
        # Extract output string
        output_str = str(result.output) if hasattr(result, 'output') else str(result)
        
        if phase == TDDPhase.RED:
            outputs["tests"] = output_str
            
        elif phase == TDDPhase.YELLOW:
            outputs["code"] = output_str
            
        elif phase == TDDPhase.GREEN:
            # Parse test execution results
            test_results = self._parse_test_results(output_str)
            outputs["test_results"] = test_results
            outputs["test_metrics"] = {
                "total": test_results.get("total_tests", 0),
                "passed": test_results.get("passed_tests", 0),
                "failed": test_results.get("failed_tests", 0)
            }
            
        return outputs
    
    def _parse_test_results(self, output: str) -> Dict[str, Any]:
        """Parse test execution results from output"""
        results = {
            "all_passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_names": []
        }
        
        # Simple parsing - look for pytest-style output
        import re
        
        # Match patterns like "5 passed" or "3 failed"
        passed_match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)
        
        if passed_match:
            results["passed_tests"] = int(passed_match.group(1))
            
        if failed_match:
            results["failed_tests"] = int(failed_match.group(1))
        else:
            results["all_passed"] = results["passed_tests"] > 0
            
        results["total_tests"] = results["passed_tests"] + results["failed_tests"]
        
        return results
    
    def _update_cycle_from_phase(self, cycle: TDDCycle, phase: TDDPhase, 
                               agent_outputs: Dict[str, Any]):
        """Update cycle data based on phase outputs"""
        if phase == TDDPhase.RED and "tests" in agent_outputs:
            cycle.generated_tests = agent_outputs["tests"]
            
        elif phase == TDDPhase.YELLOW and "code" in agent_outputs:
            cycle.generated_code = agent_outputs["code"]
    
    def _validate_phase_results(self, phase: TDDPhase, outputs: Dict[str, Any]) -> bool:
        """Validate that phase produced expected results"""
        if phase == TDDPhase.RED:
            return bool(outputs.get("tests"))
            
        elif phase == TDDPhase.YELLOW:
            return bool(outputs.get("code"))
            
        elif phase == TDDPhase.GREEN:
            # For GREEN phase, we just need test results (pass or fail)
            return "test_results" in outputs
            
        return True
    
    def _get_previous_attempts(self, feature_id: str, phase: TDDPhase) -> List[Dict]:
        """Get previous attempt information for a phase"""
        retry_history = self.retry_coordinator.retry_history.get(feature_id, [])
        
        return [
            {
                "attempt": attempt["attempt"],
                "error": attempt["error"],
                "timestamp": attempt["timestamp"]
            }
            for attempt in retry_history
            if attempt["phase"] == phase.value
        ]
    
    def _should_continue_cycles(self, cycles: List[TDDCycle]) -> bool:
        """Determine if we should continue with more cycles"""
        if not cycles:
            return True
            
        # Check for too many cycles
        if len(cycles) >= self.config.max_total_retries:
            return False
            
        # Check for stagnation (same errors repeating)
        if len(cycles) >= 3:
            # Simple check - if last 3 cycles all failed at same phase
            last_phases = []
            for cycle in cycles[-3:]:
                if cycle.phase_history:
                    last_phases.append(cycle.phase_history[-1].phase)
                    
            if len(set(last_phases)) == 1 and not cycles[-1].is_complete:
                return False
                
        return True
    
    async def execute_batch(self, features: List[TDDFeature]) -> List[FeatureResult]:
        """Execute multiple features in sequence"""
        results = []
        
        # Start session metrics
        session_id = f"tdd_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metrics_collector.start_session(session_id)
        
        for i, feature in enumerate(features):
            print(f"\n{'='*80}")
            print(f"📋 Feature {i+1}/{len(features)}: {feature.id}")
            print(f"{'='*80}")
            
            result = await self.execute_feature(feature)
            results.append(result)
            
            # Brief pause between features
            if i < len(features) - 1:
                await asyncio.sleep(1)
        
        # Complete session
        self.metrics_collector.complete_session()
        
        # Print summary
        self._print_batch_summary(results)
        
        return results
    
    def _print_batch_summary(self, results: List[FeatureResult]):
        """Print summary of batch execution"""
        print(f"\n{'='*80}")
        print("📊 Batch Execution Summary")
        print(f"{'='*80}\n")
        
        successful = sum(1 for r in results if r.success)
        total = len(results)
        
        print(f"Total Features: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {total - successful}")
        print(f"Success Rate: {(successful/total)*100:.1f}%")
        
        # Get performance report
        perf_report = self.metrics_collector.get_performance_report()
        if "summary" in perf_report:
            print(f"\nAverage Cycle Time: {perf_report['summary']['average_cycle_time_minutes']:.1f} minutes")
        
        print(f"\n{'='*80}")