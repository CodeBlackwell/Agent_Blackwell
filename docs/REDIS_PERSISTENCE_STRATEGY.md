# Redis State Persistence Strategy for Job-Oriented Architecture

## Overview
This document outlines the Redis-based persistence strategy for the new job-oriented architecture, supporting the Job and Task models defined in `src/api/v1/chatops/models.py`.

## Storage Strategy

### Job Storage
- **Key Pattern**: `job:{job_id}`
- **Data Structure**: Redis Hash
- **Fields**:
  - `job_id`: Unique identifier
  - `user_request`: Original user request text
  - `status`: Current JobStatus (planning, running, completed, failed, canceled)
  - `created_at`: ISO timestamp
  - `updated_at`: ISO timestamp
  - `task_count`: Number of associated tasks
  - `completed_tasks`: Number of completed tasks

### Task Storage
- **Key Pattern**: `task:{task_id}`
- **Data Structure**: Redis Hash
- **Fields**:
  - `task_id`: Unique identifier
  - `job_id`: Parent job identifier
  - `agent_type`: Required agent type (spec, design, code, review, test)
  - `status`: Current TaskStatus (pending, queued, running, completed, failed)
  - `description`: Task description
  - `dependencies`: JSON array of dependent task IDs
  - `result`: JSON-serialized task result (when completed)
  - `created_at`: ISO timestamp
  - `updated_at`: ISO timestamp

### Job-Task Relationships
- **Key Pattern**: `job:{job_id}:tasks`
- **Data Structure**: Redis Set
- **Purpose**: Store all task IDs belonging to a job for efficient lookup

### Task Dependencies
- **Key Pattern**: `task:{task_id}:dependencies`
- **Data Structure**: Redis Set
- **Purpose**: Store task IDs that must complete before this task can start

- **Key Pattern**: `task:{task_id}:dependents`
- **Data Structure**: Redis Set
- **Purpose**: Store task IDs that depend on this task (reverse lookup)

## Index Structures

### Jobs by Status
- **Key Pattern**: `jobs:status:{status}`
- **Data Structure**: Redis Set
- **Purpose**: Efficiently query jobs by status (planning, running, etc.)

### Tasks by Status
- **Key Pattern**: `tasks:status:{status}`
- **Data Structure**: Redis Set
- **Purpose**: Efficiently query tasks by status

### Tasks by Agent Type
- **Key Pattern**: `tasks:agent:{agent_type}`
- **Data Structure**: Redis Set
- **Purpose**: Find all tasks requiring a specific agent type

## Operations

### Job Operations
```python
# Create job
await redis.hset(f"job:{job_id}", mapping={
    "job_id": job_id,
    "user_request": user_request,
    "status": "planning",
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "task_count": 0,
    "completed_tasks": 0
})
await redis.sadd("jobs:status:planning", job_id)

# Update job status
await redis.hset(f"job:{job_id}", "status", new_status)
await redis.hset(f"job:{job_id}", "updated_at", datetime.utcnow().isoformat())
await redis.smove(f"jobs:status:{old_status}", f"jobs:status:{new_status}", job_id)

# Get job
job_data = await redis.hgetall(f"job:{job_id}")
task_ids = await redis.smembers(f"job:{job_id}:tasks")
```

### Task Operations
```python
# Create task
await redis.hset(f"task:{task_id}", mapping={
    "task_id": task_id,
    "job_id": job_id,
    "agent_type": agent_type,
    "status": "pending",
    "description": description,
    "dependencies": json.dumps(dependencies),
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
})
await redis.sadd(f"job:{job_id}:tasks", task_id)
await redis.sadd("tasks:status:pending", task_id)
await redis.sadd(f"tasks:agent:{agent_type}", task_id)

# Update task status
await redis.hset(f"task:{task_id}", "status", new_status)
await redis.hset(f"task:{task_id}", "updated_at", datetime.utcnow().isoformat())
await redis.smove(f"tasks:status:{old_status}", f"tasks:status:{new_status}", task_id)

# Handle dependencies
for dep_task_id in dependencies:
    await redis.sadd(f"task:{task_id}:dependencies", dep_task_id)
    await redis.sadd(f"task:{dep_task_id}:dependents", task_id)
```

## Cleanup Strategy

