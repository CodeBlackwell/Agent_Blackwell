# Agent Blackwell API Documentation

## Overview

Agent Blackwell provides a comprehensive REST API for job management and real-time WebSocket streaming for live updates. The API is built with FastAPI and follows OpenAPI 3.0 standards.

**Base URL**: `http://localhost:8000`
**API Version**: v1
**Documentation**: `http://localhost:8000/docs` (Swagger UI)
**OpenAPI Spec**: `http://localhost:8000/openapi.json`

## Authentication

Currently, the API does not require authentication. Authentication and authorization will be added in future releases.

## Data Models

### Job

A job represents a high-level user request that gets broken down into executable tasks.

```json
{
  "job_id": "string (UUID)",
  "user_request": "string",
  "status": "planning | running | completed | failed | canceled",
  "tasks": [Task],
  "priority": "low | medium | high",
  "tags": ["string"],
  "progress": {
    "completed_tasks": "integer",
    "total_tasks": "integer",
    "percentage": "float"
  },
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Task

A task represents an individual unit of work within a job.

```json
{
  "task_id": "string (UUID)",
  "job_id": "string (UUID)",
  "agent_type": "design | code | review | test",
  "status": "pending | queued | running | completed | failed",
  "description": "string",
  "dependencies": ["string (task_id)"],
  "result": "any (optional)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

## REST API Endpoints

### Health Check

#### GET /health

Check API health status.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Job Management

#### POST /api/v1/jobs/

Create a new job.

**Request Body**:
```json
{
  "user_request": "Build a user authentication system",
  "priority": "high",
  "tags": ["auth", "security"]
}
```

**Response**: `201 Created`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_request": "Build a user authentication system",
  "status": "planning",
  "tasks": [],
  "priority": "high",
  "tags": ["auth", "security"],
  "progress": {
    "completed_tasks": 0,
    "total_tasks": 0,
    "percentage": 0.0
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request data
- `422 Unprocessable Entity`: Validation errors

#### GET /api/v1/jobs/{job_id}

Get job status and details.

**Path Parameters**:
- `job_id` (string, required): UUID of the job

**Response**: `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_request": "Build a user authentication system",
  "status": "running",
  "tasks": [
    {
      "task_id": "task-uuid-1",
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "agent_type": "design",
      "status": "completed",
      "description": "Design authentication system architecture",
      "dependencies": [],
      "result": "Authentication system design completed",
      "created_at": "2024-01-01T00:01:00Z",
      "updated_at": "2024-01-01T00:05:00Z"
    }
  ],
  "priority": "high",
  "tags": ["auth", "security"],
  "progress": {
    "completed_tasks": 1,
    "total_tasks": 4,
    "percentage": 25.0
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Job not found

#### GET /api/v1/jobs/{job_id}/tasks/{task_id}

Get specific task status and details.

**Path Parameters**:
- `job_id` (string, required): UUID of the job
- `task_id` (string, required): UUID of the task

**Response**: `200 OK`
```json
{
  "task_id": "task-uuid-1",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_type": "design",
  "status": "completed",
  "description": "Design authentication system architecture",
  "dependencies": [],
  "result": "Authentication system design completed",
  "created_at": "2024-01-01T00:01:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Job or task not found

#### POST /api/v1/jobs/{job_id}/cancel

Cancel a running job.

**Path Parameters**:
- `job_id` (string, required): UUID of the job

**Response**: `200 OK`
```json
{
  "message": "Job cancellation requested",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "canceled"
}
```

**Error Responses**:
- `404 Not Found`: Job not found
- `400 Bad Request`: Job cannot be canceled (already completed/failed)

#### GET /api/v1/jobs/

List jobs with optional filtering.

**Query Parameters**:
- `status` (string, optional): Filter by job status
- `priority` (string, optional): Filter by priority
- `limit` (integer, optional): Maximum number of jobs to return (default: 10)
- `offset` (integer, optional): Number of jobs to skip (default: 0)

**Response**: `200 OK`
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_request": "Build a user authentication system",
      "status": "running",
      "priority": "high",
      "tags": ["auth", "security"],
      "progress": {
        "completed_tasks": 1,
        "total_tasks": 4,
        "percentage": 25.0
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:05:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## WebSocket Streaming API

### Connection Endpoints

#### Job-Specific Updates

**Endpoint**: `ws://localhost:8000/api/v1/streaming/jobs/{job_id}`

Connect to receive real-time updates for a specific job.

**Path Parameters**:
- `job_id` (string, required): UUID of the job

**Connection Flow**:
1. Client connects to WebSocket endpoint
2. Server validates job exists
3. Client receives immediate job status
4. Client receives real-time updates as job progresses

#### Global Job Updates

**Endpoint**: `ws://localhost:8000/api/v1/streaming/jobs`

Connect to receive real-time updates for all jobs.

**Connection Flow**:
1. Client connects to WebSocket endpoint
2. Client receives real-time updates for all job activities

### WebSocket Message Format

All WebSocket messages are JSON formatted with the following structure:

```json
{
  "event_type": "string",
  "timestamp": "string (ISO 8601)",
  "data": "object"
}
```

### Event Types

#### Job Status Events

Sent when a job's status changes.

```json
{
  "event_type": "job_status",
  "timestamp": "2024-01-01T00:05:00Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "tasks": [...],
  "progress": {
    "completed_tasks": 1,
    "total_tasks": 4,
    "percentage": 25.0
  }
}
```

#### Task Status Events

Sent when a task's status changes.

```json
{
  "event_type": "task_status",
  "timestamp": "2024-01-01T00:05:00Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "task-uuid-1",
  "status": "completed",
  "agent_type": "design",
  "description": "Design authentication system architecture"
}
```

#### Task Result Events

Sent when a task completes with results.

```json
{
  "event_type": "task_result",
  "timestamp": "2024-01-01T00:05:00Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "task-uuid-1",
  "result": "Authentication system design completed with API specifications"
}
```

### WebSocket Client Examples

#### JavaScript Client

```javascript
// Connect to specific job updates
const jobId = '550e8400-e29b-41d4-a716-446655440000';
const ws = new WebSocket(`ws://localhost:8000/api/v1/streaming/jobs/${jobId}`);

ws.onopen = () => {
  console.log('Connected to job updates');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Job update:', update);

  switch (update.event_type) {
    case 'job_status':
      updateJobStatus(update);
      break;
    case 'task_status':
      updateTaskStatus(update);
      break;
    case 'task_result':
      displayTaskResult(update);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};

// Send ping to keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

#### Python Client

```python
import asyncio
import json
import websockets

async def job_updates_client(job_id):
    uri = f"ws://localhost:8000/api/v1/streaming/jobs/{job_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to job {job_id} updates")

        async for message in websocket:
            update = json.loads(message)
            print(f"Update: {update}")

            if update['event_type'] == 'job_status':
                print(f"Job status: {update['status']}")
            elif update['event_type'] == 'task_status':
                print(f"Task {update['task_id']} status: {update['status']}")
            elif update['event_type'] == 'task_result':
                print(f"Task result: {update['result']}")

# Run the client
asyncio.run(job_updates_client('550e8400-e29b-41d4-a716-446655440000'))
```

### Streaming Health Check

#### GET /api/v1/streaming/health

Check streaming service health and connection statistics.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "active_connections": {
    "total": 15,
    "job_specific": 10,
    "global": 5
  },
  "redis_streams": {
    "status": "connected",
    "active_streams": 3
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  },
  "timestamp": "string (ISO 8601)"
}
```

### Common Error Codes

- `JOB_NOT_FOUND`: Requested job does not exist
- `TASK_NOT_FOUND`: Requested task does not exist
- `INVALID_JOB_STATUS`: Job is in invalid state for operation
- `VALIDATION_ERROR`: Request data validation failed
- `REDIS_CONNECTION_ERROR`: Database connection issue

## Rate Limiting

Currently, no rate limiting is implemented. Rate limiting will be added in future releases.

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

- `limit`: Maximum number of items to return (default: 10, max: 100)
- `offset`: Number of items to skip (default: 0)

## Filtering and Sorting

Job listing supports filtering by:
- `status`: Job status
- `priority`: Job priority
- `tags`: Job tags (comma-separated)

Sorting will be added in future releases.

## SDK and Client Libraries

Official SDK libraries are planned for:
- Python
- JavaScript/TypeScript
- Go

## Changelog

### v0.2.0 (Current)
- Added job-oriented architecture
- Implemented real-time WebSocket streaming
- Added comprehensive job and task management APIs
- Added Redis state persistence

### v0.1.0
- Initial API implementation
- Basic agent orchestration
- Redis streams integration
