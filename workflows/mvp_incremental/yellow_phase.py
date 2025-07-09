"""
YELLOW Phase Orchestrator for MVP Incremental TDD Workflow

This module implements the YELLOW phase logic where tests are passing
but the implementation awaits review approval before transitioning to GREEN.
"""

import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeature
from workflows.mvp_incremental.test_execution import TestResult

logger = logging.getLogger(__name__)


class YellowPhaseError(Exception):
    """Raised when YELLOW phase validation or operations fail"""
    pass


@dataclass
class YellowPhaseContext:
    """Context information for YELLOW phase state"""
    feature: TestableFeature
    test_results: TestResult
    implementation_path: str
    time_entered_yellow: datetime
    review_attempts: int = 0
    previous_feedback: List[str] = field(default_factory=list)
    implementation_summary: Optional[str] = None
    test_coverage_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert context to dictionary for serialization"""
        return {
            "feature_id": self.feature.id,
            "feature_title": self.feature.title,
            "test_results": {
                "success": self.test_results.success,
                "test_count": len(self.test_results.logs) if self.test_results.logs else 0,
                "output_summary": self.test_results.stdout[:500] if self.test_results.stdout else ""
            },
            "implementation_path": self.implementation_path,
            "time_entered_yellow": self.time_entered_yellow.isoformat(),
            "review_attempts": self.review_attempts,
            "previous_feedback": self.previous_feedback,
            "implementation_summary": self.implementation_summary,
            "phase_duration_seconds": (datetime.now() - self.time_entered_yellow).total_seconds()
        }


class YellowPhaseOrchestrator:
    """Orchestrates YELLOW phase operations and state management"""
    
    def __init__(self, phase_tracker: TDDPhaseTracker):
        self.phase_tracker = phase_tracker
        self.yellow_contexts: Dict[str, YellowPhaseContext] = {}
        
    async def enter_yellow_phase(
        self,
        feature: TestableFeature,
        test_results: TestResult,
        implementation_path: str,
        implementation_summary: Optional[str] = None
    ) -> YellowPhaseContext:
        """
        Enter YELLOW phase after tests pass
        
        Args:
            feature: The testable feature
            test_results: Passing test results
            implementation_path: Path to implementation file
            implementation_summary: Optional summary of what was implemented
            
        Returns:
            YellowPhaseContext for the feature
            
        Raises:
            YellowPhaseError if validation fails
        """
        # Validate we can enter YELLOW phase
        await self._validate_yellow_entry(feature, test_results)
        
        # Create context
        context = YellowPhaseContext(
            feature=feature,
            test_results=test_results,
            implementation_path=implementation_path,
            time_entered_yellow=datetime.now(),
            implementation_summary=implementation_summary
        )
        
        # Store context
        self.yellow_contexts[feature.id] = context
        
        # Transition phase
        self.phase_tracker.transition_to(
            feature.id,
            TDDPhase.YELLOW,
            f"Tests passing - awaiting review. All {len(test_results.logs or [])} tests passed."
        )
        
        logger.info(f"Feature {feature.id} entered YELLOW phase - tests passing, awaiting review")
        
        return context
        
    async def _validate_yellow_entry(self, feature: TestableFeature, test_results: TestResult):
        """Validate that we can enter YELLOW phase"""
        # Check current phase
        current_phase = self.phase_tracker.get_current_phase(feature.id)
        if current_phase not in [TDDPhase.RED, TDDPhase.YELLOW]:
            raise YellowPhaseError(
                f"Cannot enter YELLOW phase from {current_phase.value}. "
                "Must be in RED or YELLOW phase."
            )
            
        # Verify tests are passing
        if not test_results.success:
            raise YellowPhaseError(
                "Cannot enter YELLOW phase with failing tests. "
                "Tests must pass before review."
            )
            
    def prepare_review_context(self, feature_id: str) -> Dict[str, Any]:
        """
        Prepare context information for code review
        
        Args:
            feature_id: The feature identifier
            
        Returns:
            Dictionary with review context information
        """
        if feature_id not in self.yellow_contexts:
            raise YellowPhaseError(f"No YELLOW phase context found for feature {feature_id}")
            
        context = self.yellow_contexts[feature_id]
        
        # Calculate time in YELLOW
        time_in_yellow = (datetime.now() - context.time_entered_yellow).total_seconds()
        
        review_context = {
            "feature": {
                "id": context.feature.id,
                "title": context.feature.title,
                "test_criteria": context.feature.test_criteria
            },
            "implementation": {
                "path": context.implementation_path,
                "summary": context.implementation_summary or "No summary provided"
            },
            "test_status": {
                "all_passing": context.test_results.success,
                "test_count": len(context.test_results.logs) if context.test_results.logs else 0,
                "execution_time": getattr(context.test_results, 'execution_time', 'Unknown')
            },
            "yellow_phase_info": {
                "time_in_phase_seconds": time_in_yellow,
                "review_attempts": context.review_attempts,
                "has_previous_feedback": len(context.previous_feedback) > 0
            },
            "previous_feedback": context.previous_feedback[-3:] if context.previous_feedback else []
        }
        
        return review_context
        
    async def handle_review_result(
        self,
        feature_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ) -> str:
        """
        Handle the result of a code review
        
        Args:
            feature_id: The feature identifier
            approved: Whether the review was approved
            feedback: Optional review feedback
            
        Returns:
            Next phase after handling review
        """
        if feature_id not in self.yellow_contexts:
            raise YellowPhaseError(f"No YELLOW phase context found for feature {feature_id}")
            
        context = self.yellow_contexts[feature_id]
        
        # Update review attempts
        context.review_attempts += 1
        
        # Store feedback if provided
        if feedback:
            context.previous_feedback.append(feedback)
            
        if approved:
            # Transition to GREEN
            self.phase_tracker.transition_to(
                feature_id,
                TDDPhase.GREEN,
                f"Implementation approved after {context.review_attempts} review(s)"
            )
            
            # Clean up context
            del self.yellow_contexts[feature_id]
            
            logger.info(f"Feature {feature_id} transitioned to GREEN phase - implementation approved")
            return TDDPhase.GREEN.value
            
        else:
            # Transition back to RED for rework
            self.phase_tracker.transition_to(
                feature_id,
                TDDPhase.RED,
                f"Implementation needs revision - review attempt {context.review_attempts}"
            )
            
            logger.info(f"Feature {feature_id} transitioned back to RED phase - revision needed")
            return TDDPhase.RED.value
            
    def get_phase_metrics(self, feature_id: str) -> Dict[str, Any]:
        """
        Get metrics for YELLOW phase
        
        Args:
            feature_id: The feature identifier
            
        Returns:
            Dictionary with phase metrics
        """
        if feature_id not in self.yellow_contexts:
            return {"error": "No YELLOW phase context found"}
            
        context = self.yellow_contexts[feature_id]
        time_in_yellow = (datetime.now() - context.time_entered_yellow).total_seconds()
        
        return {
            "feature_id": feature_id,
            "phase": TDDPhase.YELLOW.value,
            "time_in_phase_seconds": time_in_yellow,
            "time_in_phase_formatted": self._format_duration(time_in_yellow),
            "review_attempts": context.review_attempts,
            "has_feedback": len(context.previous_feedback) > 0,
            "feedback_count": len(context.previous_feedback)
        }
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
            
    def get_all_yellow_features(self) -> List[str]:
        """Get list of all features currently in YELLOW phase"""
        return list(self.yellow_contexts.keys())
        
    def clear_context(self, feature_id: str):
        """Clear YELLOW phase context for a feature"""
        if feature_id in self.yellow_contexts:
            del self.yellow_contexts[feature_id]