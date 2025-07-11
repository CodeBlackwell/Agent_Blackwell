"""Enhanced Flagship Orchestrator - Uses the new Enhanced TDD workflow by default"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
import sys

# Add paths for imports BEFORE any local imports
flagship_path = Path(__file__).parent
if str(flagship_path) not in sys.path:
    sys.path.insert(0, str(flagship_path))
if str(flagship_path / "workflows" / "tdd_orchestrator") not in sys.path:
    sys.path.insert(0, str(flagship_path / "workflows" / "tdd_orchestrator"))

# Now import after path is set
from workflows.tdd_orchestrator.enhanced_orchestrator import EnhancedTDDOrchestrator
from workflows.tdd_orchestrator.enhanced_models import (
    EnhancedTDDOrchestratorConfig, EnhancedFeatureResult,
    EnhancedTDDPhase
)

# Import original models for compatibility
from models.flagship_models import (
    TDDPhase, TDDWorkflowState, PhaseTransition, PhaseResult,
    TDDWorkflowConfig, TestStatus, TestResult, AgentType
)
from models.execution_tracer import ExecutionTracer, EventType
from utils.enhanced_file_manager import EnhancedFileManager


class FlagshipOrchestratorEnhanced:
    """Enhanced orchestrator that uses the new TDD workflow with planning phases"""
    
    def __init__(self, config: TDDWorkflowConfig = None, session_id: str = None, project_root: Path = None):
        self.session_id = session_id or f"tdd_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.tracer = ExecutionTracer(self.session_id)
        
        # Initialize file manager
        if project_root is None:
            project_root = Path(__file__).parent
        self.file_manager = EnhancedFileManager(self.session_id, project_root)
        
        # Convert config to enhanced config
        enhanced_config = self._convert_to_enhanced_config(config)
        
        # Initialize enhanced orchestrator
        self.enhanced_orchestrator = EnhancedTDDOrchestrator(enhanced_config)
        
        # For compatibility, maintain a state object
        self.state: Optional[TDDWorkflowState] = None
        
        # Store output for streaming
        self.output_buffer = []
        
    def _convert_to_enhanced_config(self, config: Optional[TDDWorkflowConfig]) -> EnhancedTDDOrchestratorConfig:
        """Convert original config to enhanced config"""
        enhanced_config = EnhancedTDDOrchestratorConfig()
        
        if config:
            # Copy over compatible settings
            enhanced_config.max_phase_retries = getattr(config, 'max_retries', 3)
            enhanced_config.max_total_retries = getattr(config, 'max_iterations', 10)
            enhanced_config.timeout_seconds = getattr(config, 'timeout_seconds', 300)
            enhanced_config.test_framework = getattr(config, 'test_framework', 'pytest')
            
        # Enable all enhanced features by default
        enhanced_config.enable_requirements_analysis = True
        enhanced_config.enable_architecture_planning = True
        enhanced_config.enable_feature_validation = True
        enhanced_config.multi_file_support = True
        enhanced_config.feature_based_implementation = True
        
        return enhanced_config
    
    async def run_tdd_workflow(self, requirements: str) -> TDDWorkflowState:
        """
        Run the enhanced TDD workflow for given requirements
        
        Args:
            requirements: The requirements to implement
            
        Returns:
            The final workflow state (converted from enhanced result)
        """
        # Initialize workflow state for compatibility
        self.state = TDDWorkflowState(
            current_phase=TDDPhase.RED,
            requirements=requirements
        )
        
        # Trace workflow start
        self.tracer.trace_event(
            EventType.WORKFLOW_START,
            data={
                "requirements": requirements,
                "enhanced": True,
                "phases": ["REQUIREMENTS", "ARCHITECTURE", "RED", "YELLOW", "GREEN", "VALIDATION"]
            }
        )
        
        self._output(f"\n{'='*80}")
        self._output(f"🚀 Starting Enhanced TDD Workflow")
        self._output(f"{'='*80}\n")
        self._output(f"Requirements: {requirements}\n")
        
        try:
            # Run the enhanced workflow
            result = await self.enhanced_orchestrator.execute_feature(requirements)
            
            # Convert result to workflow state
            self._update_state_from_result(result)
            
            # Trace workflow end
            self.tracer.trace_event(
                EventType.WORKFLOW_END,
                data={
                    "success": result.success,
                    "iterations": len(result.cycles),
                    "duration_seconds": result.total_duration_seconds
                }
            )
            
            # Display summary
            self._output(f"\n{'='*80}")
            self._output(f"📊 Workflow Summary")
            self._output(f"{'='*80}")
            self._output(f"✅ Success: {result.success}")
            self._output(f"⏱️  Duration: {result.total_duration_seconds:.2f} seconds")
            self._output(f"🔄 Cycles: {len(result.cycles)}")
            
            if result.expanded_requirements:
                self._output(f"📋 Features: {len(result.expanded_requirements.features)}")
            
            if result.generated_files:
                self._output(f"📁 Files Generated: {len(result.generated_files)}")
            
            # Save generated files
            if result.generated_files:
                self._save_generated_files(result.generated_files)
            
        except Exception as e:
            self.state.end_time = datetime.now()
            self._output(f"\n❌ Error: {str(e)}")
            raise
        
        return self.state
    
    def _update_state_from_result(self, result: EnhancedFeatureResult):
        """Update workflow state from enhanced result"""
        # Update state based on result
        self.state.all_tests_passing = result.success
        self.state.iteration_count = len(result.cycles)
        
        # Extract test code and implementation
        if result.final_tests:
            self.state.generated_tests = result.final_tests
        
        if result.final_code:
            self.state.generated_code = result.final_code
        
        # Set final phase
        if result.success:
            self.state.current_phase = TDDPhase.GREEN
        else:
            # Determine phase based on what failed
            if not result.cycles:
                self.state.current_phase = TDDPhase.RED
            elif not result.final_code:
                self.state.current_phase = TDDPhase.YELLOW
            else:
                self.state.current_phase = TDDPhase.GREEN
        
        # Set end time
        self.state.end_time = datetime.now()
        
        # Add phase results
        for cycle in result.cycles:
            for phase_result in cycle.phase_history:
                self.state.phase_results.append(phase_result)
        
        # Store enhanced result for detailed access
        self.state.enhanced_result = result
    
    def _save_generated_files(self, files: Dict[str, str]):
        """Save generated files to the file manager"""
        for filepath, content in files.items():
            # Use file manager to save in session directory
            self.file_manager.write_file(filepath, content)
            self._output(f"💾 Saved: {filepath}")
    
    def save_workflow_state(self):
        """Save the workflow state to file"""
        if not self.state:
            return
        
        # Create state summary
        state_data = {
            "session_id": self.session_id,
            "requirements": self.state.requirements,
            "success": self.state.all_tests_passing,
            "current_phase": self.state.current_phase.value,
            "iterations": self.state.iteration_count,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "end_time": self.state.end_time.isoformat() if self.state.end_time else None,
            "generated_tests": len(self.state.generated_tests) if self.state.generated_tests else 0,
            "generated_code": len(self.state.generated_code) if self.state.generated_code else 0
        }
        
        # Add enhanced details if available
        if hasattr(self.state, 'enhanced_result') and self.state.enhanced_result:
            result = self.state.enhanced_result
            state_data["enhanced"] = {
                "features": len(result.expanded_requirements.features) if result.expanded_requirements else 0,
                "files_generated": len(result.generated_files),
                "architecture_type": result.architecture.project_type if result.architecture else None,
                "validation_passed": result.validation_report.all_requirements_met if result.validation_report else None
            }
        
        # Save state
        state_file = self.file_manager.get_session_path() / "workflow_state.json"
        state_file.write_text(json.dumps(state_data, indent=2))
        
        # Also save detailed execution report from tracer
        self.tracer.save_report(self.file_manager.get_session_path())
    
    def _output(self, message: str):
        """Output message and store for streaming"""
        print(message)
        self.output_buffer.append({
            "type": "output",
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    async def stream_output(self) -> AsyncGenerator[str, None]:
        """Stream output as it's generated"""
        last_index = 0
        
        while True:
            # Yield new output
            for i in range(last_index, len(self.output_buffer)):
                yield json.dumps(self.output_buffer[i]) + "\n"
            last_index = len(self.output_buffer)
            
            # Check if workflow is complete
            if self.state and self.state.end_time:
                # Send completion message
                yield json.dumps({
                    "type": "complete",
                    "timestamp": datetime.now().isoformat(),
                    "success": self.state.all_tests_passing
                }) + "\n"
                break
            
            await asyncio.sleep(0.1)


# For backward compatibility, create an alias
FlagshipOrchestrator = FlagshipOrchestratorEnhanced