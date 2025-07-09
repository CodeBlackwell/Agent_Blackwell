"""
Output formatter for consistent demo output.
Provides formatting utilities for different output types and modes.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class OutputFormatter:
    """Formats output for demos in various styles."""
    
    def __init__(self, mode: str = "normal", enable_colors: bool = True):
        """Initialize the output formatter.
        
        Args:
            mode: Output mode ('normal', 'short', 'verbose')
            enable_colors: Whether to use ANSI colors
        """
        self.mode = mode
        self.enable_colors = enable_colors
        
    def format_workflow_start(self, workflow_type: str, requirements: str) -> str:
        """Format workflow start message.
        
        Args:
            workflow_type: Type of workflow
            requirements: Project requirements
            
        Returns:
            Formatted message
        """
        if self.mode == "short":
            req_preview = requirements[:50] + "..." if len(requirements) > 50 else requirements
            return f"🚀 {workflow_type}: {req_preview}"
        elif self.mode == "verbose":
            return f"""
🚀 Starting Workflow
Type: {workflow_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Requirements:
{'-' * 60}
{requirements}
{'-' * 60}
"""
        else:  # normal
            req_preview = requirements[:100] + "..." if len(requirements) > 100 else requirements
            return f"""
🚀 Starting {workflow_type} workflow
📋 Requirements: {req_preview}
"""
    
    def format_agent_output(self, agent_name: str, output: str, 
                          duration: Optional[float] = None) -> str:
        """Format agent output.
        
        Args:
            agent_name: Name of the agent
            output: Agent's output
            duration: Execution duration in seconds
            
        Returns:
            Formatted message
        """
        if self.mode == "short":
            # Just show agent name and status
            status = "✅" if output else "❌"
            time_str = f" ({duration:.1f}s)" if duration else ""
            return f"{status} {agent_name}{time_str}"
            
        elif self.mode == "verbose":
            # Show full output
            time_str = f"\nDuration: {duration:.2f} seconds" if duration else ""
            return f"""
{'=' * 60}
🤖 {agent_name.upper()}
{'=' * 60}
{output}
{time_str}
{'=' * 60}
"""
        else:  # normal
            # Show truncated output
            preview_length = 200
            preview = output[:preview_length] + "..." if len(output) > preview_length else output
            time_str = f" ({duration:.1f}s)" if duration else ""
            
            return f"""
🤖 {agent_name}{time_str}
{'-' * 40}
{preview}
"""
    
    def format_workflow_complete(self, success: bool, duration: float,
                               session_id: Optional[str] = None,
                               generated_path: Optional[str] = None) -> str:
        """Format workflow completion message.
        
        Args:
            success: Whether workflow succeeded
            duration: Total duration in seconds
            session_id: Session ID
            generated_path: Path to generated code
            
        Returns:
            Formatted message
        """
        status = "✅ SUCCESS" if success else "❌ FAILED"
        
        if self.mode == "short":
            return f"{status} in {duration:.1f}s"
            
        message = f"\n{'=' * 60}\n"
        message += f"{status}\n"
        message += f"Duration: {duration:.1f} seconds\n"
        
        if session_id:
            message += f"Session: {session_id}\n"
            
        if generated_path and success:
            message += f"\n📁 Generated code: {generated_path}\n"
            
        message += f"{'=' * 60}\n"
        return message
        
    def format_error(self, error: str, error_type: Optional[str] = None,
                    traceback: Optional[str] = None) -> str:
        """Format error message.
        
        Args:
            error: Error message
            error_type: Type of error
            traceback: Full traceback (for verbose mode)
            
        Returns:
            Formatted error message
        """
        if self.mode == "short":
            return f"❌ Error: {error}"
            
        message = "\n❌ ERROR\n"
        message += "-" * 60 + "\n"
        
        if error_type:
            message += f"Type: {error_type}\n"
            
        message += f"Message: {error}\n"
        
        if self.mode == "verbose" and traceback:
            message += f"\nTraceback:\n{traceback}\n"
            
        message += "-" * 60 + "\n"
        return message
        
    def format_phase_progress(self, phase: str, current: int, total: int) -> str:
        """Format phase progress indicator.
        
        Args:
            phase: Current phase name
            current: Current step number
            total: Total number of steps
            
        Returns:
            Formatted progress message
        """
        if self.mode == "short":
            return f"[{current}/{total}] {phase}"
            
        percentage = (current / total * 100) if total > 0 else 0
        
        if self.mode == "verbose":
            bar_length = 40
            filled = int(bar_length * current / total) if total > 0 else 0
            bar = '█' * filled + '░' * (bar_length - filled)
            return f"""
Phase {current}/{total}: {phase}
Progress: [{bar}] {percentage:.0f}%
"""
        else:  # normal
            return f"\n🔄 Phase {current}/{total}: {phase} ({percentage:.0f}%)\n"
            
    def format_file_list(self, files: List[str], title: str = "Generated Files") -> str:
        """Format a list of files.
        
        Args:
            files: List of file paths
            title: Title for the list
            
        Returns:
            Formatted file list
        """
        if not files:
            return f"\n{title}: (none)\n"
            
        if self.mode == "short":
            return f"\n{title}: {len(files)} files\n"
            
        message = f"\n{title}:\n"
        
        if self.mode == "verbose":
            # Show full paths
            for file in sorted(files):
                message += f"  📄 {file}\n"
        else:  # normal
            # Group by directory
            by_dir: Dict[str, List[str]] = {}
            for file in files:
                dir_name = os.path.dirname(file) or "."
                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(os.path.basename(file))
                
            for dir_name, file_names in sorted(by_dir.items()):
                if len(by_dir) > 1:
                    message += f"  📁 {dir_name}/\n"
                for name in sorted(file_names):
                    prefix = "    " if len(by_dir) > 1 else "  "
                    message += f"{prefix}├── {name}\n"
                    
        return message
        
    def format_test_results(self, passed: int, failed: int, 
                          skipped: int = 0, duration: Optional[float] = None) -> str:
        """Format test execution results.
        
        Args:
            passed: Number of passed tests
            failed: Number of failed tests
            skipped: Number of skipped tests
            duration: Test duration in seconds
            
        Returns:
            Formatted test results
        """
        total = passed + failed + skipped
        
        if self.mode == "short":
            status = "✅" if failed == 0 else "❌"
            return f"{status} Tests: {passed}/{total}"
            
        message = "\n🧪 Test Results\n"
        message += "-" * 40 + "\n"
        
        if total > 0:
            message += f"✅ Passed:  {passed}\n"
            if failed > 0:
                message += f"❌ Failed:  {failed}\n"
            if skipped > 0:
                message += f"⏭️  Skipped: {skipped}\n"
                
            success_rate = (passed / total * 100) if total > 0 else 0
            message += f"\nSuccess Rate: {success_rate:.1f}%\n"
        else:
            message += "No tests found\n"
            
        if duration:
            message += f"Duration: {duration:.2f}s\n"
            
        message += "-" * 40 + "\n"
        return message
        
    def save_json_report(self, data: Dict[str, Any], 
                        output_file: Optional[Path] = None) -> Path:
        """Save data as JSON report.
        
        Args:
            data: Data to save
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("demo_outputs/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"report_{timestamp}.json"
            
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
        return output_file
    
    def print_banner(self, title: str, subtitle: Optional[str] = None, width: int = 60) -> None:
        """Print a banner with title and optional subtitle.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
            width: Banner width
        """
        print("\n" + "=" * width)
        print(title.center(width))
        if subtitle:
            print(subtitle.center(width))
        print("=" * width + "\n")
    
    def print_section(self, title: str, width: int = 60) -> None:
        """Print a section header.
        
        Args:
            title: Section title
            width: Section width
        """
        print(f"\n{title}")
        print("-" * min(len(title) + 5, width))
    
    def show_error(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        """Show an error message with optional suggestions.
        
        Args:
            message: Error message
            suggestions: List of suggested actions
        """
        print(f"\n❌ Error: {message}")
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   • {suggestion}")


# Convenience formatters for different modes
def get_formatter(mode: str = "normal") -> OutputFormatter:
    """Get a formatter for the specified mode.
    
    Args:
        mode: Output mode ('normal', 'short', 'verbose')
        
    Returns:
        OutputFormatter instance
    """
    return OutputFormatter(mode=mode)