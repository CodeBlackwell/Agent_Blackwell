"""
Test suite for the enhanced full workflow implementation.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from workflows.full.enhanced_full_workflow import (
    EnhancedFullWorkflowConfig,
    WorkflowStateManager,
    AgentCommunicationEnhancer,
    execute_enhanced_full_workflow,
    execute_phase_with_retry
)
from workflows.full.phase_transition_manager import (
    PhaseTransitionManager,
    TransitionOrchestrator,
    TransitionStatus
)
from workflows.full.workflow_cache_manager import (
    WorkflowCacheManager,
    SmartCacheStrategy
)
from workflows.full.performance_monitor import PerformanceMonitor
from shared.data_models import CodingTeamInput, TeamMember, TeamMemberResult
from workflows.monitoring import WorkflowExecutionTracer


class TestEnhancedFullWorkflowConfig:
    """Test the enhanced workflow configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = EnhancedFullWorkflowConfig()
        assert config.max_review_retries == 3
        assert config.enable_rollback == True
        assert config.enable_parallel_execution == False
        assert config.retry_delays == [1, 2, 5]
        assert config.phase_timeout == 300
        assert config.enable_feedback_loop == True
        assert config.enable_context_enrichment == True
        assert config.skip_phases == []
        assert config.custom_validation_rules == {}
        assert config.enable_caching == True
        assert config.cache_ttl_multiplier == 1.0


class TestWorkflowStateManager:
    """Test the workflow state manager."""
    
    def test_save_checkpoint(self):
        """Test saving checkpoints."""
        manager = WorkflowStateManager()
        
        manager.save_checkpoint("planner", "test output", {"key": "value"})
        
        checkpoint = manager.get_checkpoint("planner")
        assert checkpoint is not None
        assert checkpoint["output"] == "test output"
        assert checkpoint["metadata"]["key"] == "value"
        assert "timestamp" in checkpoint
        
    def test_record_error(self):
        """Test error recording."""
        manager = WorkflowStateManager()
        
        error = Exception("Test error")
        manager.record_error("planner", error, {"phase": "planning"})
        
        assert len(manager.error_history) == 1
        assert manager.error_history[0]["phase"] == "planner"
        assert "Test error" in manager.error_history[0]["error"]
        
    def test_can_recover_from_error(self):
        """Test error recovery logic."""
        manager = WorkflowStateManager()
        
        # Should allow recovery initially
        assert manager.can_recover_from_error("planner") == True
        
        # Record 3 errors
        for i in range(3):
            manager.record_error("planner", Exception(f"Error {i}"), {})
            
        # Should not allow recovery after 3 errors
        assert manager.can_recover_from_error("planner") == False


class TestAgentCommunicationEnhancer:
    """Test the agent communication enhancer."""
    
    def test_prepare_agent_input_basic(self):
        """Test basic input preparation."""
        enhancer = AgentCommunicationEnhancer(enable_feedback=False, enable_context=False)
        
        result = enhancer.prepare_agent_input("planner", "Test input", {}, None)
        assert result == "Test input"
        
    def test_prepare_agent_input_with_context(self):
        """Test input preparation with context enrichment."""
        enhancer = AgentCommunicationEnhancer(enable_feedback=False, enable_context=True)
        
        previous_outputs = {"planner": "Previous plan output"}
        result = enhancer.prepare_agent_input("designer", "Design this", previous_outputs, None)
        
        assert "Plan Context:" in result
        assert "Previous plan output" in result
        assert "Design this" in result
        
    def test_prepare_agent_input_with_feedback(self):
        """Test input preparation with feedback."""
        enhancer = AgentCommunicationEnhancer(enable_feedback=True, enable_context=False)
        
        result = enhancer.prepare_agent_input("planner", "Test input", {}, "Fix this issue")
        
        assert "Previous Feedback:" in result
        assert "Fix this issue" in result


class TestPhaseTransitionManager:
    """Test the phase transition manager."""
    
    def test_start_transition(self):
        """Test starting a phase transition."""
        manager = PhaseTransitionManager()
        
        transition = manager.start_transition("planner", "designer", {"input": "test"})
        
        assert transition.from_phase == "planner"
        assert transition.to_phase == "designer"
        assert transition.status == TransitionStatus.IN_PROGRESS
        assert transition.input_data == {"input": "test"}
        
    def test_complete_transition(self):
        """Test completing a phase transition."""
        manager = PhaseTransitionManager()
        
        transition = manager.start_transition("planner", "designer", {"input": "test"})
        success = manager.complete_transition(transition, {"plan_output": "test plan"})
        
        assert success == True
        assert transition.status == TransitionStatus.COMPLETED
        assert transition.output_data == {"plan_output": "test plan"}
        
    def test_dependency_checking(self):
        """Test phase dependency checking."""
        manager = PhaseTransitionManager()
        
        # Should fail - designer needs planner
        transition = manager.start_transition("start", "designer", {})
        assert transition.status == TransitionStatus.FAILED
        
        # Complete planner phase
        planner_transition = manager.start_transition("start", "planner", {})
        manager.complete_transition(planner_transition, {"output": "plan"})
        
        # Now designer should work
        designer_transition = manager.start_transition("planner", "designer", {})
        assert designer_transition.status == TransitionStatus.IN_PROGRESS


