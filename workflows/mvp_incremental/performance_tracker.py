"""
Performance Tracker for MVP Incremental Workflow

Tracks and reports performance metrics for all phases of the workflow.
"""

import time
import psutil
import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from workflows.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class PhaseMetrics:
    """Metrics for a single phase."""
    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: Optional[float] = None
    memory_peak: Optional[float] = None
    cpu_percent: Optional[float] = None
    sub_operations: Dict[str, float] = field(default_factory=dict)
    
    def complete(self):
        """Mark phase as complete and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        # Get memory usage
        process = psutil.Process(os.getpid())
        self.memory_peak = process.memory_info().rss / 1024 / 1024  # MB


@dataclass
class PerformanceReport:
    """Complete performance report for workflow."""
    session_id: str
    total_duration: float
    phase_metrics: List[PhaseMetrics]
    resource_usage: Dict[str, Any]
    bottlenecks: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "total_duration": self.total_duration,
            "phase_metrics": [
                {
                    "phase_name": pm.phase_name,
                    "duration": pm.duration,
                    "memory_peak_mb": pm.memory_peak,
                    "cpu_percent": pm.cpu_percent,
                    "sub_operations": pm.sub_operations
                }
                for pm in self.phase_metrics
            ],
            "resource_usage": self.resource_usage,
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


class PerformanceTracker:
    """Tracks performance metrics for MVP Incremental workflow."""
    
    # Performance targets (in seconds)
    TARGETS = {
        "phase_1_planning": 30,
        "phase_2_design": 45,
        "phase_3_feature_breakdown": 20,
        "phase_4_implementation": 180,  # 3 minutes
        "phase_5_initial_review": 60,
        "phase_6_fixes": 90,
        "phase_7_validation": 30,
        "phase_8_final_review": 45,
        "phase_9_test_execution": 120,  # 2 minutes
        "phase_10_integration": 60,
        "build_pipeline": 120,  # 2 minutes
        "config_management": 30,
        "total_workflow": 600  # 10 minutes
    }
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.workflow_start = time.time()
        self.phases: Dict[str, PhaseMetrics] = {}
        self.current_phase: Optional[str] = None
        self.sub_operation_start: Optional[float] = None
        
        # Resource tracking
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        
    def start_phase(self, phase_name: str):
        """Start tracking a phase."""
        logger.info(f"⏱️  Starting performance tracking for: {phase_name}")
        
        # Complete current phase if exists
        if self.current_phase:
            self.end_phase()
        
        # Start new phase
        self.current_phase = phase_name
        metrics = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
            memory_start=self.process.memory_info().rss / 1024 / 1024
        )
        self.phases[phase_name] = metrics
        
    def end_phase(self):
        """End tracking current phase."""
        if not self.current_phase:
            return
            
        phase = self.phases[self.current_phase]
        phase.complete()
        
        # Track CPU usage
        phase.cpu_percent = self.process.cpu_percent(interval=0.1)
        
        # Update peak memory
        if phase.memory_peak:
            self.peak_memory = max(self.peak_memory, phase.memory_peak)
        
        logger.info(
            f"⏱️  Completed {self.current_phase} in {phase.duration:.2f}s "
            f"(Memory: {phase.memory_peak:.1f}MB)"
        )
        
        self.current_phase = None
        
    def track_sub_operation(self, operation_name: str):
        """Track a sub-operation within current phase."""
        if self.current_phase and self.sub_operation_start:
            duration = time.time() - self.sub_operation_start
            self.phases[self.current_phase].sub_operations[operation_name] = duration
            
        self.sub_operation_start = time.time()
        
    def add_custom_metric(self, metric_name: str, value: float):
        """Add a custom metric to current phase."""
        if self.current_phase:
            self.phases[self.current_phase].sub_operations[metric_name] = value
            
    def generate_report(self) -> PerformanceReport:
        """Generate comprehensive performance report."""
        # Complete any ongoing phase
        if self.current_phase:
            self.end_phase()
            
        total_duration = time.time() - self.workflow_start
        
        # Analyze bottlenecks
        bottlenecks = self._identify_bottlenecks()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks)
        
        # Resource usage summary
        resource_usage = {
            "peak_memory_mb": self.peak_memory,
            "memory_growth_mb": self.peak_memory - self.initial_memory,
            "cpu_average": self._calculate_average_cpu(),
            "total_phases": len(self.phases)
        }
        
        return PerformanceReport(
            session_id=self.session_id,
            total_duration=total_duration,
            phase_metrics=list(self.phases.values()),
            resource_usage=resource_usage,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
        
    def _identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for phase_name, metrics in self.phases.items():
            if not metrics.duration:
                continue
                
            # Check against targets
            target_key = phase_name.lower().replace(" ", "_")
            if target_key in self.TARGETS:
                target = self.TARGETS[target_key]
                if metrics.duration > target * 1.5:  # 50% over target
                    bottlenecks.append(
                        f"{phase_name}: {metrics.duration:.1f}s "
                        f"(target: {target}s, {(metrics.duration/target-1)*100:.0f}% over)"
                    )
                    
            # Check memory usage
            if metrics.memory_peak and metrics.memory_start:
                memory_growth = metrics.memory_peak - metrics.memory_start
                if memory_growth > 100:  # More than 100MB growth
                    bottlenecks.append(
                        f"{phase_name}: Memory growth {memory_growth:.0f}MB"
                    )
                    
        # Check total duration
        total_duration = time.time() - self.workflow_start
        if total_duration > self.TARGETS["total_workflow"]:
            bottlenecks.append(
                f"Total workflow: {total_duration:.1f}s "
                f"(target: {self.TARGETS['total_workflow']}s)"
            )
            
        return bottlenecks
        
    def _generate_recommendations(self, bottlenecks: List[str]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check for slow phases
        slow_phases = [b for b in bottlenecks if "target:" in b]
        if slow_phases:
            recommendations.append(
                "Consider enabling caching for frequently accessed data"
            )
            
        # Check for memory issues
        memory_issues = [b for b in bottlenecks if "Memory growth" in b]
        if memory_issues:
            recommendations.append(
                "Review memory usage in phases with high growth"
            )
            recommendations.append(
                "Consider processing large files in chunks"
            )
            
        # Phase-specific recommendations
        for phase_name, metrics in self.phases.items():
            if metrics.duration and metrics.duration > 60:  # Phases over 1 minute
                if "implementation" in phase_name.lower():
                    recommendations.append(
                        "Enable parallel feature implementation for faster code generation"
                    )
                elif "test" in phase_name.lower():
                    recommendations.append(
                        "Use test parallelization to speed up test execution"
                    )
                elif "build" in phase_name.lower():
                    recommendations.append(
                        "Enable build caching and Docker layer caching"
                    )
                    
        # General recommendations
        if self.peak_memory > 2048:  # Over 2GB
            recommendations.append(
                "High memory usage detected. Consider increasing system resources"
            )
            
        return list(set(recommendations))  # Remove duplicates
        
    def _calculate_average_cpu(self) -> float:
        """Calculate average CPU usage across phases."""
        cpu_values = [
            phase.cpu_percent 
            for phase in self.phases.values() 
            if phase.cpu_percent is not None
        ]
        
        if cpu_values:
            return sum(cpu_values) / len(cpu_values)
        return 0.0
        
    def save_report(self, output_dir: Path):
        """Save performance report to file."""
        report = self.generate_report()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"performance_report_{self.session_id}.json"
        
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
            
        logger.info(f"📊 Performance report saved to: {report_path}")
        
        # Also log summary
        self._log_summary(report)
        
    def _log_summary(self, report: PerformanceReport):
        """Log performance summary."""
        logger.info("\n" + "="*60)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Duration: {report.total_duration:.1f}s")
        logger.info(f"Peak Memory: {report.resource_usage['peak_memory_mb']:.1f}MB")
        logger.info(f"Memory Growth: {report.resource_usage['memory_growth_mb']:.1f}MB")
        logger.info(f"Average CPU: {report.resource_usage['cpu_average']:.1f}%")
        
        if report.bottlenecks:
            logger.info("\n⚠️  Bottlenecks:")
            for bottleneck in report.bottlenecks:
                logger.info(f"  • {bottleneck}")
                
        if report.recommendations:
            logger.info("\n💡 Recommendations:")
            for rec in report.recommendations:
                logger.info(f"  • {rec}")
                
        logger.info("="*60)


# Singleton instance
_tracker_instance: Optional[PerformanceTracker] = None


def get_performance_tracker(session_id: str) -> PerformanceTracker:
    """Get or create performance tracker instance."""
    global _tracker_instance
    
    if _tracker_instance is None or _tracker_instance.session_id != session_id:
        _tracker_instance = PerformanceTracker(session_id)
        
    return _tracker_instance


def track_phase(phase_name: str):
    """Decorator to track phase performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            tracker = get_performance_tracker(kwargs.get("session_id", "default"))
            tracker.start_phase(phase_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                tracker.end_phase()
                
        def sync_wrapper(*args, **kwargs):
            tracker = get_performance_tracker(kwargs.get("session_id", "default"))
            tracker.start_phase(phase_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                tracker.end_phase()
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator