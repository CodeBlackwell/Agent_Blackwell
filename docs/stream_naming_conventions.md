# Redis Stream Naming Conventions

## Overview

This document outlines the standardized Redis stream naming conventions used throughout the Agent Blackwell system. Following these conventions ensures reliable message routing and environment-aware stream handling across both test and production environments.

## Canonical Format

The canonical format for agent-specific input streams is:

```
agent:<agent_type>:input
```

Examples:
- `agent:spec:input` - Input stream for the Spec Agent
- `agent:design:input` - Input stream for the Design Agent
- `agent:code:input` - Input stream for the Code Agent

## Environment-Specific Prefixes

In test environments, all stream names are prefixed with `test_`:

```
test_agent:<agent_type>:input
```

Examples:
- `test_agent:spec:input` - Test input stream for the Spec Agent
- `test_agent_tasks` - Generic test task stream

## Legacy Format Support

For backward compatibility in production environments only, the system also supports the legacy format with the `_agent` suffix:

```
agent:<agent_type>_agent:input
```

Examples:
- `agent:spec_agent:input` - Legacy input stream for the Spec Agent

**Note:** New code should always use the canonical format. Legacy formats are supported only for backward compatibility.

## Generic Streams

Generic streams for tasks and results follow these conventions:

- Production: `agent_tasks` and `agent_results`
- Test: `test_agent_tasks` and `test_agent_results`

## Implementation Details

### Environment Detection

The system detects the current environment based on:

1. Explicit `is_test_mode` flag in the Orchestrator
2. Stream name prefixes in the BaseAgentWorker

### Stream Name Normalization

When processing agent types:

1. Agent types with `_agent` suffix are normalized by removing the suffix
2. Stream names are constructed using the normalized agent type
3. In test mode, the `test_` prefix is applied to all stream names

### Stream Routing

- In test mode, all tasks are routed to the generic `test_agent_tasks` stream
- In production mode, tasks are routed to agent-specific streams using the canonical format

## Diagnostic Tools

The system provides diagnostic tools to verify stream routing:

- `Orchestrator.diagnose_task_routing(task_type)` - Logs detailed stream routing information
- Environment-aware logging with mode emojis (🧪 for test, 🚀 for production)

## Best Practices

1. Always use the canonical format for new code
2. Explicitly set the environment mode when initializing components
3. Use the provided helper methods for stream name generation
4. Check logs with environment indicators to verify correct routing
