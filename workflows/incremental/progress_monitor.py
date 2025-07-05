"""
Enhanced progress monitoring and visualization for incremental development.
Provides real-time progress tracking, analytics, and visual representations.
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict


class ProgressState(Enum):
    """States of feature progress."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    RETRY = "retry"
    STAGNANT = "stagnant"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FeatureProgress:
    """Detailed progress tracking for a single feature."""
    feature_id: str
    feature_title: str
    state: ProgressState = ProgressState.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempts: int = 0
    validation_progress: float = 0.0  # 0-100%
    test_progress: Tuple[int, int] = (0, 0)  # (passed, total)
    lines_of_code: int = 0
    files_created: List[str] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    retry_strategy: Optional[str] = None
    
    def get_duration(self) -> Optional[timedelta]:
        """Get time spent on this feature."""
        if self.start_time:
            end = self.end_time or datetime.now()
            return end - self.start_time
        return None
    
    def get_success_rate(self) -> float:
        """Calculate success rate based on attempts."""
        if self.attempts == 0:
            return 0.0
        return (1.0 if self.state == ProgressState.COMPLETED else 0.0)
    
    def get_test_pass_rate(self) -> float:
        """Get test pass rate."""
        passed, total = self.test_progress
        if total == 0:
            return 0.0
        return (passed / total) * 100.0


@dataclass
class WorkflowProgress:
    """Overall workflow progress tracking."""
    workflow_id: str
    total_features: int
    start_time: datetime = field(default_factory=datetime.now)
    features: Dict[str, FeatureProgress] = field(default_factory=dict)
    
    def get_completed_count(self) -> int:
        """Count completed features."""
        return sum(1 for f in self.features.values() if f.state == ProgressState.COMPLETED)
    
    def get_failed_count(self) -> int:
        """Count failed features."""
        return sum(1 for f in self.features.values() if f.state == ProgressState.FAILED)
    
    def get_skipped_count(self) -> int:
        """Count skipped features."""
        return sum(1 for f in self.features.values() if f.state == ProgressState.SKIPPED)
    
    def get_in_progress_count(self) -> int:
        """Count in-progress features."""
        return sum(1 for f in self.features.values() 
                  if f.state in [ProgressState.IN_PROGRESS, ProgressState.VALIDATING, ProgressState.RETRY])
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_features == 0:
            return 0.0
        
        completed = self.get_completed_count()
        in_progress = self.get_in_progress_count()
        
        # In-progress features count as partial progress
        progress_points = completed + (in_progress * 0.5)
        return (progress_points / self.total_features) * 100.0
    
    def get_estimated_completion_time(self) -> Optional[datetime]:
        """Estimate completion time based on current velocity."""
        completed = self.get_completed_count()
        if completed == 0:
            return None
        
        elapsed = datetime.now() - self.start_time
        avg_time_per_feature = elapsed / completed
        
        remaining = self.total_features - completed - self.get_skipped_count()
        if remaining <= 0:
            return datetime.now()
        
        estimated_remaining = avg_time_per_feature * remaining
        return datetime.now() + estimated_remaining


