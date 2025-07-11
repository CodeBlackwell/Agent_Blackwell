"""Metrics Collector - tracks and reports TDD workflow metrics"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from .models import TDDPhase, FeatureResult, MetricsSnapshot


@dataclass
class SessionMetrics:
    """Metrics for a complete TDD session"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    features: List[FeatureResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    
    def add_feature(self, feature_result: FeatureResult):
        """Add a completed feature to the session"""
        self.features.append(feature_result)
    
    def complete(self):
        """Mark session as complete and calculate duration"""
        self.end_time = datetime.now()
        self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()


@dataclass
class FeatureMetrics:
    """Metrics for a single feature implementation"""
    feature_id: str
    feature_description: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    phase_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agent_invocations: int = 0
    total_attempts: int = 0
    success: bool = False
    
    def record_phase(self, phase: TDDPhase, duration: float, attempts: int, 
                    test_metrics: Dict[str, Any] = None):
        """Record metrics for a phase execution"""
        if phase.value not in self.phase_metrics:
            self.phase_metrics[phase.value] = {
                "executions": 0,
                "total_duration": 0.0,
                "total_attempts": 0,
                "test_metrics": []
            }
        
        metrics = self.phase_metrics[phase.value]
        metrics["executions"] += 1
        metrics["total_duration"] += duration
        metrics["total_attempts"] += attempts
        
        if test_metrics:
            metrics["test_metrics"].append(test_metrics)
    
    def complete(self, success: bool):
        """Complete the feature metrics"""
        self.end_time = datetime.now()
        self.success = success


