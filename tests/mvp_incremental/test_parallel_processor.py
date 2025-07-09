"""
Unit tests for the parallel feature processor.

Tests dependency analysis, batch processing, and concurrent execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import time

from workflows.mvp_incremental.parallel_processor import (
    FeatureDependency, ProcessingMetrics, ParallelFeatureProcessor,
    should_use_parallel_processing
)
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureResult


class TestFeatureDependency:
    """Test the FeatureDependency dataclass."""
    
    def test_dependency_initialization(self):
        """Test dependency initialization."""
        dep = FeatureDependency("feature1")
        assert dep.feature_id == "feature1"
        assert len(dep.depends_on) == 0
        assert len(dep.dependents) == 0
        assert dep.is_independent
    
    def test_dependency_with_dependencies(self):
        """Test dependency with dependencies."""
        dep = FeatureDependency("feature2", depends_on={"feature1"})
        assert not dep.is_independent
        assert "feature1" in dep.depends_on


class TestProcessingMetrics:
    """Test the ProcessingMetrics dataclass."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = ProcessingMetrics()
        assert metrics.total_features == 0
        assert metrics.parallel_batches == 0
        assert metrics.speedup_factor == 1.0
    
    def test_speedup_calculation(self):
        """Test speedup factor calculation."""
        metrics = ProcessingMetrics()
        metrics.total_duration_seconds = 10.0
        metrics.calculate_speedup(30.0)
        assert metrics.speedup_factor == 3.0


