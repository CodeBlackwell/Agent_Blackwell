#!/usr/bin/env python3
"""
🚀 Direct Workflow Runner for Multi-Agent Coding System

This script provides direct access to all system workflows without unnecessary overhead.
It supports both interactive and command-line interfaces for easy workflow execution.

Usage:
    python run.py                    # Interactive mode
    python run.py workflow tdd --task "Build a calculator API"
    python run.py workflow mvp_incremental --task "Create a task manager"
    python run.py --help            # Get help
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
from datetime import datetime
import json
import subprocess
import platform
import atexit
import signal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import workflow components directly
from workflows.workflow_manager import execute_workflow, get_available_workflows, get_workflow_description
from shared.data_models import CodingTeamInput
from workflows.monitoring import WorkflowExecutionTracer


# Global variable to track orchestrator process
ORCHESTRATOR_PROCESS = None


def kill_process_on_port(port: int):
    """Kill any process listening on the specified port."""
    try:
        if platform.system() == "Darwin" or platform.system() == "Linux":
            # Find process using lsof
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(["kill", "-9", pid])
                        print(f"✅ Killed existing process {pid} on port {port}")
                    except Exception as e:
                        print(f"⚠️  Failed to kill process {pid}: {e}")
        elif platform.system() == "Windows":
            # Windows command to find and kill process
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{port}"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        try:
                            subprocess.run(["taskkill", "/F", "/PID", pid], shell=True)
                            print(f"✅ Killed existing process {pid} on port {port}")
                        except Exception as e:
                            print(f"⚠️  Failed to kill process {pid}: {e}")
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")


def start_orchestrator_server():
    """Start the orchestrator server in the background."""
    global ORCHESTRATOR_PROCESS
    
    # Kill any existing process on port 8080
    print("🔍 Checking for existing orchestrator on port 8080...")
    kill_process_on_port(8080)
    
    # Give it a moment to clean up
    time.sleep(1)
    
    # Start the orchestrator
    print("🚀 Starting orchestrator server...")
    orchestrator_path = Path(__file__).parent / "orchestrator" / "orchestrator_agent.py"
    
    try:
        # Start orchestrator in background
        ORCHESTRATOR_PROCESS = subprocess.Popen(
            [sys.executable, str(orchestrator_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for it to start
        time.sleep(3)
        
        # Check if it's running
        if ORCHESTRATOR_PROCESS.poll() is None:
            print("✅ Orchestrator server started successfully on port 8080")
            return True
        else:
            print("❌ Orchestrator server failed to start")
            stdout, stderr = ORCHESTRATOR_PROCESS.communicate(timeout=1)
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start orchestrator: {e}")
        return False


def cleanup_orchestrator():
    """Clean up orchestrator process on exit."""
    global ORCHESTRATOR_PROCESS
    if ORCHESTRATOR_PROCESS and ORCHESTRATOR_PROCESS.poll() is None:
        print("\n🛑 Stopping orchestrator server...")
        ORCHESTRATOR_PROCESS.terminate()
        try:
            ORCHESTRATOR_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ORCHESTRATOR_PROCESS.kill()
        print("✅ Orchestrator server stopped")


# Register cleanup function
atexit.register(cleanup_orchestrator)


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    cleanup_orchestrator()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class DirectWorkflowRunner:
    """Direct runner for workflow execution."""
    
    def __init__(self):
        self.available_workflows = get_available_workflows()
        self.orchestrator_started = False
        
    def ensure_orchestrator_running(self):
        """Ensure the orchestrator server is running."""
        if not self.orchestrator_started:
            if start_orchestrator_server():
                self.orchestrator_started = True
            else:
                raise RuntimeError("Failed to start orchestrator server")
        
    async def run_interactive(self):
        """Run in interactive mode with simple workflow selection."""
        print("\n" + "="*60)
        print("🚀 MULTI-AGENT CODING SYSTEM - Direct Workflow Runner")
        print("="*60)
        
        # Show available workflows
        print("\nAvailable Workflows:")
        for i, workflow in enumerate(self.available_workflows, 1):
            desc = get_workflow_description(workflow)
            print(f"  {i}. {workflow:<20} - {desc}")
        print("  0. Exit")
        
        # Get selection
        while True:
            try:
                choice = input("\nSelect workflow number (or 0 to exit): ").strip()
                if choice == "0":
                    print("\n👋 Thanks for using the Multi-Agent Coding System!")
                    return
                    
                idx = int(choice) - 1
                if 0 <= idx < len(self.available_workflows):
                    workflow_type = self.available_workflows[idx]
                    break
                else:
                    print("❌ Invalid selection. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        # Get requirements
        print(f"\n📝 Selected workflow: {workflow_type}")
        print("Enter your requirements (press Enter twice when done):")
        
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                lines.pop()  # Remove the extra empty line
                break
            lines.append(line)
        
        requirements = "\n".join(lines).strip()
        
        if not requirements:
            print("❌ Requirements cannot be empty.")
            return
            
        # Execute workflow
        await self._execute_workflow(requirements, workflow_type)
        
    async def _execute_workflow(self, requirements: str, workflow_type: str, 
                              config: Optional[Dict[str, Any]] = None):
        """Execute a workflow directly."""
        # Ensure orchestrator is running
        self.ensure_orchestrator_running()
        
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting {workflow_type} workflow")
        print(f"📋 Requirements: {requirements[:100]}..." if len(requirements) > 100 else f"📋 Requirements: {requirements}")
        print(f"{'='*60}\n")
        
        # Create input data
        input_data = CodingTeamInput(
            requirements=requirements,
            workflow_type=workflow_type
        )
        
        # Apply any configuration
        if config:
            for key, value in config.items():
                if hasattr(input_data, key):
                    setattr(input_data, key, value)
        
        # Create tracer for monitoring
        tracer = WorkflowExecutionTracer(workflow_type)
        
        try:
            # Execute workflow
            results, report = await execute_workflow(input_data, tracer)
            
            duration = time.time() - start_time
            
            # Show results
            print(f"\n{'='*60}")
            print(f"✅ Workflow completed successfully in {duration:.2f} seconds")
            print(f"{'='*60}")
            
            # Extract generated path from results
            generated_path = None
            for result in results:
                if hasattr(result, 'output') and 'generated' in result.output:
                    # Try to extract path from output
                    import re
                    path_match = re.search(r'generated/[^\s]+', result.output)
                    if path_match:
                        generated_path = path_match.group(0)
                        break
            
            if generated_path:
                print(f"\n📁 Generated code location: {generated_path}")
                print(f"\nNext steps:")
                print(f"1. cd {generated_path}")
                print(f"2. Review the generated files")
                print(f"3. Install dependencies (if any)")
                print(f"4. Run the application")
            
            # Save workflow reports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = Path("workflow_reports")
            report_dir.mkdir(exist_ok=True)
            
            # Save timestamped JSON report (for archive)
            timestamped_report_file = report_dir / f"workflow_{workflow_type}_{timestamp}.json"
            with open(timestamped_report_file, 'w') as f:
                json.dump(report.to_dict() if hasattr(report, 'to_dict') else {}, f, indent=2)
            
            # Save latest execution reports (JSON and CSV)
            if report and hasattr(report, 'to_json') and hasattr(report, 'to_csv'):
                # Save JSON execution report
                json_report_file = report_dir / "execution_report.json"
                with open(json_report_file, 'w') as f:
                    f.write(report.to_json())
                
                # Save CSV execution report
                csv_report_file = report_dir / "execution_report.csv"
                with open(csv_report_file, 'w') as f:
                    f.write(report.to_csv())
                
                print(f"\n📊 Reports saved:")
                print(f"   - Timestamped archive: {timestamped_report_file}")
                print(f"   - Latest JSON report: {json_report_file}")
                print(f"   - Latest CSV report: {csv_report_file}")
                
                # Also save reports in generated code directory if available
                if generated_path and hasattr(report, 'generated_code_path'):
                    gen_path = Path(report.generated_code_path) if report.generated_code_path else Path(generated_path)
                    if gen_path.exists():
                        # Save debugging reports in generated code directory
                        gen_json_file = gen_path / "execution_report.json"
                        gen_csv_file = gen_path / "execution_report.csv"
                        
                        with open(gen_json_file, 'w') as f:
                            f.write(report.to_json())
                        
                        with open(gen_csv_file, 'w') as f:
                            f.write(report.to_csv())
                        
                        print(f"   - Generated dir reports: {gen_path}/execution_report.[json|csv]")
            else:
                print(f"\n📊 Report saved to: {timestamped_report_file}")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"\n{'='*60}")
            print(f"❌ Workflow failed after {duration:.2f} seconds")
            print(f"Error: {str(e)}")
            print(f"{'='*60}")
            
            if hasattr(e, '__traceback__'):
                import traceback
                print("\nTraceback:")
                traceback.print_exc()
                
    async def run_cli(self, args):
        """Run in CLI mode based on parsed arguments."""
        if args.command == "workflow":
            await self._cli_workflow(args)
        elif args.command == "list":
            self._cli_list()
        else:
            # No command specified, run interactive
            await self.run_interactive()
            
    async def _cli_workflow(self, args):
        """Handle CLI workflow command."""
        if args.list:
            self._cli_list()
            return
            
        if not args.type:
            print("Error: Workflow type required")
            print("Use 'python run.py workflow --list' to see available workflows")
            return
            
        if not args.task:
            print("Error: Task description required (--task)")
            return
            
        # Validate workflow type
        if args.type not in self.available_workflows:
            print(f"Error: Unknown workflow type '{args.type}'")
            print(f"Available workflows: {', '.join(self.available_workflows)}")
            return
            
        # Build configuration
        config = {}
        
        # Handle TDD-specific options
        if args.type in ["tdd", "mvp_incremental_tdd"] or args.tdd:
            if args.coverage:
                config['test_coverage_threshold'] = args.coverage
            if args.strict:
                config['enforce_red_phase'] = True
                config['retry_with_hints'] = True
                
        # Handle incremental workflow options
        if args.type in ["incremental", "mvp_incremental", "mvp_incremental_tdd"]:
            if args.max_retries:
                config['max_retries'] = args.max_retries
            if args.show_progress:
                config['show_progress'] = True
                
        # Execute workflow
        await self._execute_workflow(args.task, args.type, config)
        
    def _cli_list(self):
        """List available workflows."""
        print("\nAvailable workflows:")
        for workflow in self.available_workflows:
            desc = get_workflow_description(workflow)
            print(f"  {workflow:<20} - {desc}")
            
    def _show_help(self):
        """Show detailed help information."""
        help_text = """