class MetricsCollector:
    """Collects and analyzes metrics for TDD workflows"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionMetrics] = {}
        self.current_session: Optional[SessionMetrics] = None
        self.active_features: Dict[str, FeatureMetrics] = {}
        self.completed_features: List[FeatureMetrics] = []
        
        # Aggregate metrics
        self.global_metrics = {
            "total_sessions": 0,
            "total_features": 0,
            "successful_features": 0,
            "failed_features": 0,
            "phase_distribution": defaultdict(int),
            "average_cycle_time": 0.0,
            "success_rate": 0.0
        }
    
    def start_session(self, session_id: str) -> SessionMetrics:
        """Start a new metrics collection session"""
        session = SessionMetrics(session_id=session_id)
        self.sessions[session_id] = session
        self.current_session = session
        self.global_metrics["total_sessions"] += 1
        return session
    
    def complete_session(self) -> Optional[SessionMetrics]:
        """Complete the current session"""
        if not self.current_session:
            return None
        
        self.current_session.complete()
        
        # Update global metrics
        for feature in self.current_session.features:
            if feature.success:
                self.global_metrics["successful_features"] += 1
            else:
                self.global_metrics["failed_features"] += 1
        
        session = self.current_session
        self.current_session = None
        return session
    
    def start_feature(self, feature_id: str, description: str) -> FeatureMetrics:
        """Start tracking a new feature"""
        feature = FeatureMetrics(
            feature_id=feature_id,
            feature_description=description
        )
        self.active_features[feature_id] = feature
        self.global_metrics["total_features"] += 1
        return feature
    
    def complete_feature(self, feature_id: str, success: bool) -> Optional[FeatureMetrics]:
        """Complete tracking for a feature"""
        if feature_id not in self.active_features:
            return None
        
        feature = self.active_features[feature_id]
        feature.complete(success)
        
        # Move to completed list
        self.completed_features.append(feature)
        del self.active_features[feature_id]
        
        # Create FeatureResult for session
        if self.current_session:
            feature_result = FeatureResult(
                feature_id=feature_id,
                feature_description=feature.feature_description,
                success=success,
                cycles=[],  # Would be populated from actual cycle data
                total_duration_seconds=(feature.end_time - feature.start_time).total_seconds(),
                phase_metrics=feature.phase_metrics
            )
            self.current_session.add_feature(feature_result)
        
        # Update success rate
        total = self.global_metrics["successful_features"] + self.global_metrics["failed_features"]
        if total > 0:
            self.global_metrics["success_rate"] = self.global_metrics["successful_features"] / total
        
        return feature
    
    def record_phase_complete(self, feature_id: str, phase: TDDPhase, 
                            duration_seconds: float, attempts: int,
                            success: bool, agent_invocations: int = 0,
                            test_metrics: Dict[str, Any] = None):
        """Record completion of a TDD phase"""
        if feature_id not in self.active_features:
            return
        
        feature = self.active_features[feature_id]
        feature.record_phase(phase, duration_seconds, attempts, test_metrics)
        feature.agent_invocations += agent_invocations
        feature.total_attempts += attempts
        
        # Update global phase distribution
        self.global_metrics["phase_distribution"][phase.value] += 1
        
        # Update average cycle time
        self._update_average_cycle_time()
    
    def record_agent_invocation(self, feature_id: str, agent_name: str, 
                              duration_seconds: float, success: bool):
        """Record an agent invocation"""
        if feature_id in self.active_features:
            self.active_features[feature_id].agent_invocations += 1
    
    def get_feature_metrics(self, feature_id: str) -> Optional[FeatureMetrics]:
        """Get metrics for a specific feature"""
        # Check active features first
        if feature_id in self.active_features:
            return self.active_features[feature_id]
        
        # Check completed features
        for feature in self.completed_features:
            if feature.feature_id == feature_id:
                return feature
        
        return None
    
    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session"""
        return self.sessions.get(session_id)
    
    def get_current_snapshot(self) -> MetricsSnapshot:
        """Get a snapshot of current metrics"""
        phase_dist = dict(self.global_metrics["phase_distribution"])
        
        return MetricsSnapshot(
            timestamp=datetime.now(),
            active_features=len(self.active_features),
            completed_features=len(self.completed_features),
            failed_features=self.global_metrics["failed_features"],
            total_phases_executed=sum(phase_dist.values()),
            success_rate=self.global_metrics["success_rate"],
            average_cycle_time=self.global_metrics["average_cycle_time"],
            phase_distribution=phase_dist
        )
    
    def _update_average_cycle_time(self):
        """Update the average cycle time metric"""
        if not self.completed_features:
            return
        
        total_time = sum(
            (f.end_time - f.start_time).total_seconds() 
            for f in self.completed_features 
            if f.end_time
        )
        
        self.global_metrics["average_cycle_time"] = total_time / len(self.completed_features)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        report = {
            "summary": {
                "total_sessions": self.global_metrics["total_sessions"],
                "total_features": self.global_metrics["total_features"],
                "success_rate": f"{self.global_metrics['success_rate'] * 100:.1f}%",
                "average_cycle_time_minutes": self.global_metrics["average_cycle_time"] / 60
            },
            "phase_analysis": self._analyze_phases(),
            "failure_analysis": self._analyze_failures(),
            "performance_trends": self._analyze_trends()
        }
        
        return report
    
    def _analyze_phases(self) -> Dict[str, Any]:
        """Analyze phase execution patterns"""
        phase_dist = self.global_metrics["phase_distribution"]
        total_phases = sum(phase_dist.values())
        
        if total_phases == 0:
            return {"message": "No phase data available"}
        
        analysis = {
            "phase_percentages": {
                phase: (count / total_phases) * 100
                for phase, count in phase_dist.items()
            },
            "most_executed": max(phase_dist.items(), key=lambda x: x[1])[0] if phase_dist else None
        }
        
        # Calculate average attempts per phase
        for feature in self.completed_features:
            for phase, metrics in feature.phase_metrics.items():
                if "average_attempts" not in analysis:
                    analysis["average_attempts"] = {}
                
                current_avg = analysis["average_attempts"].get(phase, 0)
                new_avg = metrics["total_attempts"] / metrics["executions"]
                
                # Running average
                count = len([f for f in self.completed_features if phase in f.phase_metrics])
                analysis["average_attempts"][phase] = (current_avg * (count - 1) + new_avg) / count
        
        return analysis
    
    def _analyze_failures(self) -> Dict[str, Any]:
        """Analyze failure patterns"""
        failed_features = [f for f in self.completed_features if not f.success]
        
        if not failed_features:
            return {"message": "No failures to analyze"}
        
        analysis = {
            "total_failures": len(failed_features),
            "failure_rate": len(failed_features) / len(self.completed_features) * 100,
            "common_failure_phases": defaultdict(int)
        }
        
        # Find which phases commonly lead to failure
        for feature in failed_features:
            last_phase = list(feature.phase_metrics.keys())[-1] if feature.phase_metrics else "UNKNOWN"
            analysis["common_failure_phases"][last_phase] += 1
        
        analysis["common_failure_phases"] = dict(analysis["common_failure_phases"])
        
        return analysis
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.completed_features) < 5:
            return {"message": "Not enough data for trend analysis"}
        
        # Sort features by completion time
        sorted_features = sorted(
            [f for f in self.completed_features if f.end_time],
            key=lambda f: f.end_time
        )
        
        # Calculate moving average of cycle times
        window_size = min(5, len(sorted_features))
        moving_averages = []
        
        for i in range(window_size, len(sorted_features) + 1):
            window = sorted_features[i-window_size:i]
            avg_time = sum(
                (f.end_time - f.start_time).total_seconds() 
                for f in window
            ) / window_size
            moving_averages.append(avg_time / 60)  # Convert to minutes
        
        # Determine trend
        if len(moving_averages) >= 2:
            trend = "improving" if moving_averages[-1] < moving_averages[0] else "degrading"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_average_minutes": moving_averages[-1] if moving_averages else 0,
            "overall_improvement": f"{((moving_averages[0] - moving_averages[-1]) / moving_averages[0] * 100):.1f}%" if len(moving_averages) >= 2 and moving_averages[0] > 0 else "N/A"
        }