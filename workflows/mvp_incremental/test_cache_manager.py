"""
Enhanced Test Cache Manager for MVP Incremental Workflow

Provides intelligent caching for test results with dependency tracking,
cache invalidation, and performance monitoring.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from collections import OrderedDict

from workflows.logger import workflow_logger as logger


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata."""
    key: str
    result: Any
    code_hash: str
    test_files_hash: str
    dependencies: Set[str]
    timestamp: float
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    
    def is_valid(self, max_age_seconds: int = 3600) -> bool:
        """Check if cache entry is still valid."""
        age = time.time() - self.timestamp
        return age < max_age_seconds


@dataclass
class CacheStatistics:
    """Statistics for cache performance monitoring."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_size_bytes: int = 0
    evictions: int = 0
    invalidations: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "total_size_mb": self.total_size_bytes / (1024 * 1024),
            "evictions": self.evictions,
            "invalidations": self.invalidations
        }


class TestCacheManager:
    """
    Intelligent cache manager for test results with dependency tracking.
    
    Features:
    - Content-based cache keys (hash of code + test files)
    - Dependency tracking for smart invalidation
    - LRU eviction policy
    - Performance statistics
    - Persistent cache option
    """
    
    def __init__(self, 
                 max_size_mb: int = 100,
                 max_entries: int = 1000,
                 max_age_seconds: int = 3600,
                 persistent_cache_path: Optional[Path] = None):
        """
        Initialize cache manager.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            max_entries: Maximum number of cache entries
            max_age_seconds: Maximum age for cache entries
            persistent_cache_path: Optional path for persistent cache storage
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.max_age_seconds = max_age_seconds
        self.persistent_cache_path = persistent_cache_path
        
        # Use OrderedDict for LRU implementation
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._dependencies: Dict[str, Set[str]] = {}  # file -> cache keys
        self._feature_entries: Dict[str, Set[str]] = {}  # feature_id -> cache keys
        self._statistics = CacheStatistics()
        
        # Load persistent cache if available
        if self.persistent_cache_path and self.persistent_cache_path.exists():
            self._load_persistent_cache()
    
    def _generate_cache_key(self, 
                           code: str, 
                           test_files: List[str],
                           feature_id: Optional[str] = None) -> str:
        """Generate a unique cache key based on content."""
        # Combine code and sorted test files for consistent hashing
        content = f"{code}::{'|'.join(sorted(test_files))}"
        if feature_id:
            content = f"{feature_id}::{content}"
        
        # Use SHA256 for consistent hashing
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _extract_dependencies(self, code: str) -> Set[str]:
        """Extract file dependencies from code."""
        dependencies = set()
        
        # Look for import statements and file references
        import_patterns = [
            r'from\s+(\S+)\s+import',
            r'import\s+(\S+)',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'#\s*filename:\s*(\S+)'
        ]
        
        import re
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                # Handle different match types
                if pattern == r'#\s*filename:\s*(\S+)':
                    # Filename comments - use as-is
                    dependencies.add(match)
                else:
                    # Import statements - convert module paths to file paths
                    if '.' in match and '/' not in match:
                        file_path = match.replace('.', '/') + '.py'
                    else:
                        file_path = match + '.py'
                    dependencies.add(file_path)
        
        return dependencies
    
    def get(self, 
            code: str, 
            test_files: List[str],
            feature_id: Optional[str] = None) -> Optional[Any]:
        """
        Get cached test result if available and valid.
        
        Args:
            code: The implementation code
            test_files: List of test files
            feature_id: Optional feature identifier
            
        Returns:
            Cached test result or None if not found/invalid
        """
        self._statistics.total_requests += 1
        
        # Generate cache key
        cache_key = self._generate_cache_key(code, test_files, feature_id)
        
        # Check if entry exists
        if cache_key not in self._cache:
            self._statistics.cache_misses += 1
            logger.debug(f"Cache miss for key: {cache_key[:8]}...")
            return None
        
        # Get entry and check validity
        entry = self._cache[cache_key]
        if not entry.is_valid(self.max_age_seconds):
            # Remove invalid entry
            self._invalidate_entry(cache_key)
            self._statistics.cache_misses += 1
            logger.debug(f"Cache entry expired for key: {cache_key[:8]}...")
            return None
        
        # Update LRU order and statistics
        self._cache.move_to_end(cache_key)
        entry.hit_count += 1
        entry.last_accessed = time.time()
        self._statistics.cache_hits += 1
        
        logger.debug(f"Cache hit for key: {cache_key[:8]}... (hits: {entry.hit_count})")
        return entry.result
    
    def set(self,
            code: str,
            test_files: List[str],
            result: Any,
            feature_id: Optional[str] = None) -> str:
        """
        Cache a test result.
        
        Args:
            code: The implementation code
            test_files: List of test files
            result: Test result to cache
            feature_id: Optional feature identifier
            
        Returns:
            Cache key for the entry
        """
        # Generate cache key and hashes
        cache_key = self._generate_cache_key(code, test_files, feature_id)
        code_hash = hashlib.md5(code.encode()).hexdigest()
        test_files_hash = hashlib.md5('|'.join(sorted(test_files)).encode()).hexdigest()
        
        # Extract dependencies
        dependencies = self._extract_dependencies(code)
        
        # Calculate size
        size_bytes = len(pickle.dumps(result))
        
        # Check if we need to evict entries
        self._evict_if_needed(size_bytes)
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            result=result,
            code_hash=code_hash,
            test_files_hash=test_files_hash,
            dependencies=dependencies,
            timestamp=time.time(),
            size_bytes=size_bytes
        )
        
        # Add to cache
        self._cache[cache_key] = entry
        self._statistics.total_size_bytes += size_bytes
        
        # Update dependency tracking
        for dep in dependencies:
            if dep not in self._dependencies:
                self._dependencies[dep] = set()
            self._dependencies[dep].add(cache_key)
        
        # Update feature tracking
        if feature_id:
            if feature_id not in self._feature_entries:
                self._feature_entries[feature_id] = set()
            self._feature_entries[feature_id].add(cache_key)
        
        logger.debug(f"Cached result for key: {cache_key[:8]}... (size: {size_bytes} bytes)")
        return cache_key
    
    def invalidate_by_file(self, file_path: str) -> int:
        """
        Invalidate all cache entries that depend on a specific file.
        
        Args:
            file_path: Path of the modified file
            
        Returns:
            Number of entries invalidated
        """
        if file_path not in self._dependencies:
            return 0
        
        # Get all cache keys that depend on this file
        affected_keys = self._dependencies[file_path].copy()
        
        # Invalidate each entry
        count = 0
        for key in affected_keys:
            if key in self._cache:
                self._invalidate_entry(key)
                count += 1
        
        logger.info(f"Invalidated {count} cache entries due to change in {file_path}")
        return count
    
    def invalidate_by_feature(self, feature_id: str) -> int:
        """
        Invalidate all cache entries for a specific feature.
        
        Args:
            feature_id: Feature identifier
            
        Returns:
            Number of entries invalidated
        """
        count = 0
        
        # Get all cache keys for this feature
        if feature_id in self._feature_entries:
            keys_to_remove = list(self._feature_entries[feature_id])
            
            # Remove entries
            for key in keys_to_remove:
                self._invalidate_entry(key)
                count += 1
            
            # Clear feature tracking
            del self._feature_entries[feature_id]
        
        logger.info(f"Invalidated {count} cache entries for feature {feature_id}")
        return count
    
    def _invalidate_entry(self, cache_key: str):
        """Invalidate a single cache entry."""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        
        # Update statistics
        self._statistics.total_size_bytes -= entry.size_bytes
        self._statistics.invalidations += 1
        
        # Remove from dependencies
        for dep in entry.dependencies:
            if dep in self._dependencies:
                self._dependencies[dep].discard(cache_key)
                if not self._dependencies[dep]:
                    del self._dependencies[dep]
        
        # Remove entry
        del self._cache[cache_key]
    
    def _evict_if_needed(self, new_size: int):
        """Evict entries if cache limits are exceeded."""
        # Check size limit
        while (self._statistics.total_size_bytes + new_size > self.max_size_bytes or
               len(self._cache) >= self.max_entries) and self._cache:
            # Remove oldest entry (LRU)
            oldest_key = next(iter(self._cache))
            self._invalidate_entry(oldest_key)
            self._statistics.evictions += 1
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._dependencies.clear()
        self._statistics.total_size_bytes = 0
        self._statistics.invalidations += count
        logger.info(f"Cleared {count} cache entries")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        stats = self._statistics.to_dict()
        stats.update({
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "dependencies_tracked": len(self._dependencies)
        })
        return stats
    
    def save_persistent_cache(self):
        """Save cache to persistent storage."""
        if not self.persistent_cache_path:
            return
        
        try:
            self.persistent_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            # Convert CacheEntry objects to serializable format
            entries_data = {}
            for k, v in self._cache.items():
                entry_dict = asdict(v)
                # Convert set to list for JSON serialization
                entry_dict["dependencies"] = list(entry_dict["dependencies"])
                entries_data[k] = entry_dict
            
            cache_data = {
                "entries": entries_data,
                "dependencies": {k: list(v) for k, v in self._dependencies.items()},
                "statistics": asdict(self._statistics),
                "timestamp": time.time()
            }
            
            # Save as JSON (more portable than pickle)
            with open(self.persistent_cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Saved {len(self._cache)} cache entries to {self.persistent_cache_path}")
        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")
    
    def _load_persistent_cache(self):
        """Load cache from persistent storage."""
        try:
            with open(self.persistent_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Restore cache entries
            for key, entry_dict in cache_data.get("entries", {}).items():
                # Convert dict back to CacheEntry
                entry_dict["dependencies"] = set(entry_dict["dependencies"])
                entry = CacheEntry(**entry_dict)
                
                # Only load if still valid
                if entry.is_valid(self.max_age_seconds):
                    self._cache[key] = entry
            
            # Restore dependencies
            for file_path, keys in cache_data.get("dependencies", {}).items():
                self._dependencies[file_path] = set(keys)
            
            # Update statistics
            self._statistics.total_size_bytes = sum(e.size_bytes for e in self._cache.values())
            
            logger.info(f"Loaded {len(self._cache)} cache entries from persistent storage")
        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")
    
    def analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyze cache performance and provide insights."""
        stats = self.get_statistics()
        
        # Add performance insights
        insights = []
        
        # Get numeric hit rate
        hit_rate = self._statistics.hit_rate
        
        if hit_rate < 30:
            insights.append("Low hit rate - consider increasing cache size or TTL")
        elif hit_rate > 80:
            insights.append("Excellent hit rate - cache is performing well")
        
        if stats["evictions"] > stats["entries"]:
            insights.append("High eviction rate - consider increasing max_entries")
        
        if stats["total_size_mb"] > stats["max_size_mb"] * 0.9:
            insights.append("Cache near size limit - monitor for evictions")
        
        # Find most hit entries
        top_entries = sorted(
            self._cache.values(),
            key=lambda e: e.hit_count,
            reverse=True
        )[:5]
        
        stats["insights"] = insights
        stats["top_entries"] = [
            {
                "key": e.key[:8] + "...",
                "hits": e.hit_count,
                "age_minutes": (time.time() - e.timestamp) / 60
            }
            for e in top_entries
        ]
        
        return stats


# Global cache instance
_global_cache: Optional[TestCacheManager] = None


def get_test_cache(persistent_path: Optional[Path] = None) -> TestCacheManager:
    """Get or create the global test cache instance."""
    global _global_cache
    
    if _global_cache is None:
        # Default to .cache directory in project root
        if persistent_path is None:
            persistent_path = Path(".cache/test_results_cache.json")
        
        _global_cache = TestCacheManager(
            max_size_mb=100,
            max_entries=1000,
            max_age_seconds=3600,
            persistent_cache_path=persistent_path
        )
    
    return _global_cache