# Agent Coordination Architecture

## Overview

The Agent Blackwell platform features a sophisticated agent coordination system that provides robust health monitoring, dynamic agent discovery and registration, and intelligent task routing with load balancing and fault tolerance. This document describes the architecture, components, and usage patterns.

## Architecture Components

### 1. Agent Health Monitor (`agent_health.py`)

The health monitoring system tracks the operational status and performance metrics of all agents in the system.

#### Key Features:
- **Real-time Health Tracking**: Monitors agent status (healthy, degraded, unhealthy, offline, initializing)
- **Performance Metrics**: Tracks task counts, success rates, response times, and current load
- **Heartbeat Management**: Maintains last-seen timestamps and detects offline agents
- **Health Score Calculation**: Combines multiple metrics into a unified health score (0.0-1.0)
- **Event Streaming**: Publishes health events to Redis streams for observability

#### Health Status Levels:
- `HEALTHY`: Agent is operating normally (health score > 0.8)
- `DEGRADED`: Agent has some issues but is functional (0.5 < health score ≤ 0.8)
- `UNHEALTHY`: Agent has significant problems (0.2 < health score ≤ 0.5)
- `OFFLINE`: Agent is not responding to heartbeats
- `INITIALIZING`: Agent is starting up

#### Usage Example:
```python
# Initialize health monitor
health_monitor = AgentHealthMonitor(
    redis_url="redis://localhost:6379",
    heartbeat_interval=30,
    health_check_interval=60,
    offline_threshold=120
)

# Register agent for monitoring
await health_monitor.register_agent("spec_agent_001", "spec")

# Record heartbeat
await health_monitor.record_heartbeat("spec_agent_001")

# Record task lifecycle
await health_monitor.record_task_start("spec_agent_001", "task_123")
await health_monitor.record_task_completion("spec_agent_001", "task_123", success=True)

# Get health metrics
health = await health_monitor.get_agent_health("spec_agent_001")
print(f"Health score: {health['health_score']}")
```

### 2. Agent Discovery Service (`agent_discovery.py`)

The discovery service manages dynamic agent registration and provides capability-based agent lookup.

#### Key Features:
- **Dynamic Registration**: Agents can register/deregister at runtime
- **Capability Indexing**: Efficient lookup by agent capabilities
- **Metadata Management**: Rich agent metadata including version, priority, tags
- **Event-Driven Discovery**: Listens for agent announcements via Redis streams
- **Automatic Cleanup**: Removes inactive agents based on timeout policies

#### Agent Registration Data:
```python
{
    "agent_id": "spec_agent_001",
    "agent_type": "spec",
    "agent_class": "SpecAgent",
    "capabilities": ["requirements_analysis", "specification_writing"],
    "version": "1.0.0",
    "max_concurrent_tasks": 5,
    "priority": 100,
    "tags": ["spec", "local", "orchestrator"],
    "metadata": {
        "initialized_at": "2024-01-01T00:00:00Z",
        "orchestrator_managed": True
    }
}
```

#### Usage Example:
```python
# Initialize discovery service
discovery_service = AgentDiscoveryService(
    redis_url="redis://localhost:6379",
    health_monitor=health_monitor,
    discovery_interval=30,
    cleanup_interval=300,
    agent_timeout=180
)

# Register agent
await discovery_service.register_agent(
    agent_id="design_agent_001",
    agent_type="design",
    agent_class="DesignAgent",
    capabilities=["system_design", "ui_design"],
    version="1.0.0",
    max_concurrent_tasks=3,
    priority=100,
    tags=["design", "local"]
)

# Find agents by capability
agents = await discovery_service.find_agents_by_capability(
    required_capabilities=["system_design"],
    preferred_tags=["design"]
)

# Find best agent for task
best_agent = await discovery_service.find_best_agent(
    agent_type="design",
    required_capabilities=["system_design"]
)
```

### 3. Agent Router (`agent_router.py`)

The intelligent routing system assigns tasks to the most suitable agents using various strategies.

