# TDD Architecture Guide

## Overview

This guide details the technical architecture of the Test-Driven Development (TDD) system implemented through Operation Red Yellow. The architecture enforces mandatory RED-YELLOW-GREEN phases with sophisticated orchestration, performance optimization, and comprehensive testing infrastructure.

## Core Architecture Components

### 1. Phase Management System

#### TDD Phase Tracker
**Location**: `workflows/mvp_incremental/tdd_phase_tracker.py`

The central component managing phase transitions:

```python
class TDDPhaseTracker:
    """Tracks and enforces TDD phase progression"""
    
    def __init__(self):
        self.current_phase = TDDPhase.RED
        self.phase_history = []
        self.phase_timings = {}
        
    def transition_to(self, new_phase: TDDPhase):
        """Validates and performs phase transitions"""
        if not self._is_valid_transition(new_phase):
            raise InvalidPhaseTransition()
```

**Key Features**:
- Strict phase progression enforcement
- Transition validation
- Phase timing tracking
- History maintenance

### 2. Phase Orchestrators

#### Red Phase Orchestrator
**Location**: `workflows/mvp_incremental/red_phase_orchestrator.py`

Manages the initial failing test phase:

```python
class RedPhaseOrchestrator:
    """Orchestrates RED phase - writing failing tests"""
    
    async def orchestrate(self, feature: Feature) -> TestFailureContext:
        # 1. Generate failing tests
        tests = await self.test_writer.write_tests(feature)
        
        # 2. Execute tests expecting failure
        results = await self.executor.run_tests(tests, expect_failure=True)
        
        # 3. Validate tests actually fail
        if results.all_passing:
            raise TestsShouldFailError()
            
        # 4. Create failure context for YELLOW phase
        return TestFailureContext(results)
```

**Responsibilities**:
- Test generation coordination
- Failure validation
- Context preparation for implementation

#### Yellow Phase Orchestrator
**Location**: `workflows/mvp_incremental/yellow_phase_orchestrator.py`

Manages the implementation and pre-review phase:

```python
class YellowPhaseOrchestrator:
    """Orchestrates YELLOW phase - implementation"""
    
    async def orchestrate(self, feature: Feature, failure_context: TestFailureContext):
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            # 1. Generate implementation with hints
            code = await self.coder.implement(feature, failure_context)
            
            # 2. Run tests
            results = await self.executor.run_tests(code)
            
            # 3. Check if ready for review
            if results.all_passing:
                return await self.request_review(code)
                
            # 4. Update failure context for retry
            failure_context.update(results)
            retry_count += 1
```

**Features**:
- Retry management with evolving hints
- Test progression tracking
- Review preparation

#### Green Phase Orchestrator
**Location**: `workflows/mvp_incremental/green_phase_orchestrator.py`

Manages the success phase:

```python
class GreenPhaseOrchestrator:
    """Orchestrates GREEN phase - success and completion"""
    
    async def orchestrate(self, feature: Feature, approved_code: Code):
        # 1. Final validation
        final_results = await self.executor.run_all_tests()
        
        # 2. Coverage check
        coverage = await self.get_test_coverage()
        if coverage < MIN_COVERAGE:
            raise InsufficientCoverageError()
            
        # 3. Generate metrics
        metrics = self.calculate_metrics()
        
        # 4. Celebrate success
        return CompletionReport(feature, metrics)
```

### 3. Performance Optimization Layer

#### Test Cache Manager
**Location**: `workflows/mvp_incremental/test_cache_manager.py`

High-performance caching system:

```python
class TestCacheManager:
    """Manages test result caching for performance"""
    
    def __init__(self, cache_size: int = 1000):
        self.cache = LRUCache(cache_size)
        self.hit_rate_tracker = HitRateTracker()
        
    async def get_or_run(self, test_id: str, test_func: Callable):
        # Check cache first
        if cached_result := self.cache.get(test_id):
            self.hit_rate_tracker.record_hit()
            return cached_result
            
        # Run test and cache result
        result = await test_func()
        self.cache.put(test_id, result)
        return result
```

**Performance Features**:
- LRU cache with configurable size
- 85%+ typical hit rate
- Async-safe operations
- Hit rate monitoring

#### Parallel Feature Processor
**Location**: `workflows/mvp_incremental/parallel_feature_processor.py`

Enables parallel processing of independent features:

