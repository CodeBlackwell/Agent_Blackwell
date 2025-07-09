"""
Unit tests for the enhanced test cache manager.

Tests cache functionality, invalidation, statistics, and performance.
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from workflows.mvp_incremental.test_cache_manager import (
    TestCacheManager, CacheEntry, CacheStatistics, get_test_cache
)


class TestCacheEntry:
    """Test the CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            result={"test": "data"},
            code_hash="abc123",
            test_files_hash="def456",
            dependencies={"file1.py", "file2.py"},
            timestamp=time.time(),
            size_bytes=100
        )
        
        assert entry.key == "test_key"
        assert entry.result == {"test": "data"}
        assert entry.hit_count == 0
        assert len(entry.dependencies) == 2
    
    def test_cache_entry_validity(self):
        """Test cache entry validity checking."""
        # Create entry with current timestamp
        entry = CacheEntry(
            key="test",
            result={},
            code_hash="hash",
            test_files_hash="hash",
            dependencies=set(),
            timestamp=time.time()
        )
        
        # Should be valid immediately
        assert entry.is_valid(max_age_seconds=3600)
        
        # Simulate old entry
        entry.timestamp = time.time() - 7200  # 2 hours ago
        assert not entry.is_valid(max_age_seconds=3600)  # 1 hour max


class TestCacheStatistics:
    """Test cache statistics tracking."""
    
    def test_statistics_initialization(self):
        """Test statistics initialization."""
        stats = CacheStatistics()
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStatistics()
        stats.total_requests = 10
        stats.cache_hits = 7
        stats.cache_misses = 3
        
        assert stats.hit_rate == 70.0
    
    def test_statistics_to_dict(self):
        """Test converting statistics to dictionary."""
        stats = CacheStatistics()
        stats.total_requests = 5
        stats.cache_hits = 3
        stats.total_size_bytes = 1024 * 1024  # 1MB
        
        result = stats.to_dict()
        assert result["total_requests"] == 5
        assert result["hit_rate"] == "60.0%"
        assert result["total_size_mb"] == 1.0