class TestParallelFeatureProcessor:
    """Test the ParallelFeatureProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a test processor."""
        return ParallelFeatureProcessor(max_workers=2, batch_timeout=5)
    
    @pytest.fixture
    def sample_features(self):
        """Create sample features for testing."""
        return [
            {
                "id": "feature1",
                "title": "Feature 1",
                "description": "First feature"
            },
            {
                "id": "feature2", 
                "title": "Feature 2",
                "description": "Second feature depends on feature1",
                "depends_on": ["feature1"]
            },
            {
                "id": "feature3",
                "title": "Feature 3",
                "description": "Third feature"
            },
            {
                "id": "feature4",
                "title": "Feature 4",
                "description": "References Feature 3 in description"
            }
        ]
    
    def test_analyze_dependencies_explicit(self, processor, sample_features):
        """Test analyzing explicit dependencies."""
        deps = processor.analyze_dependencies(sample_features)
        
        assert len(deps) == 4
        assert deps["feature1"].is_independent
        assert not deps["feature2"].is_independent
        assert "feature1" in deps["feature2"].depends_on
        assert "feature2" in deps["feature1"].dependents
    
    def test_analyze_dependencies_implicit(self, processor, sample_features):
        """Test analyzing implicit dependencies from descriptions."""
        deps = processor.analyze_dependencies(sample_features)
        
        # feature4 should depend on feature3 due to reference in description
        assert "feature3" in deps["feature4"].depends_on
        assert "feature4" in deps["feature3"].dependents
    
    def test_get_processable_features_initial(self, processor, sample_features):
        """Test getting initial processable features."""
        deps = processor.analyze_dependencies(sample_features)
        processable = processor.get_processable_features(sample_features, deps)
        
        # Should get feature1 and feature3 (independents)
        processable_ids = [f["id"] for f in processable]
        assert "feature1" in processable_ids
        assert "feature3" in processable_ids
        assert "feature2" not in processable_ids  # Has dependency
        assert "feature4" not in processable_ids  # Has implicit dependency
    
    def test_get_processable_features_after_completion(self, processor, sample_features):
        """Test getting processable features after some are completed."""
        deps = processor.analyze_dependencies(sample_features)
        
        # Mark feature1 as completed
        processor.completed_features.add("feature1")
        
        processable = processor.get_processable_features(sample_features, deps)
        processable_ids = [f["id"] for f in processable]
        
        # Now feature2 should be processable
        assert "feature2" in processable_ids
        assert "feature1" not in processable_ids  # Already completed
        assert "feature3" in processable_ids  # Still independent
    
    @pytest.mark.asyncio
    async def test_process_feature_with_semaphore(self, processor):
        """Test processing a single feature with semaphore control."""
        # Create mock implementer
        mock_implementer = Mock()
        mock_implementer._parse_code_files = Mock(return_value={"main.py": "code"})
        
        # Create successful result
        success_result = TDDFeatureResult(
            feature_id="feature1",
            feature_title="Feature 1",
            test_code="test code",
            implementation_code="impl code",
            initial_test_result=Mock(),
            final_test_result=Mock(),
            success=True
        )
        
        # Make implement_feature_tdd async
        mock_implementer.implement_feature_tdd = AsyncMock(return_value=success_result)
        
        feature = {"id": "feature1", "title": "Feature 1"}
        
        feature_id, result = await processor.process_feature_with_semaphore(
            feature=feature,
            feature_index=0,
            implementer=mock_implementer,
            existing_code={},
            requirements="requirements",
            design_output="design"
        )
        
        assert feature_id == "feature1"
        assert result.success
        assert mock_implementer.implement_feature_tdd.called
    
    @pytest.mark.asyncio
    async def test_process_feature_with_error(self, processor):
        """Test processing a feature that raises an error."""
        mock_implementer = Mock()
        mock_implementer.implement_feature_tdd = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        feature = {"id": "feature1", "title": "Feature 1"}
        
        feature_id, result = await processor.process_feature_with_semaphore(
            feature=feature,
            feature_index=0,
            implementer=mock_implementer,
            existing_code={},
            requirements="requirements",
            design_output="design"
        )
        
        assert feature_id == "feature1"
        assert not result.success
        assert result.feature_title == "Feature 1"
    
    @pytest.mark.asyncio
    async def test_process_features_parallel_simple(self, processor):
        """Test parallel processing of independent features."""
        # Create mock implementer
        mock_implementer = Mock()
        mock_implementer._parse_code_files = Mock(return_value={})
        
        # Track call order and timing
        call_times = []
        
        async def mock_implement(feature, **kwargs):
            start_time = time.time()
            call_times.append((feature["id"], start_time))
            await asyncio.sleep(0.1)  # Simulate work
            
            return TDDFeatureResult(
                feature_id=feature["id"],
                feature_title=feature["title"],
                test_code="test",
                implementation_code="impl",
                initial_test_result=Mock(),
                final_test_result=Mock(),
                success=True
            )
        
        mock_implementer.implement_feature_tdd = mock_implement
        
        # Two independent features
        features = [
            {"id": "f1", "title": "Feature 1", "description": "First"},
            {"id": "f2", "title": "Feature 2", "description": "Second"}
        ]
        
        results = await processor.process_features_parallel(
            features=features,
            implementer=mock_implementer,
            existing_code={},
            requirements="req",
            design_output="design"
        )
        
        assert len(results) == 2
        assert all(r.success for r in results)
        
        # Check they were processed in parallel (started close together)
        if len(call_times) == 2:
            time_diff = abs(call_times[0][1] - call_times[1][1])
            assert time_diff < 0.05  # Should start within 50ms of each other
    
    @pytest.mark.asyncio
    async def test_process_features_with_dependencies(self, processor):
        """Test processing features with dependencies."""
        mock_implementer = Mock()
        mock_implementer._parse_code_files = Mock(return_value={"main.py": "code"})
        
        # Track processing order
        processing_order = []
        
        async def mock_implement(feature, **kwargs):
            processing_order.append(feature["id"])
            return TDDFeatureResult(
                feature_id=feature["id"],
                feature_title=feature["title"],
                test_code="test",
                implementation_code="impl",
                initial_test_result=Mock(),
                final_test_result=Mock(),
                success=True
            )
        
        mock_implementer.implement_feature_tdd = mock_implement
        
        # Features with dependencies
        features = [
            {"id": "f1", "title": "Feature 1", "description": "First"},
            {"id": "f2", "title": "Feature 2", "description": "Second", "depends_on": ["f1"]},
            {"id": "f3", "title": "Feature 3", "description": "Third", "depends_on": ["f2"]}
        ]
        
        results = await processor.process_features_parallel(
            features=features,
            implementer=mock_implementer,
            existing_code={},
            requirements="req",
            design_output="design"
        )
        
        assert len(results) == 3
        assert all(r.success for r in results)
        
        # Check processing order respects dependencies
        assert processing_order.index("f1") < processing_order.index("f2")
        assert processing_order.index("f2") < processing_order.index("f3")
    
    @pytest.mark.asyncio
    async def test_process_features_with_timeout(self, processor):
        """Test handling of batch timeout."""
        processor.batch_timeout = 0.1  # Very short timeout
        
        mock_implementer = Mock()
        
        async def slow_implement(feature, **kwargs):
            await asyncio.sleep(1)  # Longer than timeout
            return TDDFeatureResult(
                feature_id=feature["id"],
                feature_title=feature["title"],
                test_code="test",
                implementation_code="impl",
                initial_test_result=Mock(),
                final_test_result=Mock(),
                success=True
            )
        
        mock_implementer.implement_feature_tdd = slow_implement
        
        features = [{"id": "f1", "title": "Feature 1", "description": "First"}]
        
        results = await processor.process_features_parallel(
            features=features,
            implementer=mock_implementer,
            existing_code={},
            requirements="req",
            design_output="design"
        )
        
        # Feature should be marked as failed due to timeout
        assert "f1" in processor.failed_features
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, processor):
        """Test detection of circular dependencies."""
        features = [
            {"id": "f1", "title": "Feature 1", "depends_on": ["f2"]},
            {"id": "f2", "title": "Feature 2", "depends_on": ["f1"]}
        ]
        
        mock_implementer = Mock()
        mock_implementer.implement_feature_tdd = AsyncMock()
        
        results = await processor.process_features_parallel(
            features=features,
            implementer=mock_implementer,
            existing_code={},
            requirements="req",
            design_output="design"
        )
        
        # Should detect circular dependency and break
        assert len(processor.completed_features) == 0
        assert len(processor.failed_features) == 0
    
    def test_get_metrics(self, processor):
        """Test metrics retrieval."""
        # Set up some metrics
        processor.metrics.total_features = 10
        processor.completed_features = {"f1", "f2", "f3"}
        processor.failed_features = {"f4"}
        processor.metrics.parallel_batches = 3
        processor.metrics.max_concurrency = 2
        processor.metrics.total_duration_seconds = 30.0
        
        metrics = processor.get_metrics()
        
        assert metrics["total_features"] == 10
        assert metrics["completed_features"] == 3
        assert metrics["failed_features"] == 1
        assert metrics["parallel_batches"] == 3
        assert metrics["max_concurrency"] == 2
        assert metrics["total_duration_seconds"] == 30.0
    
    @pytest.mark.asyncio
    async def test_accumulated_code_propagation(self, processor):
        """Test that code accumulates across features."""
        mock_implementer = Mock()
        
        # Track accumulated code passed to each feature
        accumulated_code_by_feature = {}
        
        async def mock_implement(feature, existing_code, **kwargs):
            accumulated_code_by_feature[feature["id"]] = existing_code.copy()
            
            # Return result with unique code
            return TDDFeatureResult(
                feature_id=feature["id"],
                feature_title=feature["title"],
                test_code="test",
                implementation_code=f"# Code for {feature['id']}",
                initial_test_result=Mock(),
                final_test_result=Mock(),
                success=True
            )
        
        mock_implementer.implement_feature_tdd = mock_implement
        mock_implementer._parse_code_files = Mock(
            side_effect=lambda code: {f"{code.split()[-1]}.py": code}
        )
        
        features = [
            {"id": "f1", "title": "Feature 1", "description": "First"},
            {"id": "f2", "title": "Feature 2", "description": "Second", "depends_on": ["f1"]}
        ]
        
        initial_code = {"base.py": "# Base code"}
        
        results = await processor.process_features_parallel(
            features=features,
            implementer=mock_implementer,
            existing_code=initial_code,
            requirements="req",
            design_output="design"
        )
        
        # f1 should only have initial code
        assert accumulated_code_by_feature["f1"] == initial_code
        
        # f2 should have initial code + f1's code
        assert "base.py" in accumulated_code_by_feature["f2"]
        assert "f1.py" in accumulated_code_by_feature["f2"]


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_should_use_parallel_processing_enough_features(self):
        """Test parallel processing recommendation with enough features."""
        features = [
            {"id": f"f{i}", "title": f"Feature {i}"}
            for i in range(5)
        ]
        
        assert should_use_parallel_processing(features)
    
    def test_should_use_parallel_processing_too_few_features(self):
        """Test parallel processing not recommended with few features."""
        features = [
            {"id": "f1", "title": "Feature 1"},
            {"id": "f2", "title": "Feature 2"}
        ]
        
        assert not should_use_parallel_processing(features)
    
    def test_should_use_parallel_processing_too_many_dependencies(self):
        """Test parallel processing not recommended with high dependency ratio."""
        features = [
            {"id": "f1", "title": "Feature 1"},
            {"id": "f2", "title": "Feature 2", "depends_on": ["f1"]},
            {"id": "f3", "title": "Feature 3", "depends_on": ["f1", "f2"]},
            {"id": "f4", "title": "Feature 4", "depends_on": ["f2", "f3"]}
        ]
        
        # 5 total dependencies / 4 features = 1.25 > 0.3
        assert not should_use_parallel_processing(features)
    
    def test_should_use_parallel_processing_custom_thresholds(self):
        """Test parallel processing with custom thresholds."""
        features = [
            {"id": "f1", "title": "Feature 1"},
            {"id": "f2", "title": "Feature 2"}
        ]
        
        # Lower minimum features threshold
        assert should_use_parallel_processing(features, min_features=2)
        
        # Higher dependency ratio threshold
        features[1]["depends_on"] = ["f1"]
        assert should_use_parallel_processing(features, min_features=2, max_dependencies_ratio=0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])