### TTL Settings
- Jobs: 30 days after completion/failure
- Tasks: 30 days after completion/failure
- Index entries: Cleaned up when parent objects expire

### Garbage Collection
- Periodic cleanup of orphaned index entries
- Removal of completed jobs older than retention period
- Cleanup of task dependency relationships for deleted tasks

## Performance Considerations

### Indexing
- All status-based queries use Redis Sets for O(1) membership testing
- Job-task relationships use Sets for efficient bulk operations
- Dependency graphs use Sets for fast dependency resolution

### Memory Optimization
- Use Redis Hash compression for job/task storage
- Implement lazy loading for task results (store large results separately)
- Consider Redis Streams for task execution history if needed

### Concurrency
- Use Redis transactions (MULTI/EXEC) for atomic state updates
- Implement optimistic locking for job status changes
- Use Redis Lua scripts for complex atomic operations

## Migration Strategy

### Phase 1: Dual Write
- Write to both old and new storage formats
- Read from new format with fallback to old format

### Phase 2: Migration
- Background process to migrate existing data
- Validation of migrated data integrity

### Phase 3: Cleanup
- Remove old storage format code
- Clean up legacy data structures

## Monitoring

### Key Metrics
- Job creation rate
- Task completion rate
- Average job duration
- Dependency resolution time
- Redis memory usage for job/task data

### Health Checks
- Verify Redis connectivity
- Check for orphaned tasks/jobs
- Validate dependency graph integrity
- Monitor index consistency

## Architecture Principles

### 1. Job-Oriented Data Model
- **Jobs** are the primary unit of work, containing multiple tasks
- **Tasks** are individual units of execution within a job
- **Dependencies** define task execution order and relationships
- **Events** provide real-time updates via Redis Streams

### 2. State Persistence Strategy
- **Redis Hashes**: Store structured job and task data
- **Redis Sets**: Manage relationships and indexes
- **Redis Streams**: Handle real-time event broadcasting
- **Redis Strings**: Store simple key-value configurations

### 3. Data Consistency
- Atomic operations for state transitions
- Transaction-based updates for related entities
- Event-driven architecture for real-time updates
- Optimistic locking for concurrent access

## Data Structures

### Job Storage

#### Primary Job Data
```
Key: job:{job_id}
Type: Hash
Fields:
  - job_id: UUID string
  - user_request: Original user request text
  - status: planning|running|completed|failed|canceled
  - priority: low|medium|high
  - tags: JSON array of string tags
  - created_at: ISO 8601 timestamp
  - updated_at: ISO 8601 timestamp
  - progress_completed_tasks: Integer count
  - progress_total_tasks: Integer count
  - progress_percentage: Float percentage
```

#### Job Status Indexes
```
Key: jobs:status:{status}
Type: Set
Members: job_id values
Purpose: Efficient querying by job status
```

#### Job Priority Indexes
```
Key: jobs:priority:{priority}
Type: Set
Members: job_id values
Purpose: Efficient querying by job priority
```

#### Job-Task Relationships
```
Key: job:{job_id}:tasks
Type: Set
Members: task_id values
Purpose: Track all tasks belonging to a job
```

### Task Storage

#### Primary Task Data
```
Key: task:{task_id}
Type: Hash
Fields:
  - task_id: UUID string
  - job_id: Parent job UUID
  - agent_type: design|code|review|test
  - status: pending|queued|running|completed|failed
  - description: Task description text
  - result: JSON serialized task result (optional)
  - created_at: ISO 8601 timestamp
  - updated_at: ISO 8601 timestamp
```

#### Task Status Indexes
```
Key: tasks:status:{status}
Type: Set
Members: task_id values
Purpose: Efficient querying by task status
```

#### Task Agent Type Indexes
```
Key: tasks:agent:{agent_type}
Type: Set
Members: task_id values
Purpose: Efficient querying by agent type
```

#### Task Dependencies
```
Key: task:{task_id}:dependencies
Type: Set
Members: task_id values of dependencies
Purpose: Track what tasks must complete before this task can run

Key: task:{task_id}:dependents
Type: Set
Members: task_id values of dependent tasks
Purpose: Track what tasks depend on this task completing
```

### Real-Time Event Streaming

#### Job-Specific Event Streams
```
Key: job-stream:{job_id}
Type: Stream
Purpose: Real-time events for specific job
Event Types:
  - job_status: Job status changes
  - task_status: Task status changes
  - task_result: Task completion with results
```

