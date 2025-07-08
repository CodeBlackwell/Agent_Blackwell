# API Reference

Complete reference documentation for the Multi-Agent Orchestrator REST API.

## 🚧 Under Construction

This documentation is currently being developed. For API usage, please refer to:
- [README.md](../../README.md#-rest-api) for API overview
- [API README](../../api/README.md) for implementation details

## Base URL

```
http://localhost:8000
```

## Endpoints

### POST /execute-workflow
Submit a new workflow execution request.

**Request Body:**
```json
{
  "requirements": "string",
  "workflow_type": "tdd|full|mvp_incremental|mvp_incremental_tdd",
  "max_retries": 3,
  "timeout_seconds": 300
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "pending",
  "message": "Workflow execution started"
}
```

### GET /workflow-status/{session_id}
Get the status and results of a workflow execution.

**Response:**
```json
{
  "session_id": "uuid",
  "status": "pending|running|completed|failed",
  "workflow_type": "string",
  "started_at": "datetime",
  "completed_at": "datetime",
  "result": {}
}
```

### GET /workflow-types
List all available workflow types.

**Response:**
```json
[
  {
    "name": "string",
    "description": "string",
    "requires_step_type": false
  }
]
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "datetime"
}
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Error Responses

All errors follow this format:
```json
{
  "error": "string",
  "message": "string",
  "status_code": 400
}
```

## Rate Limiting

No rate limiting is currently implemented. Use responsibly.

## Examples

See [Python API Example](../../README.md#api-usage-example) for usage examples.

---

[← Back to Reference](README.md) | [← Back to Docs](../README.md)