class TestWorkflowCacheManager:
    """Test the workflow cache manager."""
    
    def test_cache_hit_miss(self):
        """Test cache hits and misses."""
        cache = WorkflowCacheManager(enable_cache=True, default_ttl=3600)
        
        # Initial miss
        assert cache.get("planner", "test input") is None
        assert cache.stats["misses"] == 1
        
        # Store value
        cache.set("planner", "test input", "cached output")
        
        # Cache hit
        result = cache.get("planner", "test input")
        assert result == "cached output"
        assert cache.stats["hits"] == 1
        
    def test_cache_expiration(self):
        """Test cache expiration."""
        cache = WorkflowCacheManager(enable_cache=True, default_ttl=1)
        
        cache.set("planner", "test input", "cached output")
        
        # Simulate time passing
        import time
        time.sleep(2)
        
        # Should be expired
        result = cache.get("planner", "test input")
        assert result is None
        assert cache.stats["expirations"] == 1
        
    def test_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = WorkflowCacheManager(enable_cache=True, max_cache_size=2)
        
        cache.set("planner", "input1", "output1")
        cache.set("planner", "input2", "output2")
        cache.set("planner", "input3", "output3")  # Should evict oldest
        
        assert len(cache.cache) == 2
        assert cache.stats["evictions"] == 1


class TestPerformanceMonitor:
    """Test the performance monitor."""
    
    def test_workflow_monitoring(self):
        """Test basic workflow monitoring."""
        monitor = PerformanceMonitor()
        
        # Start workflow
        workflow = monitor.start_workflow("test-workflow")
        assert workflow.workflow_id == "test-workflow"
        
        # Start phase
        phase = monitor.start_phase("planner")
        assert phase.phase_name == "planner"
        
        # Complete phase
        monitor.complete_phase(phase, success=True)
        assert phase.success == True
        assert phase.duration is not None
        
        # Complete workflow
        monitor.complete_workflow()
        assert workflow.end_time is not None
        
    def test_performance_report(self):
        """Test performance report generation."""
        monitor = PerformanceMonitor()
        
        workflow = monitor.start_workflow("test-workflow")
        phase = monitor.start_phase("planner")
        monitor.complete_phase(phase, success=True)
        monitor.complete_workflow()
        
        report = monitor.get_performance_report()
        assert report["workflow_id"] == "test-workflow"
        assert report["status"] == "completed"
        assert report["phase_count"] == 1
        assert report["error_count"] == 0