#### Global Event Stream
```
Key: global-job-stream
Type: Stream
Purpose: All job and task events across the system
Event Types: Same as job-specific streams
```

#### Agent Task Streams
```
Key: agent:{agent_type}:input
Type: Stream
Purpose: Task routing to specific agent types
Fields:
  - task_id: Task identifier
  - job_id: Parent job identifier
  - task_data: Serialized task information
```

### Agent Coordination

#### Agent Status Tracking
```
Key: agent:{agent_type}:status
Type: Hash
Fields:
  - status: active|inactive|busy
  - last_seen: ISO 8601 timestamp
  - current_task: task_id (if busy)
  - processed_count: Integer count of processed tasks
```

#### Task Queue Management
```
Key: task_queue:{agent_type}
Type: List
Purpose: FIFO queue for tasks awaiting agent processing
```

## Data Access Patterns

### Job Lifecycle Operations

#### 1. Job Creation
```python
async def create_job(job_data):
    job_id = str(uuid.uuid4())

    # Store primary job data
    await redis.hset(f"job:{job_id}", mapping={
        "job_id": job_id,
        "user_request": job_data.user_request,
        "status": "planning",
        "priority": job_data.priority,
        "tags": json.dumps(job_data.tags),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "progress_completed_tasks": 0,
        "progress_total_tasks": 0,
        "progress_percentage": 0.0
    })

    # Add to status index
    await redis.sadd("jobs:status:planning", job_id)

    # Add to priority index
    await redis.sadd(f"jobs:priority:{job_data.priority}", job_id)

    return job_id
```

#### 2. Job Status Update
```python
async def update_job_status(job_id, new_status):
    # Get current status for index management
    current_status = await redis.hget(f"job:{job_id}", "status")

    # Update job data
    await redis.hset(f"job:{job_id}", mapping={
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

    # Update status indexes
    if current_status:
        await redis.srem(f"jobs:status:{current_status}", job_id)
    await redis.sadd(f"jobs:status:{new_status}", job_id)

    # Publish event
    await redis.xadd(f"job-stream:{job_id}", {
        "event_type": "job_status",
        "job_id": job_id,
        "status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
```

### Task Lifecycle Operations

#### 1. Task Creation with Dependencies
```python
async def create_task(task_data):
    task_id = str(uuid.uuid4())

    # Store primary task data
    await redis.hset(f"task:{task_id}", mapping={
        "task_id": task_id,
        "job_id": task_data.job_id,
        "agent_type": task_data.agent_type,
        "status": "pending",
        "description": task_data.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

    # Add to job's task set
    await redis.sadd(f"job:{task_data.job_id}:tasks", task_id)

    # Add to status index
    await redis.sadd("tasks:status:pending", task_id)

    # Set up dependencies
    if task_data.dependencies:
        await redis.sadd(f"task:{task_id}:dependencies", *task_data.dependencies)

        # Add reverse dependencies
        for dep_task_id in task_data.dependencies:
            await redis.sadd(f"task:{dep_task_id}:dependents", task_id)

    return task_id
```

#### 2. Task Completion and Dependency Resolution
```python
async def complete_task(task_id, result=None):
    # Update task status
    update_data = {
        "status": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if result:
        update_data["result"] = json.dumps(result)

    await redis.hset(f"task:{task_id}", mapping=update_data)

    # Update status indexes
    await redis.srem("tasks:status:running", task_id)
    await redis.sadd("tasks:status:completed", task_id)

    # Get dependent tasks
    dependent_tasks = await redis.smembers(f"task:{task_id}:dependents")

    # Check if dependent tasks can now be queued
    for dep_task_id in dependent_tasks:
        dependencies = await redis.smembers(f"task:{dep_task_id}:dependencies")

        # Check if all dependencies are completed
        completed_deps = 0
        for dep_id in dependencies:
            dep_status = await redis.hget(f"task:{dep_id}", "status")
            if dep_status == "completed":
                completed_deps += 1

        # If all dependencies completed, queue the task
        if completed_deps == len(dependencies):
            await enqueue_task(dep_task_id)
```

### Real-Time Streaming Operations

