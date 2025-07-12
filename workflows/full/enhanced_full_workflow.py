"""
Enhanced full workflow implementation with improved error handling and agent coordination.
"""
from typing import List, Optional, Tuple, Dict, Any
import asyncio
import json
import traceback
from datetime import datetime
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)
from workflows.workflow_config import MAX_REVIEW_RETRIES
from workflows.incremental.feature_orchestrator import run_incremental_coding_phase, extract_content_from_message
from agents.executor.session_utils import generate_session_id
from workflows.full.phase_transition_manager import (
    PhaseTransitionManager, TransitionOrchestrator
)
from workflows.full.workflow_cache_manager import (
    WorkflowCacheManager, SmartCacheStrategy
)
from workflows.full.performance_monitor import PerformanceMonitor


class EnhancedFullWorkflowConfig:
    """Configuration for enhanced full workflow."""
    def __init__(self):
        self.max_review_retries = MAX_REVIEW_RETRIES
        self.enable_rollback = True
        self.enable_parallel_execution = False
        self.retry_delays = [1, 2, 5]  # Exponential backoff in seconds
        self.phase_timeout = 300  # 5 minutes per phase
        self.enable_feedback_loop = True
        self.enable_context_enrichment = True
        self.skip_phases = []  # Phases to skip
        self.custom_validation_rules = {}
        self.enable_caching = True
        self.cache_ttl_multiplier = 1.0  # Adjust cache TTL


