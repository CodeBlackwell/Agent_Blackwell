"""Structured logging configuration and setup."""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import threading
from queue import Queue

from config.base_config import BaseConfig
from config.config_manager import get_config


@dataclass
class LogContext:
    """Context information for structured logging."""
    workflow_id: Optional[str] = None
    agent_name: Optional[str] = None
    phase: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add context if present
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'getMessage', 'context']:
                log_data[key] = value
        
        return json.dumps(log_data)


class ContextualLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""
    
    def __init__(self, logger: logging.Logger, context: LogContext):
        """Initialize with logger and context."""
        super().__init__(logger, {})
        self.context = context
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add context to log record."""
        extra = kwargs.get('extra', {})
        extra['context'] = self.context.to_dict()
        kwargs['extra'] = extra
        return msg, kwargs


class LogAggregator:
    """Aggregates logs for analysis and reporting."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize log aggregator."""
        self.logs: Queue = Queue(maxsize=max_size)
        self.stats: Dict[str, int] = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        }
        self._lock = threading.Lock()
    
    def add_log(self, log_record: Dict[str, Any]) -> None:
        """Add a log record to the aggregator."""
        with self._lock:
            # Update stats
            level = log_record.get("level", "INFO")
            if level in self.stats:
                self.stats[level] += 1
            
            # Add to queue (drop oldest if full)
            if self.logs.full():
                self.logs.get()
            self.logs.put(log_record)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._lock:
            total = sum(self.stats.values())
            return {
                "total_logs": total,
                "by_level": self.stats.copy(),
                "queue_size": self.logs.qsize()
            }
    
    def get_recent_logs(self, count: int = 100, level: Optional[str] = None) -> list:
        """Get recent logs, optionally filtered by level."""
        with self._lock:
            logs = list(self.logs.queue)
            if level:
                logs = [log for log in logs if log.get("level") == level]
            return logs[-count:]
    
    def clear(self) -> None:
        """Clear all aggregated logs."""
        with self._lock:
            self.logs.queue.clear()
            for key in self.stats:
                self.stats[key] = 0


class AggregatingHandler(logging.Handler):
    """Logging handler that sends logs to the aggregator."""
    
    def __init__(self, aggregator: LogAggregator):
        """Initialize with aggregator."""
        super().__init__()
        self.aggregator = aggregator
        self.setFormatter(StructuredFormatter())
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the aggregator."""
        try:
            log_data = json.loads(self.format(record))
            self.aggregator.add_log(log_data)
        except Exception:
            self.handleError(record)


# Global log aggregator
_log_aggregator: Optional[LogAggregator] = None


def get_log_aggregator() -> LogAggregator:
    """Get global log aggregator instance."""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator()
    return _log_aggregator


def setup_logging(config: Optional[BaseConfig] = None) -> None:
    """Setup logging configuration."""
    if config is None:
        config = get_config()
    
    # Create logs directory
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with standard formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_level))
    console_formatter = logging.Formatter(config.log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON formatter
    log_file = config.logs_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Parse rotation size (e.g., "10MB" -> 10 * 1024 * 1024)
    rotation_size = config.log_rotation.upper()
    if rotation_size.endswith("MB"):
        max_bytes = int(rotation_size[:-2]) * 1024 * 1024
    elif rotation_size.endswith("GB"):
        max_bytes = int(rotation_size[:-2]) * 1024 * 1024 * 1024
    else:
        max_bytes = 10 * 1024 * 1024  # Default 10MB
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=config.log_retention
    )
    file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Aggregating handler
    aggregator = get_log_aggregator()
    agg_handler = AggregatingHandler(aggregator)
    agg_handler.setLevel(logging.INFO)  # Only aggregate INFO and above
    root_logger.addHandler(agg_handler)
    
    # Configure specific loggers
    loggers_config = {
        "orchestrator": config.log_level,
        "agents": config.log_level,
        "workflows": config.log_level,
        "core": config.log_level,
        "api": config.log_level,
        # External libraries
        "urllib3": "WARNING",
        "asyncio": "WARNING"
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))
        logger.propagate = True


def get_logger(
    name: str,
    context: Optional[LogContext] = None
) -> Union[logging.Logger, ContextualLogger]:
    """Get a logger with optional context."""
    logger = logging.getLogger(name)
    
    if context:
        return ContextualLogger(logger, context)
    
    return logger


def log_performance_metric(
    operation: str,
    duration_ms: float,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log a performance metric."""
    logger = logging.getLogger("orchestrator.performance")
    logger.info(
        f"Performance metric: {operation}",
        extra={
            "metric_type": "performance",
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {}
        }
    )


def log_workflow_event(
    workflow_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> None:
    """Log a workflow event."""
    logger = logging.getLogger("orchestrator.workflow")
    context = LogContext(workflow_id=workflow_id)
    contextual_logger = ContextualLogger(logger, context)
    
    contextual_logger.info(
        f"Workflow event: {event_type}",
        extra={
            "event_type": event_type,
            "event_data": event_data
        }
    )


def log_agent_interaction(
    agent_name: str,
    interaction_type: str,
    input_data: Optional[str] = None,
    output_data: Optional[str] = None,
    duration_ms: Optional[float] = None
) -> None:
    """Log an agent interaction."""
    logger = logging.getLogger("orchestrator.agents")
    context = LogContext(agent_name=agent_name)
    contextual_logger = ContextualLogger(logger, context)
    
    # Truncate large inputs/outputs
    max_length = 500
    if input_data and len(input_data) > max_length:
        input_data = input_data[:max_length] + "..."
    if output_data and len(output_data) > max_length:
        output_data = output_data[:max_length] + "..."
    
    contextual_logger.info(
        f"Agent interaction: {interaction_type}",
        extra={
            "interaction_type": interaction_type,
            "input_preview": input_data,
            "output_preview": output_data,
            "duration_ms": duration_ms
        }
    )