"""
Tests for TDD-enhanced Progress Monitor functionality
"""
import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import MagicMock, patch
from workflows.mvp_incremental.progress_monitor import (
    ProgressMonitor, FeatureProgress, StepStatus
)


class TestTDDPhaseTracking:
    """Test TDD phase tracking functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a ProgressMonitor instance"""
        return ProgressMonitor()
    
    def test_phase_transition_tracking(self, monitor):
        """Test that phase transitions are properly tracked"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Initial RED phase
        monitor.update_tdd_phase("f1", "RED")
        feature = monitor.features["f1"]
        assert feature.tdd_phase == "RED"
        assert feature.time_entered_red is not None
        assert len(feature.phase_transitions) == 0
        
        # Transition to YELLOW
        monitor.update_tdd_phase("f1", "YELLOW")
        assert feature.tdd_phase == "YELLOW"
        assert feature.time_entered_yellow is not None
        assert len(feature.phase_transitions) == 1
        assert feature.phase_transitions[0][0] == "RED"
        assert feature.phase_transitions[0][1] == "YELLOW"
        
        # Transition to GREEN
        monitor.update_tdd_phase("f1", "GREEN")
        assert feature.tdd_phase == "GREEN"
        assert feature.time_entered_green is not None
        assert len(feature.phase_transitions) == 2
        assert feature.phase_transitions[1][0] == "YELLOW"
        assert feature.phase_transitions[1][1] == "GREEN"
    
    def test_phase_duration_calculation(self, monitor):
        """Test that phase durations are calculated correctly"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Mock time for consistent testing
        with patch('workflows.mvp_incremental.progress_monitor.datetime') as mock_datetime:
            # Start in RED at time 0
            start_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = start_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            monitor.update_tdd_phase("f1", "RED")
            feature = monitor.features["f1"]
            feature.time_entered_red = start_time  # Manually set for test
            
            # Move to YELLOW after 5 minutes
            mock_datetime.now.return_value = start_time + timedelta(minutes=5)
            monitor.update_tdd_phase("f1", "YELLOW")
            
            # Check RED duration
            assert "RED" in feature.phase_durations
            assert feature.phase_durations["RED"] == 300.0  # 5 minutes = 300 seconds
            
            # Move to GREEN after 3 more minutes
            mock_datetime.now.return_value = start_time + timedelta(minutes=8)
            monitor.update_tdd_phase("f1", "GREEN")
            
            # Check YELLOW duration
            assert "YELLOW" in feature.phase_durations
            assert feature.phase_durations["YELLOW"] == 180.0  # 3 minutes = 180 seconds
    
    def test_test_fix_iterations_tracking(self, monitor):
        """Test tracking of test fix iterations"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Initial RED phase
        monitor.update_tdd_phase("f1", "RED")
        feature = monitor.features["f1"]
        assert feature.test_fix_iterations == 0
        
        # First transition to YELLOW
        monitor.update_tdd_phase("f1", "YELLOW")
        assert feature.test_fix_iterations == 0
        
        # Back to RED (test failure after review)
        monitor.update_tdd_phase("f1", "RED")
        
        # Second transition to YELLOW (fix iteration)
        monitor.update_tdd_phase("f1", "YELLOW")
        assert feature.test_fix_iterations == 1
        
        # Another cycle
        monitor.update_tdd_phase("f1", "RED")
        monitor.update_tdd_phase("f1", "YELLOW")
        assert feature.test_fix_iterations == 2


class TestTDDProgressMetrics:
    """Test TDD progress metrics functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a ProgressMonitor instance"""
        return ProgressMonitor()
    
    @pytest.fixture
    def monitor_with_features(self):
        """Create a monitor with test data"""
        monitor = ProgressMonitor()
        monitor.start_workflow(total_features=2)
        
        # Feature 1: Complete TDD cycle
        monitor.start_feature("f1", "Feature One", 1)
        monitor.update_tdd_phase("f1", "RED")
        monitor.update_tdd_progress("f1", "tests_written", {
            "test_files": 2,
            "test_functions": 5
        })
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 0,
            "failed": 5,
            "attempt": 0,
            "execution_time": 2.5
        })
        
        # Simulate phase durations
        feature1 = monitor.features["f1"]
        feature1.phase_durations["RED"] = 300.0  # 5 minutes
        feature1.phase_durations["YELLOW"] = 180.0  # 3 minutes
        feature1.phase_durations["GREEN"] = 60.0  # 1 minute
        feature1.test_fix_iterations = 1
        feature1.code_coverage = 85.5
        
        # Feature 2: Partial progress
        monitor.start_feature("f2", "Feature Two", 2)
        monitor.update_tdd_phase("f2", "RED")
        monitor.update_tdd_progress("f2", "tests_written", {
            "test_files": 1,
            "test_functions": 3
        })
        
        feature2 = monitor.features["f2"]
        feature2.phase_durations["RED"] = 240.0  # 4 minutes
        
        return monitor
    
    def test_get_phase_metrics(self, monitor_with_features):
        """Test phase metrics calculation"""
        metrics = monitor_with_features.get_phase_metrics()
        
        # Check total features
        assert metrics["total_features"] == 2
        
        # Check phase summary
        phase_summary = metrics["phase_summary"]
        
        # RED phase
        assert phase_summary["RED"]["total_duration"] == 540.0  # 300 + 240
        assert phase_summary["RED"]["avg_duration"] == 270.0  # 540 / 2
        
        # YELLOW phase
        assert phase_summary["YELLOW"]["total_duration"] == 180.0
        assert phase_summary["YELLOW"]["avg_duration"] == 180.0  # Only 1 feature
        
        # GREEN phase
        assert phase_summary["GREEN"]["total_duration"] == 60.0
        assert phase_summary["GREEN"]["avg_duration"] == 60.0  # Only 1 feature
        
        # Test metrics
        test_metrics = metrics["test_metrics"]
        assert test_metrics["total_test_files"] == 3  # 2 + 1
        assert test_metrics["total_test_functions"] == 8  # 5 + 3
        assert test_metrics["total_fix_iterations"] == 1
        assert test_metrics["avg_coverage"] == 85.5  # Only feature1 has coverage
    
    def test_test_execution_time_tracking(self, monitor):
        """Test tracking of test execution times"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Record multiple test runs
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 0,
            "failed": 5,
            "execution_time": 2.5,
            "attempt": 0
        })
        
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 3,
            "failed": 2,
            "execution_time": 2.3,
            "attempt": 1
        })
        
        monitor.update_tdd_progress("f1", "tests_passing", {
            "execution_time": 2.1
        })
        
        feature = monitor.features["f1"]
        assert len(feature.test_execution_times) == 3
        assert feature.test_execution_times == [2.5, 2.3, 2.1]
        
        # Check average calculation in metrics
        metrics = monitor.get_phase_metrics()
        assert metrics["test_metrics"]["avg_test_execution_time"] == pytest.approx(2.3, 0.01)
    
    def test_test_failure_count_tracking(self, monitor):
        """Test tracking of test failures across attempts"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Initial run - all fail
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 0,
            "failed": 5,
            "attempt": 0
        })
        
        # Second attempt - some pass
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 3,
            "failed": 2,
            "attempt": 1
        })
        
        # Final attempt - all pass
        monitor.update_tdd_progress("f1", "tests_initial_run", {
            "passed": 5,
            "failed": 0,
            "attempt": 2
        })
        
        feature = monitor.features["f1"]
        assert feature.test_failure_counts == {0: 5, 1: 2, 2: 0}


class TestTDDVisualization:
    """Test TDD visualization methods"""
    
    @pytest.fixture
    def monitor(self):
        """Create a ProgressMonitor instance"""
        return ProgressMonitor()
    
    @pytest.fixture
    def monitor_with_timeline(self):
        """Create monitor with phase timeline data"""
        monitor = ProgressMonitor()
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Create phase transitions
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        feature = monitor.features["f1"]
        
        feature.time_entered_red = base_time
        feature.tdd_phase = "GREEN"
        feature.phase_transitions = [
            ("RED", "YELLOW", base_time + timedelta(minutes=5)),
            ("YELLOW", "GREEN", base_time + timedelta(minutes=8))
        ]
        feature.phase_durations = {
            "RED": 300.0,
            "YELLOW": 180.0,
            "GREEN": 60.0
        }
        feature.test_fix_iterations = 1
        feature.review_attempts = 2
        
        return monitor
    
    def test_print_tdd_phase_timeline(self, monitor_with_timeline, capsys):
        """Test phase timeline output"""
        monitor_with_timeline.print_tdd_phase_timeline()
        captured = capsys.readouterr()
        
        assert "TDD PHASE TIMELINE" in captured.out
        assert "Feature One" in captured.out
        assert "RED started at 12:00:00" in captured.out
        assert "RED → YELLOW at 12:05:00" in captured.out
        assert "YELLOW → GREEN at 12:08:00" in captured.out
        assert "Phase Durations:" in captured.out
        assert "RED: 5m 0s" in captured.out
        assert "YELLOW: 3m 0s" in captured.out
        assert "GREEN: 1m 0s" in captured.out
        assert "Test fix iterations: 1" in captured.out
        assert "Review attempts: 2" in captured.out
    
    def test_print_test_progression(self, monitor, capsys):
        """Test test progression output"""
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        monitor.update_tdd_progress("f1", "tests_written", {
            "test_files": 2,
            "test_functions": 5
        })
        
        feature = monitor.features["f1"]
        feature.test_failure_counts = {0: 5, 1: 2, 2: 0}
        feature.tests_passing = True
        feature.code_coverage = 92.5
        
        monitor.print_test_progression()
        captured = capsys.readouterr()
        
        assert "TEST PROGRESSION" in captured.out
        assert "Feature One" in captured.out
        assert "Tests created: 2 files, 5 functions" in captured.out
        assert "Test failure progression:" in captured.out
        assert "Attempt 0: ✗ 5 failures" in captured.out
        assert "Attempt 1: ✗ 2 failures" in captured.out
        assert "Attempt 2: ✓ 0 failures" in captured.out
        assert "All tests passing (coverage: 92.5%)" in captured.out
    
    def test_print_phase_progress_bars(self, monitor_with_timeline, capsys):
        """Test phase progress bar visualization"""
        monitor_with_timeline.print_phase_progress_bars()
        captured = capsys.readouterr()
        
        assert "TDD PHASE DISTRIBUTION" in captured.out
        assert "Overall Time Distribution:" in captured.out
        assert "🔴 RED" in captured.out
        assert "🟡 YELLOW" in captured.out
        assert "🟢 GREEN" in captured.out
        assert "█" in captured.out  # Progress bar characters
        assert "░" in captured.out
        assert "Per-Feature Breakdown:" in captured.out
        assert "Feature One" in captured.out


class TestEnhancedSummaryOutput:
    """Test enhanced summary output with TDD metrics"""
    
    def test_enhanced_summary_with_tdd_metrics(self, capsys):
        """Test that summary includes new TDD metrics"""
        monitor = ProgressMonitor()
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Set up test data
        feature = monitor.features["f1"]
        feature.validation_passed = True
        feature.tests_written = True
        feature.tests_passing = True
        feature.test_file_count = 2
        feature.test_function_count = 5
        feature.code_coverage = 88.5
        feature.tdd_phase = "GREEN"
        feature.phase_durations = {
            "RED": 300.0,
            "YELLOW": 180.0,
            "GREEN": 60.0
        }
        feature.test_fix_iterations = 1
        feature.test_execution_times = [2.5, 2.3]  # Add test execution times
        monitor.features["f1"] = feature
        
        # Mock workflow times
        monitor.workflow_start_time = datetime.now() - timedelta(minutes=10)
        monitor.workflow_end_time = datetime.now()
        
        monitor._print_summary()
        captured = capsys.readouterr()
        
        # Check for new TDD sections
        assert "TDD Phase Timing:" in captured.out
        assert "RED: avg" in captured.out
        assert "YELLOW: avg" in captured.out
        assert "GREEN: avg" in captured.out
        assert "Test Execution Metrics:" in captured.out


class TestExportMetricsEnhancement:
    """Test enhanced metrics export"""
    
    def test_export_includes_tdd_enhancements(self):
        """Test that export includes all new TDD fields"""
        monitor = ProgressMonitor()
        monitor.start_workflow(total_features=1)
        monitor.start_feature("f1", "Feature One", 1)
        
        # Set up comprehensive test data
        feature = monitor.features["f1"]
        feature.tdd_phase = "GREEN"
        feature.phase_durations = {"RED": 300.0, "YELLOW": 180.0}
        feature.phase_transitions = [("RED", "YELLOW", datetime.now())]
        feature.test_fix_iterations = 2
        feature.review_attempts = 1
        feature.test_execution_times = [2.5, 2.3, 2.1]
        feature.test_failure_counts = {0: 5, 1: 2, 2: 0}
        
        monitor.workflow_start_time = datetime.now() - timedelta(minutes=10)
        monitor.workflow_end_time = datetime.now()
        
        metrics = monitor.export_metrics()
        
        # Check TDD metrics structure
        assert "phase_metrics" in metrics["tdd_metrics"]
        assert "test_execution_metrics" in metrics["tdd_metrics"]
        
        # Check feature details
        f1_details = metrics["feature_details"]["f1"]
        assert f1_details["tdd_phase"] == "GREEN"
        assert f1_details["phase_durations"] == {"RED": 300.0, "YELLOW": 180.0}
        assert len(f1_details["phase_transitions"]) == 1
        assert f1_details["test_fix_iterations"] == 2
        assert f1_details["review_attempts"] == 1
        assert f1_details["test_execution_times"] == [2.5, 2.3, 2.1]
        assert f1_details["test_failure_counts"] == {0: 5, 1: 2, 2: 0}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])