```python
class ParallelFeatureProcessor:
    """Processes independent features in parallel"""
    
    async def process_features(self, features: List[Feature]):
        # 1. Build dependency graph
        graph = self.build_dependency_graph(features)
        
        # 2. Identify parallel groups
        parallel_groups = graph.get_parallel_groups()
        
        # 3. Process each group
        for group in parallel_groups:
            tasks = [self.process_feature(f) for f in group]
            await asyncio.gather(*tasks)
```

**Benefits**:
- 2.8x average speedup
- Dependency-aware scheduling
- Resource pooling
- Progress tracking

#### Code Storage Manager
**Location**: `workflows/mvp_incremental/code_storage_manager.py`

Efficient code storage with spillover:

```python
class CodeStorageManager:
    """Manages code storage with memory/disk spillover"""
    
    def __init__(self, memory_limit: int = 100_000_000):  # 100MB
        self.memory_store = {}
        self.disk_store = DiskStore()
        self.current_memory_usage = 0
        
    async def store(self, key: str, code: str):
        code_size = len(code.encode())
        
        if self.current_memory_usage + code_size > self.memory_limit:
            # Spill to disk
            await self.disk_store.write(key, code)
        else:
            # Store in memory
            self.memory_store[key] = code
            self.current_memory_usage += code_size
```

### 4. Test Infrastructure

#### Test Failure Context
**Location**: `workflows/mvp_incremental/test_failure_context.py`

Rich context for test failures:

```python
class TestFailureContext:
    """Provides context about test failures for better fixes"""
    
    def __init__(self, test_results: TestResults):
        self.failures = self.parse_failures(test_results)
        self.patterns = self.identify_patterns()
        self.hints = self.generate_hints()
        
    def generate_hints(self) -> List[ImplementationHint]:
        """Generates specific hints based on failure patterns"""
        hints = []
        
        for pattern in self.patterns:
            if pattern.type == FailureType.ASSERTION:
                hints.append(self._assertion_hint(pattern))
            elif pattern.type == FailureType.IMPORT:
                hints.append(self._import_hint(pattern))
            # ... more hint types
            
        return hints
```

#### TDD Retry Strategy
**Location**: `workflows/mvp_incremental/tdd_retry_strategy.py`

Intelligent retry with test-aware hints:

```python
class TDDRetryStrategy:
    """Implements test-driven retry strategies"""
    
    def get_retry_prompt(self, attempt: int, context: TestFailureContext) -> str:
        # Progressive strategies based on attempt
        if attempt == 1:
            return self._basic_hint_prompt(context)
        elif attempt == 2:
            return self._detailed_analysis_prompt(context)
        else:
            return self._comprehensive_debug_prompt(context)
```

### 5. Monitoring and Visualization

#### Progress Monitor
**Location**: `workflows/mvp_incremental/progress_monitor.py`

Real-time progress tracking:

```python
class ProgressMonitor:
    """Monitors and visualizes TDD progress"""
    
    def display_phase_progress(self, phase: TDDPhase, feature: str):
        """Shows real-time phase progress"""
        symbols = {
            TDDPhase.RED: "🔴",
            TDDPhase.YELLOW: "🟡", 
            TDDPhase.GREEN: "🟢"
        }
        
        print(f"{symbols[phase]} {phase.value} Phase - {feature}")
        self.show_progress_bar(phase)
        self.show_test_status(phase)
```

## Data Flow Architecture

### Phase Transition Flow

```
User Request
    ↓
Feature Parser
    ↓
┌─────────────────┐
│   RED Phase     │
│  Orchestrator   │
├─────────────────┤
│ • Test Writer   │
│ • Test Executor │
│ • Validator     │
└────────┬────────┘
         ↓
    Test Failure
    Context
         ↓
┌─────────────────┐
│  YELLOW Phase   │
│  Orchestrator   │
├─────────────────┤
│ • Coder Agent   │
│ • Test Runner   │
│ • Retry Logic   │
└────────┬────────┘
         ↓
    All Tests
    Passing
         ↓
┌─────────────────┐
│  GREEN Phase    │
│  Orchestrator   │
├─────────────────┤
│ • Reviewer      │
│ • Coverage Check│
│ • Metrics       │
└────────┬────────┘
         ↓
    Feature
    Complete
```

### Performance Optimization Flow

