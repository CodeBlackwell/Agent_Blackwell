"""
Common workflow execution logic for demos.
Provides a unified interface for running different workflow types.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput, TeamMember
from workflows.monitoring import WorkflowExecutionTracer


class WorkflowRunner:
    """Handles workflow execution with consistent interface."""
    
    # Workflow configurations
    WORKFLOW_CONFIGS = {
        "tdd": {
            "name": "Test-Driven Development",
            "team": [
                TeamMember.planner,
                TeamMember.designer,
                TeamMember.test_writer,
                TeamMember.coder,
                TeamMember.executor,
                TeamMember.reviewer
            ],
            "description": "Write tests first, then implement code"
        },
        "full": {
            "name": "Full Workflow",
            "team": [
                TeamMember.planner,
                TeamMember.designer,
                TeamMember.coder,
                TeamMember.executor,
                TeamMember.reviewer
            ],
            "description": "Complete development without test-first approach"
        },
        "mvp_incremental": {
            "name": "MVP Incremental",
            "team": [],  # Team configured by workflow
            "description": "Build features incrementally with validation"
        },
        "mvp_incremental_tdd": {
            "name": "MVP Incremental with TDD",
            "team": [],  # Team configured by workflow
            "description": "Incremental development with test-first approach"
        },
        "planning": {
            "name": "Planning Only",
            "team": [TeamMember.planner],
            "workflow_type": "individual",
            "step_type": "planning",
            "description": "Create development plan only"
        },
        "design": {
            "name": "Design Only",
            "team": [TeamMember.designer],
            "workflow_type": "individual",
            "step_type": "design",
            "description": "Create technical design only"
        },
        "implementation": {
            "name": "Implementation Only",
            "team": [TeamMember.coder],
            "workflow_type": "individual",
            "step_type": "implementation",
            "description": "Write code only"
        }
    }
    
    def __init__(self, verbose: bool = False):
        """Initialize the workflow runner.
        
        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
        
    def get_workflow_info(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a workflow type.
        
        Args:
            workflow_type: Type of workflow
            
        Returns:
            Workflow configuration or None if not found
        """
        return self.WORKFLOW_CONFIGS.get(workflow_type)
        
    def list_workflows(self) -> List[Tuple[str, str, str]]:
        """List all available workflows.
        
        Returns:
            List of (key, name, description) tuples
        """
        workflows = []
        for key, config in self.WORKFLOW_CONFIGS.items():
            workflows.append((key, config['name'], config['description']))
        return workflows
        
    async def run_workflow(self, 
                          requirements: str,
                          workflow_type: str = "tdd",
                          config: Optional[Dict[str, Any]] = None,
                          session_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Run a workflow with the given requirements.
        
        Args:
            requirements: Project requirements
            workflow_type: Type of workflow to run
            config: Optional configuration overrides
            session_id: Optional session ID for tracking
            
        Returns:
            Tuple of (success, result_data)
        """
        # Get workflow configuration
        workflow_config = self.get_workflow_info(workflow_type)
        if not workflow_config:
            return False, {"error": f"Unknown workflow type: {workflow_type}"}
            
        # Prepare configuration
        if config is None:
            config = {}
            
        # Create session ID if not provided
        if session_id is None:
            session_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Determine actual workflow type for special cases
        actual_workflow_type = workflow_config.get('workflow_type', workflow_type)
        
        # Create input
        input_data = CodingTeamInput(
            requirements=requirements,
            workflow_type=actual_workflow_type,
            team_members=workflow_config.get('team', []),
            step_type=workflow_config.get('step_type'),
            run_tests=config.get('run_tests', False),
            run_integration_verification=config.get('run_integration_verification', False)
        )
        
        # Create tracer for monitoring
        tracer = WorkflowExecutionTracer(session_id)
        
        try:
            if self.verbose:
                print(f"Starting {workflow_config['name']} workflow...")
                print(f"Session ID: {session_id}")
                
            # Execute workflow
            results, report = await execute_workflow(input_data, tracer)
            
            # Prepare result data
            result_data = {
                "session_id": session_id,
                "workflow_type": workflow_type,
                "success": True,
                "results": results,
                "report": report,
                "duration": report.total_duration_seconds if report else 0,
                "generated_path": self._find_generated_path(session_id)
            }
            
            return True, result_data
            
        except Exception as e:
            error_data = {
                "session_id": session_id,
                "workflow_type": workflow_type,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            if self.verbose:
                import traceback
                error_data["traceback"] = traceback.format_exc()
                
            return False, error_data
            
    def _find_generated_path(self, session_id: str) -> Optional[str]:
        """Find the generated code path for a session.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            Path to generated code or None
        """
        generated_dir = Path("generated")
        if not generated_dir.exists():
            return None
            
        # Look for directories containing the session ID or timestamp
        timestamp = session_id.split('_')[-1] if '_' in session_id else None
        
        for item in generated_dir.iterdir():
            if item.is_dir():
                if session_id in item.name or (timestamp and timestamp in item.name):
                    return str(item.absolute())
                    
        # Fallback: return the most recent directory
        app_dirs = [d for d in generated_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("app_generated_")]
        if app_dirs:
            latest = max(app_dirs, key=lambda d: d.stat().st_mtime)
            return str(latest.absolute())
            
        return None
        
    async def run_individual_step(self,
                                 requirements: str,
                                 step_type: str,
                                 previous_results: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Run an individual workflow step.
        
        Args:
            requirements: Project requirements
            step_type: Type of step (planning, design, implementation)
            previous_results: Results from previous steps
            
        Returns:
            Tuple of (success, result_data)
        """
        # Map step types to workflow types
        step_to_workflow = {
            "planning": "planning",
            "design": "design",
            "implementation": "implementation"
        }
        
        workflow_type = step_to_workflow.get(step_type)
        if not workflow_type:
            return False, {"error": f"Unknown step type: {step_type}"}
            
        # If we have previous results, append them to requirements
        if previous_results:
            enhanced_requirements = requirements
            if previous_results.get('planning'):
                enhanced_requirements += f"\n\nPlanning Output:\n{previous_results['planning']}"
            if previous_results.get('design'):
                enhanced_requirements += f"\n\nDesign Output:\n{previous_results['design']}"
            requirements = enhanced_requirements
            
        return await self.run_workflow(requirements, workflow_type)
        
    def estimate_duration(self, workflow_type: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Estimate workflow duration.
        
        Args:
            workflow_type: Type of workflow
            config: Optional configuration
            
        Returns:
            Estimated duration string
        """
        # Base estimates in minutes
        base_times = {
            "tdd": 3,
            "full": 2.5,
            "mvp_incremental": 5,
            "mvp_incremental_tdd": 7,
            "planning": 0.5,
            "design": 0.5,
            "implementation": 1
        }
        
        base_time = base_times.get(workflow_type, 3)
        
        if config:
            if config.get('run_tests'):
                base_time *= 1.2
            if config.get('run_integration_verification'):
                base_time *= 1.3
                
        return f"{int(base_time)}-{int(base_time * 1.5)} minutes"


# Convenience function for quick workflow execution
async def run_workflow(requirements: str, 
                      workflow_type: str = "tdd",
                      config: Optional[Dict[str, Any]] = None,
                      verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """Quick function to run a workflow.
    
    Args:
        requirements: Project requirements
        workflow_type: Type of workflow
        config: Optional configuration
        verbose: Whether to show verbose output
        
    Returns:
        Tuple of (success, result_data)
    """
    runner = WorkflowRunner(verbose=verbose)
    return await runner.run_workflow(requirements, workflow_type, config)