"""
Unit tests for the progress monitoring system
"""
import pytest
from datetime import datetime, timedelta
import json
from workflows.incremental.progress_monitor import (
    ProgressState, FeatureProgress, WorkflowProgress, ProgressMonitor
)


class TestFeatureProgress:
    """Test FeatureProgress functionality"""
    
    def test_feature_progress_initialization(self):
        """Test FeatureProgress initialization"""
        progress = FeatureProgress(
            feature_id="feature_1",
            feature_title="User Authentication"
        )
        
        assert progress.feature_id == "feature_1"
        assert progress.feature_title == "User Authentication"
        assert progress.state == ProgressState.NOT_STARTED
        assert progress.start_time is None
        assert progress.end_time is None
        assert progress.attempts == 0
        assert progress.validation_progress == 0.0
        assert progress.test_progress == (0, 0)
        assert progress.lines_of_code == 0
        assert progress.files_created == []
        assert progress.error_count == 0
        assert progress.last_error is None
        assert progress.retry_strategy is None
    
    def test_get_duration(self):
        """Test duration calculation"""
        progress = FeatureProgress("f1", "Feature 1")
        
        # No start time
        assert progress.get_duration() is None
        
        # With start time but no end time
        start = datetime.now() - timedelta(minutes=5)
        progress.start_time = start
        duration = progress.get_duration()
        assert duration is not None
        assert 4 < duration.total_seconds() / 60 < 6  # Around 5 minutes
        
        # With both start and end time
        progress.end_time = start + timedelta(minutes=10)
        duration = progress.get_duration()
        assert duration.total_seconds() / 60 == 10
    
    def test_get_success_rate(self):
        """Test success rate calculation"""
        progress = FeatureProgress("f1", "Feature 1")
        
        # No attempts
        assert progress.get_success_rate() == 0.0
        
        # With attempts but not completed
        progress.attempts = 3
        assert progress.get_success_rate() == 0.0
        
        # Completed
        progress.state = ProgressState.COMPLETED
        assert progress.get_success_rate() == 1.0
    
    def test_get_test_pass_rate(self):
        """Test test pass rate calculation"""
        progress = FeatureProgress("f1", "Feature 1")
        
        # No tests
        assert progress.get_test_pass_rate() == 0.0
        
        # Some tests passing
        progress.test_progress = (7, 10)
        assert progress.get_test_pass_rate() == 70.0
        
        # All tests passing
        progress.test_progress = (10, 10)
        assert progress.get_test_pass_rate() == 100.0


class TestWorkflowProgress:
    """Test WorkflowProgress functionality"""
    
    def test_workflow_progress_initialization(self):
        """Test WorkflowProgress initialization"""
        progress = WorkflowProgress(
            workflow_id="workflow_1",
            total_features=10
        )
        
        assert progress.workflow_id == "workflow_1"
        assert progress.total_features == 10
        assert isinstance(progress.start_time, datetime)
        assert progress.features == {}
    
    def test_count_methods(self):
        """Test feature counting methods"""
        progress = WorkflowProgress("w1", 5)
        
        # Add features with different states
        progress.features["f1"] = FeatureProgress("f1", "F1", state=ProgressState.COMPLETED)
        progress.features["f2"] = FeatureProgress("f2", "F2", state=ProgressState.FAILED)
        progress.features["f3"] = FeatureProgress("f3", "F3", state=ProgressState.SKIPPED)
        progress.features["f4"] = FeatureProgress("f4", "F4", state=ProgressState.IN_PROGRESS)
        progress.features["f5"] = FeatureProgress("f5", "F5", state=ProgressState.RETRY)
        
        assert progress.get_completed_count() == 1
        assert progress.get_failed_count() == 1
        assert progress.get_skipped_count() == 1
        assert progress.get_in_progress_count() == 2  # IN_PROGRESS + RETRY
    
    def test_get_overall_progress(self):
        """Test overall progress calculation"""
        progress = WorkflowProgress("w1", 4)
        
        # No features started
        assert progress.get_overall_progress() == 0.0
        
        # Add completed features
        progress.features["f1"] = FeatureProgress("f1", "F1", state=ProgressState.COMPLETED)
        progress.features["f2"] = FeatureProgress("f2", "F2", state=ProgressState.COMPLETED)
        assert progress.get_overall_progress() == 50.0  # 2/4 = 50%
        
        # Add in-progress feature (counts as 0.5)
        progress.features["f3"] = FeatureProgress("f3", "F3", state=ProgressState.IN_PROGRESS)
        assert progress.get_overall_progress() == 62.5  # (2 + 0.5)/4 = 62.5%
    
    def test_get_estimated_completion_time(self):
        """Test completion time estimation"""
        progress = WorkflowProgress("w1", 4)
        progress.start_time = datetime.now() - timedelta(minutes=10)
        
        # No completed features
        assert progress.get_estimated_completion_time() is None
        
        # Add completed features
        progress.features["f1"] = FeatureProgress("f1", "F1", state=ProgressState.COMPLETED)
        progress.features["f2"] = FeatureProgress("f2", "F2", state=ProgressState.COMPLETED)
        
        # Should estimate ~10 more minutes for remaining 2 features
        eta = progress.get_estimated_completion_time()
        assert eta is not None
        remaining = (eta - datetime.now()).total_seconds() / 60
        assert 8 < remaining < 12  # Around 10 minutes


