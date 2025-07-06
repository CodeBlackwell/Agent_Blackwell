# Docker Container Cleanup

This document describes the automatic Docker container cleanup feature implemented in the multi-agent system.

## Overview

The system now automatically cleans up Docker containers created by the executor agent at the end of workflows. This prevents resource leaks and ensures containers don't accumulate over time.

## How It Works

### 1. Workflow Manager Cleanup
The workflow manager (`workflows/workflow_manager.py`) automatically initiates cleanup after workflow completion:

- Extracts the session ID from executor results
- Calls `DockerEnvironmentManager.cleanup_session()` to remove containers
- Runs cleanup in a try-except block to prevent cleanup failures from breaking workflows
- Includes a `finally` block for backup cleanup on errors

### 2. API Layer Cleanup
The REST API (`api/orchestrator_api.py`) also performs cleanup:

- Cleans up after successful workflow execution
- Cleans up after workflow failures
- Logs cleanup operations for monitoring

### 3. Cleanup Process
The `DockerEnvironmentManager.cleanup_session()` method:

1. Finds all containers with the session ID label
2. Stops containers with a 5-second timeout
3. Removes containers
4. Cleans up associated Docker images

## Testing

Two test scripts are provided:

### test_docker_cleanup.py
Comprehensive test that:
- Runs a full TDD workflow
- Verifies containers are created during execution
- Confirms containers are cleaned up after completion
- Tests cleanup on workflow failure

### test_cleanup_simple.py
Simple test that:
- Counts executor containers before/after
- Uses the REST API to run a workflow
- Verifies cleanup happened

## Manual Cleanup

If needed, you can manually clean up all executor containers:

```python
from agents.executor.docker_manager import DockerEnvironmentManager
await DockerEnvironmentManager.cleanup_all_sessions()
```

Or using Docker CLI:
```bash
docker rm -f $(docker ps -a --filter "label=executor=true" -q)
```

## Configuration

Currently, cleanup is always enabled. Future enhancements could include:

- `DOCKER_CLEANUP_ENABLED` - Enable/disable automatic cleanup
- `DOCKER_CLEANUP_DELAY` - Delay before cleanup (for debugging)
- Per-workflow cleanup settings

## Monitoring

Cleanup operations are logged:

- Success: "✅ Docker cleanup completed for session: {session_id}"
- Failure: "⚠️ Docker cleanup failed: {error}"

Check logs to verify cleanup is working properly.

## Troubleshooting

If containers are not being cleaned up:

1. Check that the executor agent is running and outputting SESSION_ID
2. Verify Docker daemon is accessible
3. Check logs for cleanup errors
4. Run manual cleanup if needed

## Benefits

- **Resource Management**: Prevents container accumulation
- **Cost Savings**: Reduces resource usage
- **Stability**: Prevents Docker daemon overload
- **Security**: Removes potentially sensitive execution environments

## Implementation Details

The cleanup implementation ensures:
- Cleanup runs even if workflows fail
- Cleanup errors don't break workflows
- Both workflow manager and API perform cleanup
- Session-based cleanup (only affects specific session)