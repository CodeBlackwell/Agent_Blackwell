"""
Dynamic Agent Discovery and Registration System

This module provides dynamic discovery, registration, and management of agents
in the Agent Blackwell system, supporting both static and runtime agent registration.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable

import redis.asyncio as aioredis
from redis import Redis

from .agent_health import AgentHealthMonitor, AgentStatus

logger = logging.getLogger(__name__)


class RegistrationStatus(Enum):
    """Agent registration status."""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent_id: str
    agent_type: str
    agent_class: str
    capabilities: List[str]
    version: str
    status: RegistrationStatus = RegistrationStatus.PENDING
    
    # Configuration
    max_concurrent_tasks: int = 5
    priority: int = 100  # Lower number = higher priority
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Network/Connection info
    host: Optional[str] = None
    port: Optional[int] = None
    endpoint: Optional[str] = None
    
    # Timestamps
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_class": self.agent_class,
            "capabilities": json.dumps(self.capabilities),
            "version": self.version,
            "status": self.status.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "priority": self.priority,
            "tags": json.dumps(self.tags),
            "metadata": json.dumps(self.metadata),
            "host": self.host,
            "port": self.port,
            "endpoint": self.endpoint,
            "registered_at": self.registered_at.isoformat(),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRegistration':
        """Create from dictionary."""
        registration = cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            agent_class=data["agent_class"],
            capabilities=json.loads(data.get("capabilities", "[]")),
            version=data["version"],
            status=RegistrationStatus(data["status"]),
            max_concurrent_tasks=int(data.get("max_concurrent_tasks", 5)),
            priority=int(data.get("priority", 100)),
            tags=json.loads(data.get("tags", "[]")),
            metadata=json.loads(data.get("metadata", "{}")),
            host=data.get("host"),
            port=int(data["port"]) if data.get("port") else None,
            endpoint=data.get("endpoint"),
        )
        
        if data.get("registered_at"):
            registration.registered_at = datetime.fromisoformat(data["registered_at"])
        if data.get("last_seen"):
            registration.last_seen = datetime.fromisoformat(data["last_seen"])
            
        return registration


class AgentDiscoveryService:
    """
    Dynamic agent discovery and registration service.
    
    Features:
    - Automatic agent discovery via Redis announcements
    - Dynamic registration and deregistration
    - Agent capability matching
    - Load balancing and routing
    - Health integration
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        health_monitor: Optional[AgentHealthMonitor] = None,
        discovery_interval: int = 30,
        cleanup_interval: int = 300,
        agent_timeout: int = 180,
    ):
        """
        Initialize the agent discovery service.
        
        Args:
            redis_url: Redis connection URL
            health_monitor: Agent health monitor instance
            discovery_interval: Seconds between discovery scans
            cleanup_interval: Seconds between cleanup operations
            agent_timeout: Seconds before considering agent inactive
        """
        self.redis_url = redis_url
        self.health_monitor = health_monitor
        self.discovery_interval = discovery_interval
        self.cleanup_interval = cleanup_interval
        self.agent_timeout = agent_timeout
        
        # Redis clients
        self.redis_client = Redis.from_url(redis_url, decode_responses=True)
        self.async_redis_client = None
        
        # Agent registry
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}  # capability -> agent_ids
        
        # Discovery state
        self.discovery_active = False
        self.discovery_task = None
        self.cleanup_task = None
        
        # Event callbacks
        self.registration_callbacks: List[Callable] = []
        self.deregistration_callbacks: List[Callable] = []
        
        logger.info("Agent Discovery Service initialized")
    
    async def start_discovery(self) -> None:
        """Start the agent discovery service."""
        if self.discovery_active:
            logger.warning("Agent discovery already active")
            return
            
        self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
        self.discovery_active = True
        
        # Load existing registrations
        await self._load_existing_registrations()
        
        # Start discovery and cleanup tasks
        self.discovery_task = asyncio.create_task(self._discovery_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Agent discovery service started")
    
    async def stop_discovery(self) -> None:
        """Stop the agent discovery service."""
        self.discovery_active = False
        
        if self.discovery_task:
            self.discovery_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
        try:
            if self.discovery_task:
                await self.discovery_task
            if self.cleanup_task:
                await self.cleanup_task
        except asyncio.CancelledError:
            pass
        
        if self.async_redis_client:
            await self.async_redis_client.close()
            
        logger.info("Agent discovery service stopped")
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        agent_class: str,
        capabilities: List[str],
        version: str = "1.0.0",
        max_concurrent_tasks: int = 5,
        priority: int = 100,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        endpoint: Optional[str] = None,
    ) -> bool:
        """
        Register an agent with the discovery service.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (spec, design, coding, etc.)
            agent_class: Agent class name
            capabilities: List of agent capabilities
            version: Agent version
            max_concurrent_tasks: Maximum concurrent tasks
            priority: Agent priority (lower = higher priority)
            tags: Optional tags for categorization
            metadata: Optional metadata
            host: Agent host (for remote agents)
            port: Agent port (for remote agents)
            endpoint: Agent endpoint (for remote agents)
            
        Returns:
            True if registration successful
        """
        try:
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                agent_class=agent_class,
                capabilities=capabilities,
                version=version,
                max_concurrent_tasks=max_concurrent_tasks,
                priority=priority,
                tags=tags or [],
                metadata=metadata or {},
                host=host,
                port=port,
                endpoint=endpoint,
                status=RegistrationStatus.ACTIVE,
                last_seen=datetime.utcnow(),
            )
            
            # Store registration
            self.registered_agents[agent_id] = registration
            await self._save_registration(registration)
            
            # Update capability index
            for capability in capabilities:
                if capability not in self.agent_capabilities:
                    self.agent_capabilities[capability] = set()
                self.agent_capabilities[capability].add(agent_id)
            
            # Register with health monitor if available
            if self.health_monitor:
                await self.health_monitor.register_agent(
                    agent_id, agent_type, max_concurrent_tasks
                )
            
            # Notify callbacks
            for callback in self.registration_callbacks:
                try:
                    await callback(registration)
                except Exception as e:
                    logger.error(f"Error in registration callback: {e}")
            
            # Publish registration event
            await self._publish_discovery_event("agent_registered", {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Successfully registered agent {agent_id} ({agent_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the discovery service.
        
        Args:
            agent_id: Agent identifier to deregister
            
        Returns:
            True if deregistration successful
        """
        try:
            if agent_id not in self.registered_agents:
                logger.warning(f"Attempted to deregister unknown agent: {agent_id}")
                return False
            
            registration = self.registered_agents[agent_id]
            
            # Update status
            registration.status = RegistrationStatus.INACTIVE
            await self._save_registration(registration)
            
            # Remove from capability index
            for capability in registration.capabilities:
                if capability in self.agent_capabilities:
                    self.agent_capabilities[capability].discard(agent_id)
                    if not self.agent_capabilities[capability]:
                        del self.agent_capabilities[capability]
            
            # Remove from registry
            del self.registered_agents[agent_id]
            
            # Notify callbacks
            for callback in self.deregistration_callbacks:
                try:
                    await callback(registration)
                except Exception as e:
                    logger.error(f"Error in deregistration callback: {e}")
            
            # Publish deregistration event
            await self._publish_discovery_event("agent_deregistered", {
                "agent_id": agent_id,
                "agent_type": registration.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Successfully deregistered agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister agent {agent_id}: {e}")
            return False
    
    async def discover_agents_by_type(self, agent_type: str) -> List[AgentRegistration]:
        """
        Discover all active agents of a specific type.
        
        Args:
            agent_type: Type of agents to discover
            
        Returns:
            List of agent registrations
        """
        return [
            registration for registration in self.registered_agents.values()
            if registration.agent_type == agent_type and 
               registration.status == RegistrationStatus.ACTIVE
        ]
    
    async def discover_agents_by_capability(self, capability: str) -> List[AgentRegistration]:
        """
        Discover all active agents with a specific capability.
        
        Args:
            capability: Required capability
            
        Returns:
            List of agent registrations
        """
        if capability not in self.agent_capabilities:
            return []
        
        agent_ids = self.agent_capabilities[capability]
        return [
            self.registered_agents[agent_id] 
            for agent_id in agent_ids
            if agent_id in self.registered_agents and
               self.registered_agents[agent_id].status == RegistrationStatus.ACTIVE
        ]
    
    async def find_best_agent(
        self,
        agent_type: str,
        required_capabilities: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        exclude_agents: Optional[Set[str]] = None,
    ) -> Optional[AgentRegistration]:
        """
        Find the best available agent for a task.
        
        Args:
            agent_type: Required agent type
            required_capabilities: Required capabilities
            preferred_tags: Preferred tags for scoring
            exclude_agents: Agent IDs to exclude
            
        Returns:
            Best matching agent registration or None
        """
        candidates = await self.discover_agents_by_type(agent_type)
        
        if not candidates:
            return None
        
        # Filter by required capabilities
        if required_capabilities:
            candidates = [
                agent for agent in candidates
                if all(cap in agent.capabilities for cap in required_capabilities)
            ]
        
        # Filter out excluded agents
        if exclude_agents:
            candidates = [
                agent for agent in candidates
                if agent.agent_id not in exclude_agents
            ]
        
        if not candidates:
            return None
        
        # Score candidates
        scored_candidates = []
        for agent in candidates:
            score = await self._score_agent(agent, preferred_tags)
            scored_candidates.append((score, agent))
        
        # Sort by score (higher is better) and return best
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]
    
    async def get_agent_load_distribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current load distribution across all agents.
        
        Returns:
            Dictionary with agent load information
        """
        distribution = {}
        
        for agent_id, registration in self.registered_agents.items():
            if registration.status != RegistrationStatus.ACTIVE:
                continue
            
            # Get health metrics if available
            current_load = 0
            health_status = "unknown"
            
            if self.health_monitor:
                health = await self.health_monitor.get_agent_health(agent_id)
                if health:
                    current_load = health.current_load
                    health_status = health.status.value
            
            distribution[agent_id] = {
                "agent_type": registration.agent_type,
                "current_load": current_load,
                "max_concurrent_tasks": registration.max_concurrent_tasks,
                "load_percentage": (current_load / registration.max_concurrent_tasks) * 100,
                "health_status": health_status,
                "priority": registration.priority,
                "capabilities": registration.capabilities,
            }
        
        return distribution
    
    def add_registration_callback(self, callback: Callable) -> None:
        """Add callback for agent registration events."""
        self.registration_callbacks.append(callback)
    
    def add_deregistration_callback(self, callback: Callable) -> None:
        """Add callback for agent deregistration events."""
        self.deregistration_callbacks.append(callback)
    
    async def _discovery_loop(self) -> None:
        """Main discovery loop."""
        while self.discovery_active:
            try:
                await self._scan_for_agents()
                await asyncio.sleep(self.discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self) -> None:
        """Cleanup inactive agents."""
        while self.discovery_active:
            try:
                await self._cleanup_inactive_agents()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(10)
    
    async def _scan_for_agents(self) -> None:
        """Scan for new agent announcements."""
        try:
            # Check for agent announcements in Redis stream
            messages = await self.async_redis_client.xread(
                {"agent-announcements": "$"}, 
                count=10, 
                block=1000
            )
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    await self._process_agent_announcement(fields)
                    
        except Exception as e:
            logger.debug(f"No new agent announcements: {e}")
    
    async def _process_agent_announcement(self, announcement: Dict[str, str]) -> None:
        """Process an agent announcement."""
        try:
            agent_id = announcement.get("agent_id")
            if not agent_id:
                return
            
            # Check if this is a registration or heartbeat
            announcement_type = announcement.get("type", "registration")
            
            if announcement_type == "registration":
                await self._handle_agent_registration_announcement(announcement)
            elif announcement_type == "heartbeat":
                await self._handle_agent_heartbeat(agent_id)
            elif announcement_type == "deregistration":
                await self.deregister_agent(agent_id)
                
        except Exception as e:
            logger.error(f"Error processing agent announcement: {e}")
    
    async def _handle_agent_registration_announcement(self, announcement: Dict[str, str]) -> None:
        """Handle agent registration announcement."""
        try:
            agent_id = announcement["agent_id"]
            agent_type = announcement["agent_type"]
            agent_class = announcement.get("agent_class", "Unknown")
            capabilities = json.loads(announcement.get("capabilities", "[]"))
            version = announcement.get("version", "1.0.0")
            
            # Optional fields
            max_concurrent_tasks = int(announcement.get("max_concurrent_tasks", 5))
            priority = int(announcement.get("priority", 100))
            tags = json.loads(announcement.get("tags", "[]"))
            metadata = json.loads(announcement.get("metadata", "{}"))
            host = announcement.get("host")
            port = int(announcement["port"]) if announcement.get("port") else None
            endpoint = announcement.get("endpoint")
            
            await self.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                agent_class=agent_class,
                capabilities=capabilities,
                version=version,
                max_concurrent_tasks=max_concurrent_tasks,
                priority=priority,
                tags=tags,
                metadata=metadata,
                host=host,
                port=port,
                endpoint=endpoint,
            )
            
        except Exception as e:
            logger.error(f"Error handling registration announcement: {e}")
    
    async def _handle_agent_heartbeat(self, agent_id: str) -> None:
        """Handle agent heartbeat."""
        if agent_id in self.registered_agents:
            registration = self.registered_agents[agent_id]
            registration.last_seen = datetime.utcnow()
            await self._save_registration(registration)
            
            # Forward to health monitor
            if self.health_monitor:
                await self.health_monitor.record_heartbeat(agent_id)
    
    async def _cleanup_inactive_agents(self) -> None:
        """Clean up agents that haven't been seen recently."""
        current_time = datetime.utcnow()
        inactive_agents = []
        
        for agent_id, registration in self.registered_agents.items():
            if registration.status != RegistrationStatus.ACTIVE:
                continue
                
            if registration.last_seen:
                time_since_seen = (current_time - registration.last_seen).total_seconds()
                if time_since_seen > self.agent_timeout:
                    inactive_agents.append(agent_id)
        
        for agent_id in inactive_agents:
            logger.info(f"Marking agent {agent_id} as inactive due to timeout")
            await self.deregister_agent(agent_id)
    
    async def _score_agent(
        self, 
        agent: AgentRegistration, 
        preferred_tags: Optional[List[str]] = None
    ) -> float:
        """
        Score an agent for task assignment.
        
        Args:
            agent: Agent registration to score
            preferred_tags: Preferred tags for bonus points
            
        Returns:
            Agent score (higher is better)
        """
        score = 0.0
        
        # Base score from priority (lower priority number = higher score)
        score += (1000 - agent.priority) / 10
        
        # Health score bonus
        if self.health_monitor:
            health = await self.health_monitor.get_agent_health(agent.agent_id)
            if health:
                if health.status == AgentStatus.HEALTHY:
                    score += health.overall_health_score
                elif health.status == AgentStatus.DEGRADED:
                    score += health.overall_health_score * 0.7
                else:
                    score -= 50  # Penalty for unhealthy agents
                
                # Load balancing - prefer less loaded agents
                load_ratio = health.current_load / agent.max_concurrent_tasks
                score += (1.0 - load_ratio) * 20
        
        # Tag matching bonus
        if preferred_tags:
            matching_tags = set(agent.tags) & set(preferred_tags)
            score += len(matching_tags) * 10
        
        return score
    
    async def _save_registration(self, registration: AgentRegistration) -> None:
        """Save agent registration to Redis."""
        if not self.async_redis_client:
            return
            
        await self.async_redis_client.hset(
            f"agent:registration:{registration.agent_id}",
            mapping=registration.to_dict()
        )
        
        # Update indexes
        await self.async_redis_client.sadd("agents:all", registration.agent_id)
        await self.async_redis_client.sadd(
            f"agents:type:{registration.agent_type}", 
            registration.agent_id
        )
        await self.async_redis_client.sadd(
            f"agents:status:{registration.status.value}",
            registration.agent_id
        )
    
    async def _load_existing_registrations(self) -> None:
        """Load existing agent registrations from Redis."""
        if not self.async_redis_client:
            return
            
        agent_ids = await self.async_redis_client.smembers("agents:all")
        
        for agent_id in agent_ids:
            try:
                data = await self.async_redis_client.hgetall(f"agent:registration:{agent_id}")
                if data:
                    registration = AgentRegistration.from_dict(data)
                    self.registered_agents[agent_id] = registration
                    
                    # Update capability index
                    for capability in registration.capabilities:
                        if capability not in self.agent_capabilities:
                            self.agent_capabilities[capability] = set()
                        self.agent_capabilities[capability].add(agent_id)
                        
            except Exception as e:
                logger.error(f"Error loading registration for {agent_id}: {e}")
        
        logger.info(f"Loaded {len(self.registered_agents)} existing agent registrations")
    
    async def _publish_discovery_event(
        self, 
        event_type: str, 
        event_data: Dict[str, Any]
    ) -> None:
        """Publish discovery event to Redis stream."""
        if not self.async_redis_client:
            return
            
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **event_data
        }
        
        await self.async_redis_client.xadd("agent-discovery-events", event)
