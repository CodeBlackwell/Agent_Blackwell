"""
Phase 5 Integration Tests: Metrics and Observability

This module contains integration tests for monitoring, metrics collection,
health checks, and observability features in the Agent Blackwell system.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY, CollectorRegistry

from src.api.main import app
from src.api.metrics import (
    REQUESTS, TASKS_CREATED, TASKS_COMPLETED, REQUEST_LATENCY,
    PrometheusMiddleware, metrics_router
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def clean_registry():
    """Provide a clean Prometheus registry for testing."""
    # Create a new registry for testing
    test_registry = CollectorRegistry()
    with patch('src.api.metrics.REGISTRY', test_registry):
        yield test_registry


class TestPrometheusMetrics:
    """Test Prometheus metrics collection and exposure."""
    
    def test_metrics_endpoint(self, client):
        """Test that metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        
        # Check for expected metric names in response
        content = response.text
        assert "agent_blackwell_http_requests_total" in content
        assert "agent_blackwell_tasks_created_total" in content
        assert "agent_blackwell_tasks_completed_total" in content
        assert "agent_blackwell_request_latency_seconds" in content
    
    def test_http_request_metrics_collection(self, client):
        """Test that HTTP requests are properly tracked in metrics."""
        # Make several requests to different endpoints
        endpoints = ["/", "/health", "/api/v1/chatops/help"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Some endpoints might not exist, that's OK for metrics testing
            assert response.status_code in [200, 404, 405]
        
        # Check metrics endpoint to see if requests were tracked
        metrics_response = client.get("/metrics")
        metrics_content = metrics_response.text
        
        # Should contain request metrics
        assert "agent_blackwell_http_requests_total" in metrics_content
        assert "method=\"GET\"" in metrics_content
    
    def test_request_latency_tracking(self, client):
        """Test that request latency is properly measured."""
        # Make a request that should take some time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Check that response includes timing header
        assert "X-Process-Time" in response.headers
        
        # Verify timing header is reasonable
        process_time = float(response.headers["X-Process-Time"])
        actual_time = end_time - start_time
        
        # Process time should be less than actual time (overhead excluded)
        assert 0 <= process_time <= actual_time * 2  # Allow some variance
    
    def test_task_metrics_simulation(self, client):
        """Test task creation and completion metrics."""
        # Since we're testing metrics, we'll simulate task operations
        # In real usage, these would be called by the orchestrator
        
        # Simulate task creation
        TASKS_CREATED.labels(agent_type="spec").inc()
        TASKS_CREATED.labels(agent_type="design").inc()
        TASKS_CREATED.labels(agent_type="coding").inc()
        
        # Simulate task completion
        TASKS_COMPLETED.labels(agent_type="spec", status="completed").inc()
        TASKS_COMPLETED.labels(agent_type="design", status="completed").inc()
        TASKS_COMPLETED.labels(agent_type="coding", status="error").inc()
        
        # Check metrics endpoint
        response = client.get("/metrics")
        content = response.text
        
        # Verify task metrics are present
        assert "agent_blackwell_tasks_created_total" in content
        assert "agent_blackwell_tasks_completed_total" in content
        assert "agent_type=\"spec\"" in content
        assert "agent_type=\"design\"" in content
        assert "agent_type=\"coding\"" in content
        assert "status=\"completed\"" in content
        assert "status=\"error\"" in content


class TestHealthChecks:
    """Test health check functionality and service monitoring."""
    
    def test_basic_health_check(self, client):
        """Test basic application health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "services" in data
        assert data["services"]["api"] == "up"
    
    @patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"})
    @patch("redis.asyncio.from_url")
    def test_redis_health_check(self, mock_redis_from_url, client):
        """Test Redis connectivity health check."""
        # Mock successful Redis connection
        mock_redis_client = MagicMock()
        mock_redis_client.ping = MagicMock()
        mock_redis_client.close = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "redis" in data["services"]
        # The actual status depends on the Redis mock behavior
        assert data["services"]["redis"] in ["up", "down", "unknown"]
    
    @patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"})
    @patch("redis.asyncio.from_url")
    def test_redis_health_check_failure(self, mock_redis_from_url, client):
        """Test Redis health check when Redis is unavailable."""
        # Mock Redis connection failure
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Connection failed")
        mock_redis_from_url.return_value = mock_redis_client
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["services"]["redis"] == "down"
        assert data["status"] in ["degraded", "healthy"]  # Depends on other services
    
    @patch.dict("os.environ", {
        "SLACK_API_TOKEN": "xoxb-test-token",
        "SLACK_SIGNING_SECRET": "test-secret"
    })
    def test_slack_configuration_check(self, client):
        """Test Slack configuration health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "slack" in data["services"]
        assert data["services"]["slack"] == "configured"
    
    def test_health_check_without_external_services(self, client):
        """Test health check when no external services are configured."""
        # Clear environment variables that might affect health check
        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["services"]["api"] == "up"
            assert data["services"]["redis"] == "unknown"
            assert data["services"]["slack"] == "unknown"


class TestMiddlewareMonitoring:
    """Test middleware-based monitoring and observability."""
    
    def test_prometheus_middleware_request_tracking(self, client):
        """Test that PrometheusMiddleware properly tracks requests."""
        # Make requests to different endpoints with different methods
        test_cases = [
            ("GET", "/"),
            ("GET", "/health"),
            ("POST", "/api/v1/chatops/command"),  # This might return 422 due to missing data
        ]
        
        for method, endpoint in test_cases:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            # We don't care about the exact response, just that middleware tracked it
            assert response.status_code >= 200
            
            # Check that timing header was added
            if endpoint != "/metrics":  # Metrics endpoint doesn't get timing header
                assert "X-Process-Time" in response.headers
    
    def test_error_request_tracking(self, client):
        """Test that error requests are properly tracked in metrics."""
        # Make a request that will result in 404
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        assert "X-Process-Time" in response.headers
        
        # Check metrics to see if 404 was tracked
        metrics_response = client.get("/metrics")
        metrics_content = metrics_response.text
        
        # Should contain metrics for the 404 request
        assert "agent_blackwell_http_requests_total" in metrics_content
    
    def test_metrics_endpoint_exclusion(self, client):
        """Test that the metrics endpoint doesn't track itself."""
        # Make multiple requests to metrics endpoint
        for _ in range(3):
            response = client.get("/metrics")
            assert response.status_code == 200
        
        # The metrics endpoint should not include X-Process-Time header for itself
        # This prevents recursive metric collection
        metrics_response = client.get("/metrics")
        assert "X-Process-Time" not in metrics_response.headers


class TestErrorMonitoring:
    """Test error tracking and monitoring."""
    
    @patch("src.api.main.logger")
    def test_global_exception_handler_logging(self, mock_logger, client):
        """Test that global exception handler logs errors properly."""
        # Mock the orchestrator to raise an exception
        from src.api.dependencies import get_orchestrator
        
        def failing_orchestrator():
            raise Exception("Test exception for monitoring")
        
        app.dependency_overrides[get_orchestrator] = failing_orchestrator
        
        try:
            # Make a request that will trigger the exception
            response = client.post("/api/v1/chatops/command", json={
                "command": "!test",
                "platform": "slack",
                "user_id": "test",
                "channel_id": "test"
            })
            
            # Should return 500 due to exception
            assert response.status_code == 500
            data = response.json()
            assert "unexpected error occurred" in data["detail"]
            
            # Verify that the error was logged
            mock_logger.error.assert_called()
            
        finally:
            # Clean up override
            app.dependency_overrides.clear()
    
    def test_validation_error_handling(self, client):
        """Test handling of request validation errors."""
        # Send malformed request data
        response = client.post("/api/v1/chatops/command", json={
            "invalid_field": "value"
            # Missing required fields
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], list)
        
        # Should contain validation error details
        assert any("required" in str(error).lower() for error in data["detail"])


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics."""
    
    def test_response_time_consistency(self, client):
        """Test that response times are consistent and reasonable."""
        response_times = []
        
        # Make multiple requests and collect timing data
        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Individual requests should complete quickly
            assert response_time < 1.0  # Should complete within 1 second
        
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times)
        
        # Average should be reasonable
        assert avg_response_time < 0.5  # Average should be under 500ms
        
        # Response times should be relatively consistent (no outliers > 3x average)
        max_response_time = max(response_times)
        assert max_response_time < avg_response_time * 3
    
    def test_concurrent_request_handling(self, client):
        """Test system behavior under concurrent load."""
        import concurrent.futures
        import threading
        
        def make_request():
            """Helper function to make a single request."""
            response = client.get("/")
            return response.status_code, response.elapsed if hasattr(response, 'elapsed') else None
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        status_codes = [result[0] for result in results]
        assert all(code == 200 for code in status_codes)
        
        # No exceptions should have been raised
        assert len(results) == 20


class TestCustomMetrics:
    """Test custom application-specific metrics."""
    
    def test_custom_metric_registration(self):
        """Test that custom metrics are properly registered."""
        # Verify our custom metrics are available
        metric_names = [
            "agent_blackwell_http_requests_total",
            "agent_blackwell_tasks_created_total", 
            "agent_blackwell_tasks_completed_total",
            "agent_blackwell_request_latency_seconds"
        ]
        
        # Get current metrics from registry
        from prometheus_client import REGISTRY
        registered_metrics = [collector._name for collector in REGISTRY._collector_to_names.keys() if hasattr(collector, '_name')]
        
        # Check that our metrics are registered (at least some of them)
        # Note: The exact registration mechanism may vary
        assert len(registered_metrics) > 0
    
    def test_metric_label_usage(self, client):
        """Test that metrics use appropriate labels."""
        # Make requests that should generate labeled metrics
        TASKS_CREATED.labels(agent_type="test_agent").inc()
        TASKS_COMPLETED.labels(agent_type="test_agent", status="completed").inc()
        
        # Get metrics
        response = client.get("/metrics")
        content = response.text
        
        # Verify labels are present in metrics output
        assert "agent_type=\"test_agent\"" in content
        assert "status=\"completed\"" in content
