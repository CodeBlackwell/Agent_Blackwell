"""
Agent Health Monitoring System

This module provides comprehensive health monitoring, status tracking, and performance
metrics for all agents in the Agent Blackwell system.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as aioredis
from redis import Redis

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class HealthCheckType(Enum):
    """Types of health checks."""
    HEARTBEAT = "heartbeat"
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class AgentMetrics:
    """Agent performance and health metrics."""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.INITIALIZING
    last_heartbeat: Optional[datetime] = None
    last_task_completed: Optional[datetime] = None
    
    # Performance metrics
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    current_load: int = 0
    max_concurrent_tasks: int = 5
    
    # Error tracking
    error_count_last_hour: int = 0
    error_count_last_day: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    # Health scores (0-100)
    performance_score: float = 100.0
    reliability_score: float = 100.0
    availability_score: float = 100.0
    overall_health_score: float = 100.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for Redis storage."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_task_completed": self.last_task_completed.isoformat() if self.last_task_completed else None,
            "total_tasks_processed": self.total_tasks_processed,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "average_response_time": self.average_response_time,
            "current_load": self.current_load,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "error_count_last_hour": self.error_count_last_hour,
            "error_count_last_day": self.error_count_last_day,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "performance_score": self.performance_score,
            "reliability_score": self.reliability_score,
            "availability_score": self.availability_score,
            "overall_health_score": self.overall_health_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMetrics':
        """Create AgentMetrics from dictionary."""
        metrics = cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            status=AgentStatus(data["status"]),
            total_tasks_processed=int(data.get("total_tasks_processed", 0)),
            successful_tasks=int(data.get("successful_tasks", 0)),
            failed_tasks=int(data.get("failed_tasks", 0)),
            average_response_time=float(data.get("average_response_time", 0.0)),
            current_load=int(data.get("current_load", 0)),
            max_concurrent_tasks=int(data.get("max_concurrent_tasks", 5)),
            error_count_last_hour=int(data.get("error_count_last_hour", 0)),
            error_count_last_day=int(data.get("error_count_last_day", 0)),
            last_error=data.get("last_error"),
            performance_score=float(data.get("performance_score", 100.0)),
            reliability_score=float(data.get("reliability_score", 100.0)),
            availability_score=float(data.get("availability_score", 100.0)),
            overall_health_score=float(data.get("overall_health_score", 100.0)),
        )
        
        # Parse datetime fields
        if data.get("last_heartbeat"):
            metrics.last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        if data.get("last_task_completed"):
            metrics.last_task_completed = datetime.fromisoformat(data["last_task_completed"])
        if data.get("last_error_time"):
            metrics.last_error_time = datetime.fromisoformat(data["last_error_time"])
        if data.get("created_at"):
            metrics.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            metrics.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return metrics


class AgentHealthMonitor:
    """
    Comprehensive agent health monitoring system.
    
    Features:
    - Real-time health status tracking
    - Performance metrics collection
    - Error rate monitoring
    - Heartbeat management
    - Health score calculation
    - Alert generation
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        heartbeat_interval: int = 30,
        health_check_interval: int = 60,
        offline_threshold: int = 120,
    ):
        """
        Initialize the agent health monitor.
        
        Args:
            redis_url: Redis connection URL
            heartbeat_interval: Seconds between heartbeat checks
            health_check_interval: Seconds between health evaluations
            offline_threshold: Seconds before marking agent as offline
        """
        self.redis_url = redis_url
        self.heartbeat_interval = heartbeat_interval
        self.health_check_interval = health_check_interval
        self.offline_threshold = offline_threshold
        
        # Redis clients
        self.redis_client = Redis.from_url(redis_url, decode_responses=True)
        self.async_redis_client = None
        
        # Agent metrics storage
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
        logger.info("Agent Health Monitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start the health monitoring system."""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
            
        self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
        self.monitoring_active = True
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Agent health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop the health monitoring system."""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.async_redis_client:
            await self.async_redis_client.close()
            
        logger.info("Agent health monitoring stopped")
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        max_concurrent_tasks: int = 5
    ) -> None:
        """
        Register a new agent for health monitoring.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (spec, design, coding, etc.)
            max_concurrent_tasks: Maximum concurrent tasks for this agent
        """
        metrics = AgentMetrics(
            agent_id=agent_id,
            agent_type=agent_type,
            max_concurrent_tasks=max_concurrent_tasks,
            status=AgentStatus.INITIALIZING
        )
        
        self.agent_metrics[agent_id] = metrics
        await self._save_agent_metrics(metrics)
        
        # Add to agent registry
        await self.async_redis_client.sadd("agents:registered", agent_id)
        await self.async_redis_client.sadd(f"agents:type:{agent_type}", agent_id)
        
        logger.info(f"Registered agent {agent_id} ({agent_type}) for health monitoring")
    
    async def record_heartbeat(self, agent_id: str) -> None:
        """
        Record a heartbeat from an agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self.agent_metrics:
            logger.warning(f"Heartbeat from unregistered agent: {agent_id}")
            return
        
        metrics = self.agent_metrics[agent_id]
        metrics.last_heartbeat = datetime.utcnow()
        metrics.updated_at = datetime.utcnow()
        
        # Update status if agent was offline
        if metrics.status == AgentStatus.OFFLINE:
            metrics.status = AgentStatus.HEALTHY
            logger.info(f"Agent {agent_id} is back online")
        
        await self._save_agent_metrics(metrics)
        
        # Publish heartbeat event
        await self._publish_agent_event(agent_id, "heartbeat", {
            "timestamp": datetime.utcnow().isoformat(),
            "status": metrics.status.value
        })
    
    async def record_task_start(self, agent_id: str, task_id: str) -> None:
        """
        Record when an agent starts processing a task.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
        """
        if agent_id not in self.agent_metrics:
            logger.warning(f"Task start from unregistered agent: {agent_id}")
            return
        
        metrics = self.agent_metrics[agent_id]
        metrics.current_load += 1
        metrics.updated_at = datetime.utcnow()
        
        await self._save_agent_metrics(metrics)
        
        # Store task start time for response time calculation
        await self.async_redis_client.hset(
            f"agent:{agent_id}:tasks",
            task_id,
            time.time()
        )
    
    async def record_task_completion(
        self,
        agent_id: str,
        task_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record when an agent completes a task.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            success: Whether the task completed successfully
            error_message: Error message if task failed
        """
        if agent_id not in self.agent_metrics:
            logger.warning(f"Task completion from unregistered agent: {agent_id}")
            return
        
        metrics = self.agent_metrics[agent_id]
        
        # Update load and counters
        metrics.current_load = max(0, metrics.current_load - 1)
        metrics.total_tasks_processed += 1
        metrics.last_task_completed = datetime.utcnow()
        metrics.updated_at = datetime.utcnow()
        
        if success:
            metrics.successful_tasks += 1
        else:
            metrics.failed_tasks += 1
            metrics.error_count_last_hour += 1
            metrics.error_count_last_day += 1
            
            if error_message:
                metrics.last_error = error_message
                metrics.last_error_time = datetime.utcnow()
        
        # Calculate response time
        start_time = await self.async_redis_client.hget(f"agent:{agent_id}:tasks", task_id)
        if start_time:
            response_time = time.time() - float(start_time)
            # Update rolling average
            if metrics.total_tasks_processed == 1:
                metrics.average_response_time = response_time
            else:
                # Exponential moving average
                alpha = 0.1
                metrics.average_response_time = (
                    alpha * response_time + 
                    (1 - alpha) * metrics.average_response_time
                )
            
            # Clean up task timing data
            await self.async_redis_client.hdel(f"agent:{agent_id}:tasks", task_id)
        
        # Recalculate health scores
        await self._calculate_health_scores(metrics)
        await self._save_agent_metrics(metrics)
        
        # Publish task completion event
        await self._publish_agent_event(agent_id, "task_completed", {
            "task_id": task_id,
            "success": success,
            "error_message": error_message,
            "response_time": metrics.average_response_time,
            "current_load": metrics.current_load,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def get_agent_health(self, agent_id: str) -> Optional[AgentMetrics]:
        """
        Get current health metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent metrics or None if not found
        """
        if agent_id in self.agent_metrics:
            return self.agent_metrics[agent_id]
        
        # Try to load from Redis
        return await self._load_agent_metrics(agent_id)
    
    async def get_all_agent_health(self) -> Dict[str, AgentMetrics]:
        """
        Get health metrics for all registered agents.
        
        Returns:
            Dictionary mapping agent IDs to their metrics
        """
        # Ensure we have latest data from Redis
        agent_ids = await self.async_redis_client.smembers("agents:registered")
        
        for agent_id in agent_ids:
            if agent_id not in self.agent_metrics:
                metrics = await self._load_agent_metrics(agent_id)
                if metrics:
                    self.agent_metrics[agent_id] = metrics
        
        return self.agent_metrics.copy()
    
    async def get_agents_by_status(self, status: AgentStatus) -> List[str]:
        """
        Get list of agent IDs with specific status.
        
        Args:
            status: Agent status to filter by
            
        Returns:
            List of agent IDs
        """
        return [
            agent_id for agent_id, metrics in self.agent_metrics.items()
            if metrics.status == status
        ]
    
    async def get_healthy_agents_by_type(self, agent_type: str) -> List[str]:
        """
        Get list of healthy agent IDs of specific type.
        
        Args:
            agent_type: Type of agents to filter by
            
        Returns:
            List of healthy agent IDs
        """
        return [
            agent_id for agent_id, metrics in self.agent_metrics.items()
            if metrics.agent_type == agent_type and metrics.status == AgentStatus.HEALTHY
        ]
    
    async def get_least_loaded_agent(self, agent_type: str) -> Optional[str]:
        """
        Get the least loaded healthy agent of specific type.
        
        Args:
            agent_type: Type of agent needed
            
        Returns:
            Agent ID with lowest current load, or None if no healthy agents
        """
        healthy_agents = await self.get_healthy_agents_by_type(agent_type)
        
        if not healthy_agents:
            return None
        
        # Find agent with lowest load
        min_load = float('inf')
        best_agent = None
        
        for agent_id in healthy_agents:
            metrics = self.agent_metrics[agent_id]
            if metrics.current_load < min_load:
                min_load = metrics.current_load
                best_agent = agent_id
        
        return best_agent
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._check_agent_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _check_agent_health(self) -> None:
        """Check health of all registered agents."""
        current_time = datetime.utcnow()
        
        for agent_id, metrics in self.agent_metrics.items():
            previous_status = metrics.status
            
            # Check if agent is offline (no recent heartbeat)
            if metrics.last_heartbeat:
                time_since_heartbeat = (current_time - metrics.last_heartbeat).total_seconds()
                if time_since_heartbeat > self.offline_threshold:
                    metrics.status = AgentStatus.OFFLINE
            else:
                # No heartbeat recorded yet
                time_since_creation = (current_time - metrics.created_at).total_seconds()
                if time_since_creation > self.offline_threshold:
                    metrics.status = AgentStatus.OFFLINE
            
            # Calculate health scores if agent is online
            if metrics.status != AgentStatus.OFFLINE:
                await self._calculate_health_scores(metrics)
                
                # Determine status based on health scores
                if metrics.overall_health_score >= 80:
                    metrics.status = AgentStatus.HEALTHY
                elif metrics.overall_health_score >= 60:
                    metrics.status = AgentStatus.DEGRADED
                else:
                    metrics.status = AgentStatus.UNHEALTHY
            
            # Update timestamp
            metrics.updated_at = current_time
            
            # Save updated metrics
            await self._save_agent_metrics(metrics)
            
            # Publish status change event if status changed
            if previous_status != metrics.status:
                await self._publish_agent_event(agent_id, "status_changed", {
                    "previous_status": previous_status.value,
                    "new_status": metrics.status.value,
                    "health_score": metrics.overall_health_score,
                    "timestamp": current_time.isoformat()
                })
                
                logger.info(f"Agent {agent_id} status changed: {previous_status.value} -> {metrics.status.value}")
    
    async def _calculate_health_scores(self, metrics: AgentMetrics) -> None:
        """Calculate health scores for an agent."""
        # Performance score based on response time and load
        if metrics.average_response_time > 0:
            # Normalize response time (assume 10s is poor, 1s is good)
            response_time_score = max(0, 100 - (metrics.average_response_time - 1) * 10)
        else:
            response_time_score = 100
        
        # Load score (penalize high load relative to capacity)
        load_ratio = metrics.current_load / metrics.max_concurrent_tasks
        load_score = max(0, 100 - load_ratio * 50)
        
        metrics.performance_score = (response_time_score + load_score) / 2
        
        # Reliability score based on success rate
        if metrics.total_tasks_processed > 0:
            success_rate = metrics.successful_tasks / metrics.total_tasks_processed
            metrics.reliability_score = success_rate * 100
        else:
            metrics.reliability_score = 100
        
        # Availability score based on recent heartbeats
        if metrics.last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - metrics.last_heartbeat).total_seconds()
            if time_since_heartbeat <= self.heartbeat_interval:
                metrics.availability_score = 100
            elif time_since_heartbeat <= self.heartbeat_interval * 2:
                metrics.availability_score = 75
            elif time_since_heartbeat <= self.offline_threshold:
                metrics.availability_score = 50
            else:
                metrics.availability_score = 0
        else:
            metrics.availability_score = 0
        
        # Overall health score (weighted average)
        metrics.overall_health_score = (
            metrics.performance_score * 0.4 +
            metrics.reliability_score * 0.4 +
            metrics.availability_score * 0.2
        )
    
    async def _save_agent_metrics(self, metrics: AgentMetrics) -> None:
        """Save agent metrics to Redis."""
        if not self.async_redis_client:
            return
            
        await self.async_redis_client.hset(
            f"agent:{metrics.agent_id}:metrics",
            mapping=metrics.to_dict()
        )
        
        # Update status index
        await self.async_redis_client.sadd(
            f"agents:status:{metrics.status.value}",
            metrics.agent_id
        )
        
        # Remove from other status indexes
        for status in AgentStatus:
            if status != metrics.status:
                await self.async_redis_client.srem(
                    f"agents:status:{status.value}",
                    metrics.agent_id
                )
    
    async def _load_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Load agent metrics from Redis."""
        if not self.async_redis_client:
            return None
            
        data = await self.async_redis_client.hgetall(f"agent:{agent_id}:metrics")
        
        if not data:
            return None
        
        try:
            return AgentMetrics.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading metrics for agent {agent_id}: {e}")
            return None
    
    async def _publish_agent_event(
        self,
        agent_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Publish agent event to Redis stream."""
        if not self.async_redis_client:
            return
            
        event = {
            "event_type": event_type,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            **event_data
        }
        
        await self.async_redis_client.xadd("agent-health-events", event)
