"""
Code Storage Manager for MVP Incremental Workflow

Provides efficient storage for accumulated code during feature implementation,
with automatic spillover to disk for large codebases.
"""

import os
import json
import tempfile
import shutil
import time
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field
import hashlib
import pickle

from workflows.logger import workflow_logger as logger


@dataclass
class StorageMetrics:
    """Metrics for storage usage and performance."""
    total_files: int = 0
    memory_files: int = 0
    disk_files: int = 0
    total_size_bytes: int = 0
    memory_size_bytes: int = 0
    disk_size_bytes: int = 0
    spillovers: int = 0
    retrievals_from_memory: int = 0
    retrievals_from_disk: int = 0


class CodeStorageManager:
    """
    Manages code storage with automatic memory/disk spillover.
    
    Features:
    - Memory-first storage with configurable threshold
    - Automatic spillover to disk for large files
    - File deduplication
    - Temporary directory management
    - Cleanup on context exit
    """
    
    def __init__(self,
                 memory_threshold_mb: int = 10,
                 max_memory_files: int = 100,
                 temp_dir_prefix: str = "tdd_code_"):
        """
        Initialize storage manager.
        
        Args:
            memory_threshold_mb: Max size in MB before spilling to disk
            max_memory_files: Max number of files to keep in memory
            temp_dir_prefix: Prefix for temporary directories
        """
        self.memory_threshold_bytes = memory_threshold_mb * 1024 * 1024
        self.max_memory_files = max_memory_files
        self.temp_dir_prefix = temp_dir_prefix
        
        # Storage containers
        self._memory_storage: Dict[str, str] = {}
        self._disk_storage: Dict[str, Path] = {}
        self._file_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self._metrics = StorageMetrics()
        
        # Temporary directory (created lazily)
        self._temp_dir: Optional[Path] = None
    
    def _get_temp_dir(self) -> Path:
        """Get or create temporary directory."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix=self.temp_dir_prefix))
            logger.debug(f"Created temporary directory: {self._temp_dir}")
        return self._temp_dir
    
    def _calculate_file_hash(self, content: str) -> str:
        """Calculate hash for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def store(self, filename: str, content: str) -> bool:
        """
        Store a code file.
        
        Args:
            filename: Name/path of the file
            content: File content
            
        Returns:
            True if stored successfully
        """
        # Calculate size and hash
        size_bytes = len(content.encode())
        file_hash = self._calculate_file_hash(content)
        
        # Check for duplicate
        if filename in self._file_metadata:
            existing_hash = self._file_metadata[filename].get("hash")
            if existing_hash == file_hash:
                logger.debug(f"Skipping duplicate file: {filename}")
                return True
        
        # Update metrics
        self._metrics.total_files += 1
        self._metrics.total_size_bytes += size_bytes
        
        # Store metadata
        self._file_metadata[filename] = {
            "size": size_bytes,
            "hash": file_hash,
            "in_memory": True
        }
        
        # Decide storage location
        if (size_bytes > self.memory_threshold_bytes or 
            len(self._memory_storage) >= self.max_memory_files):
            # Store on disk
            self._store_on_disk(filename, content, size_bytes)
        else:
            # Store in memory
            self._memory_storage[filename] = content
            self._metrics.memory_files += 1
            self._metrics.memory_size_bytes += size_bytes
            self._file_metadata[filename]["in_memory"] = True
            
        return True
    
    def _store_on_disk(self, filename: str, content: str, size_bytes: int):
        """Store file on disk."""
        # Create safe filename
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        disk_path = self._get_temp_dir() / safe_filename
        
        # Write to disk
        disk_path.write_text(content, encoding="utf-8")
        
        # Update storage references
        self._disk_storage[filename] = disk_path
        self._metrics.disk_files += 1
        self._metrics.disk_size_bytes += size_bytes
        
        # Ensure metadata exists
        if filename not in self._file_metadata:
            self._file_metadata[filename] = {
                "size": size_bytes,
                "hash": hashlib.md5(content.encode()).hexdigest(),
                "in_memory": False
            }
        else:
            self._file_metadata[filename]["in_memory"] = False
        
        # Remove from memory if it was there
        if filename in self._memory_storage:
            del self._memory_storage[filename]
            self._metrics.memory_files -= 1
            self._metrics.memory_size_bytes -= size_bytes
            self._metrics.spillovers += 1
        
        logger.debug(f"Stored {filename} on disk ({size_bytes} bytes)")
    
    def get(self, filename: str) -> Optional[str]:
        """
        Retrieve a stored file.
        
        Args:
            filename: Name/path of the file
            
        Returns:
            File content or None if not found
        """
        # Check memory first
        if filename in self._memory_storage:
            self._metrics.retrievals_from_memory += 1
            return self._memory_storage[filename]
        
        # Check disk
        if filename in self._disk_storage:
            disk_path = self._disk_storage[filename]
            if disk_path.exists():
                self._metrics.retrievals_from_disk += 1
                return disk_path.read_text(encoding="utf-8")
        
        return None
    
    def get_all(self) -> Dict[str, str]:
        """
        Retrieve all stored files.
        
        Returns:
            Dictionary of filename -> content
        """
        all_files = {}
        
        # Get from memory
        all_files.update(self._memory_storage)
        
        # Get from disk
        for filename, disk_path in self._disk_storage.items():
            if disk_path.exists():
                all_files[filename] = disk_path.read_text(encoding="utf-8")
        
        return all_files
    
    def update(self, updates: Dict[str, str]):
        """
        Update multiple files at once.
        
        Args:
            updates: Dictionary of filename -> content
        """
        for filename, content in updates.items():
            self.store(filename, content)
    
    def remove(self, filename: str) -> bool:
        """
        Remove a stored file.
        
        Args:
            filename: Name/path of the file
            
        Returns:
            True if removed successfully
        """
        removed = False
        
        # Remove from memory
        if filename in self._memory_storage:
            size = self._file_metadata[filename]["size"]
            del self._memory_storage[filename]
            self._metrics.memory_files -= 1
            self._metrics.memory_size_bytes -= size
            removed = True
        
        # Remove from disk
        if filename in self._disk_storage:
            disk_path = self._disk_storage[filename]
            if disk_path.exists():
                disk_path.unlink()
            size = self._file_metadata[filename]["size"]
            del self._disk_storage[filename]
            self._metrics.disk_files -= 1
            self._metrics.disk_size_bytes -= size
            removed = True
        
        # Remove metadata
        if filename in self._file_metadata:
            self._metrics.total_files -= 1
            self._metrics.total_size_bytes -= self._file_metadata[filename]["size"]
            del self._file_metadata[filename]
        
        return removed
    
    def clear(self):
        """Clear all stored files."""
        # Clear memory
        self._memory_storage.clear()
        
        # Clear disk files
        for disk_path in self._disk_storage.values():
            if disk_path.exists():
                disk_path.unlink()
        self._disk_storage.clear()
        
        # Clear metadata
        self._file_metadata.clear()
        
        # Reset metrics
        self._metrics = StorageMetrics()
        
        logger.debug("Cleared all stored files")
    
    def optimize_storage(self):
        """
        Optimize storage by moving large files to disk and small files to memory.
        """
        changes = 0
        
        # Check memory files that should be on disk
        for filename in list(self._memory_storage.keys()):
            size = self._file_metadata[filename]["size"]
            if size > self.memory_threshold_bytes:
                content = self._memory_storage[filename]
                self._store_on_disk(filename, content, size)
                changes += 1
        
        # Check disk files that could be in memory
        if len(self._memory_storage) < self.max_memory_files:
            candidates = [
                (fn, metadata["size"]) 
                for fn, metadata in self._file_metadata.items()
                if not metadata["in_memory"] and metadata["size"] <= self.memory_threshold_bytes
            ]
            candidates.sort(key=lambda x: x[1])  # Sort by size
            
            for filename, size in candidates:
                if len(self._memory_storage) >= self.max_memory_files:
                    break
                
                # Move to memory
                content = self.get(filename)
                if content:
                    self._memory_storage[filename] = content
                    self._metrics.memory_files += 1
                    self._metrics.memory_size_bytes += size
                    
                    # Remove from disk
                    if filename in self._disk_storage:
                        disk_path = self._disk_storage[filename]
                        if disk_path.exists():
                            disk_path.unlink()
                        del self._disk_storage[filename]
                        self._metrics.disk_files -= 1
                        self._metrics.disk_size_bytes -= size
                    
                    self._file_metadata[filename]["in_memory"] = True
                    changes += 1
        
        if changes > 0:
            logger.debug(f"Storage optimization: moved {changes} files")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get storage metrics."""
        return {
            "total_files": self._metrics.total_files,
            "memory_files": self._metrics.memory_files,
            "disk_files": self._metrics.disk_files,
            "total_size_mb": self._metrics.total_size_bytes / (1024 * 1024),
            "memory_size_mb": self._metrics.memory_size_bytes / (1024 * 1024),
            "disk_size_mb": self._metrics.disk_size_bytes / (1024 * 1024),
            "spillovers": self._metrics.spillovers,
            "retrievals_from_memory": self._metrics.retrievals_from_memory,
            "retrievals_from_disk": self._metrics.retrievals_from_disk,
            "memory_hit_rate": self._calculate_memory_hit_rate()
        }
    
    def _calculate_memory_hit_rate(self) -> float:
        """Calculate memory hit rate."""
        total_retrievals = (self._metrics.retrievals_from_memory + 
                          self._metrics.retrievals_from_disk)
        if total_retrievals == 0:
            return 0.0
        return (self._metrics.retrievals_from_memory / total_retrievals) * 100
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up temp directory: {e}")
            self._temp_dir = None
        
        self.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
    
    def save_snapshot(self, snapshot_path: Path) -> bool:
        """
        Save current state to a snapshot file.
        
        Args:
            snapshot_path: Path to save snapshot
            
        Returns:
            True if saved successfully
        """
        try:
            snapshot_data = {
                "files": self.get_all(),
                "metadata": self._file_metadata,
                "metrics": self.get_metrics()
            }
            
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use pickle for efficiency with large data
            with open(snapshot_path, "wb") as f:
                pickle.dump(snapshot_data, f)
            
            logger.info(f"Saved storage snapshot to {snapshot_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False
    
    def load_snapshot(self, snapshot_path: Path) -> bool:
        """
        Load state from a snapshot file.
        
        Args:
            snapshot_path: Path to load snapshot from
            
        Returns:
            True if loaded successfully
        """
        try:
            if not snapshot_path.exists():
                logger.warning(f"Snapshot file not found: {snapshot_path}")
                return False
            
            with open(snapshot_path, "rb") as f:
                snapshot_data = pickle.load(f)
            
            # Clear current state
            self.clear()
            
            # Restore files
            for filename, content in snapshot_data["files"].items():
                self.store(filename, content)
            
            logger.info(f"Loaded storage snapshot from {snapshot_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return False


class CodeAccumulator:
    """
    High-level interface for accumulating code during retries.
    Uses CodeStorageManager internally with retry-specific features.
    """
    
    def __init__(self, feature_id: str, memory_threshold_mb: int = 10):
        """
        Initialize code accumulator for a specific feature.
        
        Args:
            feature_id: Identifier for the feature being implemented
            memory_threshold_mb: Memory threshold before disk spillover
        """
        self.feature_id = feature_id
        self.storage = CodeStorageManager(
            memory_threshold_mb=memory_threshold_mb,
            temp_dir_prefix=f"tdd_code_{feature_id}_"
        )
        self.retry_history: List[Dict[str, Any]] = []
    
    def add_retry_attempt(self, 
                         retry_count: int, 
                         code_updates: Dict[str, str],
                         test_results: Optional[Dict[str, Any]] = None):
        """
        Add code from a retry attempt.
        
        Args:
            retry_count: Current retry attempt number
            code_updates: New/updated code files
            test_results: Optional test results for this attempt
        """
        # Store the updates
        self.storage.update(code_updates)
        
        # Record in history
        self.retry_history.append({
            "retry_count": retry_count,
            "files_updated": list(code_updates.keys()),
            "test_results": test_results,
            "timestamp": time.time()
        })
        
        # Optimize storage after each retry
        if retry_count > 0:
            self.storage.optimize_storage()
    
    def get_accumulated_code(self) -> Dict[str, str]:
        """Get all accumulated code across retries."""
        return self.storage.get_all()
    
    def get_retry_summary(self) -> Dict[str, Any]:
        """Get summary of retry attempts."""
        return {
            "feature_id": self.feature_id,
            "total_retries": len(self.retry_history),
            "retry_history": self.retry_history,
            "storage_metrics": self.storage.get_metrics()
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.storage.cleanup()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()