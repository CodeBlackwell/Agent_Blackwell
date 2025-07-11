"""Execution Tracer - Comprehensive tracing of all TDD workflow events"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field, asdict


class EventType(Enum):
    """Types of events that can be traced"""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    AGENT_STREAMING = "agent_streaming"
    COMMAND_EXECUTION = "command_execution"
    FILE_OPERATION = "file_operation"
    TEST_EXECUTION = "test_execution"
    TEST_RESULT = "test_result"
    ERROR = "error"
    TRANSITION = "transition"
    VALIDATION = "validation"
    METRICS = "metrics"


@dataclass
class TracedEvent:
    """A single traced event in the execution"""
    timestamp: str
    event_type: EventType
    phase: Optional[str] = None
    agent: Optional[str] = None
    iteration: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    parent_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "data": self.data
        }
        if self.phase:
            result["phase"] = self.phase
        if self.agent:
            result["agent"] = self.agent
        if self.iteration is not None:
            result["iteration"] = self.iteration
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.parent_id:
            result["parent_id"] = self.parent_id
        return result


@dataclass
class AgentExchange:
    """Represents a complete agent exchange"""
    agent_name: str
    phase: str
    iteration: int
    request_time: str
    response_time: Optional[str] = None
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    streaming_chunks: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_name": self.agent_name,
            "phase": self.phase,
            "iteration": self.iteration,
            "request_time": self.request_time,
            "response_time": self.response_time,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "streaming_chunks_count": len(self.streaming_chunks),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error
        }


@dataclass
class CommandExecution:
    """Represents a command execution"""
    command: str
    working_directory: str
    timestamp: str
    duration_ms: float
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class TestExecution:
    """Represents test execution details"""
    test_file: str
    timestamp: str
    duration_ms: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ExecutionTracer:
    """Traces all events during TDD workflow execution"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.events: List[TracedEvent] = []
        self.agent_exchanges: List[AgentExchange] = []
        self.command_executions: List[CommandExecution] = []
        self.test_executions: List[TestExecution] = []
        self.current_exchanges: Dict[str, AgentExchange] = {}
        self.metrics: Dict[str, Any] = {
            "total_events": 0,
            "agent_interactions": 0,
            "commands_executed": 0,
            "tests_run": 0,
            "files_created": 0,
            "files_modified": 0,
            "total_duration_ms": 0
        }
        
    def trace_event(self, event_type: EventType, **kwargs) -> TracedEvent:
        """Trace a generic event"""
        event = TracedEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            **kwargs
        )
        self.events.append(event)
        self.metrics["total_events"] += 1
        return event
    
    def start_agent_exchange(self, agent_name: str, phase: str, iteration: int, 
                            request_data: Dict[str, Any]) -> str:
        """Start tracking an agent exchange"""
        exchange_id = f"{agent_name}_{iteration}_{datetime.now().timestamp()}"
        exchange = AgentExchange(
            agent_name=agent_name,
            phase=phase,
            iteration=iteration,
            request_time=datetime.now().isoformat(),
            request_data=request_data
        )
        self.current_exchanges[exchange_id] = exchange
        
        # Trace the request event
        self.trace_event(
            EventType.AGENT_REQUEST,
            agent=agent_name,
            phase=phase,
            iteration=iteration,
            data={"request": request_data, "exchange_id": exchange_id}
        )
        
        self.metrics["agent_interactions"] += 1
        return exchange_id
    
    def add_streaming_chunk(self, exchange_id: str, chunk: str):
        """Add a streaming chunk to an agent exchange"""
        if exchange_id in self.current_exchanges:
            self.current_exchanges[exchange_id].streaming_chunks.append(chunk)
            
            # Optionally trace streaming events (might be verbose)
            # self.trace_event(
            #     EventType.AGENT_STREAMING,
            #     agent=self.current_exchanges[exchange_id].agent_name,
            #     data={"exchange_id": exchange_id, "chunk_size": len(chunk)}
            # )
    
    def complete_agent_exchange(self, exchange_id: str, response_data: Dict[str, Any], 
                               success: bool = True, error: Optional[str] = None):
        """Complete an agent exchange"""
        if exchange_id not in self.current_exchanges:
            return
        
        exchange = self.current_exchanges[exchange_id]
        exchange.response_time = datetime.now().isoformat()
        exchange.response_data = response_data
        exchange.success = success
        exchange.error = error
        
        # Calculate duration
        start = datetime.fromisoformat(exchange.request_time)
        end = datetime.now()
        exchange.duration_ms = (end - start).total_seconds() * 1000
        
        # Move to completed exchanges
        self.agent_exchanges.append(exchange)
        del self.current_exchanges[exchange_id]
        
        # Trace the response event
        self.trace_event(
            EventType.AGENT_RESPONSE,
            agent=exchange.agent_name,
            phase=exchange.phase,
            iteration=exchange.iteration,
            duration_ms=exchange.duration_ms,
            data={
                "response": response_data,
                "exchange_id": exchange_id,
                "success": success,
                "error": error
            }
        )
    
    def trace_command(self, command: str, working_directory: str, exit_code: int,
                     stdout: str, stderr: str, duration_ms: float):
        """Trace a command execution"""
        cmd_exec = CommandExecution(
            command=command,
            working_directory=working_directory,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            exit_code=exit_code,
            stdout=stdout[:1000],  # Limit output size
            stderr=stderr[:1000],  # Limit output size
            success=(exit_code == 0)
        )
        self.command_executions.append(cmd_exec)
        
        self.trace_event(
            EventType.COMMAND_EXECUTION,
            data={
                "command": command,
                "exit_code": exit_code,
                "success": cmd_exec.success,
                "duration_ms": duration_ms
            }
        )
        
        self.metrics["commands_executed"] += 1
    
    def trace_test_execution(self, test_file: str, test_results: List[Dict[str, Any]],
                           duration_ms: float):
        """Trace test execution results"""
        passed = sum(1 for t in test_results if t.get("status") == "passed")
        failed = sum(1 for t in test_results if t.get("status") == "failed")
        errors = sum(1 for t in test_results if t.get("status") == "error")
        
        test_exec = TestExecution(
            test_file=test_file,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            total_tests=len(test_results),
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            test_details=test_results
        )
        self.test_executions.append(test_exec)
        
        self.trace_event(
            EventType.TEST_EXECUTION,
            data={
                "test_file": test_file,
                "total": len(test_results),
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "duration_ms": duration_ms
            }
        )
        
        self.metrics["tests_run"] += len(test_results)
    
    def trace_file_operation(self, operation: str, file_path: str, 
                           content_size: Optional[int] = None):
        """Trace file operations"""
        self.trace_event(
            EventType.FILE_OPERATION,
            data={
                "operation": operation,
                "file_path": file_path,
                "content_size": content_size
            }
        )
        
        if operation == "create":
            self.metrics["files_created"] += 1
        elif operation == "modify":
            self.metrics["files_modified"] += 1
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive execution report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds() * 1000
        self.metrics["total_duration_ms"] = total_duration
        
        report = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": total_duration,
            "metrics": self.metrics,
            "summary": {
                "total_events": len(self.events),
                "agent_exchanges": len(self.agent_exchanges),
                "command_executions": len(self.command_executions),
                "test_executions": len(self.test_executions)
            },
            "agent_exchanges": [ex.to_dict() for ex in self.agent_exchanges],
            "command_executions": [cmd.to_dict() for cmd in self.command_executions],
            "test_executions": [test.to_dict() for test in self.test_executions],
            "events": [event.to_dict() for event in self.events],
            "timeline": self._generate_timeline()
        }
        
        return report
    
    def _generate_timeline(self) -> List[Dict[str, Any]]:
        """Generate a timeline view of major events"""
        timeline = []
        
        # Add phase transitions
        phase_events = [e for e in self.events if e.event_type in 
                       [EventType.PHASE_START, EventType.PHASE_END, EventType.TRANSITION]]
        
        for event in phase_events:
            timeline.append({
                "timestamp": event.timestamp,
                "type": event.event_type.value,
                "description": self._format_timeline_description(event),
                "phase": event.phase,
                "iteration": event.iteration
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline
    
    def _format_timeline_description(self, event: TracedEvent) -> str:
        """Format a human-readable description for timeline events"""
        if event.event_type == EventType.PHASE_START:
            return f"Started {event.phase} phase"
        elif event.event_type == EventType.PHASE_END:
            success = event.data.get("success", False)
            status = "successfully" if success else "with failures"
            return f"Completed {event.phase} phase {status}"
        elif event.event_type == EventType.TRANSITION:
            from_phase = event.data.get("from_phase", "?")
            to_phase = event.data.get("to_phase", "?")
            reason = event.data.get("reason", "")
            return f"Transitioned from {from_phase} to {to_phase}: {reason}"
        return event.event_type.value
    
    def save_report(self, output_dir: Path):
        """Save execution report to file"""
        report = self.generate_report()
        
        output_file = output_dir / f"execution_report_{self.session_id}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file