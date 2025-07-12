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
import csv
from io import StringIO


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
class AgentExchange:
    """Complete record of an agent interaction."""
    exchange_id: str
    agent_name: str
    timestamp: datetime
    input_raw: str  # Full raw input sent to agent
    output_raw: str  # Full raw output from agent
    input_preview: str  # Truncated preview for display
    output_preview: str  # Truncated preview for display
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandExecution:
    """Record of a command executed during workflow."""
    command_id: str
    command: str
    executor: str  # Which agent/component ran it
    timestamp: datetime
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_seconds: Optional[float] = None
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    
    # Enhanced tracking
    agent_exchanges: List[AgentExchange] = field(default_factory=list)
    command_executions: List[CommandExecution] = field(default_factory=list)
    test_outputs: List[Dict[str, Any]] = field(default_factory=list)
    
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
    
    # Execution evidence
    proof_of_execution_path: Optional[str] = None
    proof_of_execution_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Comprehensive debugging data
    all_agent_exchanges: List[AgentExchange] = field(default_factory=list)
    all_command_executions: List[CommandExecution] = field(default_factory=list)
    all_test_reports: List[Dict[str, Any]] = field(default_factory=list)
    debug_logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Generated code tracking
    generated_code_path: Optional[str] = None
    generated_files: List[str] = field(default_factory=list)
    
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

    def to_json(self) -> str:
        """Convert the execution report to JSON."""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, WorkflowStepResult):
                return obj.__dict__
            elif isinstance(obj, ReviewResult):
                return obj.__dict__
            elif isinstance(obj, TestExecutionResult):
                return obj.__dict__
            elif isinstance(obj, RetryAttempt):
                return obj.__dict__
            elif isinstance(obj, AgentExchange):
                return obj.__dict__
            elif isinstance(obj, CommandExecution):
                return obj.__dict__
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Convert dataclass to dict for serialization
        report_dict = {
            'execution_id': self.execution_id,
            'workflow_type': self.workflow_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_duration_seconds': self.total_duration_seconds,
            'status': self.status,
            'steps': self.steps,
            'step_count': self.step_count,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'reviews': self.reviews,
            'total_reviews': self.total_reviews,
            'approved_reviews': self.approved_reviews,
            'revision_requests': self.revision_requests,
            'auto_approvals': self.auto_approvals,
            'retries': self.retries,
            'total_retries': self.total_retries,
            'test_executions': self.test_executions,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'agent_performance': self.agent_performance,
            'final_output': self.final_output,
            'error_summary': self.error_summary,
            'proof_of_execution_path': self.proof_of_execution_path,
            'proof_of_execution_data': self.proof_of_execution_data,
            'metadata': self.metadata,
            'all_agent_exchanges': self.all_agent_exchanges,
            'all_command_executions': self.all_command_executions,
            'all_test_reports': self.all_test_reports,
            'debug_logs': self.debug_logs,
            'generated_code_path': self.generated_code_path,
            'generated_files': self.generated_files
        }
        
        return json.dumps(report_dict, default=serialize_datetime, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the execution report to a dictionary."""
        def convert_value(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, (WorkflowStepResult, ReviewResult, TestExecutionResult, RetryAttempt, AgentExchange, CommandExecution)):
                # Convert dataclass to dict recursively
                result = {}
                for key, value in obj.__dict__.items():
                    result[key] = convert_value(value)
                return result
            elif isinstance(obj, list):
                return [convert_value(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_value(v) for k, v in obj.items()}
            else:
                return obj
        
        return {
            'execution_id': self.execution_id,
            'workflow_type': self.workflow_type,
            'start_time': convert_value(self.start_time),
            'end_time': convert_value(self.end_time),
            'total_duration_seconds': self.total_duration_seconds,
            'status': convert_value(self.status),
            'steps': convert_value(self.steps),
            'step_count': self.step_count,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'reviews': convert_value(self.reviews),
            'total_reviews': self.total_reviews,
            'approved_reviews': self.approved_reviews,
            'revision_requests': self.revision_requests,
            'auto_approvals': self.auto_approvals,
            'retries': convert_value(self.retries),
            'total_retries': self.total_retries,
            'test_executions': convert_value(self.test_executions),
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'agent_performance': self.agent_performance,
            'final_output': self.final_output,
            'error_summary': self.error_summary,
            'proof_of_execution_path': self.proof_of_execution_path,
            'proof_of_execution_data': self.proof_of_execution_data,
            'metadata': self.metadata,
            'all_agent_exchanges': convert_value(self.all_agent_exchanges),
            'all_command_executions': convert_value(self.all_command_executions),
            'all_test_reports': self.all_test_reports,
            'debug_logs': self.debug_logs,
            'generated_code_path': self.generated_code_path,
            'generated_files': self.generated_files
        }
    
    def to_csv(self) -> str:
        """Convert the execution report to CSV format with multiple sections."""
        output = StringIO()
        
        # Helper function to write a section header
        def write_section_header(title):
            output.write(f"\n# {title}\n")
        
        # 1. Summary Section
        write_section_header("EXECUTION SUMMARY")
        summary_writer = csv.writer(output)
        summary_writer.writerow([
            'execution_id', 'workflow_type', 'start_time', 'end_time', 
            'duration_seconds', 'status', 'total_steps', 'completed_steps', 
            'failed_steps', 'total_reviews', 'approved_reviews', 'revision_requests',
            'auto_approvals', 'total_retries', 'total_tests', 'passed_tests', 'failed_tests'
        ])
        summary_writer.writerow([
            self.execution_id,
            self.workflow_type,
            self.start_time.isoformat() if self.start_time else '',
            self.end_time.isoformat() if self.end_time else '',
            self.total_duration_seconds or 0,
            self.status.value if isinstance(self.status, Enum) else self.status,
            self.step_count,
            self.completed_steps,
            self.failed_steps,
            self.total_reviews,
            self.approved_reviews,
            self.revision_requests,
            self.auto_approvals,
            self.total_retries,
            self.total_tests,
            self.passed_tests,
            self.failed_tests
        ])
        
        # 2. Steps Section
        if self.steps:
            write_section_header("WORKFLOW STEPS")
            steps_writer = csv.writer(output)
            steps_writer.writerow([
                'step_id', 'step_name', 'agent_name', 'status', 
                'start_time', 'end_time', 'duration_seconds', 'error_message'
            ])
            for step in self.steps:
                steps_writer.writerow([
                    step.step_id,
                    step.step_name,
                    step.agent_name,
                    step.status.value if isinstance(step.status, Enum) else step.status,
                    step.start_time.isoformat() if step.start_time else '',
                    step.end_time.isoformat() if step.end_time else '',
                    step.duration_seconds or 0,
                    step.error_message or ''
                ])
        
        # 3. Reviews Section
        if self.reviews:
            write_section_header("REVIEWS")
            reviews_writer = csv.writer(output)
            reviews_writer.writerow([
                'review_id', 'reviewer_agent', 'decision', 'feedback',
                'retry_count', 'auto_approved', 'timestamp', 'target_agent'
            ])
            for review in self.reviews:
                reviews_writer.writerow([
                    review.review_id,
                    review.reviewer_agent,
                    review.decision.value if isinstance(review.decision, Enum) else review.decision,
                    (review.feedback or '').replace('\n', ' '),
                    review.retry_count,
                    review.auto_approved,
                    review.timestamp.isoformat() if review.timestamp else '',
                    review.metadata.get('target_agent', '')
                ])
        
        # 4. Test Executions Section
        if self.test_executions:
            write_section_header("TEST EXECUTIONS")
            tests_writer = csv.writer(output)
            tests_writer.writerow([
                'test_id', 'test_type', 'status', 'score', 'details', 'timestamp'
            ])
            for test in self.test_executions:
                tests_writer.writerow([
                    test.test_id,
                    test.test_type,
                    test.status.value if isinstance(test.status, Enum) else test.status,
                    test.score or 0,
                    (test.details or '').replace('\n', ' '),
                    test.timestamp.isoformat() if test.timestamp else ''
                ])
        
        # 5. Retries Section
        if self.retries:
            write_section_header("RETRIES")
            retries_writer = csv.writer(output)
            retries_writer.writerow([
                'attempt_number', 'reason', 'timestamp', 'previous_error', 'changes_made'
            ])
            for retry in self.retries:
                retries_writer.writerow([
                    retry.attempt_number,
                    retry.reason.replace('\n', ' '),
                    retry.timestamp.isoformat() if retry.timestamp else '',
                    (retry.previous_error or '').replace('\n', ' '),
                    (retry.changes_made or '').replace('\n', ' ')
                ])
        
        # 6. Agent Performance Section
        if self.agent_performance:
            write_section_header("AGENT PERFORMANCE")
            perf_writer = csv.writer(output)
            perf_writer.writerow([
                'agent_name', 'total_calls', 'successful_calls', 'failed_calls',
                'total_duration', 'average_duration', 'success_rate', 'reviews_received',
                'approvals', 'revisions'
            ])
            for agent_name, stats in self.agent_performance.items():
                perf_writer.writerow([
                    agent_name,
                    stats.get('total_calls', 0),
                    stats.get('successful_calls', 0),
                    stats.get('failed_calls', 0),
                    round(stats.get('total_duration', 0), 2),
                    round(stats.get('average_duration', 0), 2),
                    round(stats.get('success_rate', 0), 4),
                    stats.get('reviews_received', 0),
                    stats.get('approvals', 0),
                    stats.get('revisions', 0)
                ])
        
        # 7. Metadata Section (simplified key-value pairs)
        if self.metadata:
            write_section_header("METADATA")
            meta_writer = csv.writer(output)
            meta_writer.writerow(['key', 'value'])
            for key, value in self.metadata.items():
                # Convert complex values to strings
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                meta_writer.writerow([key, str(value)])
        
        # 8. Proof of Execution Section
        if self.proof_of_execution_path or self.proof_of_execution_data:
            write_section_header("PROOF OF EXECUTION")
            proof_writer = csv.writer(output)
            proof_writer.writerow(['attribute', 'value'])
            if self.proof_of_execution_path:
                proof_writer.writerow(['proof_path', self.proof_of_execution_path])
            if self.proof_of_execution_data:
                proof_writer.writerow(['session_id', self.proof_of_execution_data.get('session_id', '')])
                proof_writer.writerow(['container_id', self.proof_of_execution_data.get('container_id', '')])
                proof_writer.writerow(['execution_success', self.proof_of_execution_data.get('execution_success', False)])
        
        # 9. Agent Exchanges Section (Full debugging data)
        if self.all_agent_exchanges:
            write_section_header("AGENT EXCHANGES")
            exchanges_writer = csv.writer(output)
            exchanges_writer.writerow([
                'exchange_id', 'agent_name', 'timestamp', 'duration_seconds',
                'input_preview', 'output_preview'
            ])
            for exchange in self.all_agent_exchanges:
                exchanges_writer.writerow([
                    exchange.exchange_id,
                    exchange.agent_name,
                    exchange.timestamp.isoformat() if exchange.timestamp else '',
                    exchange.duration_seconds,
                    exchange.input_preview[:200].replace('\n', ' '),
                    exchange.output_preview[:200].replace('\n', ' ')
                ])
        
        # 10. Command Executions Section
        if self.all_command_executions:
            write_section_header("COMMAND EXECUTIONS")
            commands_writer = csv.writer(output)
            commands_writer.writerow([
                'command_id', 'command', 'executor', 'timestamp', 'exit_code',
                'duration_seconds', 'working_directory'
            ])
            for cmd in self.all_command_executions:
                commands_writer.writerow([
                    cmd.command_id,
                    cmd.command[:100].replace('\n', ' '),
                    cmd.executor,
                    cmd.timestamp.isoformat() if cmd.timestamp else '',
                    cmd.exit_code if cmd.exit_code is not None else '',
                    cmd.duration_seconds if cmd.duration_seconds is not None else '',
                    cmd.working_directory or ''
                ])
        
        # 11. Generated Files Section
        if self.generated_files:
            write_section_header("GENERATED FILES")
            files_writer = csv.writer(output)
            files_writer.writerow(['file_path'])
            for file_path in self.generated_files:
                files_writer.writerow([file_path])
        
        return output.getvalue()
    
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
    
    def record_agent_exchange(self, agent_name: str, input_raw: str, output_raw: str, 
                             duration_seconds: float, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a complete agent exchange for debugging."""
        exchange_id = f"exchange_{len(self.report.all_agent_exchanges)}_{datetime.now().strftime('%H%M%S%f')}"
        
        exchange = AgentExchange(
            exchange_id=exchange_id,
            agent_name=agent_name,
            timestamp=datetime.now(),
            input_raw=input_raw,
            output_raw=output_raw,
            input_preview=input_raw[:500] + '...' if len(input_raw) > 500 else input_raw,
            output_preview=output_raw[:500] + '...' if len(output_raw) > 500 else output_raw,
            duration_seconds=duration_seconds,
            metadata=metadata or {}
        )
        
        self.report.all_agent_exchanges.append(exchange)
        
        # Also add to current step if one is active
        for step in self._current_steps.values():
            if step.agent_name == agent_name:
                step.agent_exchanges.append(exchange)
                break
                
        return exchange_id
    
    def record_command_execution(self, command: str, executor: str, exit_code: Optional[int] = None,
                                stdout: Optional[str] = None, stderr: Optional[str] = None,
                                duration_seconds: Optional[float] = None, 
                                working_directory: Optional[str] = None,
                                environment: Optional[Dict[str, str]] = None) -> str:
        """Record a command execution for debugging."""
        command_id = f"cmd_{len(self.report.all_command_executions)}_{datetime.now().strftime('%H%M%S%f')}"
        
        cmd_exec = CommandExecution(
            command_id=command_id,
            command=command,
            executor=executor,
            timestamp=datetime.now(),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            working_directory=working_directory,
            environment=environment
        )
        
        self.report.all_command_executions.append(cmd_exec)
        
        # Also add to current step if executor matches
        for step in self._current_steps.values():
            if step.agent_name == executor:
                step.command_executions.append(cmd_exec)
                break
                
        return command_id
    
    def record_test_report(self, test_report: Dict[str, Any]):
        """Record a test execution report."""
        self.report.all_test_reports.append({
            'timestamp': datetime.now().isoformat(),
            'report': test_report
        })
    
    def record_debug_log(self, level: str, message: str, source: str, 
                        metadata: Optional[Dict[str, Any]] = None):
        """Record a debug log entry."""
        self.report.debug_logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'source': source,
            'metadata': metadata or {}
        })
    
    def set_generated_code_path(self, path: str):
        """Set the path where generated code was saved."""
        self.report.generated_code_path = path
    
    def add_generated_file(self, file_path: str):
        """Add a generated file to the tracking list."""
        if file_path not in self.report.generated_files:
            self.report.generated_files.append(file_path)
    
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