📚 HELP & DOCUMENTATION

🎯 Quick Start:
1. Run 'python run.py' for interactive mode
2. Select a workflow from the list
3. Enter your requirements
4. Wait for the system to generate your code

⚙️  Orchestrator Management:
  - The orchestrator server starts automatically on port 8080
  - Existing processes on port 8080 are killed first
  - The server stops automatically when run.py exits
  - Use --no-orchestrator if managing it manually

📋 Command Line Usage:
  python run.py workflow <type> --task "..."   # Run a specific workflow
  python run.py workflow --list                 # List available workflows
  python run.py --help                          # Show CLI help
  python run.py --no-orchestrator ...           # Skip auto-start

🔧 Available Workflows:
  - tdd: Test-Driven Development (Tests → Implementation → Review)
  - full: Full development workflow (Planning → Design → Implementation → Review)
  - incremental: Feature-based incremental development
  - mvp_incremental: MVP incremental with validation
  - mvp_incremental_tdd: MVP incremental with TDD
  - planning: Planning phase only
  - design: Design phase only
  - implementation: Implementation phase only
  - review: Review phase only

💡 Examples:
  python run.py workflow tdd --task "Create a calculator API"
  python run.py workflow mvp_incremental --task "Build a task management system"
  python run.py workflow tdd --task "..." --strict --coverage 90

