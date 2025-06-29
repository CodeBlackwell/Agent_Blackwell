"""
Unit tests for the StateManager.

Tests the StateManager's ability to track pipeline states, manage persistence,
and handle concurrent access safely.
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state.state_manager import StateManager, PipelineState, PipelineStage


class TestPipelineState:
    """Test suite for PipelineState data class."""
    
    def test_pipeline_state_initialization(self):
        """Test PipelineState initialization."""
        pipeline_id = "test_pipeline_123"
        feature_name = "Test Feature"
        repo_name = "test_repo"
        
        state = PipelineState(pipeline_id, feature_name, repo_name)
        
        assert state.pipeline_id == pipeline_id
        assert state.feature_name == feature_name
        assert state.repo_name == repo_name
        assert state.current_stage == PipelineStage.PLANNING
        assert state.branch_name is None
        assert state.artifacts == {}
        assert state.status == "active"
        assert state.created_at is None
        assert state.updated_at is None
        assert state.human_feedback == {}
    
    def test_pipeline_state_to_dict(self):
        """Test PipelineState serialization to dictionary."""
        state = PipelineState("test_id", "Test Feature", "test_repo")
        state.branch_name = "feature/test"
        state.artifacts = {"specification": ["spec1", "spec2"]}
        state.human_feedback = {"design": ["feedback1"]}
        
        state_dict = state.to_dict()
        
        assert state_dict["pipeline_id"] == "test_id"
        assert state_dict["feature_name"] == "Test Feature"
        assert state_dict["repo_name"] == "test_repo"
        assert state_dict["current_stage"] == "planning"
        assert state_dict["branch_name"] == "feature/test"
        assert state_dict["artifacts"] == {"specification": ["spec1", "spec2"]}
        assert state_dict["human_feedback"] == {"design": ["feedback1"]}
    
    def test_pipeline_state_from_dict(self):
        """Test PipelineState deserialization from dictionary."""
        state_data = {
            "pipeline_id": "test_id",
            "feature_name": "Test Feature",
            "repo_name": "test_repo",
            "current_stage": "design",
            "branch_name": "feature/test",
            "artifacts": {"specification": ["spec1"]},
            "status": "active",
            "created_at": 1234567890,
            "updated_at": 1234567891,
            "human_feedback": {"design": ["feedback1"]}
        }
        
        state = PipelineState.from_dict(state_data)
        
        assert state.pipeline_id == "test_id"
        assert state.feature_name == "Test Feature"
        assert state.repo_name == "test_repo"
        assert state.current_stage == PipelineStage.DESIGN
        assert state.branch_name == "feature/test"
        assert state.artifacts == {"specification": ["spec1"]}
        assert state.status == "active"
        assert state.created_at == 1234567890
        assert state.updated_at == 1234567891
        assert state.human_feedback == {"design": ["feedback1"]}


class TestStateManager:
    """Test suite for StateManager functionality."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def state_manager(self, temp_state_file):
        """Create a StateManager instance for testing."""
        return StateManager(temp_state_file)
    
    @pytest.mark.asyncio
    async def test_create_pipeline(self, state_manager):
        """Test creating a new pipeline."""
        feature_name = "Test Feature"
        repo_name = "test_repo"
        
        pipeline_state = await state_manager.create_pipeline(feature_name, repo_name)
        
        assert pipeline_state.feature_name == feature_name
        assert pipeline_state.repo_name == repo_name
        assert pipeline_state.pipeline_id is not None
        assert pipeline_state.created_at is not None
        assert pipeline_state.updated_at is not None
        
        # Verify it's stored in the manager
        assert pipeline_state.pipeline_id in state_manager.pipelines
    
    @pytest.mark.asyncio
    async def test_update_pipeline_stage(self, state_manager):
        """Test updating pipeline stage."""
        # Create a pipeline first
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Update stage
        await state_manager.update_pipeline_stage(pipeline_id, PipelineStage.DESIGN)
        
        # Verify update
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert updated_state.current_stage == PipelineStage.DESIGN
        assert updated_state.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_pipeline_stage_not_found(self, state_manager):
        """Test updating stage for non-existent pipeline."""
        with pytest.raises(ValueError, match="Pipeline nonexistent not found"):
            await state_manager.update_pipeline_stage("nonexistent", PipelineStage.DESIGN)
    
    @pytest.mark.asyncio
    async def test_update_stage_status(self, state_manager):
        """Test updating stage status."""
        # Create a pipeline first
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Update stage status
        await state_manager.update_stage_status(pipeline_id, PipelineStage.SPECIFICATION, "running")
        
        # Verify update
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert hasattr(updated_state, 'stage_statuses')
        assert 'specification_status' in updated_state.stage_statuses
        assert updated_state.stage_statuses['specification_status']['status'] == "running"
        assert updated_state.stage_statuses['specification_status']['stage'] == "specification"
        assert updated_state.current_stage == PipelineStage.SPECIFICATION
    
    @pytest.mark.asyncio
    async def test_update_stage_status_not_found(self, state_manager):
        """Test updating stage status for non-existent pipeline."""
        with pytest.raises(ValueError, match="Pipeline nonexistent not found"):
            await state_manager.update_stage_status("nonexistent", PipelineStage.SPECIFICATION, "running")
    
    @pytest.mark.asyncio
    async def test_add_artifact(self, state_manager):
        """Test adding artifacts to pipeline."""
        # Create a pipeline first
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Add artifact
        artifact = {"type": "specification", "content": "Test specification"}
        await state_manager.add_artifact(pipeline_id, PipelineStage.SPECIFICATION, artifact)
        
        # Verify artifact was added
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert "specification" in updated_state.artifacts
        assert len(updated_state.artifacts["specification"]) == 1
        
        artifact_entry = updated_state.artifacts["specification"][0]
        assert artifact_entry["content"] == artifact
        assert artifact_entry["stage"] == "specification"
        assert "timestamp" in artifact_entry
    
    @pytest.mark.asyncio
    async def test_add_artifact_not_found(self, state_manager):
        """Test adding artifact to non-existent pipeline."""
        with pytest.raises(ValueError, match="Pipeline nonexistent not found"):
            await state_manager.add_artifact("nonexistent", PipelineStage.SPECIFICATION, {})
    
    @pytest.mark.asyncio
    async def test_get_pipeline(self, state_manager):
        """Test retrieving pipeline by ID."""
        # Create a pipeline first
        original_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = original_state.pipeline_id
        
        # Retrieve pipeline
        retrieved_state = await state_manager.get_pipeline(pipeline_id)
        
        assert retrieved_state.pipeline_id == original_state.pipeline_id
        assert retrieved_state.feature_name == original_state.feature_name
        assert retrieved_state.repo_name == original_state.repo_name
    
    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, state_manager):
        """Test retrieving non-existent pipeline."""
        with pytest.raises(ValueError, match="Pipeline nonexistent not found"):
            await state_manager.get_pipeline("nonexistent")
    
    @pytest.mark.asyncio
    async def test_add_human_feedback(self, state_manager):
        """Test adding human feedback to pipeline."""
        # Create a pipeline first
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Add feedback
        feedback = "This looks good, proceed with implementation"
        await state_manager.add_human_feedback(pipeline_id, PipelineStage.DESIGN, feedback)
        
        # Verify feedback was added
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert "design" in updated_state.human_feedback
        assert len(updated_state.human_feedback["design"]) == 1
        
        feedback_entry = updated_state.human_feedback["design"][0]
        assert feedback_entry["feedback"] == feedback
        assert feedback_entry["stage"] == "design"
        assert feedback_entry["reviewer"] == "human"
        assert "timestamp" in feedback_entry
    
    @pytest.mark.asyncio
    async def test_add_human_feedback_not_found(self, state_manager):
        """Test adding feedback to non-existent pipeline."""
        with pytest.raises(ValueError, match="Pipeline nonexistent not found"):
            await state_manager.add_human_feedback("nonexistent", PipelineStage.DESIGN, "feedback")
    
    @pytest.mark.asyncio
    async def test_save_and_load_state(self, temp_state_file):
        """Test state persistence to file."""
        # Create state manager and add some data
        state_manager1 = StateManager(temp_state_file)
        pipeline_state = await state_manager1.create_pipeline("Test Feature", "test_repo")
        await state_manager1.add_artifact(pipeline_state.pipeline_id, PipelineStage.SPECIFICATION, {"test": "data"})
        
        # Create new state manager and load from same file
        state_manager2 = StateManager(temp_state_file)
        await state_manager2.load_state()
        
        # Verify data was persisted and loaded
        assert pipeline_state.pipeline_id in state_manager2.pipelines
        loaded_state = state_manager2.pipelines[pipeline_state.pipeline_id]
        assert loaded_state.feature_name == "Test Feature"
        assert loaded_state.repo_name == "test_repo"
        assert "specification" in loaded_state.artifacts
    
    @pytest.mark.asyncio
    async def test_load_state_nonexistent_file(self, state_manager):
        """Test loading state when file doesn't exist."""
        # Should not raise an exception
        await state_manager.load_state()
        assert len(state_manager.pipelines) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, state_manager):
        """Test concurrent access to state manager."""
        async def create_pipeline(name):
            return await state_manager.create_pipeline(f"Feature {name}", "test_repo")
        
        # Create multiple pipelines concurrently
        tasks = [create_pipeline(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all pipelines were created
        assert len(results) == 5
        assert len(state_manager.pipelines) == 5
        
        # Verify all have unique IDs
        pipeline_ids = [r.pipeline_id for r in results]
        assert len(set(pipeline_ids)) == 5  # All unique
    
    @pytest.mark.asyncio
    async def test_multiple_artifacts_same_stage(self, state_manager):
        """Test adding multiple artifacts to the same stage."""
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Add multiple artifacts to same stage
        artifact1 = {"type": "spec", "content": "Specification 1"}
        artifact2 = {"type": "spec", "content": "Specification 2"}
        
        await state_manager.add_artifact(pipeline_id, PipelineStage.SPECIFICATION, artifact1)
        await state_manager.add_artifact(pipeline_id, PipelineStage.SPECIFICATION, artifact2)
        
        # Verify both artifacts are stored
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert len(updated_state.artifacts["specification"]) == 2
        
        contents = [entry["content"] for entry in updated_state.artifacts["specification"]]
        assert artifact1 in contents
        assert artifact2 in contents
    
    @pytest.mark.asyncio
    async def test_multiple_feedback_same_stage(self, state_manager):
        """Test adding multiple feedback entries to the same stage."""
        pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
        pipeline_id = pipeline_state.pipeline_id
        
        # Add multiple feedback entries
        feedback1 = "First review feedback"
        feedback2 = "Second review feedback"
        
        await state_manager.add_human_feedback(pipeline_id, PipelineStage.DESIGN, feedback1)
        await state_manager.add_human_feedback(pipeline_id, PipelineStage.DESIGN, feedback2)
        
        # Verify both feedback entries are stored
        updated_state = await state_manager.get_pipeline(pipeline_id)
        assert len(updated_state.human_feedback["design"]) == 2
        
        feedbacks = [entry["feedback"] for entry in updated_state.human_feedback["design"]]
        assert feedback1 in feedbacks
        assert feedback2 in feedbacks


class TestStateManagerIntegration:
    """Integration tests for StateManager."""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_lifecycle(self):
        """Test complete pipeline lifecycle from creation to completion."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            state_manager = StateManager(temp_path)
            
            # Create pipeline
            pipeline_state = await state_manager.create_pipeline("Complete Feature", "test_repo")
            pipeline_id = pipeline_state.pipeline_id
            
            # Simulate complete workflow
            stages = [
                PipelineStage.SPECIFICATION,
                PipelineStage.DESIGN,
                PipelineStage.CODING,
                PipelineStage.REVIEW,
                PipelineStage.TESTING
            ]
            
            for stage in stages:
                # Update to running
                await state_manager.update_stage_status(pipeline_id, stage, "running")
                
                # Add artifact
                artifact = {"stage": stage.value, "content": f"{stage.value} artifact"}
                await state_manager.add_artifact(pipeline_id, stage, artifact)
                
                # Add human feedback for review stages
                if stage in [PipelineStage.DESIGN, PipelineStage.REVIEW]:
                    feedback = f"Human feedback for {stage.value}"
                    await state_manager.add_human_feedback(pipeline_id, stage, feedback)
                
                # Update to completed
                await state_manager.update_stage_status(pipeline_id, stage, "completed")
                
                # Update pipeline stage
                await state_manager.update_pipeline_stage(pipeline_id, stage)
            
            # Verify final state
            final_state = await state_manager.get_pipeline(pipeline_id)
            assert final_state.current_stage == PipelineStage.TESTING
            
            # Verify all stages have artifacts
            for stage in stages:
                assert stage.value in final_state.artifacts
                assert len(final_state.artifacts[stage.value]) == 1
            
            # Verify human feedback for review stages
            assert "design" in final_state.human_feedback
            assert "review" in final_state.human_feedback
            
            # Verify stage statuses
            for stage in stages:
                running_key = f"{stage.value}_status"
                assert running_key in final_state.stage_statuses
                assert final_state.stage_statuses[running_key]["status"] == "completed"
            
            # Test persistence
            new_state_manager = StateManager(temp_path)
            await new_state_manager.load_state()
            
            loaded_state = await new_state_manager.get_pipeline(pipeline_id)
            assert loaded_state.current_stage == PipelineStage.TESTING
            assert len(loaded_state.artifacts) == 5
            assert len(loaded_state.human_feedback) == 2
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_error_handling_with_corrupted_state_file(self):
        """Test error handling when state file is corrupted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("This is not valid JSON")
            temp_path = f.name
        
        try:
            state_manager = StateManager(temp_path)
            
            # Should handle corrupted file gracefully
            await state_manager.load_state()
            
            # Should still be able to create new pipelines
            pipeline_state = await state_manager.create_pipeline("Test Feature", "test_repo")
            assert pipeline_state is not None
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
