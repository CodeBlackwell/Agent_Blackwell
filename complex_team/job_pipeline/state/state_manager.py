"""
State Manager for Job Pipeline

This module provides state tracking and persistence for the job pipeline,
managing multiple pipelines, feature sets, and their progress.

References the State Management pattern from ACP examples.
"""

import os
import json
import asyncio
from typing import Dict, List, Any
from enum import Enum
import time
import uuid


class PipelineStage(Enum):
    """Enum for pipeline stages."""
    PLANNING = "planning"
    SPECIFICATION = "specification"
    DESIGN = "design"
    CODING = "coding"
    REVIEW = "review" 
    TESTING = "testing"
    COMPLETE = "complete"


class PipelineState:
    """
    Data class for tracking the state of a single pipeline.
    
    Tracks a feature set through the development pipeline stages.
    """
    
    def __init__(self, pipeline_id: str, feature_name: str, repo_name: str):
        """
        Initialize a pipeline state.
        
        Args:
            pipeline_id: Unique identifier for this pipeline
            feature_name: Name of the feature being developed
            repo_name: Repository where code will be committed
        """
        self.pipeline_id = pipeline_id
        self.feature_name = feature_name
        self.repo_name = repo_name
        self.current_stage = PipelineStage.PLANNING
        self.branch_name = None
        self.artifacts = {}  # Stage -> artifact mapping
        self.status = "active"
        self.created_at = None
        self.updated_at = None
        self.human_feedback = {}  # Stage -> feedback mapping
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "pipeline_id": self.pipeline_id,
            "feature_name": self.feature_name,
            "repo_name": self.repo_name,
            "current_stage": self.current_stage.value,
            "branch_name": self.branch_name,
            "artifacts": self.artifacts,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "human_feedback": self.human_feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineState':
        """Create state from dictionary."""
        instance = cls(
            data["pipeline_id"],
            data["feature_name"],
            data["repo_name"]
        )
        instance.current_stage = PipelineStage(data["current_stage"])
        instance.branch_name = data["branch_name"]
        instance.artifacts = data["artifacts"]
        instance.status = data["status"]
        instance.created_at = data["created_at"]
        instance.updated_at = data["updated_at"]
        instance.human_feedback = data["human_feedback"]
        return instance


class StateManager:
    """
    State Manager for tracking and persisting pipeline states.
    
    Maintains the state of all active feature development pipelines
    and provides methods for updating and querying state.
    """
    
    def __init__(self, state_file_path: str = None):
        """
        Initialize the state manager.
        
        Args:
            state_file_path: Path to the state file for persistence
        """
        self.pipelines: Dict[str, PipelineState] = {}
        self.state_file_path = state_file_path or "pipeline_state.json"
        self.lock = asyncio.Lock()
    
    async def load_state(self):
        """Load state from file if it exists."""
        if not os.path.exists(self.state_file_path):
            return
            
        async with self.lock:
            try:
                with open(self.state_file_path, 'r') as f:
                    data = json.load(f)
                    
                self.pipelines = {
                    p_id: PipelineState.from_dict(p_data)
                    for p_id, p_data in data.items()
                }
            except Exception as e:
                print(f"Error loading state: {e}")
    
    async def save_state(self):
        """Save state to file."""
        async with self.lock:
            try:
                with open(self.state_file_path, 'w') as f:
                    json.dump(
                        {p_id: p.to_dict() for p_id, p in self.pipelines.items()},
                        f,
                        indent=2
                    )
            except Exception as e:
                print(f"Error saving state: {e}")
    
    async def create_pipeline(self, feature_name: str, repo_name: str) -> PipelineState:
        """
        Create a new pipeline for a feature.
        
        Args:
            feature_name: Name of the feature to develop
            repo_name: Repository to commit code to
            
        Returns:
            The created pipeline state
        """
        
        
        # Generate unique pipeline ID
        pipeline_id = str(uuid.uuid4())
        
        # Create new pipeline state
        pipeline_state = PipelineState(pipeline_id, feature_name, repo_name)
        pipeline_state.created_at = time.time()
        pipeline_state.updated_at = time.time()
        
        # Store in memory and save to file
        async with self.lock:
            self.pipelines[pipeline_id] = pipeline_state
            await self.save_state()
        
        return pipeline_state
    
    async def update_pipeline_stage(self, pipeline_id: str, stage: PipelineStage):
        """
        Update the stage of a pipeline.
        
        Args:
            pipeline_id: ID of the pipeline to update
            stage: New stage for the pipeline
        """
        
        async with self.lock:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = self.pipelines[pipeline_id]
            pipeline.current_stage = stage
            pipeline.updated_at = time.time()
            
            # Save updated state
            await self.save_state()
    
    async def update_stage_status(self, pipeline_id: str, stage: PipelineStage, status: str):
        """
        Update the status of a pipeline stage.
        
        Args:
            pipeline_id: Unique identifier for the pipeline
            stage: The pipeline stage to update
            status: New status for the stage
        """
        
        async with self.lock:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = self.pipelines[pipeline_id]
            
            # Update stage status with metadata
            stage_key = f"{stage.value}_status"
            if not hasattr(pipeline, 'stage_statuses'):
                pipeline.stage_statuses = {}
            
            pipeline.stage_statuses[stage_key] = {
                "status": status,
                "timestamp": time.time(),
                "stage": stage.value
            }
            
            # Update current stage if this is a progression
            if status == "running":
                pipeline.current_stage = stage
            
            pipeline.updated_at = time.time()
            
            # Save updated state
            await self.save_state()
    
    async def add_artifact(self, pipeline_id: str, stage: PipelineStage, artifact: Any):
        """
        Add an artifact to a pipeline stage.
        
        Args:
            pipeline_id: ID of the pipeline
            stage: Stage the artifact belongs to
            artifact: The artifact (specification, design doc, code, etc.)
        """
        
        async with self.lock:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = self.pipelines[pipeline_id]
            
            # Add artifact to stage
            stage_key = stage.value
            if stage_key not in pipeline.artifacts:
                pipeline.artifacts[stage_key] = []
            
            # Add artifact with metadata
            artifact_entry = {
                "content": artifact,
                "timestamp": time.time(),
                "stage": stage.value
            }
            
            pipeline.artifacts[stage_key].append(artifact_entry)
            pipeline.updated_at = time.time()
            
            # Save updated state
            await self.save_state()
    
    async def get_pipeline(self, pipeline_id: str) -> PipelineState:
        """
        Get a pipeline by ID.
        
        Args:
            pipeline_id: ID of the pipeline
            
        Returns:
            The pipeline state
        """
        async with self.lock:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            return self.pipelines[pipeline_id]
    
    async def add_human_feedback(self, pipeline_id: str, stage: PipelineStage, feedback: str):
        """
        Add human feedback to a pipeline stage.
        
        Args:
            pipeline_id: Unique identifier for the pipeline
            stage: The stage the feedback applies to
            feedback: Human feedback text
        """
        
        async with self.lock:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = self.pipelines[pipeline_id]
            
            # Add feedback with metadata
            feedback_entry = {
                "feedback": feedback,
                "timestamp": time.time(),
                "stage": stage.value,
                "reviewer": "human"  # In a real system, this would be the actual reviewer ID
            }
            
            stage_key = stage.value
            if stage_key not in pipeline.human_feedback:
                pipeline.human_feedback[stage_key] = []
            
            pipeline.human_feedback[stage_key].append(feedback_entry)
            pipeline.updated_at = time.time()
            
            # Save updated state
            await self.save_state()
