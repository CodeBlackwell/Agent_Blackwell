"""Log analysis and reporting utilities."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import re

from .logging_config import get_log_aggregator


class LogAnalyzer:
    """Analyze logs for patterns and insights."""
    
    def __init__(self, log_directory: Optional[Path] = None):
        """Initialize log analyzer."""
        self.log_directory = log_directory
        self.aggregator = get_log_aggregator()
    
    def analyze_performance(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze performance metrics from logs."""
        logs = self._get_logs(time_window, log_type="performance")
        
        if not logs:
            return {"message": "No performance metrics found"}
        
        # Aggregate by operation
        operations = defaultdict(list)
        for log in logs:
            if log.get("metric_type") == "performance":
                operation = log.get("operation", "unknown")
                duration = log.get("duration_ms", 0)
                operations[operation].append(duration)
        
        # Calculate statistics
        stats = {}
        for operation, durations in operations.items():
            if durations:
                stats[operation] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "total_ms": sum(durations)
                }
        
        return {
            "time_window": str(time_window) if time_window else "all",
            "operations": stats,
            "total_operations": sum(len(d) for d in operations.values())
        }
    
    def analyze_errors(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze error patterns from logs."""
        logs = self._get_logs(time_window, level="ERROR")
        
        if not logs:
            return {"message": "No errors found"}
        
        # Categorize errors
        error_patterns = defaultdict(list)
        error_modules = Counter()
        error_functions = Counter()
        
        for log in logs:
            # Extract error type from message
            message = log.get("message", "")
            module = log.get("module", "unknown")
            function = log.get("function", "unknown")
            
            error_modules[module] += 1
            error_functions[f"{module}.{function}"] += 1
            
            # Simple pattern matching
            if "timeout" in message.lower():
                error_patterns["timeout"].append(log)
            elif "connection" in message.lower():
                error_patterns["connection"].append(log)
            elif "validation" in message.lower():
                error_patterns["validation"].append(log)
            elif "not found" in message.lower():
                error_patterns["not_found"].append(log)
            else:
                error_patterns["other"].append(log)
        
        return {
            "time_window": str(time_window) if time_window else "all",
            "total_errors": len(logs),
            "error_patterns": {k: len(v) for k, v in error_patterns.items()},
            "top_error_modules": dict(error_modules.most_common(5)),
            "top_error_functions": dict(error_functions.most_common(5)),
            "recent_errors": [
                {
                    "timestamp": log.get("timestamp"),
                    "message": log.get("message", "")[:100],
                    "module": log.get("module")
                }
                for log in logs[-5:]
            ]
        }
    
    def analyze_workflows(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze workflow execution patterns."""
        logs = self._get_logs(time_window, logger_prefix="orchestrator.workflow")
        
        workflows = defaultdict(lambda: {
            "count": 0,
            "events": defaultdict(int),
            "durations": []
        })
        
        # Track workflow starts and completions
        workflow_times = {}
        
        for log in logs:
            context = log.get("context", {})
            workflow_id = context.get("workflow_id")
            if not workflow_id:
                continue
            
            event_type = log.get("event_type", "")
            timestamp = log.get("timestamp", "")
            
            workflows[workflow_id]["count"] += 1
            workflows[workflow_id]["events"][event_type] += 1
            
            # Track duration
            if event_type == "workflow_started":
                workflow_times[workflow_id] = timestamp
            elif event_type == "workflow_completed" and workflow_id in workflow_times:
                start_time = datetime.fromisoformat(workflow_times[workflow_id])
                end_time = datetime.fromisoformat(timestamp)
                duration = (end_time - start_time).total_seconds()
                workflows[workflow_id]["durations"].append(duration)
        
        # Aggregate statistics
        workflow_stats = {}
        for wf_type, data in workflows.items():
            durations = data["durations"]
            workflow_stats[wf_type] = {
                "total_executions": len(durations),
                "total_events": data["count"],
                "event_breakdown": dict(data["events"]),
                "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
                "min_duration_seconds": min(durations) if durations else 0,
                "max_duration_seconds": max(durations) if durations else 0
            }
        
        return {
            "time_window": str(time_window) if time_window else "all",
            "workflow_types": workflow_stats,
            "total_workflows": sum(ws["total_executions"] for ws in workflow_stats.values())
        }
    
    def analyze_agents(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze agent interaction patterns."""
        logs = self._get_logs(time_window, logger_prefix="orchestrator.agents")
        
        agents = defaultdict(lambda: {
            "interactions": 0,
            "interaction_types": defaultdict(int),
            "avg_duration_ms": 0,
            "total_duration_ms": 0
        })
        
        for log in logs:
            context = log.get("context", {})
            agent_name = context.get("agent_name")
            if not agent_name:
                continue
            
            interaction_type = log.get("interaction_type", "unknown")
            duration = log.get("duration_ms", 0)
            
            agents[agent_name]["interactions"] += 1
            agents[agent_name]["interaction_types"][interaction_type] += 1
            agents[agent_name]["total_duration_ms"] += duration
        
        # Calculate averages
        for agent_data in agents.values():
            if agent_data["interactions"] > 0:
                agent_data["avg_duration_ms"] = (
                    agent_data["total_duration_ms"] / agent_data["interactions"]
                )
        
        return {
            "time_window": str(time_window) if time_window else "all",
            "agents": dict(agents),
            "total_interactions": sum(a["interactions"] for a in agents.values()),
            "most_active_agent": max(agents.items(), key=lambda x: x[1]["interactions"])[0] if agents else None
        }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive summary report."""
        # Get aggregator stats
        agg_stats = self.aggregator.get_stats()
        
        # Analyze last hour
        last_hour = timedelta(hours=1)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_stats": agg_stats,
            "last_hour": {
                "performance": self.analyze_performance(last_hour),
                "errors": self.analyze_errors(last_hour),
                "workflows": self.analyze_workflows(last_hour),
                "agents": self.analyze_agents(last_hour)
            }
        }
    
    def _get_logs(
        self,
        time_window: Optional[timedelta] = None,
        level: Optional[str] = None,
        logger_prefix: Optional[str] = None,
        log_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get logs from aggregator or files."""
        # First try aggregator
        logs = self.aggregator.get_recent_logs(1000, level)
        
        # Filter by time window
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            logs = [
                log for log in logs
                if datetime.fromisoformat(log.get("timestamp", "")) > cutoff_time
            ]
        
        # Filter by logger prefix
        if logger_prefix:
            logs = [
                log for log in logs
                if log.get("logger", "").startswith(logger_prefix)
            ]
        
        # Filter by log type (e.g., performance)
        if log_type:
            logs = [
                log for log in logs
                if log.get("metric_type") == log_type or log_type in log.get("message", "")
            ]
        
        return logs
    
    def export_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Export report to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)


def generate_daily_report(output_dir: Path) -> Path:
    """Generate daily log analysis report."""
    analyzer = LogAnalyzer()
    report = analyzer.generate_summary_report()
    
    # Add daily analysis
    report["daily_analysis"] = {
        "performance": analyzer.analyze_performance(timedelta(days=1)),
        "errors": analyzer.analyze_errors(timedelta(days=1)),
        "workflows": analyzer.analyze_workflows(timedelta(days=1)),
        "agents": analyzer.analyze_agents(timedelta(days=1))
    }
    
    # Save report
    report_path = output_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
    analyzer.export_report(report, report_path)
    
    return report_path