"""
Integration tests for agent coordination system.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from src.orchestrator.agent_health import AgentHealthMonitor, AgentStatus
from src.orchestrator.agent_discovery import AgentDiscoveryService, AgentRegistration
from src.orchestrator.agent_router import AgentRouter, RoutingRequest, TaskPriority, RoutingStrategy
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestAgentCoordination(BaseAgentIntegrationTest):
    """Test agent coordination system integration."""

    @pytest.fixture
    async def coordination_services(self, redis_client):
        """Initialize coordination services for testing."""
        from src.config.settings import get_settings
        settings = get_settings("test")
        redis_url = f"redis://{settings.redis.host}:{settings.redis.port}"
        
        # Initialize coordination components
        health_monitor = AgentHealthMonitor(
            redis_url=redis_url,
            heartbeat_interval=5,  # Short intervals for testing
            health_check_interval=10,
            offline_threshold=15
        )
        
        discovery_service = AgentDiscoveryService(
            redis_url=redis_url,
            health_monitor=health_monitor,
            discovery_interval=5,
            cleanup_interval=30,
            agent_timeout=20
        )
        
        agent_router = AgentRouter(
            redis_url=redis_url,
            health_monitor=health_monitor,
            discovery_service=discovery_service,
            default_strategy=RoutingStrategy.HEALTH_AWARE
        )
        
        # Start coordination services
        await health_monitor.start_monitoring()
        await discovery_service.start_discovery()
        # Agent router doesn't need explicit start method
        
        # Clear any existing data
        await redis_client.flushdb()
        
        services = {
            'health_monitor': health_monitor,
            'discovery_service': discovery_service,
            'agent_router': agent_router
        }
        
        yield services
        
        # Cleanup
        await health_monitor.stop_monitoring()
        await discovery_service.stop_discovery()

    async def test_agent_health_monitoring(self, coordination_services):
        """Test agent health monitoring functionality."""
        health_monitor = coordination_services['health_monitor']
        agent_id = "test_agent_001"
        
        # Register agent for monitoring
        await health_monitor.register_agent(agent_id, "test")
        
        # Record heartbeat
        await health_monitor.record_heartbeat(agent_id)
        
        # Get initial health metrics
        health = await health_monitor.get_agent_health(agent_id)
        self.assertIsNotNone(health)
        self.assertEqual(health["status"], AgentStatus.HEALTHY.value)
        self.assertEqual(health["total_tasks"], 0)
        
        # Record task start and completion
        task_id = "test_task_001"
        await health_monitor.record_task_start(agent_id, task_id)
        
        # Simulate task processing time
        await asyncio.sleep(0.1)
        
        await health_monitor.record_task_completion(agent_id, task_id, success=True)
        
        # Check updated health metrics
        updated_health = await health_monitor.get_agent_health(agent_id)
        self.assertEqual(updated_health["total_tasks"], 1)
        self.assertEqual(updated_health["successful_tasks"], 1)
        self.assertEqual(updated_health["success_rate"], 1.0)
        self.assertGreater(updated_health["health_score"], 0.8)

    async def test_agent_discovery_and_registration(self, coordination_services):
        """Test agent discovery and registration."""
        discovery_service = coordination_services['discovery_service']
        agent_id = "test_spec_agent_001"
        
        # Register agent
        await discovery_service.register_agent(
            agent_id=agent_id,
            agent_type="spec",
            agent_class="SpecAgent",
            capabilities=["requirements_analysis", "specification_writing"],
            version="1.0.0",
            max_concurrent_tasks=3,
            priority=100,
            tags=["spec", "test", "local"],
            metadata={"test": True}
        )
        
        # Verify registration
        agent_data = await discovery_service.get_agent(agent_id)
        self.assertIsNotNone(agent_data)
        self.assertEqual(agent_data["agent_type"], "spec")
        self.assertEqual(agent_data["agent_class"], "SpecAgent")
        self.assertIn("requirements_analysis", agent_data["capabilities"])
        
        # Test capability-based discovery
        agents = await discovery_service.find_agents_by_capability(
            required_capabilities=["requirements_analysis"],
            preferred_tags=["spec"]
        )
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]["agent_id"], agent_id)
        
        # Test finding best agent
        best_agent = await discovery_service.find_best_agent(
            agent_type="spec",
            required_capabilities=["requirements_analysis"]
        )
        self.assertIsNotNone(best_agent)
        self.assertEqual(best_agent["agent_id"], agent_id)

    async def test_intelligent_agent_routing(self, coordination_services):
        """Test intelligent agent routing with different strategies."""
        discovery_service = coordination_services['discovery_service']
        agent_router = coordination_services['agent_router']
        
        # Register multiple agents
        agents = [
            {
                "agent_id": "spec_agent_001",
                "agent_type": "spec",
                "priority": 100,
                "capabilities": ["requirements_analysis"]
            },
            {
                "agent_id": "spec_agent_002", 
                "agent_type": "spec",
                "priority": 80,
                "capabilities": ["requirements_analysis", "user_stories"]
            }
        ]
        
        for agent_config in agents:
            await discovery_service.register_agent(
                agent_id=agent_config["agent_id"],
                agent_type=agent_config["agent_type"],
                agent_class="SpecAgent",
                capabilities=agent_config["capabilities"],
                version="1.0.0",
                max_concurrent_tasks=5,
                priority=agent_config["priority"],
                tags=["spec", "test"]
            )
            
            # Register for health monitoring
            await coordination_services['health_monitor'].register_agent(
                agent_config["agent_id"], 
                agent_config["agent_type"]
            )
            await coordination_services['health_monitor'].record_heartbeat(agent_config["agent_id"])
        
        # Test routing request
        routing_request = RoutingRequest(
            task_id="test_task_001",
            task_type="spec",
            priority=TaskPriority.NORMAL,
            required_capabilities=["requirements_analysis"],
            preferred_tags=["spec"],
            max_retries=2,
            timeout_seconds=30
        )
        
        # Test priority-based routing
        agent_router.default_strategy = RoutingStrategy.PRIORITY_BASED
        result = await agent_router.route_task(routing_request)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.agent_id)
        self.assertEqual(result.routing_strategy, RoutingStrategy.PRIORITY_BASED)
        self.assertGreater(result.routing_time_ms, 0)
        
        # Should route to higher priority agent
        self.assertEqual(result.agent_id, "spec_agent_001")

    async def test_routing_with_load_balancing(self, coordination_services):
        """Test routing with load balancing."""
        discovery_service = coordination_services['discovery_service']
        agent_router = coordination_services['agent_router']
        
        # Register agents
        agent_ids = ["design_agent_001", "design_agent_002", "design_agent_003"]
        
        for agent_id in agent_ids:
            await discovery_service.register_agent(
                agent_id=agent_id,
                agent_type="design",
                agent_class="DesignAgent",
                capabilities=["system_design", "architecture_planning"],
                version="1.0.0",
                max_concurrent_tasks=2,
                priority=100,
                tags=["design", "test"]
            )
            
            await coordination_services['health_monitor'].register_agent(agent_id, "design")
            await coordination_services['health_monitor'].record_heartbeat(agent_id)
        
        # Simulate different loads
        await coordination_services['health_monitor'].record_task_start("design_agent_001", "task1")
        await coordination_services['health_monitor'].record_task_start("design_agent_001", "task2")
        await coordination_services['health_monitor'].record_task_start("design_agent_002", "task3")
        
        # Test least loaded routing
        agent_router.default_strategy = RoutingStrategy.LEAST_LOADED
        
        routing_request = RoutingRequest(
            task_id="test_task_002",
            task_type="design",
            priority=TaskPriority.NORMAL,
            required_capabilities=["system_design"]
        )
        
        result = await agent_router.route_task(routing_request)
        
        self.assertTrue(result.success)
        # Should route to least loaded agent (design_agent_003)
        self.assertEqual(result.agent_id, "design_agent_003")

    async def test_fault_tolerance_and_circuit_breaker(self, coordination_services):
        """Test fault tolerance and circuit breaker functionality."""
        discovery_service = coordination_services['discovery_service']
        health_monitor = coordination_services['health_monitor']
        
        agent_id = "failing_agent_001"
        
        # Register agent
        await discovery_service.register_agent(
            agent_id=agent_id,
            agent_type="test",
            agent_class="TestAgent",
            capabilities=["testing"],
            version="1.0.0",
            max_concurrent_tasks=5,
            priority=100,
            tags=["test"]
        )
        
        await health_monitor.register_agent(agent_id, "test")
        await health_monitor.record_heartbeat(agent_id)
        
        # Simulate multiple failures to trigger circuit breaker
        for i in range(5):
            task_id = f"failing_task_{i}"
            await health_monitor.record_task_start(agent_id, task_id)
            await asyncio.sleep(0.1)
            await health_monitor.record_task_completion(agent_id, task_id, success=False, error="Simulated failure")
        
        # Check that agent health degraded
        health = await health_monitor.get_agent_health(agent_id)
        self.assertLess(health["success_rate"], 0.5)
        self.assertLess(health["health_score"], 0.5)
        
        # Test routing with degraded agent
        routing_request = RoutingRequest(
            task_id="test_task_003",
            task_type="test",
            priority=TaskPriority.NORMAL,
            required_capabilities=["testing"]
        )
        
        # Should fail to route due to circuit breaker
        result = await coordination_services['agent_router'].route_task(routing_request)
        self.assertFalse(result.success)
        self.assertIn("circuit breaker", result.error_message.lower())

    async def test_agent_coordination_integration(self, coordination_services):
        """Test full integration of all coordination components."""
        discovery_service = coordination_services['discovery_service']
        health_monitor = coordination_services['health_monitor']
        agent_router = coordination_services['agent_router']
        
        # Register multiple agent types
        agent_configs = [
            {"id": "spec_agent_001", "type": "spec", "capabilities": ["requirements_analysis"]},
            {"id": "design_agent_001", "type": "design", "capabilities": ["system_design"]},
            {"id": "coding_agent_001", "type": "coding", "capabilities": ["code_generation"]},
        ]
        
        for config in agent_configs:
            await discovery_service.register_agent(
                agent_id=config["id"],
                agent_type=config["type"],
                agent_class=f"{config['type'].capitalize()}Agent",
                capabilities=config["capabilities"],
                version="1.0.0",
                max_concurrent_tasks=3,
                priority=100,
                tags=[config["type"], "integration_test"]
            )
            
            await health_monitor.register_agent(config["id"], config["type"])
            await health_monitor.record_heartbeat(config["id"])
        
        # Test routing to different agent types
        for config in agent_configs:
            routing_request = RoutingRequest(
                task_id=f"integration_task_{config['type']}",
                task_type=config["type"],
                priority=TaskPriority.NORMAL,
                required_capabilities=config["capabilities"]
            )
            
            result = await agent_router.route_task(routing_request)
            
            self.assertTrue(result.success, f"Failed to route {config['type']} task")
            self.assertEqual(result.agent_id, config["id"])
            
            # Record successful task completion
            await health_monitor.record_task_start(result.agent_id, routing_request.task_id)
            await health_monitor.record_task_completion(
                result.agent_id, routing_request.task_id, success=True
            )
        
        # Verify all agents have good health scores
        for config in agent_configs:
            health = await health_monitor.get_agent_health(config["id"])
            self.assertGreaterEqual(health["success_rate"], 1.0)
            self.assertGreaterEqual(health["health_score"], 0.8)

    async def test_routing_statistics_and_metrics(self, coordination_services):
        """Test routing statistics collection."""
        discovery_service = coordination_services['discovery_service']
        health_monitor = coordination_services['health_monitor']
        agent_router = coordination_services['agent_router']
        
        # Register agent
        agent_id = "metrics_agent_001"
        await discovery_service.register_agent(
            agent_id=agent_id,
            agent_type="test",
            agent_class="TestAgent",
            capabilities=["testing"],
            version="1.0.0",
            max_concurrent_tasks=5,
            priority=100,
            tags=["test", "metrics"]
        )
        
        await health_monitor.register_agent(agent_id, "test")
        await health_monitor.record_heartbeat(agent_id)
        
        # Perform multiple routing operations
        for i in range(5):
            routing_request = RoutingRequest(
                task_id=f"metrics_task_{i}",
                task_type="test",
                priority=TaskPriority.NORMAL,
                required_capabilities=["testing"]
            )
            
            result = await agent_router.route_task(routing_request)
            self.assertTrue(result.success)
            
            # Record task success
            await health_monitor.record_task_start(agent_id, routing_request.task_id)
            await health_monitor.record_task_completion(agent_id, routing_request.task_id, success=True)
        
        # Get routing statistics
        stats = await agent_router.get_routing_statistics()
        
        self.assertGreaterEqual(stats["total_requests"], 5)
        self.assertGreaterEqual(stats["successful_routes"], 5)
        self.assertIn(agent_id, stats["agent_utilization"])
        self.assertGreaterEqual(stats["agent_utilization"][agent_id], 5)


if __name__ == "__main__":
    # Run tests
    import unittest
    unittest.main()