class TestTestCacheManager:
    """Test the TestCacheManager class."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a test cache manager."""
        return TestCacheManager(
            max_size_mb=1,
            max_entries=10,
            max_age_seconds=300,
            persistent_cache_path=None
        )
    
    def test_cache_key_generation(self, cache_manager):
        """Test cache key generation."""
        code = "def test(): pass"
        test_files = ["test1.py", "test2.py"]
        
        key1 = cache_manager._generate_cache_key(code, test_files)
        key2 = cache_manager._generate_cache_key(code, test_files)
        
        # Same inputs should produce same key
        assert key1 == key2
        
        # Different inputs should produce different keys
        key3 = cache_manager._generate_cache_key(code + " ", test_files)
        assert key1 != key3
    
    def test_basic_cache_operations(self, cache_manager):
        """Test basic get/set operations."""
        code = "def hello(): return 'world'"
        test_files = ["test_hello.py"]
        result = {"passed": 1, "failed": 0}
        
        # Cache miss
        assert cache_manager.get(code, test_files) is None
        assert cache_manager._statistics.cache_misses == 1
        
        # Set value
        cache_manager.set(code, test_files, result)
        
        # Cache hit
        cached_result = cache_manager.get(code, test_files)
        assert cached_result == result
        assert cache_manager._statistics.cache_hits == 1
    
    def test_cache_with_feature_id(self, cache_manager):
        """Test caching with feature ID."""
        code = "def feature(): pass"
        test_files = ["test_feature.py"]
        result = {"passed": 1}
        
        # Set with feature ID
        cache_manager.set(code, test_files, result, feature_id="feature_123")
        
        # Get without feature ID should miss
        assert cache_manager.get(code, test_files) is None
        
        # Get with correct feature ID should hit
        assert cache_manager.get(code, test_files, feature_id="feature_123") == result
    
    def test_cache_eviction_by_size(self, cache_manager):
        """Test cache eviction when size limit is reached."""
        # Set small max size (1KB)
        cache_manager.max_size_bytes = 1024
        
        # Add entries until size limit is exceeded
        large_result = {"data": "x" * 500}  # ~500 bytes when serialized
        
        cache_manager.set("code1", ["test1.py"], large_result)
        cache_manager.set("code2", ["test2.py"], large_result)
        cache_manager.set("code3", ["test3.py"], large_result)  # Should trigger eviction
        
        # First entry should be evicted
        assert cache_manager.get("code1", ["test1.py"]) is None
        assert cache_manager._statistics.evictions > 0
    
    def test_cache_eviction_by_count(self):
        """Test cache eviction when entry limit is reached."""
        cache = TestCacheManager(max_entries=3)
        
        # Add 4 entries
        for i in range(4):
            cache.set(f"code{i}", [f"test{i}.py"], {"result": i})
        
        # First entry should be evicted
        assert cache.get("code0", ["test0.py"]) is None
        assert len(cache._cache) == 3
    
    def test_dependency_extraction(self, cache_manager):
        """Test dependency extraction from code."""
        code = """
from module1 import func1
import module2
require('module3')
# filename: src/file1.py
"""
        
        deps = cache_manager._extract_dependencies(code)
        
        assert "module1.py" in deps or "module1/func1.py" in deps
        assert "module2.py" in deps
        assert "module3.py" in deps
        assert "src/file1.py" in deps
    
    def test_invalidate_by_file(self, cache_manager):
        """Test cache invalidation by file change."""
        code_with_dep = """
import helper
def test(): return helper.func()
"""
        
        # Cache result with dependency
        cache_manager.set(code_with_dep, ["test.py"], {"passed": 1})
        
        # Should be in cache
        assert cache_manager.get(code_with_dep, ["test.py"]) is not None
        
        # Invalidate by changing dependent file
        count = cache_manager.invalidate_by_file("helper.py")
        
        # Should be invalidated
        assert count > 0
        assert cache_manager.get(code_with_dep, ["test.py"]) is None
    
    def test_invalidate_by_feature(self, cache_manager):
        """Test cache invalidation by feature."""
        code = "def test(): pass"
        
        # Cache multiple entries for same feature
        cache_manager.set(code, ["test1.py"], {"result": 1}, feature_id="feat_1")
        cache_manager.set(code, ["test2.py"], {"result": 2}, feature_id="feat_1")
        cache_manager.set(code, ["test3.py"], {"result": 3}, feature_id="feat_2")
        
        # Invalidate feature 1
        count = cache_manager.invalidate_by_feature("feat_1")
        assert count == 2
        
        # Feature 1 entries should be gone
        assert cache_manager.get(code, ["test1.py"], feature_id="feat_1") is None
        assert cache_manager.get(code, ["test2.py"], feature_id="feat_1") is None
        
        # Feature 2 should still exist
        assert cache_manager.get(code, ["test3.py"], feature_id="feat_2") is not None
    
    def test_cache_statistics(self, cache_manager):
        """Test cache statistics tracking."""
        # Perform various operations
        cache_manager.get("code", ["test.py"])  # Miss
        cache_manager.set("code", ["test.py"], {"result": 1})
        cache_manager.get("code", ["test.py"])  # Hit
        cache_manager.get("code", ["test.py"])  # Hit
        
        stats = cache_manager.get_statistics()
        
        assert stats["total_requests"] == 3
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == "66.7%"
        assert stats["entries"] == 1
    
    def test_cache_clear(self, cache_manager):
        """Test clearing the cache."""
        # Add some entries
        cache_manager.set("code1", ["test1.py"], {"result": 1})
        cache_manager.set("code2", ["test2.py"], {"result": 2})
        
        assert len(cache_manager._cache) == 2
        
        # Clear cache
        cache_manager.clear()
        
        assert len(cache_manager._cache) == 0
        assert cache_manager._statistics.total_size_bytes == 0
    
    def test_persistent_cache(self, tmp_path):
        """Test persistent cache save/load."""
        cache_file = tmp_path / "test_cache.json"
        
        # Create cache with persistent storage
        cache1 = TestCacheManager(persistent_cache_path=cache_file)
        
        # Add entries
        cache1.set("code1", ["test1.py"], {"result": 1})
        cache1.set("code2", ["test2.py"], {"result": 2})
        
        # Save cache
        cache1.save_persistent_cache()
        assert cache_file.exists()
        
        # Create new cache and load
        cache2 = TestCacheManager(persistent_cache_path=cache_file)
        
        # Should have loaded entries
        assert cache2.get("code1", ["test1.py"]) == {"result": 1}
        assert cache2.get("code2", ["test2.py"]) == {"result": 2}
    
    def test_performance_analysis(self, cache_manager):
        """Test cache performance analysis."""
        # Create some cache activity
        for i in range(10):
            cache_manager.set(f"code{i}", [f"test{i}.py"], {"result": i})
        
        # Access some entries multiple times
        for _ in range(5):
            cache_manager.get("code0", ["test0.py"])
            cache_manager.get("code1", ["test1.py"])
        
        analysis = cache_manager.analyze_cache_performance()
        
        assert "insights" in analysis
        assert "top_entries" in analysis
        assert len(analysis["top_entries"]) > 0
        
        # Top entries should be the most accessed
        top_entry = analysis["top_entries"][0]
        assert top_entry["hits"] >= 5


class TestGlobalCache:
    """Test global cache instance."""
    
    def test_global_cache_singleton(self):
        """Test that global cache returns same instance."""
        cache1 = get_test_cache()
        cache2 = get_test_cache()
        
        assert cache1 is cache2
    
    def test_global_cache_with_custom_path(self, tmp_path):
        """Test global cache with custom persistent path."""
        cache_path = tmp_path / "custom_cache.json"
        
        # Reset global instance
        import workflows.mvp_incremental.test_cache_manager
        workflows.mvp_incremental.test_cache_manager._global_cache = None
        
        cache = get_test_cache(persistent_path=cache_path)
        
        # Add entry
        cache.set("test_code", ["test.py"], {"passed": 1})
        cache.save_persistent_cache()
        
        assert cache_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])