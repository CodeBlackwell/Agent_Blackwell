"""
GREEN Phase Orchestrator for MVP Incremental TDD Workflow

This module implements the GREEN phase of the TDD cycle where:
- Tests pass and code has been reviewed/approved
- Feature is marked as complete
- Success metrics are tracked
- Completion is confirmed
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeature

logger = logging.getLogger(__name__)


@dataclass
class GreenPhaseMetrics:
    """Metrics collected during GREEN phase completion"""
    feature_id: str
    feature_title: str
    red_phase_start: datetime
    yellow_phase_start: datetime
    green_phase_start: datetime
    green_phase_end: Optional[datetime] = None
    
    # Phase durations (in seconds)
    red_phase_duration: Optional[float] = None
    yellow_phase_duration: Optional[float] = None
    total_cycle_time: Optional[float] = None
    
    # Attempt counts
    implementation_attempts: int = 0
    review_attempts: int = 0
    test_execution_count: int = 0
    
    # Success indicators
    all_tests_passed: bool = False
    code_reviewed: bool = False
    code_approved: bool = False
    
    def calculate_durations(self):
        """Calculate phase durations once GREEN phase is complete"""
        if self.green_phase_end:
            self.red_phase_duration = (self.yellow_phase_start - self.red_phase_start).total_seconds()
            self.yellow_phase_duration = (self.green_phase_start - self.yellow_phase_start).total_seconds()
            self.total_cycle_time = (self.green_phase_end - self.red_phase_start).total_seconds()


@dataclass
class GreenPhaseContext:
    """Context for GREEN phase completion"""
    feature: TestableFeature
    metrics: GreenPhaseMetrics
    review_feedback: Optional[str] = None
    completion_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "feature_id": self.feature.id,
            "feature_title": self.feature.title,
            "metrics": {
                "cycle_time_seconds": self.metrics.total_cycle_time,
                "red_duration_seconds": self.metrics.red_phase_duration,
                "yellow_duration_seconds": self.metrics.yellow_phase_duration,
                "implementation_attempts": self.metrics.implementation_attempts,
                "review_attempts": self.metrics.review_attempts,
                "test_execution_count": self.metrics.test_execution_count,
            },
            "review_feedback": self.review_feedback,
            "completion_notes": self.completion_notes,
            "completed_at": self.metrics.green_phase_end.isoformat() if self.metrics.green_phase_end else None
        }


class GreenPhaseError(Exception):
    """Raised when GREEN phase validation fails"""
    pass


class GreenPhaseOrchestrator:
    """Orchestrates the GREEN phase of TDD cycle"""
    
    def __init__(self, phase_tracker: TDDPhaseTracker):
        self.phase_tracker = phase_tracker
        self.completed_features: List[GreenPhaseContext] = []
        
    def validate_green_phase_entry(self, feature: TestableFeature) -> None:
        """Validate that feature can enter GREEN phase"""
        current_phase = self.phase_tracker.get_current_phase(feature.id)
        
        if current_phase != TDDPhase.YELLOW:
            raise GreenPhaseError(
                f"Cannot enter GREEN phase from {current_phase.value}. "
                "Feature must be in YELLOW phase (tests passing, awaiting review)."
            )
            
        # Additional validations can be added here
        # e.g., check if review is actually approved
        
    def enter_green_phase(
        self, 
        feature: TestableFeature,
        metrics: GreenPhaseMetrics,
        review_approved: bool,
        review_feedback: Optional[str] = None
    ) -> GreenPhaseContext:
        """Enter GREEN phase for a feature"""
        # Validate entry
        self.validate_green_phase_entry(feature)
        
        if not review_approved:
            raise GreenPhaseError(
                "Cannot enter GREEN phase without review approval. "
                "Code must be reviewed and approved first."
            )
        
        # Update metrics
        metrics.green_phase_start = datetime.now()
        metrics.code_reviewed = True
        metrics.code_approved = review_approved
        metrics.all_tests_passed = True  # Must be true to reach GREEN
        
        # Transition to GREEN phase
        self.phase_tracker.transition_to_phase(feature.id, TDDPhase.GREEN)
        
        logger.info(f"🟢 Feature '{feature.title}' entered GREEN phase")
        
        # Create context
        context = GreenPhaseContext(
            feature=feature,
            metrics=metrics,
            review_feedback=review_feedback,
            completion_notes=[]
        )
        
        return context
        
    def complete_feature(
        self, 
        context: GreenPhaseContext,
        completion_notes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mark feature as complete in GREEN phase"""
        # Verify still in GREEN phase
        current_phase = self.phase_tracker.get_current_phase(context.feature.id)
        if current_phase != TDDPhase.GREEN:
            raise GreenPhaseError(
                f"Cannot complete feature - not in GREEN phase (current: {current_phase.value})"
            )
        
        # Update completion time and calculate durations
        context.metrics.green_phase_end = datetime.now()
        context.metrics.calculate_durations()
        
        # Add completion notes
        if completion_notes:
            context.completion_notes.extend(completion_notes)
            
        # Add to completed features
        self.completed_features.append(context)
        
        # Log success
        logger.info(
            f"✅ Feature '{context.feature.title}' completed successfully! "
            f"Total cycle time: {context.metrics.total_cycle_time:.1f}s"
        )
        
        # Generate completion summary
        return self._generate_completion_summary(context)
        
    def _generate_completion_summary(self, context: GreenPhaseContext) -> Dict[str, Any]:
        """Generate a summary of the completed feature"""
        summary = {
            "status": "completed",
            "feature": context.to_dict(),
            "success_indicators": {
                "tdd_cycle_complete": True,
                "tests_written_first": True,
                "tests_failed_initially": True,
                "implementation_guided_by_tests": True,
                "code_reviewed": context.metrics.code_reviewed,
                "code_approved": context.metrics.code_approved,
            },
            "phase_progression": {
                "RED": {
                    "duration_seconds": context.metrics.red_phase_duration,
                    "description": "Tests written and confirmed to fail"
                },
                "YELLOW": {
                    "duration_seconds": context.metrics.yellow_phase_duration,
                    "description": "Implementation complete, tests passing"
                },
                "GREEN": {
                    "duration_seconds": (
                        (context.metrics.green_phase_end - context.metrics.green_phase_start).total_seconds()
                        if context.metrics.green_phase_end else None
                    ),
                    "description": "Code reviewed and approved"
                }
            },
            "celebration_message": self._get_celebration_message(context)
        }
        
        return summary
        
    def _get_celebration_message(self, context: GreenPhaseContext) -> str:
        """Generate a celebration message based on metrics"""
        time = context.metrics.total_cycle_time
        attempts = context.metrics.implementation_attempts
        
        if time < 300:  # Less than 5 minutes
            time_msg = "Lightning fast!"
        elif time < 900:  # Less than 15 minutes
            time_msg = "Great pace!"
        else:
            time_msg = "Well done!"
            
        if attempts == 1:
            attempt_msg = "First try success! "
        elif attempts <= 3:
            attempt_msg = "Good iteration! "
        else:
            attempt_msg = "Persistence pays off! "
            
        return f"🎉 {attempt_msg}{time_msg} Feature completed with TDD!"
        
    def get_completion_report(self) -> Dict[str, Any]:
        """Generate a report of all completed features"""
        if not self.completed_features:
            return {
                "total_features": 0,
                "message": "No features completed yet"
            }
            
        total_time = sum(
            ctx.metrics.total_cycle_time or 0 
            for ctx in self.completed_features
        )
        
        avg_time = total_time / len(self.completed_features) if self.completed_features else 0
        
        return {
            "total_features": len(self.completed_features),
            "total_cycle_time_seconds": total_time,
            "average_cycle_time_seconds": avg_time,
            "features": [ctx.to_dict() for ctx in self.completed_features],
            "summary": {
                "fastest_feature": min(
                    self.completed_features,
                    key=lambda x: x.metrics.total_cycle_time or float('inf')
                ).feature.title if self.completed_features else None,
                "most_attempts": max(
                    self.completed_features,
                    key=lambda x: x.metrics.implementation_attempts
                ).feature.title if self.completed_features else None,
            }
        }
        
    def reset_metrics(self):
        """Reset completed features (useful for testing)"""
        self.completed_features.clear()