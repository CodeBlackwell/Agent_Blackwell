"""Metrics module for Prometheus monitoring."""
import time

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Create a router for metrics endpoints
metrics_router = APIRouter()

# Define metrics
REQUESTS = Counter(
    "agent_blackwell_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

TASKS_CREATED = Counter(
    "agent_blackwell_tasks_created_total", "Total tasks created", ["agent_type"]
)

TASKS_COMPLETED = Counter(
    "agent_blackwell_tasks_completed_total",
    "Total tasks completed",
    ["agent_type", "status"],
)

REQUEST_LATENCY = Histogram(
    "agent_blackwell_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)


class PrometheusMiddleware:
    """Middleware to track request metrics."""

    def __init__(self, app):
        """Initialize middleware with the application."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process request and record metrics."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope["method"]
        path = scope["path"]

        # Original response
        original_send = send

        # Track status code
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await original_send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            # Record 500 on exceptions
            status_code = 500
            raise exc
        finally:
            # Record metrics
            if status_code and path != "/metrics":  # Don't track metrics endpoint
                REQUESTS.labels(
                    method=method, endpoint=path, status_code=status_code
                ).inc()
                REQUEST_LATENCY.labels(method=method, endpoint=path).observe(
                    time.time() - start_time
                )


@metrics_router.get("/metrics")
async def metrics():
    """Endpoint that returns Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