class ProgressMonitor:
    """
    Monitors and visualizes incremental development progress.
    """
    
    def __init__(self, workflow_id: str, total_features: int):
        self.progress = WorkflowProgress(
            workflow_id=workflow_id,
            total_features=total_features
        )
        self.update_callbacks = []
        self.milestone_thresholds = [25, 50, 75, 90, 100]
        self.last_milestone = 0
    
    def start_feature(self, feature_id: str, feature_title: str):
        """Mark a feature as started."""
        self.progress.features[feature_id] = FeatureProgress(
            feature_id=feature_id,
            feature_title=feature_title,
            state=ProgressState.IN_PROGRESS,
            start_time=datetime.now()
        )
        self._notify_update("feature_started", feature_id)
    
    def update_feature(self, feature_id: str, **kwargs):
        """Update feature progress."""
        if feature_id not in self.progress.features:
            return
        
        feature = self.progress.features[feature_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(feature, key):
                setattr(feature, key, value)
        
        self._notify_update("feature_updated", feature_id)
    
    def complete_feature(self, feature_id: str, success: bool, 
                        files_created: List[str], lines_of_code: int):
        """Mark a feature as completed."""
        if feature_id not in self.progress.features:
            return
        
        feature = self.progress.features[feature_id]
        feature.state = ProgressState.COMPLETED if success else ProgressState.FAILED
        feature.end_time = datetime.now()
        feature.files_created = files_created
        feature.lines_of_code = lines_of_code
        
        self._notify_update("feature_completed", feature_id)
        self._check_milestones()
    
    def skip_feature(self, feature_id: str, reason: str):
        """Mark a feature as skipped."""
        if feature_id not in self.progress.features:
            self.progress.features[feature_id] = FeatureProgress(
                feature_id=feature_id,
                feature_title="Unknown",
                state=ProgressState.SKIPPED
            )
        else:
            feature = self.progress.features[feature_id]
            feature.state = ProgressState.SKIPPED
            feature.end_time = datetime.now()
            feature.last_error = reason
        
        self._notify_update("feature_skipped", feature_id)
    
    def record_retry(self, feature_id: str, retry_strategy: str, error: str):
        """Record a retry attempt."""
        if feature_id not in self.progress.features:
            return
        
        feature = self.progress.features[feature_id]
        feature.state = ProgressState.RETRY
        feature.attempts += 1
        feature.error_count += 1
        feature.last_error = error
        feature.retry_strategy = retry_strategy
        
        self._notify_update("retry_recorded", feature_id)
    
    def mark_stagnant(self, feature_id: str):
        """Mark a feature as stagnant."""
        if feature_id not in self.progress.features:
            return
        
        feature = self.progress.features[feature_id]
        feature.state = ProgressState.STAGNANT
        
        self._notify_update("feature_stagnant", feature_id)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary."""
        completed = self.get_completed_count()
        failed = self.get_failed_count()
        skipped = self.get_skipped_count()
        in_progress = self.get_in_progress_count()
        
        # Calculate metrics
        total_attempts = sum(f.attempts for f in self.progress.features.values())
        total_errors = sum(f.error_count for f in self.progress.features.values())
        total_loc = sum(f.lines_of_code for f in self.progress.features.values() 
                       if f.state == ProgressState.COMPLETED)
        
        # Get velocity
        elapsed = datetime.now() - self.progress.start_time
        velocity = completed / elapsed.total_seconds() * 3600 if elapsed.total_seconds() > 0 else 0
        
        return {
            "workflow_id": self.progress.workflow_id,
            "overall_progress": self.progress.get_overall_progress(),
            "features": {
                "total": self.progress.total_features,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "in_progress": in_progress,
                "not_started": self.progress.total_features - completed - failed - skipped - in_progress
            },
            "metrics": {
                "total_attempts": total_attempts,
                "total_errors": total_errors,
                "total_lines_of_code": total_loc,
                "average_attempts_per_feature": total_attempts / max(1, completed + failed),
                "velocity_per_hour": velocity
            },
            "time": {
                "elapsed": str(elapsed).split('.')[0],
                "estimated_completion": self.progress.get_estimated_completion_time(),
                "average_per_feature": str(elapsed / max(1, completed)).split('.')[0]
            }
        }
    
    def get_feature_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of feature progress."""
        timeline = []
        
        for feature_id, feature in self.progress.features.items():
            if feature.start_time:
                timeline.append({
                    "timestamp": feature.start_time.isoformat(),
                    "event": "started",
                    "feature_id": feature_id,
                    "feature_title": feature.feature_title
                })
            
            if feature.end_time:
                timeline.append({
                    "timestamp": feature.end_time.isoformat(),
                    "event": feature.state.value,
                    "feature_id": feature_id,
                    "feature_title": feature.feature_title,
                    "duration": str(feature.get_duration()).split('.')[0] if feature.get_duration() else None
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline
    
    def visualize_progress(self) -> str:
        """Generate ASCII visualization of progress."""
        completed = self.get_completed_count()
        failed = self.get_failed_count()
        skipped = self.get_skipped_count()
        in_progress = self.get_in_progress_count()
        not_started = self.progress.total_features - completed - failed - skipped - in_progress
        
        # Progress bar
        bar_width = 50
        progress_pct = self.progress.get_overall_progress()
        filled = int(bar_width * progress_pct / 100)
        
        visualization = []
        visualization.append(f"\n{'='*60}")
        visualization.append(f"INCREMENTAL DEVELOPMENT PROGRESS")
        visualization.append(f"{'='*60}")
        
        # Overall progress bar
        bar = '█' * filled + '░' * (bar_width - filled)
        visualization.append(f"\nOverall: [{bar}] {progress_pct:.1f}%")
        
        # Feature breakdown
        visualization.append(f"\nFeatures ({self.progress.total_features} total):")
        visualization.append(f"  ✅ Completed:   {completed:3d} ({completed/self.progress.total_features*100:.1f}%)")
        visualization.append(f"  ❌ Failed:      {failed:3d} ({failed/self.progress.total_features*100:.1f}%)")
        visualization.append(f"  ⏭️  Skipped:     {skipped:3d} ({skipped/self.progress.total_features*100:.1f}%)")
        visualization.append(f"  🔄 In Progress: {in_progress:3d} ({in_progress/self.progress.total_features*100:.1f}%)")
        visualization.append(f"  ⏸️  Not Started: {not_started:3d} ({not_started/self.progress.total_features*100:.1f}%)")
        
        # Time metrics
        elapsed = datetime.now() - self.progress.start_time
        eta = self.progress.get_estimated_completion_time()
        visualization.append(f"\nTime:")
        visualization.append(f"  ⏱️  Elapsed: {str(elapsed).split('.')[0]}")
        if eta:
            remaining = eta - datetime.now()
            visualization.append(f"  🎯 ETA: {eta.strftime('%H:%M:%S')} ({str(remaining).split('.')[0]} remaining)")
        
        # Current features in progress
        in_progress_features = [f for f in self.progress.features.values() 
                               if f.state in [ProgressState.IN_PROGRESS, ProgressState.RETRY]]
        if in_progress_features:
            visualization.append(f"\nCurrently working on:")
            for feature in in_progress_features[:3]:  # Show top 3
                state_icon = "🔄" if feature.state == ProgressState.RETRY else "🔨"
                visualization.append(f"  {state_icon} {feature.feature_title} (attempt {feature.attempts})")
        
        visualization.append(f"\n{'='*60}")
        
        return '\n'.join(visualization)
    
    def export_progress_data(self) -> str:
        """Export progress data as JSON."""
        data = {
            "summary": self.get_progress_summary(),
            "timeline": self.get_feature_timeline(),
            "features": {
                fid: {
                    "id": f.feature_id,
                    "title": f.feature_title,
                    "state": f.state.value,
                    "attempts": f.attempts,
                    "validation_progress": f.validation_progress,
                    "test_progress": {"passed": f.test_progress[0], "total": f.test_progress[1]},
                    "lines_of_code": f.lines_of_code,
                    "files_created": f.files_created,
                    "error_count": f.error_count,
                    "last_error": f.last_error,
                    "duration": str(f.get_duration()).split('.')[0] if f.get_duration() else None
                }
                for fid, f in self.progress.features.items()
            }
        }
        
        return json.dumps(data, indent=2, default=str)
    
    def _notify_update(self, event_type: str, feature_id: str):
        """Notify callbacks of progress updates."""
        for callback in self.update_callbacks:
            callback(event_type, feature_id, self.get_progress_summary())
    
    def _check_milestones(self):
        """Check if we've reached any milestones."""
        progress = self.progress.get_overall_progress()
        
        for milestone in self.milestone_thresholds:
            if progress >= milestone and self.last_milestone < milestone:
                self.last_milestone = milestone
                print(f"\n🎉 MILESTONE: {milestone}% complete!")
                self._notify_update("milestone_reached", str(milestone))
    
    def add_update_callback(self, callback):
        """Add a callback for progress updates."""
        self.update_callbacks.append(callback)
    
    def get_completed_count(self) -> int:
        """Delegate to workflow progress."""
        return self.progress.get_completed_count()
    
    def get_failed_count(self) -> int:
        """Delegate to workflow progress."""
        return self.progress.get_failed_count()
    
    def get_skipped_count(self) -> int:
        """Delegate to workflow progress."""
        return self.progress.get_skipped_count()
    
    def get_in_progress_count(self) -> int:
        """Delegate to workflow progress."""
        return self.progress.get_in_progress_count()