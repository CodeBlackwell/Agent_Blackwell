"""
Unit tests for the code storage manager.

Tests memory/disk spillover, deduplication, and performance.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from workflows.mvp_incremental.code_storage_manager import (
    CodeStorageManager, StorageMetrics, CodeAccumulator
)


class TestStorageMetrics:
    """Test the StorageMetrics dataclass."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = StorageMetrics()
        assert metrics.total_files == 0
        assert metrics.memory_files == 0
        assert metrics.disk_files == 0
        assert metrics.spillovers == 0


class TestCodeStorageManager:
    """Test the CodeStorageManager class."""
    
    @pytest.fixture
    def storage_manager(self):
        """Create a test storage manager."""
        return CodeStorageManager(
            memory_threshold_mb=1,  # Small threshold for testing
            max_memory_files=5,
            temp_dir_prefix="test_tdd_code_"
        )
    
    @pytest.fixture(autouse=True)
    def cleanup(self, storage_manager):
        """Ensure cleanup after each test."""
        yield
        storage_manager.cleanup()
    
    def test_memory_storage(self, storage_manager):
        """Test storing files in memory."""
        content = "def hello(): return 'world'"
        
        # Store small file
        assert storage_manager.store("hello.py", content)
        
        # Should be in memory
        assert "hello.py" in storage_manager._memory_storage
        assert storage_manager._metrics.memory_files == 1
        assert storage_manager._metrics.disk_files == 0
        
        # Retrieve file
        retrieved = storage_manager.get("hello.py")
        assert retrieved == content
        assert storage_manager._metrics.retrievals_from_memory == 1
    
    def test_disk_spillover_by_size(self, storage_manager):
        """Test spillover to disk when file is too large."""
        # Create content larger than threshold (1MB)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        
        # Store large file
        assert storage_manager.store("large.py", large_content)
        
        # Should be on disk, not in memory
        assert "large.py" not in storage_manager._memory_storage
        assert "large.py" in storage_manager._disk_storage
        assert storage_manager._metrics.disk_files == 1
        assert storage_manager._metrics.memory_files == 0
        
        # Retrieve should work
        retrieved = storage_manager.get("large.py")
        assert retrieved == large_content
        assert storage_manager._metrics.retrievals_from_disk == 1
    
    def test_disk_spillover_by_count(self, storage_manager):
        """Test spillover when max memory files is reached."""
        # Fill memory to max capacity
        for i in range(6):  # Max is 5
            storage_manager.store(f"file{i}.py", f"content{i}")
        
        # Last file should be on disk
        assert storage_manager._metrics.memory_files == 5
        assert storage_manager._metrics.disk_files == 1
        assert "file5.py" in storage_manager._disk_storage
    
    def test_file_deduplication(self, storage_manager):
        """Test that duplicate files are not stored twice."""
        content = "def duplicate(): pass"
        
        # Store file
        storage_manager.store("file1.py", content)
        initial_size = storage_manager._metrics.total_size_bytes
        
        # Store same content again
        storage_manager.store("file1.py", content)
        
        # Size should not increase
        assert storage_manager._metrics.total_size_bytes == initial_size
        assert storage_manager._metrics.total_files == 1
    
    def test_get_all_files(self, storage_manager):
        """Test retrieving all files."""
        files = {
            "file1.py": "content1",
            "file2.py": "content2",
            "large.py": "x" * (2 * 1024 * 1024)  # Force to disk
        }
        
        # Store files
        for name, content in files.items():
            storage_manager.store(name, content)
        
        # Get all files
        all_files = storage_manager.get_all()
        
        assert len(all_files) == 3
        for name, content in files.items():
            assert all_files[name] == content
    
    def test_update_multiple_files(self, storage_manager):
        """Test updating multiple files at once."""
        updates = {
            "file1.py": "content1",
            "file2.py": "content2",
            "file3.py": "content3"
        }
        
        storage_manager.update(updates)
        
        assert storage_manager._metrics.total_files == 3
        for name, content in updates.items():
            assert storage_manager.get(name) == content
    
    def test_remove_file(self, storage_manager):
        """Test removing files."""
        # Store in memory
        storage_manager.store("memory.py", "small content")
        
        # Store on disk
        large_content = "x" * (2 * 1024 * 1024)
        storage_manager.store("disk.py", large_content)
        
        # Remove memory file
        assert storage_manager.remove("memory.py")
        assert storage_manager.get("memory.py") is None
        assert storage_manager._metrics.memory_files == 0
        
        # Remove disk file
        assert storage_manager.remove("disk.py")
        assert storage_manager.get("disk.py") is None
        assert storage_manager._metrics.disk_files == 0
    
    def test_clear_storage(self, storage_manager):
        """Test clearing all storage."""
        # Add various files
        storage_manager.store("file1.py", "content1")
        storage_manager.store("file2.py", "x" * (2 * 1024 * 1024))
        
        # Clear
        storage_manager.clear()
        
        assert len(storage_manager._memory_storage) == 0
        assert len(storage_manager._disk_storage) == 0
        assert storage_manager._metrics.total_files == 0
    
    def test_storage_optimization(self, storage_manager):
        """Test storage optimization."""
        # Store small file on disk (simulate)
        small_content = "small"
        storage_manager._store_on_disk("small.py", small_content, len(small_content))
        
        # Store large file in memory (simulate misconfiguration)
        storage_manager._memory_storage["large.py"] = "x" * (2 * 1024 * 1024)
        storage_manager._file_metadata["large.py"] = {
            "size": 2 * 1024 * 1024,
            "hash": "hash",
            "in_memory": True
        }
        
        # Optimize
        storage_manager.optimize_storage()
        
        # Large file should move to disk
        assert "large.py" not in storage_manager._memory_storage
        assert "large.py" in storage_manager._disk_storage
        
        # Small file should move to memory (if space available)
        if len(storage_manager._memory_storage) < storage_manager.max_memory_files:
            assert "small.py" in storage_manager._memory_storage
    
    def test_metrics_reporting(self, storage_manager):
        """Test metrics reporting."""
        # Create some activity
        storage_manager.store("file1.py", "content1")
        storage_manager.store("file2.py", "x" * (2 * 1024 * 1024))
        storage_manager.get("file1.py")
        storage_manager.get("file2.py")
        
        metrics = storage_manager.get_metrics()
        
        assert metrics["total_files"] == 2
        assert metrics["memory_files"] == 1
        assert metrics["disk_files"] == 1
        assert metrics["retrievals_from_memory"] == 1
        assert metrics["retrievals_from_disk"] == 1
        assert metrics["memory_hit_rate"] == 50.0
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with CodeStorageManager() as storage:
            storage.store("test.py", "content")
            temp_dir = storage._get_temp_dir()
            assert temp_dir.exists()
        
        # After exiting context, temp dir should be cleaned up
        assert not temp_dir.exists()
    
    def test_snapshot_save_load(self, tmp_path):
        """Test saving and loading snapshots."""
        snapshot_path = tmp_path / "snapshot.pkl"
        
        # Create and populate storage
        storage1 = CodeStorageManager()
        storage1.store("file1.py", "content1")
        storage1.store("file2.py", "content2")
        
        # Save snapshot
        assert storage1.save_snapshot(snapshot_path)
        assert snapshot_path.exists()
        
        # Load into new storage
        storage2 = CodeStorageManager()
        assert storage2.load_snapshot(snapshot_path)
        
        # Verify contents
        assert storage2.get("file1.py") == "content1"
        assert storage2.get("file2.py") == "content2"
        
        # Cleanup
        storage1.cleanup()
        storage2.cleanup()