#### Routing Strategies:
- **ROUND_ROBIN**: Distributes tasks evenly across available agents
- **LEAST_LOADED**: Routes to agents with the lowest current load
- **WEIGHTED_RANDOM**: Random selection weighted by agent priority
- **HEALTH_AWARE**: Considers agent health scores in routing decisions
- **PRIORITY_BASED**: Routes to highest priority agents first

#### Fault Tolerance Features:
- **Circuit Breaker**: Avoids routing to consistently failing agents
- **Automatic Retry**: Retries failed routing with fallback strategies
- **Load Balancing**: Distributes load based on agent capacity and current utilization

#### Usage Example:
```python
# Initialize router
agent_router = AgentRouter(
    redis_url="redis://localhost:6379",
    health_monitor=health_monitor,
    discovery_service=discovery_service,
    default_strategy=RoutingStrategy.HEALTH_AWARE
)

# Create routing request
routing_request = RoutingRequest(
    task_id="task_123",
    task_type="spec",
    priority=TaskPriority.HIGH,
    required_capabilities=["requirements_analysis"],
    preferred_tags=["spec"],
    max_retries=3,
    timeout_seconds=300
)

# Route task
result = await agent_router.route_with_retry(routing_request)

if result.success:
    print(f"Task routed to {result.agent_id} using {result.routing_strategy}")
else:
    print(f"Routing failed: {result.error_message}")
```

## Integration with Orchestrator

The orchestrator integrates all coordination components to provide seamless task management:

### Initialization
```python
# Orchestrator automatically initializes coordination components
orchestrator = Orchestrator(
    redis_url="redis://localhost:6379",
    is_test_mode=False
)

# Initialize agents and start coordination
orchestrator.initialize_agents()
await orchestrator.start_coordination()
```

### Enhanced Task Processing
The orchestrator now uses intelligent routing instead of simple stream-based task distribution:

1. **Task Creation**: Tasks are created with priority and capability requirements
2. **Intelligent Routing**: Router selects the best agent based on health, load, and capabilities
3. **Health Tracking**: Task lifecycle events are recorded for health monitoring
4. **Fault Tolerance**: Failed routing attempts trigger fallback strategies

## API Endpoints

The system exposes comprehensive REST API endpoints for agent management:

### Agent Management
- `GET /api/v1/agents/` - List all agents with filtering options
- `GET /api/v1/agents/{agent_id}` - Get detailed agent information
- `PUT /api/v1/agents/{agent_id}` - Update agent configuration
- `DELETE /api/v1/agents/{agent_id}` - Deregister agent

### Agent Discovery
- `POST /api/v1/agents/discover` - Find agents by capabilities and filters
- `POST /api/v1/agents/{agent_id}/heartbeat` - Send agent heartbeat

### Monitoring and Statistics
- `GET /api/v1/agents/routing/statistics` - Get routing performance metrics
- `GET /api/v1/agents/events/discovery` - Stream discovery events (SSE)
- `GET /api/v1/agents/events/health` - Stream health events (SSE)

### Example API Usage
```bash
# List all healthy agents
curl "http://localhost:8000/api/v1/agents/?status=healthy"

# Find agents with specific capabilities
curl -X POST "http://localhost:8000/api/v1/agents/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "required_capabilities": ["system_design"],
    "min_health_score": 0.8,
    "max_load": 3
  }'

# Get routing statistics
curl "http://localhost:8000/api/v1/agents/routing/statistics"

# Stream health events
curl "http://localhost:8000/api/v1/agents/events/health"
```

## Redis Data Structures

The coordination system uses several Redis data structures for persistence and communication:

### Health Monitoring
- `agent:health:{agent_id}` (Hash) - Agent health metrics
- `agent:health:events` (Stream) - Health change events

### Discovery Service
- `agent:registry:{agent_id}` (Hash) - Agent registration data
- `agent:capabilities:{capability}` (Set) - Agents by capability
- `agent:discovery:events` (Stream) - Discovery events

### Routing System
- `agent:routing:stats` (Hash) - Routing statistics
- `agent:routing:events` (Stream) - Routing decisions and events

## Configuration