class TestProgressMonitor:
    """Test ProgressMonitor functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a ProgressMonitor instance"""
        return ProgressMonitor(workflow_id="test_workflow", total_features=5)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.progress.workflow_id == "test_workflow"
        assert monitor.progress.total_features == 5
        assert monitor.update_callbacks == []
        assert monitor.milestone_thresholds == [25, 50, 75, 90, 100]
        assert monitor.last_milestone == 0
    
    def test_start_feature(self, monitor):
        """Test starting a feature"""
        monitor.start_feature("f1", "Feature One")
        
        assert "f1" in monitor.progress.features
        feature = monitor.progress.features["f1"]
        assert feature.feature_id == "f1"
        assert feature.feature_title == "Feature One"
        assert feature.state == ProgressState.IN_PROGRESS
        assert feature.start_time is not None
    
    def test_update_feature(self, monitor):
        """Test updating feature progress"""
        monitor.start_feature("f1", "Feature One")
        
        monitor.update_feature(
            "f1",
            validation_progress=50.0,
            test_progress=(5, 10),
            attempts=2
        )
        
        feature = monitor.progress.features["f1"]
        assert feature.validation_progress == 50.0
        assert feature.test_progress == (5, 10)
        assert feature.attempts == 2
    
    def test_complete_feature_success(self, monitor):
        """Test completing a feature successfully"""
        monitor.start_feature("f1", "Feature One")
        
        monitor.complete_feature(
            "f1",
            success=True,
            files_created=["main.py", "test.py"],
            lines_of_code=150
        )
        
        feature = monitor.progress.features["f1"]
        assert feature.state == ProgressState.COMPLETED
        assert feature.end_time is not None
        assert feature.files_created == ["main.py", "test.py"]
        assert feature.lines_of_code == 150
    
    def test_complete_feature_failure(self, monitor):
        """Test completing a feature with failure"""
        monitor.start_feature("f1", "Feature One")
        
        monitor.complete_feature(
            "f1",
            success=False,
            files_created=[],
            lines_of_code=0
        )
        
        feature = monitor.progress.features["f1"]
        assert feature.state == ProgressState.FAILED
        assert feature.end_time is not None
    
    def test_skip_feature(self, monitor):
        """Test skipping a feature"""
        # Skip a feature that was started
        monitor.start_feature("f1", "Feature One")
        monitor.skip_feature("f1", "Dependencies not met")
        
        feature = monitor.progress.features["f1"]
        assert feature.state == ProgressState.SKIPPED
        assert feature.last_error == "Dependencies not met"
        
        # Skip a feature that wasn't started
        monitor.skip_feature("f2", "Previous feature failed")
        assert "f2" in monitor.progress.features
        assert monitor.progress.features["f2"].state == ProgressState.SKIPPED
    
    def test_record_retry(self, monitor):
        """Test recording retry attempts"""
        monitor.start_feature("f1", "Feature One")
        
        monitor.record_retry(
            "f1",
            retry_strategy="exponential_backoff",
            error="Validation failed: syntax error"
        )
        
        feature = monitor.progress.features["f1"]
        assert feature.state == ProgressState.RETRY
        assert feature.attempts == 1
        assert feature.error_count == 1
        assert feature.last_error == "Validation failed: syntax error"
        assert feature.retry_strategy == "exponential_backoff"
    
    def test_mark_stagnant(self, monitor):
        """Test marking a feature as stagnant"""
        monitor.start_feature("f1", "Feature One")
        monitor.mark_stagnant("f1")
        
        feature = monitor.progress.features["f1"]
        assert feature.state == ProgressState.STAGNANT
    
    def test_get_progress_summary(self, monitor):
        """Test getting progress summary"""
        # Set up some features
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        monitor.start_feature("f2", "Feature Two")
        monitor.record_retry("f2", "backoff", "Error")
        monitor.complete_feature("f2", False, [], 0)
        
        monitor.skip_feature("f3", "Skipped")
        
        summary = monitor.get_progress_summary()
        
        assert summary["workflow_id"] == "test_workflow"
        assert summary["features"]["total"] == 5
        assert summary["features"]["completed"] == 1
        assert summary["features"]["failed"] == 1
        assert summary["features"]["skipped"] == 1
        assert summary["features"]["in_progress"] == 0
        assert summary["features"]["not_started"] == 2
        
        assert summary["metrics"]["total_attempts"] == 1
        assert summary["metrics"]["total_errors"] == 1
        assert summary["metrics"]["total_lines_of_code"] == 100
    
    def test_get_feature_timeline(self, monitor):
        """Test getting feature timeline"""
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        timeline = monitor.get_feature_timeline()
        
        assert len(timeline) == 2  # start and complete events
        assert timeline[0]["event"] == "started"
        assert timeline[0]["feature_id"] == "f1"
        assert timeline[1]["event"] == "completed"
        assert timeline[1]["duration"] is not None
    
    def test_visualize_progress(self, monitor):
        """Test progress visualization"""
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        visualization = monitor.visualize_progress()
        
        assert "INCREMENTAL DEVELOPMENT PROGRESS" in visualization
        assert "Overall:" in visualization
        assert "✅ Completed:" in visualization
        assert "20.0%" in visualization  # 1/5 = 20%
    
    def test_export_progress_data(self, monitor):
        """Test exporting progress data as JSON"""
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        json_data = monitor.export_progress_data()
        data = json.loads(json_data)
        
        assert "summary" in data
        assert "timeline" in data
        assert "features" in data
        assert "f1" in data["features"]
        assert data["features"]["f1"]["state"] == "completed"
    
    def test_milestone_detection(self, monitor):
        """Test milestone detection"""
        # Complete features to reach 25% milestone
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        # Should not reach 25% with just 1/5 features (20%)
        assert monitor.last_milestone == 0
        
        # Complete another to reach 40% (past 25% milestone)
        monitor.start_feature("f2", "Feature Two")
        monitor.complete_feature("f2", True, ["f2.py"], 100)
        
        assert monitor.last_milestone == 25
    
    def test_update_callbacks(self, monitor):
        """Test update callback mechanism"""
        events = []
        
        def callback(event_type, feature_id, summary):
            events.append((event_type, feature_id))
        
        monitor.add_update_callback(callback)
        
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        assert len(events) == 2
        assert events[0] == ("feature_started", "f1")
        assert events[1] == ("feature_completed", "f1")
    
    def test_delegation_methods(self, monitor):
        """Test delegation methods to workflow progress"""
        # Set up features
        monitor.start_feature("f1", "Feature One")
        monitor.complete_feature("f1", True, ["f1.py"], 100)
        
        monitor.start_feature("f2", "Feature Two")
        monitor.complete_feature("f2", False, [], 0)
        
        monitor.skip_feature("f3", "Skipped")
        
        monitor.start_feature("f4", "Feature Four")
        
        # Test delegated methods
        assert monitor.get_completed_count() == 1
        assert monitor.get_failed_count() == 1
        assert monitor.get_skipped_count() == 1
        assert monitor.get_in_progress_count() == 1