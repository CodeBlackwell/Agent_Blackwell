"""TDD Workflow coordination for the flagship orchestrator"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from flagship_orchestrator import FlagshipOrchestrator
from models.flagship_models import TDDWorkflowConfig, TDDWorkflowState


class FlagshipTDDWorkflow:
    """Manages and coordinates TDD workflows"""
    
    def __init__(self, config: TDDWorkflowConfig = None):
        self.config = config or TDDWorkflowConfig()
        self.orchestrator = FlagshipOrchestrator(self.config)
        self.workflow_history: Dict[str, TDDWorkflowState] = {}
    
    async def execute_workflow(self, 
                             requirements: str,
                             workflow_id: Optional[str] = None) -> TDDWorkflowState:
        """
        Execute a TDD workflow for given requirements
        
        Args:
            requirements: The requirements to implement
            workflow_id: Optional ID for the workflow (generated if not provided)
            
        Returns:
            The completed workflow state
        """
        # Generate workflow ID if not provided
        if not workflow_id:
            workflow_id = f"tdd_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🏁 Starting TDD Workflow: {workflow_id}")
        print(f"Configuration:")
        print(f"  - Max Iterations: {self.config.max_iterations}")
        print(f"  - Timeout: {self.config.timeout_seconds}s")
        print(f"  - Test Framework: {self.config.test_framework}")
        print(f"  - Strict TDD: {self.config.strict_tdd}")
        
        # Execute the workflow
        try:
            state = await asyncio.wait_for(
                self.orchestrator.run_tdd_workflow(requirements),
                timeout=self.config.timeout_seconds
            )
            
            # Store in history
            self.workflow_history[workflow_id] = state
            
            # Save to disk
            self.orchestrator.save_workflow_state(self.config.code_directory)
            
            return state
            
        except asyncio.TimeoutError:
            print(f"\n⏱️  Workflow timed out after {self.config.timeout_seconds} seconds")
            raise
        except Exception as e:
            print(f"\n❌ Workflow failed with error: {str(e)}")
            raise
    
    def get_workflow_state(self, workflow_id: str) -> Optional[TDDWorkflowState]:
        """Get the state of a specific workflow"""
        return self.workflow_history.get(workflow_id)
    
    def list_workflows(self) -> Dict[str, Dict[str, Any]]:
        """List all executed workflows with summary info"""
        summaries = {}
        
        for workflow_id, state in self.workflow_history.items():
            duration = 0
            if state.end_time and state.start_time:
                duration = (state.end_time - state.start_time).total_seconds()
            
            summaries[workflow_id] = {
                "requirements": state.requirements[:50] + "..." if len(state.requirements) > 50 else state.requirements,
                "iterations": state.iteration_count,
                "all_tests_passing": state.all_tests_passing,
                "duration_seconds": duration,
                "test_summary": state.get_test_summary()
            }
        
        return summaries
    
    async def run_workflow_with_custom_config(self,
                                            requirements: str,
                                            max_iterations: int = None,
                                            timeout_seconds: int = None,
                                            strict_tdd: bool = None) -> TDDWorkflowState:
        """
        Run a workflow with custom configuration overrides
        
        Args:
            requirements: The requirements to implement
            max_iterations: Override max iterations
            timeout_seconds: Override timeout
            strict_tdd: Override strict TDD mode
            
        Returns:
            The completed workflow state
        """
        # Create custom config
        custom_config = TDDWorkflowConfig(
            max_iterations=max_iterations or self.config.max_iterations,
            timeout_seconds=timeout_seconds or self.config.timeout_seconds,
            strict_tdd=strict_tdd if strict_tdd is not None else self.config.strict_tdd,
            verbose_output=self.config.verbose_output,
            test_framework=self.config.test_framework,
            test_directory=self.config.test_directory,
            code_directory=self.config.code_directory,
            coverage_threshold=self.config.coverage_threshold
        )
        
        # Create new orchestrator with custom config
        custom_orchestrator = FlagshipOrchestrator(custom_config)
        
        # Run workflow
        state = await custom_orchestrator.run_tdd_workflow(requirements)
        
        # Save results
        custom_orchestrator.save_workflow_state(custom_config.code_directory)
        
        return state


# Convenience functions for common workflows

async def run_simple_tdd(requirements: str) -> TDDWorkflowState:
    """Run a simple TDD workflow with default settings"""
    workflow = FlagshipTDDWorkflow()
    return await workflow.execute_workflow(requirements)


async def run_strict_tdd(requirements: str, max_iterations: int = 3) -> TDDWorkflowState:
    """Run a strict TDD workflow that enforces failing tests first"""
    workflow = FlagshipTDDWorkflow()
    return await workflow.run_workflow_with_custom_config(
        requirements,
        max_iterations=max_iterations,
        strict_tdd=True
    )


async def run_quick_tdd(requirements: str) -> TDDWorkflowState:
    """Run a quick TDD workflow with reduced iterations and timeout"""
    workflow = FlagshipTDDWorkflow()
    return await workflow.run_workflow_with_custom_config(
        requirements,
        max_iterations=2,
        timeout_seconds=60
    )