"""
Human Review Interface for Job Pipeline

This module provides a Streamlit-based UI for human review of milestone
deliverables from the job pipeline. It interfaces with the orchestrator
to provide feedback on PRs and milestone completions.

References the BeeAI Chat interface pattern from ACP examples.
"""

import os
import sys
import asyncio
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state.state_manager import StateManager, PipelineStage
from config.config import STREAMLIT_PORT


class ReviewApp:
    """
    Streamlit app for human review of pipeline deliverables.
    
    Provides interface for reviewing code, specs, and designs
    at pipeline milestone checkpoints, and submitting feedback.
    """
    
    def __init__(self):
        """Initialize the review app."""
        self.state_manager = StateManager()
        self.orchestrator_client = None  # Will hold ACP client to Orchestrator
        
    async def initialize(self):
        """Initialize state and connections."""
        # Load state from file
        await self.state_manager.load_state()
        
        # Initialize orchestrator client
        # Placeholder for connection setup
        pass
    
    def render_pipeline_list(self):
        """Render list of active pipelines."""
        st.header("Active Development Pipelines")
        
        # This would be populated from state_manager.pipelines
        pipelines = [
            {"id": "placeholder-1", "feature": "Example Feature", "stage": "Design"},
            {"id": "placeholder-2", "feature": "Another Feature", "stage": "Coding"}
        ]
        
        for pipe in pipelines:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(pipe["feature"])
            with col2:
                st.write(pipe["stage"])
            with col3:
                st.button("View", key=f"view_{pipe['id']}")
        
        # Add new pipeline button
        st.button("+ New Pipeline", key="new_pipeline")
    
    def render_pipeline_detail(self, pipeline_id: str):
        """
        Render detailed view of a pipeline.
        
        Args:
            pipeline_id: ID of the pipeline to view
        """
        st.header("Pipeline Detail")
        
        # Placeholder for pipeline details
        # This would be populated from state_manager.get_pipeline(pipeline_id)
        pipeline = {
            "feature": "Example Feature",
            "current_stage": "Design",
            "artifacts": {
                "planning": {"content": "Planning details..."},
                "specification": {"content": "Spec details..."},
                "design": {"content": "Design details..."}
            }
        }
        
        st.subheader(pipeline["feature"])
        st.write(f"Current Stage: {pipeline['current_stage']}")
        
        # Display tabs for stages
        tabs = st.tabs(["Planning", "Specification", "Design", "Code", "Review", "Test"])
        
        with tabs[0]:
            if "planning" in pipeline["artifacts"]:
                st.write(pipeline["artifacts"]["planning"]["content"])
                
        with tabs[1]:
            if "specification" in pipeline["artifacts"]:
                st.write(pipeline["artifacts"]["specification"]["content"])
                
        with tabs[2]:
            if "design" in pipeline["artifacts"]:
                st.write(pipeline["artifacts"]["design"]["content"])
        
        # Add feedback section if this is the current stage
        if pipeline["current_stage"] == "Design":
            st.subheader("Provide Feedback")
            feedback = st.text_area("Feedback")
            if st.button("Submit Feedback"):
                # This would call state_manager.add_human_feedback
                st.success("Feedback submitted")
                
            if st.button("Approve & Continue"):
                # This would call orchestrator to advance the pipeline
                st.success("Pipeline advancing to next stage")
    
    def run_app(self):
        """Run the Streamlit app."""
        st.title("Job Pipeline Review Dashboard")
        
        # Initialize session state
        if "page" not in st.session_state:
            st.session_state.page = "pipeline_list"
            
        if "selected_pipeline" not in st.session_state:
            st.session_state.selected_pipeline = None
        
        # Handle navigation
        if st.session_state.page == "pipeline_list":
            self.render_pipeline_list()
        elif st.session_state.page == "pipeline_detail":
            self.render_pipeline_detail(st.session_state.selected_pipeline)


# Main app initialization function (wrapped for async support)
def init_and_run_app():
    """Initialize and run the app."""
    app = ReviewApp()
    
    # Run initialization in a new event loop
    loop = asyncio.new_event_loop()
    loop.run_until_complete(app.initialize())
    
    # Run the Streamlit app
    app.run_app()


# Entry point when running this script directly
if __name__ == "__main__":
    init_and_run_app()
