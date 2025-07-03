"""
Comprehensive workflow execution monitoring and traceability system.

This module provides detailed tracking of all workflow steps, including:
- Agent calls and responses
- Review interactions and feedback
- Retry attempts and reasons
- Test execution results
- Performance metrics and timing
- Structured audit trails
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import uuid


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class ReviewDecision(Enum):
    """Review decision outcomes."""
    APPROVED = "approved"
    REVISION_NEEDED = "revision_needed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class WorkflowStepResult:
    """Detailed result of a single workflow step."""
    step_id: str
    step_name: str
    agent_name: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, output_data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Mark step as completed and calculate duration."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if error:
            self.status = StepStatus.FAILED
            self.error_message = error
        else:
            self.status = StepStatus.COMPLETED
            self.output_data = output_data


@dataclass
class ReviewResult:
    """Detailed result of a review interaction."""
    review_id: str
    reviewer_agent: str
    reviewed_content: str
    decision: ReviewDecision
    feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    auto_approved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestExecutionResult:
    """Result of test execution during workflow."""
    test_id: str
    test_type: str
    status: StepStatus
    score: Optional[float] = None
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryAttempt:
    """Details of a retry attempt."""
    attempt_number: int
    reason: str
    timestamp: datetime
    previous_error: Optional[str] = None
    changes_made: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionReport:
    """Comprehensive report of workflow execution."""
    execution_id: str
    workflow_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    status: StepStatus = StepStatus.PENDING
    
    # Step tracking
    steps: List[WorkflowStepResult] = field(default_factory=list)
    step_count: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    
    # Review tracking
    reviews: List[ReviewResult] = field(default_factory=list)
    total_reviews: int = 0
    approved_reviews: int = 0
    revision_requests: int = 0
    auto_approvals: int = 0
    
    # Retry tracking
    retries: List[RetryAttempt] = field(default_factory=list)
    total_retries: int = 0
    
    # Test execution tracking
    test_executions: List[TestExecutionResult] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    
    # Performance metrics
    agent_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Final results
    final_output: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, final_output: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Mark execution as completed and calculate metrics."""
        self.end_time = datetime.now()
        self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if error:
            self.status = StepStatus.FAILED
            self.error_summary = error
        else:
            self.status = StepStatus.COMPLETED
            self.final_output = final_output
        
        # Calculate summary metrics
        self.step_count = len(self.steps)
        self.completed_steps = len([s for s in self.steps if s.status == StepStatus.COMPLETED])
        self.failed_steps = len([s for s in self.steps if s.status == StepStatus.FAILED])
        
        self.total_reviews = len(self.reviews)
        self.approved_reviews = len([r for r in self.reviews if r.decision == ReviewDecision.APPROVED])
        self.revision_requests = len([r for r in self.reviews if r.decision == ReviewDecision.REVISION_NEEDED])
        self.auto_approvals = len([r for r in self.reviews if r.auto_approved])
        
        self.total_retries = len(self.retries)
        
        self.total_tests = len(self.test_executions)
        self.passed_tests = len([t for t in self.test_executions if t.status == StepStatus.COMPLETED])
        self.failed_tests = len([t for t in self.test_executions if t.status == StepStatus.FAILED])
        
        # Calculate agent performance metrics
        self._calculate_agent_performance()
    
    def _calculate_agent_performance(self):
        """Calculate performance metrics for each agent."""
        agent_stats = {}
        
        for step in self.steps:
            agent = step.agent_name
            if agent not in agent_stats:
                agent_stats[agent] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_duration': 0.0,
                    'average_duration': 0.0,
                    'reviews_received': 0,
                    'approvals': 0,
                    'revisions': 0
                }
            
            stats = agent_stats[agent]
            stats['total_calls'] += 1
            
            if step.status == StepStatus.COMPLETED:
                stats['successful_calls'] += 1
            elif step.status == StepStatus.FAILED:
                stats['failed_calls'] += 1
            
            if step.duration_seconds:
                stats['total_duration'] += step.duration_seconds
        
        # Calculate averages and review stats
        for agent, stats in agent_stats.items():
            if stats['total_calls'] > 0:
                stats['average_duration'] = stats['total_duration'] / stats['total_calls']
                stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
            
            # Count reviews for this agent
            agent_reviews = [r for r in self.reviews if r.metadata.get('target_agent') == agent]
            stats['reviews_received'] = len(agent_reviews)
            stats['approvals'] = len([r for r in agent_reviews if r.decision == ReviewDecision.APPROVED])
            stats['revisions'] = len([r for r in agent_reviews if r.decision == ReviewDecision.REVISION_NEEDED])
        
        self.agent_performance = agent_stats