🚀 Workflow Options:
  --strict         : Enable strict TDD enforcement
  --coverage N     : Set test coverage threshold (TDD workflows)
  --max-retries N  : Set max retries for incremental workflows
  --show-progress  : Show detailed progress (incremental workflows)

📁 Output:
  - Generated code is saved in the 'generated/' directory
  - Workflow reports are saved in 'workflow_reports/'
  - Each run creates a timestamped subdirectory

🔴🟡🟢 TDD Workflow:
  The TDD workflow follows the RED-YELLOW-GREEN cycle:
  - RED: Write failing tests first
  - YELLOW: Implement code to pass tests
  - GREEN: All tests pass and code is approved
  
  This ensures every line of code is tested!

🏗️ Incremental Workflows:
  Incremental workflows break down projects into features:
  - Each feature is implemented and validated separately
  - Smart retry logic handles errors
  - Progress tracking shows completion status
  
  Perfect for complex projects!
"""
        print(help_text)


def create_parser():
    """Create argument parser for CLI mode."""
    parser = argparse.ArgumentParser(
        description="Direct Workflow Runner for Multi-Agent Coding System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                                 # Interactive mode
  python run.py workflow tdd --task "..."       # Run TDD workflow
  python run.py workflow full --task "..."      # Run full workflow
  python run.py workflow --list                 # List workflows
  
TDD Examples:
  python run.py workflow tdd --task "Calculator API" --strict
  python run.py workflow tdd --task "..." --coverage 90
  
Incremental Examples:
  python run.py workflow incremental --task "Task manager"
  python run.py workflow mvp_incremental --task "..." --show-progress
  
Note: The orchestrator server will be started automatically on port 8080.
      Use --no-orchestrator if you're managing it manually.
"""
    )
    
    # Global options
    parser.add_argument("--no-orchestrator", action="store_true",
                       help="Don't start the orchestrator server (assumes it's already running)")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run a workflow")
    workflow_parser.add_argument("type", nargs="?", help="Workflow type (e.g., tdd, full, incremental)")
    workflow_parser.add_argument("--task", help="Task description")
    workflow_parser.add_argument("--list", action="store_true", help="List available workflows")
    
    # TDD options
    workflow_parser.add_argument("--tdd", action="store_true", 
                                help="Use TDD approach (for non-TDD workflows)")
    workflow_parser.add_argument("--strict", action="store_true",
                                help="Enable strict TDD enforcement")
    workflow_parser.add_argument("--coverage", type=int,
                                help="Test coverage threshold (default: 85)")
    
    # Incremental workflow options
    workflow_parser.add_argument("--max-retries", type=int,
                                help="Max retries for incremental workflows")
    workflow_parser.add_argument("--show-progress", action="store_true",
                                help="Show detailed progress")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available workflows")
    
    return parser


async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create runner
    runner = DirectWorkflowRunner()
    
    # Handle --no-orchestrator flag
    if hasattr(args, 'no_orchestrator') and args.no_orchestrator:
        runner.orchestrator_started = True  # Skip auto-start
        print("ℹ️  Skipping orchestrator startup (--no-orchestrator flag)")
    
    # Show help if no arguments
    if len(sys.argv) == 1:
        # Run interactive mode
        await runner.run_interactive()
    else:
        try:
            await runner.run_cli(args)
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())