class WorkflowStateManager:
    """Manages workflow state for rollback and recovery."""
    def __init__(self):
        self.checkpoints = {}
        self.phase_outputs = {}
        self.error_history = []
        
    def save_checkpoint(self, phase: str, output: Any, metadata: Dict[str, Any] = None):
        """Save a checkpoint for potential rollback."""
        self.checkpoints[phase] = {
            "output": output,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.phase_outputs[phase] = output
        
    def get_checkpoint(self, phase: str) -> Optional[Dict[str, Any]]:
        """Retrieve a checkpoint."""
        return self.checkpoints.get(phase)
        
    def record_error(self, phase: str, error: Exception, context: Dict[str, Any]):
        """Record error for pattern analysis."""
        self.error_history.append({
            "phase": phase,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
    def can_recover_from_error(self, phase: str) -> bool:
        """Check if we can recover from errors in this phase."""
        phase_errors = [e for e in self.error_history if e["phase"] == phase]
        return len(phase_errors) < 3  # Allow up to 3 attempts per phase


class AgentCommunicationEnhancer:
    """Enhances communication between agents."""
    def __init__(self, enable_feedback: bool = True, enable_context: bool = True):
        self.enable_feedback = enable_feedback
        self.enable_context = enable_context
        self.conversation_history = []
        
    def prepare_agent_input(self, 
                          agent: str, 
                          base_input: str, 
                          previous_outputs: Dict[str, str],
                          feedback: Optional[str] = None) -> str:
        """Prepare enriched input for an agent."""
        enriched_input = base_input
        
        if self.enable_context and previous_outputs:
            # Add relevant context from previous agents
            context_parts = []
            if agent == "designer" and "planner" in previous_outputs:
                context_parts.append(f"Plan Context:\n{previous_outputs['planner'][:500]}")
            elif agent == "coder" and "designer" in previous_outputs:
                context_parts.append(f"Design Context:\n{previous_outputs['designer'][:500]}")
                
            if context_parts:
                enriched_input = "\n\n".join(context_parts) + "\n\n" + enriched_input
                
        if self.enable_feedback and feedback:
            enriched_input += f"\n\nPrevious Feedback:\n{feedback}"
            
        self.conversation_history.append({
            "agent": agent,
            "input": enriched_input[:200] + "...",
            "timestamp": datetime.now().isoformat()
        })
        
        return enriched_input


async def execute_enhanced_full_workflow(
    input_data: CodingTeamInput, 
    config: Optional[EnhancedFullWorkflowConfig] = None,
    tracer: Optional[WorkflowExecutionTracer] = None
) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute enhanced full workflow with improved error handling and coordination.
    
    Args:
        input_data: The input data containing requirements and workflow configuration
        config: Enhanced workflow configuration
        tracer: Optional tracer for monitoring execution
        
    Returns:
        Tuple of (team member results, execution report)
    """
    # Initialize configuration and tracer
    config = config or EnhancedFullWorkflowConfig()
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="EnhancedFull",
            execution_id=f"enhanced_full_{int(asyncio.get_event_loop().time())}"
        )
    
    # Initialize state manager and communication enhancer
    state_manager = WorkflowStateManager()
    comm_enhancer = AgentCommunicationEnhancer(
        enable_feedback=config.enable_feedback_loop,
        enable_context=config.enable_context_enrichment
    )
    
    # Initialize phase transition manager
    transition_manager = PhaseTransitionManager()
    transition_orchestrator = TransitionOrchestrator(transition_manager)
    
    # Initialize cache manager
    cache_manager = WorkflowCacheManager(
        enable_cache=config.enable_caching,
        default_ttl=int(3600 * config.cache_ttl_multiplier)
    )
    smart_cache = SmartCacheStrategy(cache_manager)
    
    # Initialize performance monitor
    performance_monitor = PerformanceMonitor()
    workflow_metrics = performance_monitor.start_workflow(
        f"enhanced_full_{tracer.execution_id}"
    )
    
    # Add configuration to tracer metadata
    tracer.add_metadata("workflow_config", {
        "max_review_retries": config.max_review_retries,
        "enable_rollback": config.enable_rollback,
        "enable_parallel_execution": config.enable_parallel_execution,
        "enable_feedback_loop": config.enable_feedback_loop,
        "skip_phases": config.skip_phases
    })
    
    try:
        # Execute the enhanced workflow
        team_members = ["planner", "designer", "coder", "reviewer"]
        if TeamMember.executor in input_data.team_members:
            team_members.append("executor")
            
        results = await run_enhanced_full_workflow(
            requirements=input_data.requirements,
            team_members=team_members,
            tracer=tracer,
            config=config,
            state_manager=state_manager,
            comm_enhancer=comm_enhancer,
            cache_manager=cache_manager,
            smart_cache=smart_cache,
            performance_monitor=performance_monitor
        )
        
        # Complete performance monitoring
        performance_monitor.complete_workflow()
        performance_monitor.update_cache_stats(cache_manager.get_stats())
        
        # Get performance report
        perf_report = performance_monitor.get_performance_report()
        optimization_suggestions = performance_monitor.get_optimization_suggestions()
        
        # Complete workflow execution
        tracer.complete_execution(final_output={
            "workflow": "EnhancedFull",
            "results_count": len(results),
            "success": True,
            "error_recovery_count": len(state_manager.error_history),
            "checkpoints_saved": len(state_manager.checkpoints),
            "performance_metrics": perf_report,
            "optimization_suggestions": optimization_suggestions
        })
        
    except Exception as e:
        # Enhanced error handling
        error_msg = f"Enhanced full workflow error: {str(e)}"
        error_context = {
            "error_history": state_manager.error_history,
            "completed_phases": list(state_manager.checkpoints.keys()),
            "last_checkpoint": list(state_manager.checkpoints.keys())[-1] if state_manager.checkpoints else None
        }
        tracer.complete_execution(error=error_msg, metadata=error_context)
        raise
    
    # Return results and execution report
    return results, tracer.get_report()


async def run_enhanced_full_workflow(
    requirements: str,
    team_members: List[str],
    tracer: WorkflowExecutionTracer,
    config: EnhancedFullWorkflowConfig,
    state_manager: WorkflowStateManager,
    comm_enhancer: AgentCommunicationEnhancer,
    cache_manager: WorkflowCacheManager,
    smart_cache: SmartCacheStrategy,
    performance_monitor: PerformanceMonitor
) -> List[TeamMemberResult]:
    """
    Run enhanced full workflow with improved error handling and agent coordination.
    """
    from core.migration import run_team_member_with_tracking
    from workflows import workflow_utils
    review_output = workflow_utils.review_output
    
    results = []
    phase_outputs = {}
    
    print(f"🚀 Starting enhanced full workflow for: {requirements[:50]}...")
    
    # Phase 1: Planning
    if "planner" in team_members and "planner" not in config.skip_phases:
        phase_result = await execute_phase_with_retry(
            phase_name="planning",
            agent_name="planner_agent",
            input_data=requirements,
            tracer=tracer,
            config=config,
            state_manager=state_manager,
            comm_enhancer=comm_enhancer,
            phase_outputs=phase_outputs,
            team_member=TeamMember.planner,
            cache_manager=cache_manager,
            smart_cache=smart_cache,
            performance_monitor=performance_monitor
        )
        
        if phase_result:
            results.append(phase_result)
            phase_outputs["planner"] = phase_result.output
    
    # Phase 2: Design
    if "designer" in team_members and "designer" not in config.skip_phases:
        design_input = comm_enhancer.prepare_agent_input(
            "designer",
            f"Requirements: {requirements}",
            phase_outputs
        )
        
        phase_result = await execute_phase_with_retry(
            phase_name="design",
            agent_name="designer_agent",
            input_data=design_input,
            tracer=tracer,
            config=config,
            state_manager=state_manager,
            comm_enhancer=comm_enhancer,
            phase_outputs=phase_outputs,
            team_member=TeamMember.designer,
            cache_manager=cache_manager,
            smart_cache=smart_cache,
            performance_monitor=performance_monitor
        )
        
        if phase_result:
            results.append(phase_result)
            phase_outputs["designer"] = phase_result.output
    
    # Phase 3: Implementation
    if "coder" in team_members and "coder" not in config.skip_phases:
        await execute_coding_phase(
            requirements=requirements,
            phase_outputs=phase_outputs,
            results=results,
            tracer=tracer,
            config=config,
            state_manager=state_manager,
            comm_enhancer=comm_enhancer,
            team_members=team_members,
            performance_monitor=performance_monitor
        )
    
    # Phase 4: Final Review
    if "reviewer" in team_members and "reviewer" not in config.skip_phases and phase_outputs:
        review_input = comm_enhancer.prepare_agent_input(
            "reviewer",
            f"Requirements: {requirements}",
            phase_outputs
        )
        
        phase_result = await execute_phase_with_retry(
            phase_name="final_review",
            agent_name="reviewer_agent",
            input_data=review_input,
            tracer=tracer,
            config=config,
            state_manager=state_manager,
            comm_enhancer=comm_enhancer,
            phase_outputs=phase_outputs,
            team_member=TeamMember.reviewer,
            cache_manager=cache_manager,
            smart_cache=smart_cache,
            performance_monitor=performance_monitor
        )
        
        if phase_result:
            results.append(phase_result)
    
    return results


async def execute_phase_with_retry(
    phase_name: str,
    agent_name: str,
    input_data: str,
    tracer: WorkflowExecutionTracer,
    config: EnhancedFullWorkflowConfig,
    state_manager: WorkflowStateManager,
    comm_enhancer: AgentCommunicationEnhancer,
    phase_outputs: Dict[str, str],
    team_member: TeamMember,
    cache_manager: Optional[WorkflowCacheManager] = None,
    smart_cache: Optional[SmartCacheStrategy] = None,
    performance_monitor: Optional[PerformanceMonitor] = None
) -> Optional[TeamMemberResult]:
    """Execute a phase with retry logic and error recovery."""
    from core.migration import run_team_member_with_tracking
    
    # Start performance monitoring for this phase
    phase_metrics = None
    if performance_monitor:
        phase_metrics = performance_monitor.start_phase(phase_name)
    
    # Check cache first
    if cache_manager:
        cached_result = cache_manager.get(phase_name, input_data, phase_outputs)
        if cached_result:
            # Return cached result immediately
            print(f"📦 Using cached result for {phase_name}")
            if phase_metrics:
                phase_metrics.cache_hit = True
                performance_monitor.complete_phase(phase_metrics, success=True)
            return TeamMemberResult(
                team_member=team_member,
                output=cached_result,
                name=agent_name.replace("_agent", "")
            )
    
    for attempt in range(len(config.retry_delays) + 1):
        try:
            print(f"{'🔄' if attempt > 0 else '📋'} {phase_name.capitalize()} phase{' (retry)' if attempt > 0 else ''}...")
            
            step_id = tracer.start_step(phase_name, agent_name, {
                "input": input_data[:200] + "...",
                "attempt": attempt + 1,
                "cached": False
            })
            
            # Track retry count
            if phase_metrics:
                phase_metrics.retry_count = attempt
            
            # Track execution time for smart caching
            start_time = asyncio.get_event_loop().time()
            
            # Record agent call
            if performance_monitor:
                performance_monitor.record_agent_call(agent_name)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                run_team_member_with_tracking(agent_name, input_data, f"enhanced_{phase_name}"),
                timeout=config.phase_timeout
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            # Extract content from the result properly
            output = extract_content_from_message(result)
            
            # Save checkpoint
            state_manager.save_checkpoint(phase_name, output, {
                "agent": agent_name,
                "attempt": attempt + 1
            })
            
            tracer.complete_step(step_id, {
                "output": output[:200] + "...",
                "execution_time": execution_time
            })
            
            # Cache the result if appropriate
            if cache_manager and smart_cache:
                if smart_cache.should_cache(phase_name, input_data, execution_time):
                    cache_manager.set(phase_name, input_data, output, phase_outputs, {
                        "execution_time": execution_time,
                        "attempt": attempt + 1
                    })
            
            # Complete performance monitoring
            if phase_metrics and performance_monitor:
                phase_metrics.metadata["execution_time"] = execution_time
                performance_monitor.complete_phase(phase_metrics, success=True)
            
            return TeamMemberResult(
                team_member=team_member,
                output=output,
                name=agent_name.replace("_agent", "")
            )
            
        except asyncio.TimeoutError:
            error_msg = f"{phase_name} phase timed out after {config.phase_timeout}s"
            state_manager.record_error(phase_name, asyncio.TimeoutError(error_msg), {
                "agent": agent_name,
                "attempt": attempt + 1
            })
            
            if attempt < len(config.retry_delays):
                await asyncio.sleep(config.retry_delays[attempt])
                continue
            else:
                tracer.complete_step(step_id, error=error_msg)
                if phase_metrics and performance_monitor:
                    performance_monitor.complete_phase(phase_metrics, success=False, error=error_msg)
                if config.enable_rollback and state_manager.can_recover_from_error(phase_name):
                    return await attempt_rollback_recovery(phase_name, state_manager, phase_outputs)
                raise
                
        except Exception as e:
            error_msg = f"{phase_name} phase error: {str(e)}"
            state_manager.record_error(phase_name, e, {
                "agent": agent_name,
                "attempt": attempt + 1,
                "input": input_data[:500]
            })
            
            if attempt < len(config.retry_delays):
                print(f"⚠️ {error_msg}, retrying in {config.retry_delays[attempt]}s...")
                await asyncio.sleep(config.retry_delays[attempt])
                
                # Modify input based on error for next attempt
                if config.enable_feedback_loop:
                    input_data = comm_enhancer.prepare_agent_input(
                        agent_name.replace("_agent", ""),
                        input_data,
                        phase_outputs,
                        f"Previous attempt failed with: {str(e)}"
                    )
                continue
            else:
                tracer.complete_step(step_id, error=error_msg)
                if phase_metrics and performance_monitor:
                    performance_monitor.complete_phase(phase_metrics, success=False, error=error_msg)
                if config.enable_rollback and state_manager.can_recover_from_error(phase_name):
                    return await attempt_rollback_recovery(phase_name, state_manager, phase_outputs)
                raise
    
    return None


async def execute_coding_phase(
    requirements: str,
    phase_outputs: Dict[str, str],
    results: List[TeamMemberResult],
    tracer: WorkflowExecutionTracer,
    config: EnhancedFullWorkflowConfig,
    state_manager: WorkflowStateManager,
    comm_enhancer: AgentCommunicationEnhancer,
    team_members: List[str],
    performance_monitor: Optional[PerformanceMonitor] = None
) -> None:
    """Execute the coding phase with incremental orchestrator fallback."""
    from core.migration import run_team_member_with_tracking
    
    print("💻 Implementation phase...")
    
    step_id = tracer.start_step("implementation", "incremental_coding", {
        "has_plan": "planner" in phase_outputs,
        "has_design": "designer" in phase_outputs,
        "requirements": requirements[:200] + "..."
    })
    
    try:
        # Use incremental feature orchestrator
        design_output = phase_outputs.get("designer", "")
        code_output, execution_metrics = await run_incremental_coding_phase(
            designer_output=design_output,
            requirements=requirements,
            tests=None,
            tracer=tracer,
            max_retries=config.max_review_retries
        )
        
        # Save checkpoint
        state_manager.save_checkpoint("coding", code_output, {
            "method": "incremental",
            "metrics": execution_metrics
        })
        
        # Add execution metrics
        tracer.add_metadata("incremental_execution_metrics", execution_metrics)
        tracer.complete_step(step_id, {
            "output": code_output[:200] + "...",
            "features_completed": execution_metrics['completed_features'],
            "total_features": execution_metrics['total_features']
        })
        
        print(f"✅ Completed {execution_metrics['completed_features']}/{execution_metrics['total_features']} features")
        print(f"📊 Success rate: {execution_metrics['success_rate']:.1f}%")
        
        # Check if workflow was cancelled
        if execution_metrics.get('workflow_cancelled', False):
            cancellation_reason = execution_metrics.get('cancellation_reason', 'Unknown reason')
            error_msg = f"Workflow cancelled: {cancellation_reason}"
            print(f"\n❌ {error_msg}")
            
            # Record the cancellation
            state_manager.record_error("coding", Exception(error_msg), {
                "method": "incremental",
                "cancellation": True,
                "reason": cancellation_reason
            })
            
            # Mark the workflow as failed
            tracer.complete_execution(error=error_msg)
            
            # Raise an exception to stop the workflow
            raise RuntimeError(error_msg)
        
        results.append(TeamMemberResult(
            team_member=TeamMember.coder,
            output=code_output,
            name="coder"
        ))
        phase_outputs["coder"] = code_output
        
        # Execute if needed
        if "executor" in team_members:
            await execute_code_in_container(
                code_output=code_output,
                requirements=requirements,
                results=results,
                tracer=tracer,
                state_manager=state_manager,
                fallback=False
            )
        
    except Exception as e:
        error_msg = f"Incremental coding phase error: {str(e)}"
        print(f"❌ {error_msg}")
        state_manager.record_error("coding", e, {"method": "incremental"})
        tracer.complete_step(step_id, {"error": error_msg}, error=error_msg)
        
        # Fallback to standard coder
        print("⚠️ Falling back to standard implementation...")
        
        code_input = comm_enhancer.prepare_agent_input(
            "coder",
            f"Requirements: {requirements}",
            phase_outputs
        )
        
        code_result = await run_team_member_with_tracking("coder_agent", code_input, "enhanced_coding_fallback")
        code_output = extract_content_from_message(code_result)
        
        # Save checkpoint
        state_manager.save_checkpoint("coding", code_output, {"method": "standard"})
        
        results.append(TeamMemberResult(
            team_member=TeamMember.coder,
            output=code_output,
            name="coder"
        ))
        phase_outputs["coder"] = code_output
        
        # Execute if needed
        if "executor" in team_members:
            await execute_code_in_container(
                code_output=code_output,
                requirements=requirements,
                results=results,
                tracer=tracer,
                state_manager=state_manager,
                fallback=True
            )


async def execute_code_in_container(
    code_output: str,
    requirements: str,
    results: List[TeamMemberResult],
    tracer: WorkflowExecutionTracer,
    state_manager: WorkflowStateManager,
    fallback: bool = False
) -> None:
    """Execute code in Docker container with proper error handling."""
    from core.migration import run_team_member_with_tracking
    from agents.executor.proof_reader import extract_proof_from_executor_output
    
    print(f"🐳 Executing code in Docker container{' (fallback)' if fallback else ''}...")
    
    session_id = generate_session_id(requirements)
    
    step_id = tracer.start_step(
        "execution" if not fallback else "execution_fallback",
        "executor_agent",
        {
            "session_id": session_id,
            "code_preview": code_output[:200] + "...",
            "is_fallback": fallback
        }
    )
    
    try:
        execution_input = f"""SESSION_ID: {session_id}

Execute the following code:

{code_output}
"""
        
        execution_result = await run_team_member_with_tracking(
            "executor_agent",
            execution_input,
            f"enhanced_execution{'_fallback' if fallback else ''}"
        )
        execution_output = extract_content_from_message(execution_result)
        
        # Extract proof of execution
        proof_details = extract_proof_from_executor_output(execution_output, session_id)
        if proof_details and "No proof of execution found" not in proof_details:
            execution_output += f"\n\n{proof_details}"
        
        # Save checkpoint
        state_manager.save_checkpoint("execution", execution_output, {
            "session_id": session_id,
            "has_proof": bool(proof_details)
        })
        
        tracer.complete_step(step_id, {
            "output": execution_output[:200] + "...",
            "has_proof": bool(proof_details)
        })
        
        results.append(TeamMemberResult(
            team_member=TeamMember.executor,
            output=execution_output,
            name="executor"
        ))
        
    except Exception as e:
        error_msg = f"Execution error: {str(e)}"
        state_manager.record_error("execution", e, {"session_id": session_id})
        tracer.complete_step(step_id, error=error_msg)
        print(f"⚠️ {error_msg}")


async def attempt_rollback_recovery(
    phase_name: str,
    state_manager: WorkflowStateManager,
    phase_outputs: Dict[str, str]
) -> Optional[TeamMemberResult]:
    """Attempt to recover from error using rollback."""
    print(f"🔄 Attempting rollback recovery for {phase_name}...")
    
    # Try to use the last successful checkpoint
    checkpoint = state_manager.get_checkpoint(phase_name)
    if checkpoint:
        print(f"✅ Recovered from checkpoint: {checkpoint['timestamp']}")
        phase_outputs[phase_name] = checkpoint["output"]
        
        # Create a result from checkpoint
        return TeamMemberResult(
            team_member=TeamMember[phase_name.replace("_agent", "")],
            output=checkpoint["output"],
            name=phase_name
        )
    
    return None