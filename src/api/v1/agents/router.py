"""
Agent management API router.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from .models import (
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
    AgentCapabilityFilter,
    RoutingStatistics,
    AgentDiscoveryEvent,
    AgentHealthEvent,
    AgentStatus,
    AgentHealthMetrics
)
from src.orchestrator.agent_health import AgentHealthMonitor
from src.orchestrator.agent_discovery import AgentDiscoveryService
from src.orchestrator.agent_router import AgentRouter
from src.orchestrator.main import get_orchestrator

router = APIRouter(prefix="/agents", tags=["Agent Management"])


async def get_agent_services():
    """Get agent coordination services from orchestrator."""
    orchestrator = get_orchestrator()
    return {
        "health_monitor": orchestrator.health_monitor,
        "discovery_service": orchestrator.discovery_service,
        "agent_router": orchestrator.agent_router
    }


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    include_offline: bool = Query(True, description="Include offline agents"),
    services: Dict = Depends(get_agent_services)
) -> AgentListResponse:
    """
    List all registered agents with their current status and metrics.
    """
    try:
        health_monitor = services["health_monitor"]
        discovery_service = services["discovery_service"]
        
        # Get all registered agents
        all_agents = await discovery_service.get_all_agents()
        
        # Filter agents based on query parameters
        filtered_agents = []
        for agent_data in all_agents:
            agent_id = agent_data["agent_id"]
            
            # Apply filters
            if agent_type and agent_data.get("agent_type") != agent_type:
                continue
                
            # Get health metrics
            health_metrics = await health_monitor.get_agent_health(agent_id)
            if not health_metrics:
                continue
                
            agent_status = AgentStatus(health_metrics.get("status", "offline"))
            
            if status and agent_status != status:
                continue
                
            if not include_offline and agent_status == AgentStatus.OFFLINE:
                continue
            
            # Build agent info
            agent_info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_data.get("agent_type", "unknown"),
                agent_class=agent_data.get("agent_class", "Unknown"),
                status=agent_status,
                capabilities=agent_data.get("capabilities", []),
                version=agent_data.get("version", "1.0.0"),
                priority=agent_data.get("priority", 100),
                tags=agent_data.get("tags", []),
                max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 5),
                last_seen=datetime.fromisoformat(health_metrics.get("last_seen", datetime.utcnow().isoformat())),
                registered_at=datetime.fromisoformat(agent_data.get("registered_at", datetime.utcnow().isoformat())),
                health_metrics=AgentHealthMetrics(
                    total_tasks=health_metrics.get("total_tasks", 0),
                    successful_tasks=health_metrics.get("successful_tasks", 0),
                    failed_tasks=health_metrics.get("failed_tasks", 0),
                    success_rate=health_metrics.get("success_rate", 0.0),
                    average_response_time=health_metrics.get("average_response_time", 0.0),
                    current_load=health_metrics.get("current_load", 0),
                    max_concurrency=agent_data.get("max_concurrent_tasks", 5),
                    error_count=health_metrics.get("error_count", 0),
                    last_error=health_metrics.get("last_error"),
                    health_score=health_metrics.get("health_score", 0.0)
                ),
                metadata=agent_data.get("metadata", {})
            )
            
            filtered_agents.append(agent_info)
        
        # Calculate status counts
        status_counts = {
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "offline": 0
        }
        
        for agent in filtered_agents:
            status_counts[agent.status.value] += 1
        
        return AgentListResponse(
            agents=filtered_agents,
            total_count=len(filtered_agents),
            healthy_count=status_counts["healthy"],
            degraded_count=status_counts["degraded"],
            unhealthy_count=status_counts["unhealthy"],
            offline_count=status_counts["offline"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(
    agent_id: str,
    services: Dict = Depends(get_agent_services)
) -> AgentInfo:
    """
    Get detailed information about a specific agent.
    """
    try:
        health_monitor = services["health_monitor"]
        discovery_service = services["discovery_service"]
        
        # Get agent registration data
        agent_data = await discovery_service.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Get health metrics
        health_metrics = await health_monitor.get_agent_health(agent_id)
        if not health_metrics:
            raise HTTPException(status_code=404, detail=f"Health metrics for agent {agent_id} not found")
        
        return AgentInfo(
            agent_id=agent_id,
            agent_type=agent_data.get("agent_type", "unknown"),
            agent_class=agent_data.get("agent_class", "Unknown"),
            status=AgentStatus(health_metrics.get("status", "offline")),
            capabilities=agent_data.get("capabilities", []),
            version=agent_data.get("version", "1.0.0"),
            priority=agent_data.get("priority", 100),
            tags=agent_data.get("tags", []),
            max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 5),
            last_seen=datetime.fromisoformat(health_metrics.get("last_seen", datetime.utcnow().isoformat())),
            registered_at=datetime.fromisoformat(agent_data.get("registered_at", datetime.utcnow().isoformat())),
            health_metrics=AgentHealthMetrics(
                total_tasks=health_metrics.get("total_tasks", 0),
                successful_tasks=health_metrics.get("successful_tasks", 0),
                failed_tasks=health_metrics.get("failed_tasks", 0),
                success_rate=health_metrics.get("success_rate", 0.0),
                average_response_time=health_metrics.get("average_response_time", 0.0),
                current_load=health_metrics.get("current_load", 0),
                max_concurrency=agent_data.get("max_concurrent_tasks", 5),
                error_count=health_metrics.get("error_count", 0),
                last_error=health_metrics.get("last_error"),
                health_score=health_metrics.get("health_score", 0.0)
            ),
            metadata=agent_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.put("/{agent_id}", response_model=AgentInfo)
async def update_agent(
    agent_id: str,
    update_request: AgentUpdateRequest,
    services: Dict = Depends(get_agent_services)
) -> AgentInfo:
    """
    Update agent configuration.
    """
    try:
        discovery_service = services["discovery_service"]
        
        # Get current agent data
        agent_data = await discovery_service.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Update fields if provided
        updates = {}
        if update_request.priority is not None:
            updates["priority"] = update_request.priority
        if update_request.max_concurrent_tasks is not None:
            updates["max_concurrent_tasks"] = update_request.max_concurrent_tasks
        if update_request.tags is not None:
            updates["tags"] = update_request.tags
        if update_request.metadata is not None:
            updates["metadata"] = {**agent_data.get("metadata", {}), **update_request.metadata}
        
        # Update agent in discovery service
        await discovery_service.update_agent(agent_id, updates)
        
        # Return updated agent info
        return await get_agent(agent_id, services)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.post("/discover", response_model=List[AgentInfo])
async def discover_agents(
    filter_request: AgentCapabilityFilter,
    services: Dict = Depends(get_agent_services)
) -> List[AgentInfo]:
    """
    Discover agents based on capabilities and filters.
    """
    try:
        discovery_service = services["discovery_service"]
        health_monitor = services["health_monitor"]
        
        # Find agents matching criteria
        matching_agents = await discovery_service.find_agents_by_capability(
            required_capabilities=filter_request.required_capabilities or [],
            preferred_tags=filter_request.preferred_tags or []
        )
        
        # Apply additional filters and build response
        result_agents = []
        for agent_data in matching_agents:
            agent_id = agent_data["agent_id"]
            
            # Apply type filter
            if filter_request.agent_types and agent_data.get("agent_type") not in filter_request.agent_types:
                continue
            
            # Get health metrics for additional filtering
            health_metrics = await health_monitor.get_agent_health(agent_id)
            if not health_metrics:
                continue
            
            agent_status = AgentStatus(health_metrics.get("status", "offline"))
            
            # Apply status filter
            if filter_request.status_filter and agent_status not in filter_request.status_filter:
                continue
            
            # Apply health score filter
            health_score = health_metrics.get("health_score", 0.0)
            if filter_request.min_health_score and health_score < filter_request.min_health_score:
                continue
            
            # Apply load filter
            current_load = health_metrics.get("current_load", 0)
            if filter_request.max_load and current_load > filter_request.max_load:
                continue
            
            # Build agent info
            agent_info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_data.get("agent_type", "unknown"),
                agent_class=agent_data.get("agent_class", "Unknown"),
                status=agent_status,
                capabilities=agent_data.get("capabilities", []),
                version=agent_data.get("version", "1.0.0"),
                priority=agent_data.get("priority", 100),
                tags=agent_data.get("tags", []),
                max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 5),
                last_seen=datetime.fromisoformat(health_metrics.get("last_seen", datetime.utcnow().isoformat())),
                registered_at=datetime.fromisoformat(agent_data.get("registered_at", datetime.utcnow().isoformat())),
                health_metrics=AgentHealthMetrics(
                    total_tasks=health_metrics.get("total_tasks", 0),
                    successful_tasks=health_metrics.get("successful_tasks", 0),
                    failed_tasks=health_metrics.get("failed_tasks", 0),
                    success_rate=health_metrics.get("success_rate", 0.0),
                    average_response_time=health_metrics.get("average_response_time", 0.0),
                    current_load=health_metrics.get("current_load", 0),
                    max_concurrency=agent_data.get("max_concurrent_tasks", 5),
                    error_count=health_metrics.get("error_count", 0),
                    last_error=health_metrics.get("last_error"),
                    health_score=health_score
                ),
                metadata=agent_data.get("metadata", {})
            )
            
            result_agents.append(agent_info)
        
        # Sort by health score and priority
        result_agents.sort(key=lambda x: (x.health_metrics.health_score, x.priority), reverse=True)
        
        return result_agents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover agents: {str(e)}")


@router.get("/routing/statistics", response_model=RoutingStatistics)
async def get_routing_statistics(
    services: Dict = Depends(get_agent_services)
) -> RoutingStatistics:
    """
    Get routing statistics and performance metrics.
    """
    try:
        agent_router = services["agent_router"]
        
        # Get routing statistics
        stats = await agent_router.get_routing_statistics()
        
        return RoutingStatistics(
            total_requests=stats.get("total_requests", 0),
            successful_routes=stats.get("successful_routes", 0),
            failed_routes=stats.get("failed_routes", 0),
            average_routing_time=stats.get("average_routing_time", 0.0),
            strategy_usage=stats.get("strategy_usage", {}),
            agent_utilization=stats.get("agent_utilization", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get routing statistics: {str(e)}")


@router.get("/events/discovery")
async def stream_discovery_events(
    services: Dict = Depends(get_agent_services)
):
    """
    Stream agent discovery events in real-time.
    """
    async def event_generator():
        try:
            discovery_service = services["discovery_service"]
            
            # Subscribe to discovery events
            async for event_data in discovery_service.subscribe_to_events():
                event = AgentDiscoveryEvent(
                    event_type=event_data.get("event_type", "unknown"),
                    agent_id=event_data.get("agent_id", ""),
                    agent_type=event_data.get("agent_type", ""),
                    timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                    details=event_data.get("details", {})
                )
                
                yield f"data: {event.json()}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.get("/events/health")
async def stream_health_events(
    services: Dict = Depends(get_agent_services)
):
    """
    Stream agent health events in real-time.
    """
    async def event_generator():
        try:
            health_monitor = services["health_monitor"]
            
            # Subscribe to health events
            async for event_data in health_monitor.subscribe_to_events():
                event = AgentHealthEvent(
                    event_type=event_data.get("event_type", "unknown"),
                    agent_id=event_data.get("agent_id", ""),
                    old_status=AgentStatus(event_data["old_status"]) if event_data.get("old_status") else None,
                    new_status=AgentStatus(event_data.get("new_status", "offline")),
                    health_score=event_data.get("health_score", 0.0),
                    timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                    details=event_data.get("details", {})
                )
                
                yield f"data: {event.json()}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/{agent_id}/heartbeat")
async def send_heartbeat(
    agent_id: str,
    services: Dict = Depends(get_agent_services)
) -> Dict[str, str]:
    """
    Send a heartbeat for an agent (useful for external agents).
    """
    try:
        health_monitor = services["health_monitor"]
        
        await health_monitor.record_heartbeat(agent_id)
        
        return {"status": "success", "message": f"Heartbeat recorded for agent {agent_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record heartbeat: {str(e)}")


@router.delete("/{agent_id}")
async def deregister_agent(
    agent_id: str,
    services: Dict = Depends(get_agent_services)
) -> Dict[str, str]:
    """
    Deregister an agent from the system.
    """
    try:
        discovery_service = services["discovery_service"]
        
        await discovery_service.deregister_agent(agent_id)
        
        return {"status": "success", "message": f"Agent {agent_id} deregistered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deregister agent: {str(e)}")
