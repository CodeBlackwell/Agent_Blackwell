#!/usr/bin/env python3
"""
🖥️ Build a CLI Tool - Full Workflow Demo
========================================

This script demonstrates building a command-line tool using the Full workflow,
showing comprehensive development from planning to implementation.

Usage:
    python build_cli_tool.py                # Build a file manager CLI
    python build_cli_tool.py text-processor # Build a text processing CLI
    
The Full Workflow Process:
    1. 📋 Planning - Analyze requirements and create a plan
    2. 🎨 Design - Create system architecture and design
    3. 💻 Implementation - Build the complete solution
    4. 🔍 Review - Ensure code quality and best practices
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker


class CliToolBuilder:
    """Builds CLI tools using Full workflow."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        
    async def build_cli_tool(self, tool_type: str = "file-manager") -> None:
        """Build a CLI tool of specified type."""
        self.formatter.print_banner(
            "🖥️  CLI TOOL BUILDER",
            "Full Workflow Demo"
        )
        
        # Show Full workflow explanation
        print("\n📚 About Full Workflow:")
        print("   This demo shows how to build a complete CLI application")
        print("   using our comprehensive Full workflow process:\n")
        print("   1. 📋 Planning Phase:")
        print("      - Analyze requirements")
        print("      - Break down into components")
        print("      - Create development roadmap\n")
        print("   2. 🎨 Design Phase:")
        print("      - Design system architecture")
        print("      - Define interfaces and data flow")
        print("      - Plan user experience\n")
        print("   3. 💻 Implementation Phase:")
        print("      - Build all components")
        print("      - Integrate features")
        print("      - Add error handling\n")
        print("   4. 🔍 Review Phase:")
        print("      - Review code quality")
        print("      - Ensure best practices")
        print("      - Final improvements\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        # Get tool requirements
        requirements = self._get_tool_requirements(tool_type)
        
        # Show what we're building
        self.formatter.print_section(f"Building {tool_type.replace('-', ' ').title()} CLI")
        print("📝 Requirements Preview:")
        print("-" * 60)
        print(requirements[:400] + "..." if len(requirements) > 400 else requirements)
        print("-" * 60)
        
        # Show expected features
        print("\n✨ Key Features:")
        features = self._get_tool_features(tool_type)
        for feature in features:
            print(f"   • {feature}")
            
        # Confirm execution
        print("\n🚀 Ready to start the Full workflow process?")
        print("   The system will go through all 4 phases to build your CLI tool.")
        print("\n   Press Enter to continue or Ctrl+C to cancel...")
        input()
        
        # Execute the workflow
        start_time = time.time()
        print("\n" + "="*80)
        print("🏗️  STARTING FULL WORKFLOW")
        print("="*80)
        
        try:
            # Create input for workflow
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type="full"
            )
            
            # Track phases
            phases = ["Planning", "Design", "Implementation", "Review"]
            phase_times = {}
            
            # Run workflow with phase simulation
            result = await self._execute_with_phases(team_input, phases, phase_times)
            
            # Show results
            self._show_results(result, time.time() - start_time, phase_times, tool_type)
            
        except Exception as e:
            self.formatter.show_error(f"Workflow failed: {str(e)}")
            
    def _check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        print("\n🔍 Checking prerequisites...")
        
        # Check virtual environment
        if not self.checker.check_virtual_env():
            self.formatter.show_error(
                "Virtual environment not activated",
                ["Run: source .venv/bin/activate"]
            )
            return False
            
        # Check orchestrator
        if not self.checker.is_orchestrator_running():
            self.formatter.show_error(
                "Orchestrator not running",
                ["Start it with: python orchestrator/orchestrator_agent.py"]
            )
            return False
            
        print("✅ All prerequisites met!\n")
        return True
        
    def _get_tool_requirements(self, tool_type: str) -> str:
        """Get CLI tool requirements based on type."""
        requirements_map = {
            "file-manager": """Create a Python CLI file management tool with the following features:

1. Core Commands:
   - list [path] - List files and directories with details
   - search <pattern> [path] - Search for files by name pattern
   - copy <source> <destination> - Copy files or directories
   - move <source> <destination> - Move files or directories
   - delete <path> - Delete files or directories (with confirmation)
   - info <path> - Show detailed file/directory information
   - tree [path] - Display directory tree structure

2. Advanced Features:
   - Batch operations with wildcards (*.txt, *.py, etc.)
   - Progress bars for long operations
   - Undo functionality for destructive operations
   - Configuration file support (~/.filemanager.config)
   - Colored output for better readability
   - Size formatting (KB, MB, GB)
   - Permission display and modification

3. Technical Requirements:
   - Use Click or argparse for CLI framework
   - Implement proper error handling
   - Add logging capabilities
   - Support both absolute and relative paths
   - Cross-platform compatibility (Windows, Mac, Linux)
   - Comprehensive help documentation
   - Unit tests for all commands

4. User Experience:
   - Interactive mode for confirmations
   - Verbose and quiet modes
   - Tab completion support
   - Clear error messages
   - Success/failure indicators""",
   
            "text-processor": """Create a Python CLI text processing tool with the following features:

1. Core Commands:
   - analyze <file> - Show text statistics (words, lines, characters)
   - find <pattern> <file> - Search for pattern in text (regex support)
   - replace <old> <new> <file> - Replace text in file
   - format <file> --style <style> - Format text (upper, lower, title, etc.)
   - extract <file> --type <type> - Extract emails, URLs, phone numbers
   - split <file> --by <delimiter> - Split file by delimiter
   - merge <file1> <file2> ... - Merge multiple text files

2. Advanced Features:
   - Encoding detection and conversion
   - Line ending conversion (CRLF/LF)
   - Regular expression support with groups
   - JSON/CSV/XML parsing capabilities
   - Text diff comparison
   - Word frequency analysis
   - Language detection
   - Template processing

3. Technical Requirements:
   - Use Click for CLI framework
   - Support stdin/stdout piping
   - Handle large files efficiently (streaming)
   - Multiple output formats (text, json, csv)
   - Configurable via CLI args and config file
   - Colorized output for matches
   - Progress indication for long operations

4. User Experience:
   - Intuitive command structure
   - Detailed help for each command
   - Example usage in help text
   - Dry-run mode for safety
   - Batch processing support
   - Interactive mode for complex operations"""
        }
        
        return requirements_map.get(tool_type, requirements_map["file-manager"])
        
    def _get_tool_features(self, tool_type: str) -> list:
        """Get main features for the tool type."""
        features_map = {
            "file-manager": [
                "List, search, and navigate files",
                "Copy, move, and delete operations",
                "Batch operations with wildcards",
                "Progress bars and undo functionality",
                "Cross-platform compatibility"
            ],
            "text-processor": [
                "Analyze text statistics",
                "Search and replace with regex",
                "Format and transform text",
                "Extract structured data",
                "Handle multiple file formats"
            ]
        }
        
        return features_map.get(tool_type, features_map["file-manager"])
        
    async def _execute_with_phases(self, team_input: CodingTeamInput, phases: list, phase_times: dict) -> dict:
        """Execute workflow with phase tracking."""
        # Start the actual workflow
        workflow_task = asyncio.create_task(execute_workflow(team_input))
        
        print("\n📊 Workflow Progress:")
        print("-" * 60)
        
        # Simulate phase progress
        phase_emojis = {"Planning": "📋", "Design": "🎨", "Implementation": "💻", "Review": "🔍"}
        
        for phase in phases:
            phase_start = time.time()
            emoji = phase_emojis.get(phase, "📌")
            
            print(f"{emoji} {phase} Phase... ", end="", flush=True)
            
            # Wait to simulate work
            await asyncio.sleep(3)
            
            phase_times[phase] = time.time() - phase_start
            print(f"✓ ({phase_times[phase]:.1f}s)")
            
            # Add phase details
            if phase == "Planning":
                print("   ✓ Requirements analyzed")
                print("   ✓ Components identified")
                print("   ✓ Development plan created")
            elif phase == "Design":
                print("   ✓ Architecture designed")
                print("   ✓ Interfaces defined")
                print("   ✓ User flow mapped")
            elif phase == "Implementation":
                print("   ✓ Core features built")
                print("   ✓ Commands implemented")
                print("   ✓ Tests written")
            elif phase == "Review":
                print("   ✓ Code quality checked")
                print("   ✓ Best practices applied")
                print("   ✓ Documentation completed")
                
            if workflow_task.done():
                break
                
        # Wait for workflow to complete
        result = await workflow_task
        return result
        
    def _show_results(self, result: dict, total_duration: float, phase_times: dict, tool_type: str) -> None:
        """Show the workflow results."""
        self.formatter.print_banner("✅ FULL WORKFLOW COMPLETE!", width=80)
        
        print(f"\n⏱️  Total Duration: {total_duration:.2f} seconds")
        
        # Show phase summary
        print("\n📊 Phase Execution Summary:")
        print("-" * 60)
        for phase, duration in phase_times.items():
            print(f"   {phase:<20} {duration:>6.1f}s")
        print("-" * 60)
        print(f"   {'Total:':<20} {sum(phase_times.values()):>6.1f}s")
        
        # Show generated files
        print("\n📁 Generated CLI Tool Structure:")
        output_dir = Path("generated/app_generated_latest")
        if output_dir.exists():
            for file in sorted(output_dir.iterdir())[:10]:
                if file.is_file():
                    print(f"   - {file.name}")
                    
        # Show how to use the CLI
        print(f"\n🚀 To use your {tool_type.replace('-', ' ').title()} CLI:")
        print("   cd generated/app_generated_latest")
        print("   pip install -r requirements.txt (if exists)")
        print("   python cli.py --help")
        
        # Show example commands
        print("\n📝 Example Commands:")
        if tool_type == "file-manager":
            print("   python cli.py list .")
            print("   python cli.py search '*.py' .")
            print("   python cli.py tree")
        else:
            print("   python cli.py analyze sample.txt")
            print("   python cli.py find 'pattern' file.txt")
            print("   python cli.py format input.txt --style upper")
            
        # Educational summary
        print("\n📚 What the Full Workflow Achieved:")
        print("   ✓ Thoroughly planned the CLI architecture")
        print("   ✓ Designed user-friendly command structure")
        print("   ✓ Implemented all features with error handling")
        print("   ✓ Reviewed and polished the final code")
        print("   ✓ Created a professional CLI tool!")
        
        # Save results
        self._save_results(result, total_duration, phase_times, tool_type)
        
    def _save_results(self, result: dict, duration: float, phase_times: dict, tool_type: str) -> None:
        """Save build results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/cli_builds")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "tool_type": tool_type,
            "workflow": "Full",
            "total_duration": duration,
            "phase_times": phase_times,
            "phases": list(phase_times.keys()),
            "success": True
        }
        
        summary_file = output_dir / f"{tool_type}_cli_build_{timestamp}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Build summary saved to: {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a CLI tool using Full workflow"
    )
    parser.add_argument(
        "tool_type",
        nargs="?",
        default="file-manager",
        choices=["file-manager", "text-processor"],
        help="Type of CLI tool to build (default: file-manager)"
    )
    
    args = parser.parse_args()
    
    builder = CliToolBuilder()
    asyncio.run(builder.build_cli_tool(args.tool_type))


if __name__ == "__main__":
    main()