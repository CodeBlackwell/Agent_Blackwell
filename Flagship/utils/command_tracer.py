"""Command execution wrapper with tracing support"""

import subprocess
import time
from typing import Optional
from pathlib import Path

from models.execution_tracer import ExecutionTracer


class TracedCommand:
    """Wrapper for subprocess commands that includes tracing"""
    
    def __init__(self, tracer: Optional[ExecutionTracer] = None):
        self.tracer = tracer
    
    def run(self, command: list, cwd: str = None, **kwargs) -> subprocess.CompletedProcess:
        """
        Run a command and trace its execution
        
        Args:
            command: Command as list of strings
            cwd: Working directory
            **kwargs: Additional arguments for subprocess.run
            
        Returns:
            CompletedProcess instance
        """
        # Start timing
        start_time = time.time()
        
        # Run command
        result = subprocess.run(command, cwd=cwd, **kwargs)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Trace if tracer is available
        if self.tracer:
            self.tracer.trace_command(
                command=' '.join(command),
                working_directory=str(cwd or Path.cwd()),
                exit_code=result.returncode,
                stdout=result.stdout if hasattr(result, 'stdout') and isinstance(result.stdout, str) else '',
                stderr=result.stderr if hasattr(result, 'stderr') and isinstance(result.stderr, str) else '',
                duration_ms=duration_ms
            )
        
        return result


def create_traced_runner(tracer: Optional[ExecutionTracer] = None):
    """Create a traced command runner function"""
    traced = TracedCommand(tracer)
    return traced.run