class TestCodeAccumulator:
    """Test the CodeAccumulator class."""
    
    def test_basic_accumulation(self):
        """Test basic code accumulation."""
        with CodeAccumulator("feature_123") as acc:
            # First attempt
            acc.add_retry_attempt(0, {
                "main.py": "def feature(): pass"
            })
            
            # Second attempt with updates
            acc.add_retry_attempt(1, {
                "main.py": "def feature(): return True",
                "test.py": "def test_feature(): assert feature()"
            })
            
            # Get accumulated code
            all_code = acc.get_accumulated_code()
            assert len(all_code) == 2
            assert all_code["main.py"] == "def feature(): return True"
            assert "test.py" in all_code
    
    def test_retry_history(self):
        """Test retry history tracking."""
        with CodeAccumulator("feature_456") as acc:
            # Add attempts with test results
            acc.add_retry_attempt(0, {"main.py": "v1"}, {"passed": 0, "failed": 1})
            acc.add_retry_attempt(1, {"main.py": "v2"}, {"passed": 1, "failed": 0})
            
            summary = acc.get_retry_summary()
            
            assert summary["feature_id"] == "feature_456"
            assert summary["total_retries"] == 2
            assert len(summary["retry_history"]) == 2
            
            # Check first attempt
            first = summary["retry_history"][0]
            assert first["retry_count"] == 0
            assert first["test_results"]["failed"] == 1
    
    def test_large_accumulation_performance(self):
        """Test performance with large code accumulation."""
        # Set small memory threshold and max files to force spillover
        with CodeAccumulator("feature_perf", memory_threshold_mb=1) as acc:
            # Override max_memory_files to force spillover
            acc.storage.max_memory_files = 5
            
            # Simulate multiple retries with growing codebase
            for retry in range(3):
                updates = {}
                for i in range(10):
                    # Create large files - last retry files will be > 1MB
                    if retry == 2:
                        # Make files > 1MB to trigger size-based spillover
                        content = "x" * (1024 * 1024 + 100)  # Just over 1MB
                    else:
                        content = f"content_{retry}_{i}" * 1000
                    updates[f"file_{retry}_{i}.py"] = content
                
                acc.add_retry_attempt(retry, updates)
            
            # Should handle large accumulation efficiently
            all_code = acc.get_accumulated_code()
            assert len(all_code) == 30  # 3 retries * 10 files
            
            # Check storage metrics
            metrics = acc.storage.get_metrics()
            
            # Either spillovers should have happened OR we should have files on disk
            assert metrics["disk_files"] > 0 or metrics["spillovers"] > 0  # Should have spilled to disk
            assert metrics["memory_files"] <= 5  # Respects max memory files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])