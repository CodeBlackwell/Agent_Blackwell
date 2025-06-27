"""
Intelligent Agent Routing and Load Balancing System

This module provides intelligent task routing, load balancing, and fault tolerance
for the Agent Blackwell system, integrating with health monitoring and discovery services.
"""

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import redis.asyncio as aioredis
from redis import Redis

from .agent_health import AgentHealthMonitor, AgentStatus
from .agent_discovery import AgentDiscoveryService, AgentRegistration

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Task routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED_RANDOM = "weighted_random"
    HEALTH_AWARE = "health_aware"
    PRIORITY_BASED = "priority_based"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RoutingRequest:
    """Task routing request."""
    task_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    required_capabilities: List[str] = field(default_factory=list)
    preferred_tags: List[str] = field(default_factory=list)
    exclude_agents: Set[str] = field(default_factory=set)
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingResult:
    """Task routing result."""
    success: bool
    agent_id: Optional[str] = None
    agent_registration: Optional[AgentRegistration] = None
    routing_strategy: Optional[RoutingStrategy] = None
    routing_time_ms: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False


class AgentRouter:
    """
    Intelligent agent routing and load balancing system.
    
    Features:
    - Multiple routing strategies
    - Health-aware routing
    - Load balancing
    - Fault tolerance with retries
    - Circuit breaker pattern
    - Performance monitoring
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        health_monitor: Optional[AgentHealthMonitor] = None,
        discovery_service: Optional[AgentDiscoveryService] = None,
        default_strategy: RoutingStrategy = RoutingStrategy.HEALTH_AWARE,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """
        Initialize the agent router.
        
        Args:
            redis_url: Redis connection URL
            health_monitor: Agent health monitor instance
            discovery_service: Agent discovery service instance
            default_strategy: Default routing strategy
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds to keep circuit open
        """
        self.redis_url = redis_url
        self.health_monitor = health_monitor
        self.discovery_service = discovery_service
        self.default_strategy = default_strategy
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        # Redis clients
        self.redis_client = Redis.from_url(redis_url, decode_responses=True)
        self.async_redis_client = None
        
        # Routing state
        self.round_robin_counters: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.routing_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.total_routes = 0
        self.successful_routes = 0
        self.failed_routes = 0
        self.average_routing_time = 0.0
        
        logger.info("Agent Router initialized")
    
    async def initialize(self) -> None:
        """Initialize the router with async Redis client."""
        self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
        await self._load_routing_stats()
        logger.info("Agent Router initialized with async client")
    
    async def route_task(
        self,
        request: RoutingRequest,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingResult:
        """
        Route a task to the best available agent.
        
        Args:
            request: Routing request with task details
            strategy: Optional routing strategy override
            
        Returns:
            Routing result with selected agent or error
        """
        start_time = datetime.utcnow()
        routing_strategy = strategy or self.default_strategy
        
        try:
            # Validate request
            if not request.task_type:
                return RoutingResult(
                    success=False,
                    error_message="Task type is required",
                    routing_strategy=routing_strategy
                )
            
            # Check if we have any agents for this task type
            if not self.discovery_service:
                return RoutingResult(
                    success=False,
                    error_message="Discovery service not available",
                    routing_strategy=routing_strategy
                )
            
            # Get available agents
            available_agents = await self.discovery_service.discover_agents_by_type(
                request.task_type
            )
            
            if not available_agents:
                return RoutingResult(
                    success=False,
                    error_message=f"No agents available for task type: {request.task_type}",
                    routing_strategy=routing_strategy
                )
            
            # Filter agents based on requirements and health
            suitable_agents = await self._filter_suitable_agents(
                available_agents, request
            )
            
            if not suitable_agents:
                return RoutingResult(
                    success=False,
                    error_message="No suitable agents found after filtering",
                    routing_strategy=routing_strategy
                )
            
            # Select agent using routing strategy
            selected_agent = await self._select_agent(
                suitable_agents, request, routing_strategy
            )
            
            if not selected_agent:
                return RoutingResult(
                    success=False,
                    error_message="Failed to select agent",
                    routing_strategy=routing_strategy
                )
            
            # Check circuit breaker
            if await self._is_circuit_open(selected_agent.agent_id):
                # Try to find alternative agent
                alternative_agents = [
                    agent for agent in suitable_agents 
                    if agent.agent_id != selected_agent.agent_id and
                       not await self._is_circuit_open(agent.agent_id)
                ]
                
                if alternative_agents:
                    selected_agent = await self._select_agent(
                        alternative_agents, request, routing_strategy
                    )
                    if not selected_agent:
                        return RoutingResult(
                            success=False,
                            error_message="All suitable agents have open circuits",
                            routing_strategy=routing_strategy
                        )
                else:
                    return RoutingResult(
                        success=False,
                        error_message="Selected agent circuit is open, no alternatives",
                        routing_strategy=routing_strategy
                    )
            
            # Record routing decision
            routing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self._record_routing_decision(request, selected_agent, routing_strategy)
            
            # Update statistics
            self.total_routes += 1
            self.successful_routes += 1
            self._update_average_routing_time(routing_time)
            
            return RoutingResult(
                success=True,
                agent_id=selected_agent.agent_id,
                agent_registration=selected_agent,
                routing_strategy=routing_strategy,
                routing_time_ms=routing_time
            )
            
        except Exception as e:
            routing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.total_routes += 1
            self.failed_routes += 1
            
            logger.error(f"Error routing task {request.task_id}: {e}")
            return RoutingResult(
                success=False,
                error_message=str(e),
                routing_strategy=routing_strategy,
                routing_time_ms=routing_time
            )
    
    async def route_with_retry(
        self,
        request: RoutingRequest,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingResult:
        """
        Route a task with automatic retry and fallback strategies.
        
        Args:
            request: Routing request
            strategy: Optional routing strategy override
            
        Returns:
            Final routing result after retries
        """
        original_strategy = strategy or self.default_strategy
        current_strategy = original_strategy
        
        for attempt in range(request.max_retries + 1):
            result = await self.route_task(request, current_strategy)
            
            if result.success:
                result.retry_count = attempt
                return result
            
            # If this isn't the last attempt, try fallback strategies
            if attempt < request.max_retries:
                # Record failure for circuit breaker
                if result.agent_id:
                    await self._record_agent_failure(result.agent_id)
                
                # Try different strategy on retry
                fallback_strategies = self._get_fallback_strategies(current_strategy)
                if fallback_strategies:
                    current_strategy = fallback_strategies[attempt % len(fallback_strategies)]
                    result.fallback_used = True
                    logger.info(
                        f"Retrying task {request.task_id} with strategy {current_strategy.value}"
                    )
                
                # Brief delay before retry
                await asyncio.sleep(min(2 ** attempt, 10))
        
        # All retries exhausted
        result.retry_count = request.max_retries
        return result
    
    async def record_task_success(self, agent_id: str, task_id: str) -> None:
        """
        Record successful task completion for routing optimization.
        
        Args:
            agent_id: Agent that completed the task
            task_id: Task identifier
        """
        await self._record_agent_success(agent_id)
        
        # Update routing statistics
        if agent_id not in self.routing_stats:
            self.routing_stats[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 1.0,
                "average_response_time": 0.0,
                "last_success": datetime.utcnow().isoformat()
            }
        
        stats = self.routing_stats[agent_id]
        stats["total_tasks"] += 1
        stats["successful_tasks"] += 1
        stats["success_rate"] = stats["successful_tasks"] / stats["total_tasks"]
        stats["last_success"] = datetime.utcnow().isoformat()
        
        await self._save_routing_stats()
    
    async def record_task_failure(
        self, 
        agent_id: str, 
        task_id: str, 
        error_message: Optional[str] = None
    ) -> None:
        """
        Record task failure for routing optimization.
        
        Args:
            agent_id: Agent that failed the task
            task_id: Task identifier
            error_message: Optional error message
        """
        await self._record_agent_failure(agent_id)
        
        # Update routing statistics
        if agent_id not in self.routing_stats:
            self.routing_stats[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "last_failure": datetime.utcnow().isoformat()
            }
        
        stats = self.routing_stats[agent_id]
        stats["total_tasks"] += 1
        stats["failed_tasks"] += 1
        stats["success_rate"] = stats["successful_tasks"] / stats["total_tasks"]
        stats["last_failure"] = datetime.utcnow().isoformat()
        
        await self._save_routing_stats()
    
    async def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive routing statistics.
        
        Returns:
            Dictionary with routing performance metrics
        """
        return {
            "total_routes": self.total_routes,
            "successful_routes": self.successful_routes,
            "failed_routes": self.failed_routes,
            "success_rate": self.successful_routes / max(self.total_routes, 1),
            "average_routing_time_ms": self.average_routing_time,
            "agent_statistics": self.routing_stats.copy(),
            "circuit_breakers": {
                agent_id: {
                    "state": cb["state"],
                    "failure_count": cb["failure_count"],
                    "last_failure": cb["last_failure"]
                }
                for agent_id, cb in self.circuit_breakers.items()
            }
        }
    
    async def _filter_suitable_agents(
        self,
        agents: List[AgentRegistration],
        request: RoutingRequest
    ) -> List[AgentRegistration]:
        """Filter agents based on requirements and health."""
        suitable_agents = []
        
        for agent in agents:
            # Skip excluded agents
            if agent.agent_id in request.exclude_agents:
                continue
            
            # Check required capabilities
            if request.required_capabilities:
                if not all(cap in agent.capabilities for cap in request.required_capabilities):
                    continue
            
            # Check health status
            if self.health_monitor:
                health = await self.health_monitor.get_agent_health(agent.agent_id)
                if health:
                    # Skip unhealthy agents for high priority tasks
                    if (request.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL] and
                        health.status not in [AgentStatus.HEALTHY, AgentStatus.DEGRADED]):
                        continue
                    
                    # Skip offline agents
                    if health.status == AgentStatus.OFFLINE:
                        continue
                    
                    # Skip overloaded agents
                    if health.current_load >= agent.max_concurrent_tasks:
                        continue
            
            suitable_agents.append(agent)
        
        return suitable_agents
    
    async def _select_agent(
        self,
        agents: List[AgentRegistration],
        request: RoutingRequest,
        strategy: RoutingStrategy
    ) -> Optional[AgentRegistration]:
        """Select agent using specified routing strategy."""
        if not agents:
            return None
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return await self._select_round_robin(agents, request.task_type)
        elif strategy == RoutingStrategy.LEAST_LOADED:
            return await self._select_least_loaded(agents)
        elif strategy == RoutingStrategy.WEIGHTED_RANDOM:
            return await self._select_weighted_random(agents)
        elif strategy == RoutingStrategy.HEALTH_AWARE:
            return await self._select_health_aware(agents, request)
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return await self._select_priority_based(agents, request)
        else:
            # Default to first available agent
            return agents[0]
    
    async def _select_round_robin(
        self,
        agents: List[AgentRegistration],
        task_type: str
    ) -> AgentRegistration:
        """Select agent using round-robin strategy."""
        if task_type not in self.round_robin_counters:
            self.round_robin_counters[task_type] = 0
        
        index = self.round_robin_counters[task_type] % len(agents)
        self.round_robin_counters[task_type] += 1
        
        return agents[index]
    
    async def _select_least_loaded(self, agents: List[AgentRegistration]) -> AgentRegistration:
        """Select agent with lowest current load."""
        if not self.health_monitor:
            return agents[0]
        
        min_load = float('inf')
        best_agent = agents[0]
        
        for agent in agents:
            health = await self.health_monitor.get_agent_health(agent.agent_id)
            current_load = health.current_load if health else 0
            
            if current_load < min_load:
                min_load = current_load
                best_agent = agent
        
        return best_agent
    
    async def _select_weighted_random(self, agents: List[AgentRegistration]) -> AgentRegistration:
        """Select agent using weighted random selection based on health scores."""
        if not self.health_monitor:
            return random.choice(agents)
        
        weights = []
        for agent in agents:
            health = await self.health_monitor.get_agent_health(agent.agent_id)
            weight = health.overall_health_score if health else 50.0
            weights.append(max(weight, 1.0))  # Ensure positive weight
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return agents[0]
        
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for i, weight in enumerate(weights):
            cumulative_weight += weight
            if r <= cumulative_weight:
                return agents[i]
        
        return agents[-1]  # Fallback
    
    async def _select_health_aware(
        self,
        agents: List[AgentRegistration],
        request: RoutingRequest
    ) -> Optional[AgentRegistration]:
        """Select agent using health-aware strategy."""
        if not self.health_monitor:
            return await self._select_least_loaded(agents)
        
        # Score agents based on multiple factors
        scored_agents = []
        
        for agent in agents:
            health = await self.health_monitor.get_agent_health(agent.agent_id)
            
            score = 0.0
            
            if health:
                # Health score (40% weight)
                score += health.overall_health_score * 0.4
                
                # Load balancing (30% weight)
                load_ratio = health.current_load / agent.max_concurrent_tasks
                score += (1.0 - load_ratio) * 30
                
                # Reliability (20% weight)
                score += health.reliability_score * 0.2
                
                # Response time (10% weight)
                if health.average_response_time > 0:
                    # Prefer faster agents (normalize to 0-10 scale)
                    response_score = max(0, 10 - health.average_response_time)
                    score += response_score
            else:
                score = 50.0  # Default score for agents without health data
            
            # Priority bonus
            priority_bonus = (1000 - agent.priority) / 100
            score += priority_bonus
            
            # Tag matching bonus
            if request.preferred_tags:
                matching_tags = set(agent.tags) & set(request.preferred_tags)
                score += len(matching_tags) * 5
            
            scored_agents.append((score, agent))
        
        # Sort by score and return best agent
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return scored_agents[0][1]
    
    async def _select_priority_based(
        self,
        agents: List[AgentRegistration],
        request: RoutingRequest
    ) -> AgentRegistration:
        """Select agent based on priority and task priority."""
        # Sort agents by priority (lower number = higher priority)
        sorted_agents = sorted(agents, key=lambda a: a.priority)
        
        # For critical tasks, always use highest priority agent
        if request.priority == TaskPriority.CRITICAL:
            return sorted_agents[0]
        
        # For other tasks, consider load balancing among high priority agents
        high_priority_agents = [
            agent for agent in sorted_agents[:3]  # Top 3 priority agents
        ]
        
        return await self._select_least_loaded(high_priority_agents)
    
    def _get_fallback_strategies(self, strategy: RoutingStrategy) -> List[RoutingStrategy]:
        """Get fallback strategies for retry attempts."""
        fallback_map = {
            RoutingStrategy.HEALTH_AWARE: [
                RoutingStrategy.LEAST_LOADED,
                RoutingStrategy.PRIORITY_BASED,
                RoutingStrategy.ROUND_ROBIN
            ],
            RoutingStrategy.LEAST_LOADED: [
                RoutingStrategy.HEALTH_AWARE,
                RoutingStrategy.ROUND_ROBIN,
                RoutingStrategy.WEIGHTED_RANDOM
            ],
            RoutingStrategy.PRIORITY_BASED: [
                RoutingStrategy.HEALTH_AWARE,
                RoutingStrategy.LEAST_LOADED,
                RoutingStrategy.ROUND_ROBIN
            ],
            RoutingStrategy.ROUND_ROBIN: [
                RoutingStrategy.LEAST_LOADED,
                RoutingStrategy.HEALTH_AWARE,
                RoutingStrategy.WEIGHTED_RANDOM
            ],
            RoutingStrategy.WEIGHTED_RANDOM: [
                RoutingStrategy.HEALTH_AWARE,
                RoutingStrategy.LEAST_LOADED,
                RoutingStrategy.ROUND_ROBIN
            ]
        }
        
        return fallback_map.get(strategy, [RoutingStrategy.ROUND_ROBIN])
    
    async def _is_circuit_open(self, agent_id: str) -> bool:
        """Check if circuit breaker is open for an agent."""
        if agent_id not in self.circuit_breakers:
            return False
        
        cb = self.circuit_breakers[agent_id]
        
        if cb["state"] == "open":
            # Check if timeout has passed
            if datetime.utcnow() > cb["open_until"]:
                cb["state"] = "half_open"
                cb["failure_count"] = 0
                logger.info(f"Circuit breaker for agent {agent_id} moved to half-open")
                return False
            return True
        
        return False
    
    async def _record_agent_success(self, agent_id: str) -> None:
        """Record successful task completion for circuit breaker."""
        if agent_id in self.circuit_breakers:
            cb = self.circuit_breakers[agent_id]
            if cb["state"] == "half_open":
                cb["state"] = "closed"
                cb["failure_count"] = 0
                logger.info(f"Circuit breaker for agent {agent_id} closed after success")
    
    async def _record_agent_failure(self, agent_id: str) -> None:
        """Record task failure for circuit breaker."""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None,
                "open_until": None
            }
        
        cb = self.circuit_breakers[agent_id]
        cb["failure_count"] += 1
        cb["last_failure"] = datetime.utcnow()
        
        if cb["failure_count"] >= self.circuit_breaker_threshold:
            cb["state"] = "open"
            cb["open_until"] = datetime.utcnow() + timedelta(seconds=self.circuit_breaker_timeout)
            logger.warning(
                f"Circuit breaker opened for agent {agent_id} "
                f"after {cb['failure_count']} failures"
            )
    
    async def _record_routing_decision(
        self,
        request: RoutingRequest,
        selected_agent: AgentRegistration,
        strategy: RoutingStrategy
    ) -> None:
        """Record routing decision for analytics."""
        if not self.async_redis_client:
            return
        
        decision = {
            "task_id": request.task_id,
            "task_type": request.task_type,
            "agent_id": selected_agent.agent_id,
            "agent_type": selected_agent.agent_type,
            "strategy": strategy.value,
            "priority": request.priority.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.async_redis_client.xadd("routing-decisions", decision)
    
    def _update_average_routing_time(self, routing_time: float) -> None:
        """Update average routing time using exponential moving average."""
        if self.average_routing_time == 0:
            self.average_routing_time = routing_time
        else:
            alpha = 0.1  # Smoothing factor
            self.average_routing_time = (
                alpha * routing_time + 
                (1 - alpha) * self.average_routing_time
            )
    
    async def _save_routing_stats(self) -> None:
        """Save routing statistics to Redis."""
        if not self.async_redis_client:
            return
        
        await self.async_redis_client.hset(
            "routing:statistics",
            mapping={
                "total_routes": self.total_routes,
                "successful_routes": self.successful_routes,
                "failed_routes": self.failed_routes,
                "average_routing_time": self.average_routing_time,
                "agent_stats": json.dumps(self.routing_stats)
            }
        )
    
    async def _load_routing_stats(self) -> None:
        """Load routing statistics from Redis."""
        if not self.async_redis_client:
            return
        
        try:
            stats = await self.async_redis_client.hgetall("routing:statistics")
            if stats:
                self.total_routes = int(stats.get("total_routes", 0))
                self.successful_routes = int(stats.get("successful_routes", 0))
                self.failed_routes = int(stats.get("failed_routes", 0))
                self.average_routing_time = float(stats.get("average_routing_time", 0.0))
                
                agent_stats_json = stats.get("agent_stats", "{}")
                self.routing_stats = json.loads(agent_stats_json)
                
        except Exception as e:
            logger.error(f"Error loading routing statistics: {e}")
