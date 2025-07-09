"""
Debug Logger for MVP Incremental Workflow
Captures comprehensive execution details including agent interactions, errors, and system state
"""
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading
import queue
import atexit


class DebugLogger:
    """Comprehensive debug logger that captures all workflow execution details."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize debug logger with specified directory."""
        self.start_time = datetime.now()
        self.log_dir = log_dir or Path("demo_outputs/debug_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique log filename
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"debug_log_{timestamp}.json"
        self.transcript_file = self.log_dir / f"transcript_{timestamp}.txt"
        
        # Initialize log data structure
        self.log_data = {
            "session_info": {
                "start_time": self.start_time.isoformat(),
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "command_line": sys.argv,
            },
            "import_verification": {},
            "agent_interactions": [],
            "errors": [],
            "phases": [],
            "system_events": [],
            "final_status": "running"
        }
        
        # Thread-safe queue for logging
        self.log_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        
        # Start background writer thread
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()
        
        # Register cleanup on exit
        atexit.register(self.finalize)
        
        # Redirect stdout/stderr to capture all output
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self.stdout_capture = OutputCapture(self, "stdout")
        self.stderr_capture = OutputCapture(self, "stderr")
        
    def enable_output_capture(self):
        """Enable capturing of stdout/stderr."""
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        
    def disable_output_capture(self):
        """Disable capturing of stdout/stderr."""
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        
    def log_import_verification(self, module_name: str, items: List[str], success: bool, error: Optional[str] = None):
        """Log import verification results."""
        self.log_data["import_verification"][module_name] = {
            "items": items,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self._queue_write()
        
    def log_agent_interaction(self, agent_name: str, input_data: str, output_data: str, 
                            metadata: Optional[Dict[str, Any]] = None):
        """Log an agent interaction."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input": input_data[:5000],  # Truncate very long inputs
            "output": output_data[:5000],  # Truncate very long outputs
            "input_length": len(input_data),
            "output_length": len(output_data),
            "metadata": metadata or {},
            "duration_seconds": metadata.get("duration") if metadata else None
        }
        self.log_data["agent_interactions"].append(interaction)
        
        # Also write to transcript
        self._write_transcript(f"\n{'='*80}\n")
        self._write_transcript(f"AGENT: {agent_name}\n")
        self._write_transcript(f"TIME: {interaction['timestamp']}\n")
        self._write_transcript(f"INPUT ({len(input_data)} chars):\n{input_data[:1000]}\n")
        if len(input_data) > 1000:
            self._write_transcript(f"... truncated {len(input_data) - 1000} chars ...\n")
        self._write_transcript(f"\nOUTPUT ({len(output_data)} chars):\n{output_data[:2000]}\n")
        if len(output_data) > 2000:
            self._write_transcript(f"... truncated {len(output_data) - 2000} chars ...\n")
        
        self._queue_write()
        
    def log_phase(self, phase_name: str, phase_number: int, status: str, 
                  duration: Optional[float] = None, context: Optional[str] = None):
        """Log workflow phase execution with optional context."""
        # If context is provided, append it to the phase name
        display_name = f"{phase_name}: {context}" if context else phase_name
        
        phase_info = {
            "name": display_name,
            "number": phase_number,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "base_phase": phase_name,
            "context": context
        }
        self.log_data["phases"].append(phase_info)
        self._queue_write()
        
    def log_error(self, error_type: str, error_message: str, stack_trace: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None):
        """Log an error with full details."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "stack_trace": stack_trace or traceback.format_exc(),
            "context": context or {}
        }
        self.log_data["errors"].append(error_info)
        
        # Write to transcript
        self._write_transcript(f"\n{'!'*80}\n")
        self._write_transcript(f"ERROR: {error_type}\n")
        self._write_transcript(f"MESSAGE: {error_message}\n")
        if stack_trace:
            self._write_transcript(f"STACK TRACE:\n{stack_trace}\n")
        self._write_transcript(f"{'!'*80}\n")
        
        self._queue_write()
        
    def log_system_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a system event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        self.log_data["system_events"].append(event)
        self._queue_write()
        
    def capture_output(self, stream_type: str, text: str):
        """Capture stdout/stderr output."""
        # Write to original stream
        if stream_type == "stdout":
            self._original_stdout.write(text)
            self._original_stdout.flush()
        else:
            self._original_stderr.write(text)
            self._original_stderr.flush()
            
        # Log significant output
        if text.strip():
            self._write_transcript(text)
            
    def _write_transcript(self, text: str):
        """Queue text for transcript writing."""
        self.transcript_queue.put(text)
        
    def _queue_write(self):
        """Queue the current log data for writing."""
        self.log_queue.put(self.log_data.copy())
        
    def _writer_loop(self):
        """Background thread that writes log data to disk."""
        while True:
            # Write JSON log
            try:
                log_data = self.log_queue.get(timeout=0.1)
                with open(self.log_file, 'w') as f:
                    json.dump(log_data, f, indent=2, default=str)
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error writing log: {e}", file=self._original_stderr)
                
            # Write transcript
            try:
                while not self.transcript_queue.empty():
                    text = self.transcript_queue.get_nowait()
                    with open(self.transcript_file, 'a', encoding='utf-8') as f:
                        f.write(text)
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error writing transcript: {e}", file=self._original_stderr)
                
    def finalize(self, status: str = "completed"):
        """Finalize the log with ending status."""
        self.disable_output_capture()
        
        self.log_data["final_status"] = status
        self.log_data["session_info"]["end_time"] = datetime.now().isoformat()
        self.log_data["session_info"]["total_duration_seconds"] = (
            datetime.now() - self.start_time
        ).total_seconds()
        
        # Final write
        self._queue_write()
        
        # Give writer thread time to finish
        import time
        time.sleep(0.5)
        
        print(f"\n📝 Debug log saved to: {self.log_file}", file=self._original_stdout)
        print(f"📄 Transcript saved to: {self.transcript_file}", file=self._original_stdout)


class OutputCapture:
    """Captures stdout/stderr output."""
    
    def __init__(self, logger: DebugLogger, stream_type: str):
        self.logger = logger
        self.stream_type = stream_type
        
    def write(self, text: str):
        """Capture and forward output."""
        self.logger.capture_output(self.stream_type, text)
        
    def flush(self):
        """Flush the output stream."""
        pass
        
    def __getattr__(self, name):
        """Forward other attributes to original stream."""
        original = self.logger._original_stdout if self.stream_type == "stdout" else self.logger._original_stderr
        return getattr(original, name)


# Global logger instance
_debug_logger: Optional[DebugLogger] = None


def get_debug_logger() -> Optional[DebugLogger]:
    """Get the global debug logger instance."""
    return _debug_logger


def init_debug_logger(log_dir: Optional[Path] = None) -> DebugLogger:
    """Initialize the global debug logger."""
    global _debug_logger
    _debug_logger = DebugLogger(log_dir)
    return _debug_logger