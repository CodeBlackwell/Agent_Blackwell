"""
Unit tests for Performance Tracker
"""

import pytest
import time
import tempfile
from pathlib import Path
from workflows.mvp_incremental.performance_tracker import (
    PerformanceTracker, PhaseMetrics, PerformanceReport,
    get_performance_tracker, track_phase
)


class TestPerformanceTracker:
    
    def test_initialization(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker("test_session_123")
        
        assert tracker.session_id == "test_session_123"
        assert tracker.workflow_start > 0
        assert len(tracker.phases) == 0
        assert tracker.current_phase is None
        assert tracker.initial_memory > 0
        
    def test_phase_tracking(self):
        """Test phase start and end tracking."""
        tracker = PerformanceTracker("test_session")
        
        # Start a phase
        tracker.start_phase("Test Phase 1")
        assert tracker.current_phase == "Test Phase 1"
        assert "Test Phase 1" in tracker.phases
        
        # Simulate some work
        time.sleep(0.1)
        
        # End the phase
        tracker.end_phase()
        assert tracker.current_phase is None
        
        # Check metrics
        phase = tracker.phases["Test Phase 1"]
        assert phase.duration is not None
        assert phase.duration >= 0.1
        assert phase.memory_peak is not None
        assert phase.cpu_percent is not None
        
    def test_multiple_phases(self):
        """Test tracking multiple phases."""
        tracker = PerformanceTracker("test_session")
        
        # Track multiple phases
        phases = ["Planning", "Implementation", "Testing"]
        
        for phase_name in phases:
            tracker.start_phase(phase_name)
            time.sleep(0.05)
            tracker.end_phase()
            
        assert len(tracker.phases) == 3
        for phase_name in phases:
            assert phase_name in tracker.phases
            assert tracker.phases[phase_name].duration >= 0.05
            
    def test_sub_operations(self):
        """Test tracking sub-operations within phases."""
        tracker = PerformanceTracker("test_session")
        
        tracker.start_phase("Complex Phase")
        
        # Track sub-operations
        tracker.track_sub_operation("parsing")
        time.sleep(0.05)
        tracker.track_sub_operation("validation")
        time.sleep(0.05)
        tracker.track_sub_operation("generation")
        
        tracker.end_phase()
        
        phase = tracker.phases["Complex Phase"]
        assert "validation" in phase.sub_operations
        assert phase.sub_operations["validation"] >= 0.05
        
    def test_custom_metrics(self):
        """Test adding custom metrics."""
        tracker = PerformanceTracker("test_session")
        
        tracker.start_phase("Metric Phase")
        tracker.add_custom_metric("lines_processed", 1000)
        tracker.add_custom_metric("files_generated", 15)
        tracker.end_phase()
        
        phase = tracker.phases["Metric Phase"]
        assert phase.sub_operations["lines_processed"] == 1000
        assert phase.sub_operations["files_generated"] == 15
        
    def test_bottleneck_identification(self):
        """Test bottleneck identification."""
        tracker = PerformanceTracker("test_session")
        
        # Create a slow phase
        tracker.start_phase("phase_1_planning")
        time.sleep(0.1)  # Simulate work
        tracker.end_phase()
        
        # Manually set duration to exceed target
        tracker.phases["phase_1_planning"].duration = 50  # Target is 30s
        
        bottlenecks = tracker._identify_bottlenecks()
        assert len(bottlenecks) > 0
        assert any("phase_1_planning" in b for b in bottlenecks)
        
    def test_recommendations(self):
        """Test recommendation generation."""
        tracker = PerformanceTracker("test_session")
        
        # Create phases with different characteristics
        tracker.start_phase("Implementation Phase")
        tracker.end_phase()
        # Manually override duration after end_phase to simulate long running phase
        tracker.phases["Implementation Phase"].duration = 200  # Long duration
        
        tracker.start_phase("Test Phase")
        tracker.end_phase()
        # Manually override duration after end_phase to simulate long running phase
        tracker.phases["Test Phase"].duration = 150  # Long duration
        
        report = tracker.generate_report()
        
        assert len(report.recommendations) > 0
        # Should recommend parallelization for long phases
        assert any("parallel" in r.lower() for r in report.recommendations)
        
    def test_performance_report_generation(self):
        """Test complete performance report generation."""
        tracker = PerformanceTracker("test_session")
        
        # Simulate a workflow
        phases = [
            ("Planning", 0.1),
            ("Implementation", 0.2),
            ("Testing", 0.15)
        ]
        
        for phase_name, duration in phases:
            tracker.start_phase(phase_name)
            time.sleep(duration)
            tracker.end_phase()
            
        report = tracker.generate_report()
        
        assert report.session_id == "test_session"
        assert report.total_duration > 0.45  # Sum of all phase durations
        assert len(report.phase_metrics) == 3
        assert report.resource_usage["total_phases"] == 3
        assert report.resource_usage["peak_memory_mb"] > 0
        assert isinstance(report.bottlenecks, list)
        assert isinstance(report.recommendations, list)
        
    def test_report_serialization(self):
        """Test report serialization to dict."""
        tracker = PerformanceTracker("test_session")
        
        tracker.start_phase("Test Phase")
        time.sleep(0.1)
        tracker.end_phase()
        
        report = tracker.generate_report()
        report_dict = report.to_dict()
        
        assert report_dict["session_id"] == "test_session"
        assert "total_duration" in report_dict
        assert "phase_metrics" in report_dict
        assert len(report_dict["phase_metrics"]) == 1
        assert report_dict["phase_metrics"][0]["phase_name"] == "Test Phase"
        
    def test_save_report(self):
        """Test saving report to file."""
        tracker = PerformanceTracker("test_session")
        
        tracker.start_phase("Test Phase")
        time.sleep(0.1)
        tracker.end_phase()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            tracker.save_report(output_dir)
            
            # Check file was created
            report_files = list(output_dir.glob("performance_report_*.json"))
            assert len(report_files) == 1
            
            # Verify content
            import json
            with open(report_files[0]) as f:
                data = json.load(f)
                assert data["session_id"] == "test_session"
                
    def test_singleton_behavior(self):
        """Test singleton behavior of get_performance_tracker."""
        tracker1 = get_performance_tracker("session1")
        tracker2 = get_performance_tracker("session1")
        
        assert tracker1 is tracker2  # Same instance
        
        tracker3 = get_performance_tracker("session2")
        assert tracker3 is not tracker1  # Different instance for different session
        
    def test_track_phase_decorator(self):
        """Test the track_phase decorator."""
        @track_phase("Decorated Phase")
        def test_function(session_id="test"):
            time.sleep(0.1)
            return "result"
            
        result = test_function(session_id="decorator_test")
        assert result == "result"
        
        tracker = get_performance_tracker("decorator_test")
        assert "Decorated Phase" in tracker.phases
        assert tracker.phases["Decorated Phase"].duration >= 0.1
        
    @pytest.mark.asyncio
    async def test_track_phase_decorator_async(self):
        """Test the track_phase decorator with async functions."""
        @track_phase("Async Decorated Phase")
        async def async_test_function(session_id="test"):
            import asyncio
            await asyncio.sleep(0.1)
            return "async_result"
            
        result = await async_test_function(session_id="async_decorator_test")
        assert result == "async_result"
        
        tracker = get_performance_tracker("async_decorator_test")
        assert "Async Decorated Phase" in tracker.phases
        assert tracker.phases["Async Decorated Phase"].duration >= 0.1
        
    def test_memory_tracking(self):
        """Test memory tracking capabilities."""
        tracker = PerformanceTracker("test_session")
        
        tracker.start_phase("Memory Phase")
        
        # Allocate some memory
        large_list = [0] * 1000000  # ~8MB
        
        tracker.end_phase()
        
        phase = tracker.phases["Memory Phase"]
        assert phase.memory_start is not None
        assert phase.memory_peak is not None
        assert phase.memory_peak >= phase.memory_start
        
        # Clean up
        del large_list
        
    def test_performance_targets(self):
        """Test performance target definitions."""
        assert PerformanceTracker.TARGETS["total_workflow"] == 600  # 10 minutes
        assert PerformanceTracker.TARGETS["build_pipeline"] == 120  # 2 minutes
        assert PerformanceTracker.TARGETS["phase_4_implementation"] == 180  # 3 minutes
        
        # All targets should be positive
        for target_name, target_value in PerformanceTracker.TARGETS.items():
            assert target_value > 0, f"{target_name} should have positive target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])