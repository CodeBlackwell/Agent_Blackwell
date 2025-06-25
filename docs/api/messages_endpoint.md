# Messages Endpoint Documentation

## Overview

The `/api/v1/messages` endpoint provides direct access to inter-agent communication stored in Redis Streams. This allows for real-time observability and debugging of the orchestrator and agent interactions without requiring direct access to Redis CLI or GUI tools.

## Endpoint Details

- **URL**: `/api/v1/messages`
- **Method**: `GET`
- **Auth Required**: Depends on your API security configuration

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number_of_messages` | Integer | No | Limits the number of messages returned. If not provided, all messages will be returned. Must be greater than 0. |
| `task_id` | String | No | Filters messages to only include those related to the specified task ID. This searches both task and result fields for matching task_id values. |

### Response Format

```json
{
  "messages": [
    {
      "id": "1719436729173-0",
      "agent_id": "spec_agent",
      "content": "Task analysis complete. Breaking down into subtasks.",
      "timestamp": "1719436729173",
      "task_id": "task-123456"
    },
    {
      "id": "1719436729174-0",
      "agent_id": "design_agent",
      "content": "Received design task. Creating system architecture diagram.",
      "timestamp": "1719436729174",
      "task_id": "task-123456"
    }
  ]
}
```

> **Note**: The actual fields in each message will depend on what data your agents write to the Redis stream. The example above shows typical fields.

### Status Codes

- **200 OK**: Successfully retrieved messages
- **500 Internal Server Error**: Error occurred while fetching messages, details provided in response

## Example Requests

```bash
# Get all messages
curl -X GET "http://localhost:8000/api/v1/messages"

# Get only the 5 most recent messages
curl -X GET "http://localhost:8000/api/v1/messages?number_of_messages=5"

# Get all messages for a specific task
curl -X GET "http://localhost:8000/api/v1/messages?task_id=3a7c2e8f-1d92-4c08-9f2a-b3e7d301b86a"

# Get the 3 most recent messages for a specific task
curl -X GET "http://localhost:8000/api/v1/messages?task_id=3a7c2e8f-1d92-4c08-9f2a-b3e7d301b86a&number_of_messages=3"
```

## Usage Tips

1. **Monitoring Agent Progress**: Track tasks as they move through different agents in the system.
2. **Debugging**: When a task produces unexpected results, review the message stream to identify where the process deviated.
3. **Interview Demos**: Use this endpoint to show interviewers or stakeholders how agents collaborate in real-time.
4. **System Health**: Monitor message frequency and content to ensure the orchestrator is functioning properly.

## Environment Configuration

This endpoint relies on the following environment variables:

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
- `AGENT_MESSAGE_STREAM`: The name of the Redis stream to read (default: `orchestrator_tasks`)
