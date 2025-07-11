"""
Workflow runner for executing different workflow types.
"""
from typing import List, Tuple, Dict, Any
import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.workflow_manager import execute_workflow


class WorkflowRunner:
    """Runs workflows with proper configuration."""
    
    def __init__(self):
        self.workflow_types = {
            'tdd': ('Test-Driven Development', 'Write tests first, then implement'),
            'full': ('Full Workflow', 'Complete development workflow'),
            'mvp_incremental': ('MVP Incremental', 'Feature-by-feature development'),
            'mvp_incremental_tdd': ('MVP Incremental TDD', 'TDD with incremental features'),
            'individual': ('Individual Steps', 'Run specific workflow steps')
        }
        
    def list_workflows(self) -> List[Tuple[str, str, str]]:
        """List available workflows."""
        workflows = []
        for key, (name, desc) in self.workflow_types.items():
            workflows.append((key, name, desc))
        return workflows
        
    async def run_workflow(self, requirements: str, workflow_type: str, config: Dict[str, Any] = None):
        """Run a specific workflow."""
        if workflow_type not in self.workflow_types:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
        # Execute the workflow
        result = await execute_workflow(requirements, workflow_type, config or {})
        return result