class WorkflowExecutionTracer:
    """
    Comprehensive workflow execution tracer that tracks all workflow steps,
    reviews, retries, and test executions.
    """
    
    def __init__(self, workflow_type: str, execution_id: Optional[str] = None):
        """Initialize the tracer for a workflow execution."""
        self.execution_id = execution_id or str(uuid.uuid4())
        self.report = WorkflowExecutionReport(
            execution_id=self.execution_id,
            workflow_type=workflow_type,
            start_time=datetime.now()
        )
        self._current_steps: Dict[str, WorkflowStepResult] = {}
    
    def start_step(self, step_name: str, agent_name: str, input_data: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking a workflow step."""
        step_id = f"{step_name}_{len(self.report.steps)}_{datetime.now().strftime('%H%M%S')}"
        
        step_result = WorkflowStepResult(
            step_id=step_id,
            step_name=step_name,
            agent_name=agent_name,
            status=StepStatus.RUNNING,
            start_time=datetime.now(),
            input_data=input_data
        )
        
        self._current_steps[step_id] = step_result
        self.report.steps.append(step_result)
        
        return step_id
    
    def complete_step(self, step_id: str, output_data: Optional[Dict[str, Any]] = None, 
                     error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Complete a workflow step."""
        if step_id in self._current_steps:
            step = self._current_steps[step_id]
            step.complete(output_data, error)
            
            if metadata:
                step.metadata.update(metadata)
            
            del self._current_steps[step_id]
    
    def record_review(self, reviewer_agent: str, reviewed_content: str, 
                     decision: ReviewDecision, feedback: Optional[str] = None,
                     retry_count: int = 0, auto_approved: bool = False,
                     target_agent: Optional[str] = None) -> str:
        """Record a review interaction."""
        review_id = f"review_{len(self.report.reviews)}_{datetime.now().strftime('%H%M%S')}"
        
        review_result = ReviewResult(
            review_id=review_id,
            reviewer_agent=reviewer_agent,
            reviewed_content=reviewed_content,
            decision=decision,
            feedback=feedback,
            retry_count=retry_count,
            auto_approved=auto_approved
        )
        
        if target_agent:
            review_result.metadata['target_agent'] = target_agent
        
        self.report.reviews.append(review_result)
        return review_id
    
    def record_retry(self, attempt_number: int, reason: str, 
                    previous_error: Optional[str] = None, 
                    changes_made: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None):
        """Record a retry attempt."""
        retry_attempt = RetryAttempt(
            attempt_number=attempt_number,
            reason=reason,
            timestamp=datetime.now(),
            previous_error=previous_error,
            changes_made=changes_made,
            metadata=metadata or {}
        )
        
        self.report.retries.append(retry_attempt)
    
    def record_test_execution(self, test_type: str, status: StepStatus,
                            score: Optional[float] = None, details: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a test execution."""
        test_id = f"test_{len(self.report.test_executions)}_{datetime.now().strftime('%H%M%S')}"
        
        test_result = TestExecutionResult(
            test_id=test_id,
            test_type=test_type,
            status=status,
            score=score,
            details=details,
            metadata=metadata or {}
        )
        
        self.report.test_executions.append(test_result)
        return test_id
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the execution report."""
        self.report.metadata[key] = value
    
    def complete_execution(self, final_output: Optional[Dict[str, Any]] = None, 
                          error: Optional[str] = None):
        """Complete the workflow execution and finalize the report."""
        self.report.complete(final_output, error)
    
    def get_report(self) -> WorkflowExecutionReport:
        """Get the current execution report."""
        return self.report
    
    def to_json(self) -> str:
        """Convert the execution report to JSON."""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(self.report, default=serialize_datetime, indent=2)
    
    def save_report(self, filepath: str):
        """Save the execution report to a file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
