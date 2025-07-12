"""
Cache manager for full workflow to improve performance.
"""
import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Represents a cached workflow result."""
    key: str
    value: Any
    phase: str
    timestamp: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry has expired."""
        age = datetime.now() - self.timestamp
        return age.total_seconds() > ttl_seconds


class WorkflowCacheManager:
    """Manages caching for workflow phases to improve performance."""
    
    def __init__(self, 
                 enable_cache: bool = True,
                 default_ttl: int = 3600,  # 1 hour default TTL
                 max_cache_size: int = 100):
        self.enable_cache = enable_cache
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CacheEntry] = {}
        self.phase_ttls = {
            "planner": 1800,     # 30 minutes
            "designer": 1800,    # 30 minutes  
            "coder": 900,        # 15 minutes
            "reviewer": 600,     # 10 minutes
            "executor": 300      # 5 minutes
        }
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
    def generate_cache_key(self, phase: str, input_data: str, context: Dict[str, Any] = None) -> str:
        """Generate a unique cache key for the input."""
        # Create a stable hash of the input
        key_parts = [phase, input_data]
        
        # Add relevant context that affects output
        if context:
            # Only include deterministic context
            deterministic_context = {
                k: v for k, v in context.items() 
                if k in ["requirements", "design_approach", "technology_stack"]
            }
            if deterministic_context:
                key_parts.append(json.dumps(deterministic_context, sort_keys=True))
                
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
        
    def get(self, phase: str, input_data: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """Retrieve cached result if available and not expired."""
        if not self.enable_cache:
            return None
            
        key = self.generate_cache_key(phase, input_data, context)
        
        if key in self.cache:
            entry = self.cache[key]
            ttl = self.phase_ttls.get(phase, self.default_ttl)
            
            if entry.is_expired(ttl):
                # Remove expired entry
                del self.cache[key]
                self.stats["expirations"] += 1
                self.stats["misses"] += 1
                return None
            else:
                # Cache hit
                entry.hit_count += 1
                self.stats["hits"] += 1
                print(f"📦 Cache hit for {phase} (hits: {entry.hit_count})")
                return entry.value
        else:
            self.stats["misses"] += 1
            return None
            
    def set(self, phase: str, input_data: str, value: Any, context: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """Store result in cache."""
        if not self.enable_cache:
            return
            
        # Check cache size limit
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()
            
        key = self.generate_cache_key(phase, input_data, context)
        
        entry = CacheEntry(
            key=key,
            value=value,
            phase=phase,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.cache[key] = entry
        print(f"💾 Cached result for {phase}")
        
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
            
        # Find entry with oldest timestamp and lowest hit count
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].timestamp, -self.cache[k].hit_count)
        )
        
        del self.cache[lru_key]
        self.stats["evictions"] += 1
        
    def invalidate_phase(self, phase: str):
        """Invalidate all cache entries for a specific phase."""
        keys_to_remove = [
            key for key, entry in self.cache.items() 
            if entry.phase == phase
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
            
        if keys_to_remove:
            print(f"🗑️ Invalidated {len(keys_to_remove)} cache entries for {phase}")
            
    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        print("🗑️ Cache cleared")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "enabled": self.enable_cache,
            "size": len(self.cache),
            "max_size": self.max_cache_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"],
            "phases_cached": list(set(entry.phase for entry in self.cache.values()))
        }
        
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about cached entries."""
        info = []
        for key, entry in self.cache.items():
            ttl = self.phase_ttls.get(entry.phase, self.default_ttl)
            age = (datetime.now() - entry.timestamp).total_seconds()
            remaining = max(0, ttl - age)
            
            info.append({
                "phase": entry.phase,
                "hit_count": entry.hit_count,
                "age_seconds": int(age),
                "ttl_remaining": int(remaining),
                "metadata": entry.metadata
            })
            
        return sorted(info, key=lambda x: x["hit_count"], reverse=True)


class SmartCacheStrategy:
    """Intelligent caching strategy based on workflow patterns."""
    
    def __init__(self, cache_manager: WorkflowCacheManager):
        self.cache_manager = cache_manager
        self.pattern_tracker = {
            "repeated_requirements": {},
            "similar_inputs": {},
            "phase_dependencies": {}
        }
        
    def should_cache(self, phase: str, input_data: str, execution_time: float) -> bool:
        """Determine if a result should be cached based on patterns."""
        # Always cache expensive operations
        if execution_time > 5.0:  # More than 5 seconds
            return True
            
        # Cache if we've seen similar input before
        input_hash = hashlib.md5(input_data.encode()).hexdigest()[:8]
        if input_hash in self.pattern_tracker["similar_inputs"]:
            self.pattern_tracker["similar_inputs"][input_hash] += 1
            if self.pattern_tracker["similar_inputs"][input_hash] > 2:
                return True
        else:
            self.pattern_tracker["similar_inputs"][input_hash] = 1
            
        # Phase-specific rules
        if phase in ["planner", "designer"]:
            # These phases are more stable, cache more aggressively
            return execution_time > 2.0
        elif phase == "coder":
            # Coder output changes frequently, be selective
            return execution_time > 10.0
            
        return False
        
    def optimize_cache_ttl(self, phase: str, change_frequency: float) -> int:
        """Dynamically adjust TTL based on change frequency."""
        base_ttl = self.cache_manager.phase_ttls.get(phase, self.cache_manager.default_ttl)
        
        # If content changes frequently, reduce TTL
        if change_frequency > 0.5:  # Changes more than 50% of the time
            return int(base_ttl * 0.5)
        elif change_frequency < 0.1:  # Changes less than 10% of the time
            return int(base_ttl * 2.0)
            
        return base_ttl