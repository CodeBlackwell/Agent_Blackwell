"""
Real-time agent output handler for displaying step-by-step agent interactions.
"""
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class AgentInteraction:
    """Represents a single agent interaction"""
    agent_name: str
    input_text: str
    output_text: str
    timestamp: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealTimeOutputHandler:
    """Handles real-time display of agent outputs"""
    
    def __init__(self, display_mode: str = "detailed", max_input_chars: int = 1000, max_output_chars: int = 2000):
        """
        Initialize the output handler.
        
        Args:
            display_mode: "detailed" for full output, "summary" for condensed view, "minimal" for one-line status
            max_input_chars: Maximum characters to display for input
            max_output_chars: Maximum characters to display for output
        """
        self.display_mode = display_mode
        self.max_input_chars = max_input_chars
        self.max_output_chars = max_output_chars
        self.interactions: list[AgentInteraction] = []
        self.start_time = time.time()
        self.current_agent_start = None
        self.agent_descriptions = {
            "planner_agent": "Creating project plan",
            "designer_agent": "Architecting system",
            "feature_parser": "Breaking down features", 
            "coder_agent": "Implementing code",
            "test_writer_agent": "Writing tests",
            "reviewer_agent": "Reviewing code",
            "executor_agent": "Running tests",
            "validator_agent": "Validating implementation",
            "error_analyzer": "Analyzing errors",
            "progress_tracker": "Tracking progress",
            "integration_verifier": "Verifying integration"
        }
        
    def display_separator(self, char: str = "=", length: int = 80):
        """Display a separator line"""
        print(char * length)
        
    def display_agent_header(self, agent_name: str, step_number: int):
        """Display agent header with formatting"""
        self.display_separator()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🤖 AGENT #{step_number}: {agent_name.upper()} [{timestamp}]")
        self.display_separator("-", 80)
        
    def display_input(self, input_text: str):
        """Display agent input"""
        print("📥 INPUT:")
        print("-" * 40)
        if self.display_mode == "detailed":
            print(input_text[:self.max_input_chars])
            if len(input_text) > self.max_input_chars:
                print(f"\n... (truncated {len(input_text) - self.max_input_chars} characters)")
        else:
            # Summary mode - show first 200 chars
            print(input_text[:200] + "..." if len(input_text) > 200 else input_text)
        print()
        
    def display_output(self, output_text: str):
        """Display agent output"""
        print("📤 OUTPUT:")
        print("-" * 40)
        if self.display_mode == "detailed":
            print(output_text[:self.max_output_chars])
            if len(output_text) > self.max_output_chars:
                print(f"\n... (truncated {len(output_text) - self.max_output_chars} characters)")
        else:
            # Summary mode - show first 300 chars
            print(output_text[:300] + "..." if len(output_text) > 300 else output_text)
        print()
        
    def display_metadata(self, metadata: Dict[str, Any]):
        """Display additional metadata"""
        if metadata:
            print("📊 METADATA:")
            print("-" * 40)
            for key, value in metadata.items():
                print(f"  • {key}: {value}")
            print()
    
    def on_agent_start(self, agent_name: str, input_text: str, step_number: int) -> float:
        """
        Called when an agent starts processing.
        
        Returns:
            Start timestamp
        """
        start_time = time.time()
        self.current_agent_start = start_time
        
        if self.display_mode == "minimal":
            # Get agent description
            agent_key = agent_name.lower()
            description = self.agent_descriptions.get(agent_key, "Processing")
            
            # Check if this is a feature-specific task
            if "feature" in input_text.lower():
                # Try to extract feature info
                lines = input_text.split('\n')
                for line in lines:
                    if "feature" in line.lower() and "/" in line:
                        description = f"{description} {line.strip()}"
                        break
            
            print(f"⏳ {agent_name.replace('_', ' ').title()}: {description}...", end='', flush=True)
        else:
            self.display_agent_header(agent_name, step_number)
            self.display_input(input_text)
            print("⏳ Processing...")
            print()
        return start_time
        
    def on_agent_complete(self, agent_name: str, input_text: str, output_text: str, 
                         start_time: float, step_number: int, metadata: Optional[Dict[str, Any]] = None):
        """Called when an agent completes processing"""
        duration = time.time() - start_time
        
        # Store interaction
        interaction = AgentInteraction(
            agent_name=agent_name,
            input_text=input_text,
            output_text=output_text,
            timestamp=start_time,
            duration=duration,
            metadata=metadata or {}
        )
        self.interactions.append(interaction)
        
        if self.display_mode == "minimal":
            # Determine success/failure
            success = True
            if metadata and metadata.get("error"):
                success = False
            elif "error" in output_text.lower() or "failed" in output_text.lower():
                success = False
            
            status_emoji = "✅" if success else "❌"
            print(f" {status_emoji} ({duration:.1f}s)")
        else:
            # Display output
            self.display_output(output_text)
            
            # Display metadata if available
            if metadata:
                self.display_metadata(metadata)
                
            # Display completion info
            print(f"✅ COMPLETED in {duration:.2f} seconds")
            self.display_separator()
            print()
        
    def on_review_start(self, stage: str, target_agent: str):
        """Called when a review starts"""
        if self.display_mode != "minimal":
            print(f"🔍 REVIEWING {stage} output from {target_agent}...")
        
    def on_review_complete(self, approved: bool, feedback: str):
        """Called when a review completes"""
        if self.display_mode == "minimal":
            # Only show if revision needed
            if not approved:
                print(f"🔄 Revision needed: {feedback[:50]}...")
        else:
            status = "✅ APPROVED" if approved else "❌ NEEDS REVISION"
            print(f"{status}")
            if feedback:
                print(f"   Feedback: {feedback}")
            print()
        
    def on_retry(self, agent_name: str, attempt: int, reason: str):
        """Called when an agent retry occurs"""
        if self.display_mode == "minimal":
            print(f"🔄 Retry #{attempt}: {reason[:30]}...")
        else:
            print(f"🔄 RETRY #{attempt} for {agent_name}: {reason}")
            print()
        
    def generate_summary(self) -> str:
        """Generate a summary of all interactions"""
        total_duration = time.time() - self.start_time
        
        summary = ["", "📊 WORKFLOW EXECUTION SUMMARY", "=" * 80]
        summary.append(f"Total Duration: {total_duration:.2f} seconds")
        summary.append(f"Total Agents Executed: {len(self.interactions)}")
        summary.append("")
        
        summary.append("Agent Execution Sequence:")
        summary.append("-" * 40)
        for i, interaction in enumerate(self.interactions, 1):
            summary.append(f"{i}. {interaction.agent_name} ({interaction.duration:.2f}s)")
            
        summary.append("")
        summary.append("Detailed Timing Breakdown:")
        summary.append("-" * 40)
        for interaction in self.interactions:
            timestamp = datetime.fromtimestamp(interaction.timestamp).strftime("%H:%M:%S")
            summary.append(f"• {interaction.agent_name}: {interaction.duration:.2f}s (started at {timestamp})")
            
        return "\n".join(summary)
    
    def export_interactions(self, filepath: str):
        """Export all interactions to a JSON file"""
        data = {
            "workflow_duration": time.time() - self.start_time,
            "interactions": [
                {
                    "agent_name": i.agent_name,
                    "input_preview": i.input_text[:200] + "..." if len(i.input_text) > 200 else i.input_text,
                    "output_preview": i.output_text[:200] + "..." if len(i.output_text) > 200 else i.output_text,
                    "timestamp": i.timestamp,
                    "duration": i.duration,
                    "metadata": i.metadata
                }
                for i in self.interactions
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"📁 Interactions exported to: {filepath}")

# Global handler instance
_global_handler: Optional[RealTimeOutputHandler] = None

def get_output_handler() -> RealTimeOutputHandler:
    """Get or create the global output handler"""
    global _global_handler
    if _global_handler is None:
        _global_handler = RealTimeOutputHandler()
    return _global_handler

def set_output_handler(handler: RealTimeOutputHandler):
    """Set the global output handler"""
    global _global_handler
    _global_handler = handler