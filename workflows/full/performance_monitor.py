"""
Performance monitoring for full workflow execution.
"""
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""
    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    memory_delta: Optional[int] = None
    success: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark phase as complete and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error


@dataclass 
class WorkflowMetrics:
    """Aggregated metrics for entire workflow execution."""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    phase_metrics: List[PhaseMetrics] = field(default_factory=list)
    agent_call_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cache_stats: Dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    retry_count: int = 0
    
    def complete(self):
        """Mark workflow as complete."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        self.error_count = sum(1 for p in self.phase_metrics if not p.success)
        self.retry_count = sum(p.retry_count for p in self.phase_metrics)


class PerformanceMonitor:
    """Monitors and analyzes workflow performance."""
    
    def __init__(self):
        self.current_workflow: Optional[WorkflowMetrics] = None
        self.historical_metrics: List[WorkflowMetrics] = []
        self.phase_benchmarks: Dict[str, List[float]] = defaultdict(list)
        self.alerts: List[Dict[str, Any]] = []
        
    def start_workflow(self, workflow_id: str) -> WorkflowMetrics:
        """Start monitoring a new workflow."""
        self.current_workflow = WorkflowMetrics(
            workflow_id=workflow_id,
            start_time=time.time()
        )
        return self.current_workflow
        
    def start_phase(self, phase_name: str, cache_hit: bool = False) -> PhaseMetrics:
        """Start monitoring a phase."""
        metrics = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
            cache_hit=cache_hit
        )
        
        if self.current_workflow:
            self.current_workflow.phase_metrics.append(metrics)
            
        # Track memory usage if available
        try:
            import psutil
            process = psutil.Process()
            metrics.memory_before = process.memory_info().rss
        except ImportError:
            pass
            
        return metrics
        
    def complete_phase(self, metrics: PhaseMetrics, success: bool = True, error: Optional[str] = None):
        """Complete phase monitoring."""
        metrics.complete(success, error)
        
        # Track memory usage
        try:
            import psutil
            process = psutil.Process()
            metrics.memory_after = process.memory_info().rss
            if metrics.memory_before:
                metrics.memory_delta = metrics.memory_after - metrics.memory_before
        except ImportError:
            pass
            
        # Update benchmarks
        if success and metrics.duration:
            self.phase_benchmarks[metrics.phase_name].append(metrics.duration)
            
        # Check for performance anomalies
        self._check_performance_anomalies(metrics)
        
    def complete_workflow(self):
        """Complete workflow monitoring."""
        if self.current_workflow:
            self.current_workflow.complete()
            self.historical_metrics.append(self.current_workflow)
            
            # Analyze overall performance
            self._analyze_workflow_performance(self.current_workflow)
            
    def record_agent_call(self, agent_name: str):
        """Record an agent call."""
        if self.current_workflow:
            self.current_workflow.agent_call_count[agent_name] += 1
            
    def update_cache_stats(self, cache_stats: Dict[str, int]):
        """Update cache statistics."""
        if self.current_workflow:
            self.current_workflow.cache_stats.update(cache_stats)
            
    def _check_performance_anomalies(self, metrics: PhaseMetrics):
        """Check for performance anomalies in phase execution."""
        if not metrics.duration:
            return
            
        # Check against historical benchmarks
        if metrics.phase_name in self.phase_benchmarks:
            benchmarks = self.phase_benchmarks[metrics.phase_name]
            if len(benchmarks) >= 5:
                avg_duration = statistics.mean(benchmarks[-5:])
                std_dev = statistics.stdev(benchmarks[-5:]) if len(benchmarks) > 1 else 0
                
                # Alert if duration is 2 standard deviations above average
                if metrics.duration > avg_duration + (2 * std_dev):
                    self.alerts.append({
                        "type": "slow_phase",
                        "phase": metrics.phase_name,
                        "duration": metrics.duration,
                        "expected": avg_duration,
                        "timestamp": datetime.now().isoformat()
                    })
                    
        # Check memory usage
        if metrics.memory_delta and metrics.memory_delta > 100 * 1024 * 1024:  # 100MB
            self.alerts.append({
                "type": "high_memory",
                "phase": metrics.phase_name,
                "memory_increase_mb": metrics.memory_delta / (1024 * 1024),
                "timestamp": datetime.now().isoformat()
            })
            
    def _analyze_workflow_performance(self, workflow: WorkflowMetrics):
        """Analyze overall workflow performance."""
        if not workflow.total_duration:
            return
            
        # Check total duration against historical average
        if len(self.historical_metrics) >= 5:
            recent_durations = [w.total_duration for w in self.historical_metrics[-5:] if w.total_duration]
            if recent_durations:
                avg_duration = statistics.mean(recent_durations)
                
                if workflow.total_duration > avg_duration * 1.5:
                    self.alerts.append({
                        "type": "slow_workflow",
                        "workflow_id": workflow.workflow_id,
                        "duration": workflow.total_duration,
                        "expected": avg_duration,
                        "timestamp": datetime.now().isoformat()
                    })
                    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        if not self.current_workflow:
            return {"error": "No workflow being monitored"}
            
        workflow = self.current_workflow
        
        # Calculate phase statistics
        phase_stats = {}
        for phase_name, durations in self.phase_benchmarks.items():
            if durations:
                phase_stats[phase_name] = {
                    "avg_duration": statistics.mean(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "execution_count": len(durations)
                }
                
        # Calculate cache effectiveness
        cache_hit_rate = 0
        if workflow.cache_stats:
            total_requests = workflow.cache_stats.get("hits", 0) + workflow.cache_stats.get("misses", 0)
            if total_requests > 0:
                cache_hit_rate = workflow.cache_stats.get("hits", 0) / total_requests * 100
                
        report = {
            "workflow_id": workflow.workflow_id,
            "status": "in_progress" if workflow.end_time is None else "completed",
            "duration": workflow.total_duration or (time.time() - workflow.start_time),
            "phase_count": len(workflow.phase_metrics),
            "error_count": workflow.error_count,
            "retry_count": workflow.retry_count,
            "phase_statistics": phase_stats,
            "agent_calls": dict(workflow.agent_call_count),
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "cache_stats": workflow.cache_stats,
            "recent_alerts": self.alerts[-10:],  # Last 10 alerts
            "phase_breakdown": self._get_phase_breakdown(workflow)
        }
        
        return report
        
    def _get_phase_breakdown(self, workflow: WorkflowMetrics) -> List[Dict[str, Any]]:
        """Get detailed breakdown of phase execution."""
        breakdown = []
        
        for phase in workflow.phase_metrics:
            breakdown.append({
                "phase": phase.phase_name,
                "duration": phase.duration,
                "success": phase.success,
                "cache_hit": phase.cache_hit,
                "retry_count": phase.retry_count,
                "memory_delta_mb": (phase.memory_delta / (1024 * 1024)) if phase.memory_delta else None,
                "error": phase.error
            })
            
        return breakdown
        
    def get_optimization_suggestions(self) -> List[str]:
        """Get suggestions for optimizing workflow performance."""
        suggestions = []
        
        if not self.current_workflow:
            return suggestions
            
        workflow = self.current_workflow
        
        # Check cache utilization
        if workflow.cache_stats:
            hit_rate = workflow.cache_stats.get("hits", 0) / max(1, workflow.cache_stats.get("hits", 0) + workflow.cache_stats.get("misses", 0))
            if hit_rate < 0.3:
                suggestions.append("Consider enabling or tuning cache settings - current hit rate is below 30%")
                
        # Check for frequent retries
        if workflow.retry_count > len(workflow.phase_metrics):
            suggestions.append("High retry rate detected - consider adjusting timeout or error handling")
            
        # Check for slow phases
        for phase_name, durations in self.phase_benchmarks.items():
            if durations and len(durations) >= 3:
                avg_duration = statistics.mean(durations)
                if avg_duration > 30:  # More than 30 seconds
                    suggestions.append(f"Phase '{phase_name}' averages {avg_duration:.1f}s - consider optimization")
                    
        # Check memory usage
        total_memory_increase = sum(
            p.memory_delta for p in workflow.phase_metrics 
            if p.memory_delta and p.memory_delta > 0
        )
        if total_memory_increase > 500 * 1024 * 1024:  # 500MB
            suggestions.append(f"High memory usage detected ({total_memory_increase / (1024*1024):.0f}MB increase)")
            
        return suggestions