@pytest.mark.asyncio
class TestEnhancedFullWorkflow:
    """Integration tests for the enhanced full workflow."""
    
    async def test_basic_workflow_execution(self):
        """Test basic workflow execution with mocked agents."""
        # Create input
        input_data = CodingTeamInput(
            requirements="Build a Hello World API",
            workflow_type="enhanced_full",
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.coder, TeamMember.reviewer]
        )
        
        # Create config with short timeouts for testing
        config = EnhancedFullWorkflowConfig()
        config.phase_timeout = 10
        config.retry_delays = [0.1, 0.2]
        
        # Mock the agent execution
        with patch('core.migration.run_team_member_with_tracking') as mock_run:
            # Configure mock responses
            mock_run.side_effect = [
                "Plan: Create a simple API",
                "Design: REST API with /hello endpoint",
                "Code: from flask import Flask...",
                "Review: Code looks good"
            ]
            
            # Execute workflow
            results, report = await execute_enhanced_full_workflow(input_data, config)
            
            # Verify results
            assert len(results) == 4
            assert results[0].team_member == TeamMember.planner
            assert results[1].team_member == TeamMember.designer
            assert results[2].team_member == TeamMember.coder
            assert results[3].team_member == TeamMember.reviewer
            
            # Verify report
            assert report.workflow_type == "EnhancedFull"
            assert report.status == "completed"
            
    async def test_workflow_with_retry(self):
        """Test workflow with phase retry on failure."""
        input_data = CodingTeamInput(
            requirements="Build a Hello World API",
            workflow_type="enhanced_full",
            team_members=[TeamMember.planner]
        )
        
        config = EnhancedFullWorkflowConfig()
        config.retry_delays = [0.1]
        
        with patch('core.migration.run_team_member_with_tracking') as mock_run:
            # First call fails, second succeeds
            mock_run.side_effect = [
                Exception("Network error"),
                "Plan: Create API after retry"
            ]
            
            results, report = await execute_enhanced_full_workflow(input_data, config)
            
            assert len(results) == 1
            assert "retry" in results[0].output.lower()
            assert mock_run.call_count == 2
            
    async def test_workflow_with_caching(self):
        """Test workflow with caching enabled."""
        input_data = CodingTeamInput(
            requirements="Build a Hello World API",
            workflow_type="enhanced_full",
            team_members=[TeamMember.planner]
        )
        
        config = EnhancedFullWorkflowConfig()
        config.enable_caching = True
        
        with patch('core.migration.run_team_member_with_tracking') as mock_run:
            mock_run.return_value = "Cached plan output"
            
            # First execution
            results1, _ = await execute_enhanced_full_workflow(input_data, config)
            
            # Second execution should use cache
            results2, report = await execute_enhanced_full_workflow(input_data, config)
            
            # Agent should only be called once due to caching
            assert mock_run.call_count == 1
            assert results1[0].output == results2[0].output
            
    async def test_workflow_with_phase_skip(self):
        """Test workflow with phase skipping."""
        input_data = CodingTeamInput(
            requirements="Build a Hello World API",
            workflow_type="enhanced_full",
            team_members=[TeamMember.planner, TeamMember.designer, TeamMember.coder]
        )
        
        config = EnhancedFullWorkflowConfig()
        config.skip_phases = ["designer"]
        
        with patch('core.migration.run_team_member_with_tracking') as mock_run:
            mock_run.side_effect = [
                "Plan output",
                "Code output"  # Designer should be skipped
            ]
            
            results, _ = await execute_enhanced_full_workflow(input_data, config)
            
            # Should only have planner and coder results
            assert len(results) == 2
            assert results[0].team_member == TeamMember.planner
            assert results[1].team_member == TeamMember.coder


@pytest.mark.asyncio 
async def test_hello_world_api_validation():
    """Validate the enhanced workflow can handle a simple Hello World API request."""
    input_data = CodingTeamInput(
        requirements="Build a Hello World API with a single endpoint that returns 'Hello, World!' as JSON",
        workflow_type="enhanced_full",
        team_members=[TeamMember.planner, TeamMember.designer, TeamMember.coder, TeamMember.reviewer]
    )
    
    # Use default config
    config = EnhancedFullWorkflowConfig()
    
    # Mock the incremental coding phase
    with patch('workflows.incremental.feature_orchestrator.run_incremental_coding_phase') as mock_incremental:
        # Mock successful incremental execution
        mock_incremental.return_value = (
            """from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/hello')
def hello_world():
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(debug=True)
""",
            {
                "total_features": 1,
                "completed_features": 1,
                "success_rate": 100.0,
                "execution_time": 5.2
            }
        )
        
        # Mock other agent calls
        with patch('core.migration.run_team_member_with_tracking') as mock_run:
            mock_run.side_effect = [
                "Plan: Create a Flask API with a /hello endpoint that returns JSON",
                "Design: Simple REST API using Flask framework with single GET endpoint",
                "Review: Code is clean, follows best practices, ready for deployment"
            ]
            
            # Execute workflow
            results, report = await execute_enhanced_full_workflow(input_data, config)
            
            # Validate results
            assert len(results) == 4
            
            # Check planner output
            assert results[0].team_member == TeamMember.planner
            assert "Flask" in results[0].output
            
            # Check designer output  
            assert results[1].team_member == TeamMember.designer
            assert "REST API" in results[1].output
            
            # Check coder output
            assert results[2].team_member == TeamMember.coder
            assert "from flask import Flask" in results[2].output
            assert "@app.route('/hello')" in results[2].output
            assert "Hello, World!" in results[2].output
            
            # Check reviewer output
            assert results[3].team_member == TeamMember.reviewer
            assert "ready" in results[3].output.lower()
            
            # Validate report
            assert report.status == "completed"
            assert report.workflow_type == "EnhancedFull"
            assert "performance_metrics" in report.metadata
            
            # Check performance metrics were captured
            perf_metrics = report.metadata.get("performance_metrics", {})
            assert perf_metrics.get("phase_count", 0) > 0
            assert perf_metrics.get("error_count", 0) == 0
            
    print("✅ Hello World API validation test passed!")


if __name__ == "__main__":
    # Run the Hello World API validation test
    asyncio.run(test_hello_world_api_validation())