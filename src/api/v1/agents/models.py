"""
Agent management API models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class AgentHealthMetrics(BaseModel):
    """Agent health metrics model."""
    total_tasks: int = Field(description="Total number of tasks processed")
    successful_tasks: int = Field(description="Number of successful tasks")
    failed_tasks: int = Field(description="Number of failed tasks")
    success_rate: float = Field(description="Task success rate (0.0-1.0)")
    average_response_time: float = Field(description="Average response time in seconds")
    current_load: int = Field(description="Current number of active tasks")
    max_concurrency: int = Field(description="Maximum concurrent tasks allowed")
    error_count: int = Field(description="Recent error count")
    last_error: Optional[str] = Field(description="Last error message", default=None)
    health_score: float = Field(description="Overall health score (0.0-1.0)")


class AgentInfo(BaseModel):
    """Agent information model."""
    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Type of agent (spec, design, coding, etc.)")
    agent_class: str = Field(description="Agent class name")
    status: AgentStatus = Field(description="Current agent status")
    capabilities: List[str] = Field(description="Agent capabilities")
    version: str = Field(description="Agent version")
    priority: int = Field(description="Agent priority (higher = more preferred)")
    tags: List[str] = Field(description="Agent tags for filtering")
    max_concurrent_tasks: int = Field(description="Maximum concurrent tasks")
    last_seen: datetime = Field(description="Last heartbeat timestamp")
    registered_at: datetime = Field(description="Registration timestamp")
    health_metrics: AgentHealthMetrics = Field(description="Health metrics")
    metadata: Dict[str, Any] = Field(description="Additional metadata", default_factory=dict)


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    agents: List[AgentInfo] = Field(description="List of agents")
    total_count: int = Field(description="Total number of agents")
    healthy_count: int = Field(description="Number of healthy agents")
    degraded_count: int = Field(description="Number of degraded agents")
    unhealthy_count: int = Field(description="Number of unhealthy agents")
    offline_count: int = Field(description="Number of offline agents")


class AgentUpdateRequest(BaseModel):
    """Request model for updating agent configuration."""
    priority: Optional[int] = Field(description="New priority", default=None)
    max_concurrent_tasks: Optional[int] = Field(description="New max concurrent tasks", default=None)
    tags: Optional[List[str]] = Field(description="New tags", default=None)
    metadata: Optional[Dict[str, Any]] = Field(description="New metadata", default=None)


class AgentCapabilityFilter(BaseModel):
    """Filter for finding agents by capability."""
    required_capabilities: Optional[List[str]] = Field(description="Required capabilities", default=None)
    preferred_tags: Optional[List[str]] = Field(description="Preferred tags", default=None)
    min_health_score: Optional[float] = Field(description="Minimum health score", default=None)
    max_load: Optional[int] = Field(description="Maximum current load", default=None)
    agent_types: Optional[List[str]] = Field(description="Filter by agent types", default=None)
    status_filter: Optional[List[AgentStatus]] = Field(description="Filter by status", default=None)


class RoutingStatistics(BaseModel):
    """Routing statistics model."""
    total_requests: int = Field(description="Total routing requests")
    successful_routes: int = Field(description="Successful routes")
    failed_routes: int = Field(description="Failed routes")
    average_routing_time: float = Field(description="Average routing time in milliseconds")
    strategy_usage: Dict[str, int] = Field(description="Usage count by strategy")
    agent_utilization: Dict[str, int] = Field(description="Task count by agent")


class AgentDiscoveryEvent(BaseModel):
    """Agent discovery event model."""
    event_type: str = Field(description="Event type (registered, deregistered, updated)")
    agent_id: str = Field(description="Agent identifier")
    agent_type: str = Field(description="Agent type")
    timestamp: datetime = Field(description="Event timestamp")
    details: Dict[str, Any] = Field(description="Event details", default_factory=dict)


class AgentHealthEvent(BaseModel):
    """Agent health event model."""
    event_type: str = Field(description="Event type (status_change, heartbeat, error)")
    agent_id: str = Field(description="Agent identifier")
    old_status: Optional[AgentStatus] = Field(description="Previous status", default=None)
    new_status: AgentStatus = Field(description="Current status")
    health_score: float = Field(description="Current health score")
    timestamp: datetime = Field(description="Event timestamp")
    details: Dict[str, Any] = Field(description="Event details", default_factory=dict)