#### 1. Event Publishing
```python
async def publish_task_event(job_id, task_id, event_type, data):
    event_data = {
        "event_type": event_type,
        "job_id": job_id,
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data
    }

    # Publish to job-specific stream
    await redis.xadd(f"job-stream:{job_id}", event_data)

    # Publish to global stream
    await redis.xadd("global-job-stream", event_data)
```

#### 2. Event Consumption
```python
async def consume_job_events(job_id, last_id="$"):
    while True:
        try:
            # Read from job-specific stream
            streams = await redis.xread({f"job-stream:{job_id}": last_id}, block=1000)

            for stream_name, messages in streams:
                for message_id, fields in messages:
                    # Process event
                    await process_event(fields)
                    last_id = message_id

        except Exception as e:
            logger.error(f"Error consuming events: {e}")
            await asyncio.sleep(1)
```

## Performance Optimizations

### 1. Connection Pooling
```python
# Redis connection pool configuration
redis_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    max_connections=20,
    retry_on_timeout=True,
    socket_keepalive=True,
    socket_keepalive_options={}
)
```

### 2. Batch Operations
```python
async def batch_update_tasks(task_updates):
    pipe = redis.pipeline()

    for task_id, updates in task_updates.items():
        pipe.hset(f"task:{task_id}", mapping=updates)

    await pipe.execute()
```

### 3. Index Maintenance
```python
async def cleanup_completed_jobs():
    # Remove old completed jobs from indexes
    completed_jobs = await redis.smembers("jobs:status:completed")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    for job_id in completed_jobs:
        created_at = await redis.hget(f"job:{job_id}", "created_at")
        if datetime.fromisoformat(created_at) < cutoff_date:
            await cleanup_job(job_id)
```

## Monitoring and Observability

### 1. Redis Health Checks
```python
async def redis_health_check():
    try:
        # Test basic connectivity
        await redis.ping()

        # Check memory usage
        info = await redis.info("memory")
        memory_usage = info["used_memory"]

        # Check stream lengths
        job_streams = await redis.keys("job-stream:*")
        stream_lengths = {}
        for stream in job_streams:
            length = await redis.xlen(stream)
            stream_lengths[stream] = length

        return {
            "status": "healthy",
            "memory_usage": memory_usage,
            "stream_lengths": stream_lengths
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 2. Performance Metrics
```python
async def get_redis_metrics():
    info = await redis.info()

    return {
        "connected_clients": info["connected_clients"],
        "total_commands_processed": info["total_commands_processed"],
        "keyspace_hits": info["keyspace_hits"],
        "keyspace_misses": info["keyspace_misses"],
        "used_memory": info["used_memory"],
        "used_memory_peak": info["used_memory_peak"]
    }
```

## Data Retention and Cleanup

### 1. Stream Trimming
```python
async def trim_old_streams():
    # Keep only last 1000 events per job stream
    job_streams = await redis.keys("job-stream:*")

    for stream in job_streams:
        await redis.xtrim(stream, maxlen=1000, approximate=True)
```

### 2. Completed Job Cleanup
```python
async def cleanup_old_jobs():
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    completed_jobs = await redis.smembers("jobs:status:completed")

    for job_id in completed_jobs:
        created_at = await redis.hget(f"job:{job_id}", "created_at")
        if datetime.fromisoformat(created_at) < cutoff_date:
            await delete_job_and_tasks(job_id)
```

## Security Considerations

### 1. Access Control
- Redis AUTH enabled in production
- Network-level access restrictions
- TLS encryption for Redis connections

### 2. Data Validation
- Input sanitization before Redis operations
- Schema validation for stored data
- Rate limiting for API endpoints

### 3. Audit Logging
- All state changes logged with timestamps
- User actions tracked in audit streams
- Security events monitored and alerted

## Disaster Recovery

### 1. Backup Strategy
- Redis RDB snapshots every 6 hours
- AOF (Append Only File) enabled for durability
- Cross-region backup replication

### 2. Recovery Procedures
- Point-in-time recovery from RDB snapshots
- AOF replay for recent changes
- Job state reconstruction from event streams

## Configuration

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_STREAM_TRIM_INTERVAL=3600
REDIS_CLEANUP_INTERVAL=86400
```

### Redis Configuration
```conf
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

This Redis persistence strategy provides a robust, scalable foundation for Agent Blackwell's job-oriented architecture with real-time streaming capabilities.