### Environment Variables
```bash
# Redis connection
REDIS_URL=redis://localhost:6379

# Health monitoring intervals (seconds)
AGENT_HEARTBEAT_INTERVAL=30
AGENT_HEALTH_CHECK_INTERVAL=60
AGENT_OFFLINE_THRESHOLD=120

# Discovery service intervals (seconds)
AGENT_DISCOVERY_INTERVAL=30
AGENT_CLEANUP_INTERVAL=300
AGENT_TIMEOUT=180

# Routing configuration
DEFAULT_ROUTING_STRATEGY=health_aware
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

### Agent Configuration
Agents can be configured with the following parameters:

```python
{
    "max_concurrent_tasks": 5,      # Maximum parallel tasks
    "priority": 100,                # Routing priority (higher = preferred)
    "capabilities": [...],          # List of agent capabilities
    "tags": [...],                  # Tags for filtering and routing
    "version": "1.0.0",            # Agent version
    "metadata": {...}              # Additional metadata
}
```

## Monitoring and Observability

### Health Metrics
- Task success/failure rates
- Average response times
- Current load and capacity utilization
- Error rates and recent errors
- Overall health scores

### Routing Metrics
- Total routing requests
- Success/failure rates by strategy
- Average routing times
- Agent utilization distribution
- Circuit breaker activations

### Event Streams
Real-time events are published to Redis streams for monitoring:

- **Health Events**: Status changes, heartbeats, errors
- **Discovery Events**: Agent registration/deregistration
- **Routing Events**: Task assignments, failures, retries

## Best Practices

### Agent Implementation
1. **Regular Heartbeats**: Agents should send heartbeats every 30 seconds
2. **Capability Declaration**: Accurately declare agent capabilities
3. **Error Reporting**: Report task failures with detailed error information
4. **Graceful Shutdown**: Deregister when shutting down

### System Configuration
1. **Health Thresholds**: Tune health check intervals based on system load
2. **Circuit Breaker**: Configure appropriate failure thresholds
3. **Load Balancing**: Set realistic max_concurrent_tasks limits
4. **Monitoring**: Set up alerts for agent health degradation

### Performance Optimization
1. **Redis Optimization**: Use Redis clustering for high-scale deployments
2. **Connection Pooling**: Use connection pools for Redis clients
3. **Batch Operations**: Batch health updates and routing decisions
4. **Caching**: Cache frequently accessed agent metadata

## Troubleshooting

### Common Issues

#### Agents Not Discovered
- Check agent registration in Redis: `HGETALL agent:registry:{agent_id}`
- Verify heartbeat timestamps: `HGET agent:health:{agent_id} last_seen`
- Check discovery service logs for registration events

#### Routing Failures
- Verify agent health scores: `HGET agent:health:{agent_id} health_score`
- Check circuit breaker status in routing statistics
- Review required capabilities vs. available agents

#### Performance Issues
- Monitor Redis memory usage and connection counts
- Check health monitoring intervals and adjust if needed
- Review routing strategy performance in statistics

### Debugging Commands
```bash
# Check agent registration
redis-cli HGETALL agent:registry:spec_agent_001

# View health metrics
redis-cli HGETALL agent:health:spec_agent_001

# List recent health events
redis-cli XREAD STREAMS agent:health:events 0

# Check routing statistics
redis-cli HGETALL agent:routing:stats
```

## Future Enhancements

### Planned Features
1. **Auto-scaling**: Automatic agent scaling based on load
2. **Geographic Distribution**: Location-aware routing
3. **Advanced Metrics**: Machine learning-based health prediction
4. **Integration**: Kubernetes operator for agent management
5. **Security**: Authentication and authorization for agent registration

### Extension Points
The architecture is designed for extensibility:

- **Custom Routing Strategies**: Implement new routing algorithms
- **Health Metrics**: Add domain-specific health indicators
- **Event Handlers**: Custom handlers for coordination events
- **Storage Backends**: Alternative storage for agent metadata

This coordination system provides a robust foundation for scalable, observable, and fault-tolerant agent orchestration in the Agent Blackwell platform.