```
Test Execution Request
         ↓
    Cache Check
    ┌────┴────┐
    │ Hit?    │
    ├─────────┤
    │ Yes │ No│
    └──┬──┴──┬┘
       ↓     ↓
   Return  Execute
   Cached    Test
   Result     ↓
       ↓   Update
       ↓   Cache
       ↓     ↓
    Test Result
```

## Configuration Architecture

### Hierarchical Configuration

```python
# Global TDD Configuration
TDD_CONFIG = {
    "phases": {
        "red": RedPhaseConfig(),
        "yellow": YellowPhaseConfig(),
        "green": GreenPhaseConfig()
    },
    "performance": {
        "cache": CacheConfig(),
        "parallel": ParallelConfig(),
        "storage": StorageConfig()
    },
    "monitoring": {
        "progress": ProgressConfig(),
        "metrics": MetricsConfig()
    }
}
```

### Environment-Based Overrides

```python
# Development
if ENV == "development":
    TDD_CONFIG["performance"]["cache"]["size"] = 100
    TDD_CONFIG["phases"]["yellow"]["max_retries"] = 5

# Production
elif ENV == "production":
    TDD_CONFIG["performance"]["cache"]["size"] = 10000
    TDD_CONFIG["phases"]["yellow"]["max_retries"] = 3
```

## Integration Points

### Agent Integration

Each agent has specific integration points with the TDD system:

1. **Test Writer Agent**
   - Triggered during RED phase
   - Generates failing tests
   - Provides test specifications

2. **Coder Agent**
   - Active during YELLOW phase
   - Receives test failure context
   - Implements solutions

3. **Executor Agent**
   - Runs throughout all phases
   - Provides test results
   - Manages test environments

4. **Reviewer Agent**
   - Final approval in GREEN phase
   - Validates code quality
   - Ensures TDD compliance

### External System Integration

1. **MCP Filesystem**
   - Test file management
   - Code storage
   - Result persistence

2. **Docker Integration**
   - Isolated test execution
   - Environment management
   - Resource control

3. **REST API**
   - Phase status endpoints
   - Progress monitoring
   - Metric collection

## Best Practices for Extension

### Adding New Phase Orchestrators

```python
class CustomPhaseOrchestrator(BasePhaseOrchestrator):
    """Template for new phase orchestrators"""
    
    async def orchestrate(self, context: PhaseContext):
        # 1. Validate preconditions
        self.validate_entry_conditions(context)
        
        # 2. Execute phase logic
        result = await self.execute_phase_logic(context)
        
        # 3. Update metrics
        self.update_metrics(result)
        
        # 4. Prepare for next phase
        return self.prepare_transition(result)
```

### Implementing Custom Retry Strategies

```python
class CustomRetryStrategy(BaseRetryStrategy):
    """Template for custom retry strategies"""
    
    def should_retry(self, context: TestFailureContext) -> bool:
        # Custom retry logic
        pass
        
    def get_retry_hints(self, context: TestFailureContext) -> List[str]:
        # Custom hint generation
        pass
```

## Performance Considerations

### Memory Management
- Code storage spillover at 100MB threshold
- LRU cache eviction for test results
- Streaming responses for large outputs

### CPU Optimization
- Parallel test execution (2.8x speedup)
- Async I/O throughout
- Efficient dependency resolution

### Network Optimization
- Connection pooling for agents
- Batch operations where possible
- Result streaming

## Monitoring and Debugging

### Debug Logging

```python
# Enable detailed TDD logging
import logging
logging.getLogger('tdd.orchestrator').setLevel(logging.DEBUG)
logging.getLogger('tdd.phase').setLevel(logging.DEBUG)
```

### Performance Profiling

```python
# Enable performance metrics
from workflows.mvp_incremental.metrics import enable_profiling
enable_profiling()

# Access metrics
metrics = TDDMetrics.get_instance()
print(f"Cache hit rate: {metrics.cache_hit_rate}%")
print(f"Average phase duration: {metrics.avg_phase_duration}")
```

## Future Architecture Considerations

1. **Distributed Testing**
   - Multi-node test execution
   - Result aggregation
   - Load balancing

2. **Machine Learning Integration**
   - Predictive test generation
   - Intelligent retry strategies
   - Pattern-based optimization

3. **Cross-Language Support**
   - Language-agnostic phase orchestration
   - Universal test runner
   - Polyglot caching

---

[← Back to Architecture](README.md) | [← Back to Developer Guide](../README.md)