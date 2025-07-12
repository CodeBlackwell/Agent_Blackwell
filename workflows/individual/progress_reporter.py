"""
Progress reporting utilities for workflow execution.
"""
import time
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import threading


class ProgressReporter:
    """Reports progress for workflow execution with ETA estimation."""
    
    def __init__(
        self,
        workflow_type: str,
        total_steps: int,
        show_eta: bool = True,
        update_interval: float = 1.0
    ):
        """
        Initialize progress reporter.
        
        Args:
            workflow_type: Type of workflow being executed
            total_steps: Total number of steps in workflow
            show_eta: Whether to show estimated time to completion
            update_interval: How often to update progress display (seconds)
        """
        self.workflow_type = workflow_type
        self.total_steps = total_steps
        self.show_eta = show_eta
        self.update_interval = update_interval
        
        self.current_step = 0
        self.completed_steps = 0
        self.step_times: Dict[str, float] = {}
        self.step_status: Dict[str, str] = {}
        
        self.start_time = time.time()
        self.current_step_start = None
        self.current_step_name = None
        
        self._stop_event = threading.Event()
        self._update_thread = None
        
        # Start progress display
        self._start_display()
    
    def start_step(self, step_name: str) -> None:
        """Mark the start of a workflow step."""
        self.current_step += 1
        self.current_step_name = step_name
        self.current_step_start = time.time()
        self.step_status[step_name] = "running"
        self._update_display()
    
    def complete_step(self, step_name: str) -> None:
        """Mark the completion of a workflow step."""
        if self.current_step_start:
            duration = time.time() - self.current_step_start
            self.step_times[step_name] = duration
        
        self.completed_steps += 1
        self.step_status[step_name] = "completed"
        self.current_step_name = None
        self.current_step_start = None
        self._update_display()
    
    def error_step(self, step_name: str, error: str) -> None:
        """Mark a step as failed."""
        if self.current_step_start:
            duration = time.time() - self.current_step_start
            self.step_times[step_name] = duration
        
        self.step_status[step_name] = f"failed: {error[:50]}"
        self.current_step_name = None
        self.current_step_start = None
        self._update_display()
    
    def _start_display(self) -> None:
        """Start the progress display update thread."""
        self._update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self._update_thread.start()
    
    def _update_loop(self) -> None:
        """Background thread that updates the progress display."""
        while not self._stop_event.is_set():
            self._update_display()
            self._stop_event.wait(self.update_interval)
    
    def _update_display(self) -> None:
        """Update the progress display."""
        # Clear line and return to start
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        
        # Calculate progress
        progress = (self.completed_steps / self.total_steps) * 100 if self.total_steps > 0 else 0
        elapsed = time.time() - self.start_time
        
        # Build progress bar
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Build status line
        status_parts = [
            f"[{bar}]",
            f"{progress:.0f}%",
            f"({self.completed_steps}/{self.total_steps})"
        ]
        
        # Add current step if running
        if self.current_step_name:
            step_elapsed = time.time() - self.current_step_start if self.current_step_start else 0
            status_parts.append(f"| {self.current_step_name} ({step_elapsed:.1f}s)")
        
        # Add elapsed time
        status_parts.append(f"| Elapsed: {self._format_duration(elapsed)}")
        
        # Add ETA if enabled
        if self.show_eta and self.completed_steps > 0:
            avg_time_per_step = elapsed / self.completed_steps
            remaining_steps = self.total_steps - self.completed_steps
            eta_seconds = avg_time_per_step * remaining_steps
            status_parts.append(f"| ETA: {self._format_duration(eta_seconds)}")
        
        # Write status
        status_line = " ".join(status_parts)
        sys.stdout.write(status_line)
        sys.stdout.flush()
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def stop(self) -> None:
        """Stop the progress display."""
        self._stop_event.set()
        if self._update_thread:
            self._update_thread.join()
        
        # Final update and newline
        self._update_display()
        sys.stdout.write('\n')
        sys.stdout.flush()
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of execution progress."""
        total_elapsed = time.time() - self.start_time
        
        return {
            "workflow_type": self.workflow_type,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "total_elapsed_seconds": total_elapsed,
            "average_step_seconds": total_elapsed / self.completed_steps if self.completed_steps > 0 else 0,
            "step_times": self.step_times.copy(),
            "step_status": self.step_status.copy()
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class SimpleProgressBar:
    """Simple progress bar for basic progress indication."""
    
    def __init__(self, total: int, prefix: str = "", width: int = 50):
        """Initialize simple progress bar."""
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
    
    def update(self, current: int, suffix: str = "") -> None:
        """Update progress bar."""
        self.current = current
        progress = current / self.total if self.total > 0 else 0
        
        # Build bar
        filled = int(self.width * progress)
        bar = '=' * filled + '-' * (self.width - filled)
        
        # Display
        sys.stdout.write(f'\r{self.prefix} [{bar}] {progress*100:.0f}% {suffix}')
        sys.stdout.flush()
        
        if current >= self.total:
            sys.stdout.write('\n')
    
    def increment(self, suffix: str = "") -> None:
        """Increment progress by one."""
        self.update(self.current + 1, suffix)