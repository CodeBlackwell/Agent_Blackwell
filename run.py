#!/usr/bin/env python3
"""
🚀 Direct Workflow Runner for Multi-Agent Coding System

This script provides direct access to all system workflows without unnecessary overhead.
It supports both interactive and command-line interfaces for easy workflow execution.

Usage:
    python run.py                    # Interactive mode
    python run.py workflow tdd --task "Build a calculator API"
    python run.py workflow mvp_incremental --task "Create a task manager"
    python run.py workflow enhanced_full --task "Build a REST API"
    python run.py --debug            # Enable debug logging
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
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import workflow components directly
from workflows.workflow_manager import execute_workflow, get_available_workflows, get_workflow_description
from shared.data_models import CodingTeamInput
from workflows.monitoring import WorkflowExecutionTracer


# Global variables
ORCHESTRATOR_PROCESS = None
DEBUG_MODE = False
_current_tracer = None


def signal_handler(signum, frame):
    """Handle interrupt signals to save partial reports."""
    global _current_tracer
    if _current_tracer:
        print("\n\n⚠️  Workflow interrupted! Saving partial report...")
        _current_tracer._auto_save(force=True)
        print("✅ Partial report saved to workflow_reports/")
    sys.exit(1)


def configure_logging(debug=False):
    """Configure logging based on debug mode."""
    import logging
    
    if debug:
        # Debug mode: show all logs with timestamps
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
    else:
        # Normal mode: minimal output
        logging.basicConfig(
            level=logging.WARNING,
            format='%(message)s',
            force=True
        )
        
        # Suppress verbose loggers
        logging.getLogger('workflow_manager').setLevel(logging.WARNING)
        logging.getLogger('orchestrator').setLevel(logging.WARNING)
        logging.getLogger('core').setLevel(logging.WARNING)
        logging.getLogger('core.initialize').setLevel(logging.ERROR)  # Suppress init messages
        logging.getLogger('workflows').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)
        logging.getLogger('docker').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('aiohttp').setLevel(logging.ERROR)


        logging.getLogger('shared').setLevel(logging.WARNING)
        logging.getLogger('mcp').setLevel(logging.WARNING)


def kill_process_on_port(port: int, debug: bool = False):
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
                        if debug:
                            print(f"✅ Killed existing process {pid} on port {port}")
                    except Exception as e:
                        if debug:
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
                            if debug:
                                print(f"✅ Killed existing process {pid} on port {port}")
                        except Exception as e:
                            if debug:
                                print(f"⚠️  Failed to kill process {pid}: {e}")
    except Exception as e:
        if debug:
            print(f"⚠️  Error checking port {port}: {e}")


def start_orchestrator_server(debug: bool = False):
    """Start the orchestrator server in the background."""
    global ORCHESTRATOR_PROCESS
    
    # Kill any existing process on port 8080
    if debug:
        print("🔍 Checking for existing orchestrator on port 8080...")
    kill_process_on_port(8080, debug=debug)
    
    # Give it a moment to clean up
    time.sleep(1)
    
    # Start the orchestrator
    if debug:
        print("🚀 Starting orchestrator server...")
    orchestrator_path = Path(__file__).parent / "orchestrator" / "orchestrator_agent.py"
    
    try:
        # Set debug environment variable if needed
        env = os.environ.copy()
        if debug:
            env['ORCHESTRATOR_DEBUG'] = '1'
        
        # Start orchestrator in background
        ORCHESTRATOR_PROCESS = subprocess.Popen(
            [sys.executable, str(orchestrator_path)],
            stdout=subprocess.PIPE if not debug else None,
            stderr=subprocess.PIPE if not debug else None,
            text=True,
            env=env
        )
        
        # Wait a bit for it to start
        time.sleep(3)
        
        # Check if it's running
        if ORCHESTRATOR_PROCESS.poll() is None:
            if debug:
                print("✅ Orchestrator server started successfully on port 8080")
            return True
        else:
            print("❌ Orchestrator server failed to start")
            if debug:
                stdout, stderr = ORCHESTRATOR_PROCESS.communicate(timeout=1)
                if stderr:
                    print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start orchestrator: {e}")
        return False


def cleanup_orchestrator():
    """Clean up orchestrator process on exit."""
    global ORCHESTRATOR_PROCESS, DEBUG_MODE
    if ORCHESTRATOR_PROCESS and ORCHESTRATOR_PROCESS.poll() is None:
        if DEBUG_MODE:
            print("\n🛑 Stopping orchestrator server...")
        ORCHESTRATOR_PROCESS.terminate()
        try:
            ORCHESTRATOR_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ORCHESTRATOR_PROCESS.kill()
        if DEBUG_MODE:
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
        self.debug_mode = DEBUG_MODE
        
    def ensure_orchestrator_running(self):
        """Ensure the orchestrator server is running."""
        if not self.orchestrator_started:
            if start_orchestrator_server(debug=self.debug_mode):
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
        
        # Handle individual workflow all-steps mode
        if workflow_type == "individual" and config and config.get('run_all_steps'):
            await self._execute_individual_all_steps(requirements, config)
            return
        
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
        
        # Create tracer for monitoring with auto-save
        global _current_tracer
        report_dir = Path("workflow_reports")
        report_dir.mkdir(exist_ok=True)
        auto_save_path = report_dir / "execution_report.json"
        tracer = WorkflowExecutionTracer(workflow_type, auto_save_path=str(auto_save_path))
        _current_tracer = tracer
        
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
            
            # Clear global tracer
            _current_tracer = None
            
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
    
    async def _execute_individual_all_steps(self, requirements: str, config: Dict[str, Any]):
        """Execute all individual workflow steps sequentially."""
        steps = ["planning", "design", "test_writing", "implementation", "review", "execution"]
        overall_start = time.time()
        results_by_step = {}
        
        # Import session utilities
        from agents.executor.session_utils import generate_session_id
        
        # Generate a single session ID for all steps
        session_id = generate_session_id(requirements)
        generated_code_path = None
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Individual Workflow - All Steps Mode")
        print(f"📋 Requirements: {requirements[:100]}..." if len(requirements) > 100 else f"📋 Requirements: {requirements}")
        print(f"📝 Steps to execute: {', '.join(steps)}")
        print(f"🔑 Session ID: {session_id}")
        print(f"{'='*60}\n")
        
        for i, step in enumerate(steps, 1):
            print(f"\n{'='*50}")
            print(f"📍 Step {i}/{len(steps)}: {step.upper()}")
            print(f"{'='*50}")
            
            # Prepare requirements with session ID and generated code path
            step_requirements = f"SESSION_ID: {session_id}\n"
            if generated_code_path and step in ["execution", "review"]:
                step_requirements += f"GENERATED_CODE_PATH: {generated_code_path}\n"
            step_requirements += f"\n{requirements}"
            
            # Create input data for this step
            input_data = CodingTeamInput(
                requirements=step_requirements,
                workflow_type="individual",
                step_type=step,
                # Skip Docker cleanup for all steps except the last one
                skip_docker_cleanup=(i < len(steps))
            )
            
            # Apply timeout if specified
            if config.get('timeout'):
                input_data.timeout = config['timeout']
            
            # Create tracer for this step with auto-save
            report_dir = Path("workflow_reports")
            report_dir.mkdir(exist_ok=True)
            auto_save_path = report_dir / f"execution_report_{step}.json"
            tracer = WorkflowExecutionTracer(f"individual_{step}", auto_save_path=str(auto_save_path))
            
            try:
                step_start = time.time()
                
                # Execute the step
                results, report = await execute_workflow(input_data, tracer)
                
                step_duration = time.time() - step_start
                results_by_step[step] = {
                    "results": results,
                    "report": report,
                    "duration": step_duration
                }
                
                print(f"✅ {step} completed in {step_duration:.2f} seconds")
                
                # Show brief output preview
                if results and len(results) > 0:
                    output_preview = results[0].output[:200] + "..." if len(results[0].output) > 200 else results[0].output
                    print(f"📄 Output preview: {output_preview}")
                    
                    # Extract generated code path from implementation step
                    if step == "implementation" and not generated_code_path:
                        import re
                        # Look for generated path in the output
                        path_match = re.search(r'generated/[^\s]+', results[0].output)
                        if path_match:
                            generated_code_path = path_match.group(0)
                            print(f"📁 Captured generated code path: {generated_code_path}")
                
            except Exception as e:
                print(f"❌ {step} failed: {str(e)}")
                if not config.get('continue_on_error', False):
                    print(f"\n⛔ Stopping execution due to error in {step} step")
                    break
                results_by_step[step] = {
                    "error": str(e),
                    "duration": time.time() - step_start
                }
        
        # Summary
        overall_duration = time.time() - overall_start
        successful_steps = [s for s, r in results_by_step.items() if "error" not in r]
        failed_steps = [s for s, r in results_by_step.items() if "error" in r]
        
        print(f"\n{'='*60}")
        print(f"📊 Individual Workflow Summary")
        print(f"{'='*60}")
        print(f"Total Duration: {overall_duration:.2f} seconds")
        print(f"Steps Completed: {len(successful_steps)}/{len(steps)}")
        
        if successful_steps:
            print(f"✅ Successful: {', '.join(successful_steps)}")
        if failed_steps:
            print(f"❌ Failed: {', '.join(failed_steps)}")
        
        # Save consolidated report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("workflow_reports")
        report_dir.mkdir(exist_ok=True)
        
        consolidated_report = {
            "workflow_type": "individual_all_steps",
            "timestamp": timestamp,
            "requirements": requirements,
            "session_id": session_id,
            "generated_code_path": generated_code_path,
            "total_duration": overall_duration,
            "steps": results_by_step
        }
        
        report_file = report_dir / f"individual_all_steps_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(consolidated_report, f, indent=2, default=str)
        
        print(f"\n📊 Consolidated report saved to: {report_file}")
        
        # Final Docker cleanup message
        if successful_steps and "execution" in successful_steps:
            print(f"\n🧹 Docker containers for session {session_id} were cleaned up after final step")
                
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
        
        # Handle Individual workflow options
        if args.type == "individual":
            if args.step:
                config['step_type'] = args.step
                print(f"📌 Running individual workflow - {args.step} step only")
            elif args.all_steps:
                # We'll run all steps sequentially
                print("📌 Running individual workflow - all steps")
                config['run_all_steps'] = True
            
            if args.timeout:
                config['timeout'] = args.timeout
                
            if args.config:
                # Load configuration from file
                import yaml
                with open(args.config, 'r') as f:
                    custom_config = yaml.safe_load(f)
                    config.update(custom_config)
        
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
  python run.py --debug ...                     # Enable verbose debug logging
  python run.py --no-orchestrator ...           # Skip auto-start

🔧 Available Workflows:
  - individual: Execute individual workflow steps with enhanced features
  - tdd: Test-Driven Development (Tests → Implementation → Review)
  - full: Full development workflow (Planning → Design → Implementation → Review)
  - enhanced_full: Enhanced full workflow with retry, caching, monitoring & rollback
  - incremental: Feature-based incremental development
  - mvp_incremental: MVP incremental with validation
  - mvp_incremental_tdd: MVP incremental with TDD
  
📍 Individual Workflow Steps:
  - planning: Generate project plan and structure
  - design: Create detailed design and architecture
  - test_writing: Write comprehensive test suite
  - implementation: Implement the solution
  - review: Review and validate implementation
  - execution: Execute and validate the code

💡 Examples:
  python run.py workflow individual --task "Create REST API" --step planning
  python run.py workflow individual --task "Build calculator" --all-steps
  python run.py workflow individual --task "..." --timeout 600
  python run.py workflow tdd --task "Create a calculator API"
  python run.py workflow mvp_incremental --task "Build a task management system"
  python run.py workflow enhanced_full --task "Build Hello World API"
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

🐛 Debug Mode:
  Use --debug flag to enable verbose logging:
  - Shows detailed workflow execution steps
  - Displays HTTP requests and agent communications
  - Includes full error tracebacks
  - Helps troubleshoot issues
  
  Example: python run.py workflow tdd --task "..." --debug
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
  python run.py workflow enhanced_full --task "..." # Run enhanced full workflow
  python run.py workflow --list                 # List workflows
  python run.py --debug workflow tdd --task "..." # Run with debug logging
  
Individual Workflow Examples:
  python run.py workflow individual --task "Create API" --step planning
  python run.py workflow individual --task "Build app" --all-steps
  python run.py workflow individual --task "..." --step design --timeout 600
  python run.py workflow individual --task "..." --config custom.yaml
  
TDD Examples:
  python run.py workflow tdd --task "Calculator API" --strict
  python run.py workflow tdd --task "..." --coverage 90
  python run.py --debug workflow tdd --task "..." # Debug TDD workflow
  
Incremental Examples:
  python run.py workflow incremental --task "Task manager"
  python run.py workflow mvp_incremental --task "..." --show-progress
  
Enhanced Full Workflow:
  python run.py workflow enhanced_full --task "Hello World API"
  # Features: retry logic, caching, performance monitoring, rollback
  
Note: The orchestrator server will be started automatically on port 8080.
      Use --no-orchestrator if you're managing it manually.
      Use --debug to enable verbose logging for troubleshooting.
"""
    )
    
    # Global options
    parser.add_argument("--debug", action="store_true",
                       help="Enable verbose debug logging")
    parser.add_argument("--no-orchestrator", action="store_true",
                       help="Don't start the orchestrator server (assumes it's already running)")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run a workflow")
    workflow_parser.add_argument("type", nargs="?", help="Workflow type (e.g., tdd, full, incremental, individual)")
    workflow_parser.add_argument("--task", help="Task description")
    workflow_parser.add_argument("--list", action="store_true", help="List available workflows")
    
    # Individual workflow options
    workflow_parser.add_argument("--step", choices=["planning", "design", "test_writing", "implementation", "review", "execution"],
                                help="Run specific step for individual workflow")
    workflow_parser.add_argument("--all-steps", action="store_true",
                                help="Run all steps sequentially (individual workflow)")
    workflow_parser.add_argument("--timeout", type=int,
                                help="Override timeout in seconds")
    workflow_parser.add_argument("--config", help="Path to configuration file")
    
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
    global DEBUG_MODE
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging based on debug flag
    DEBUG_MODE = hasattr(args, 'debug') and args.debug
    configure_logging(debug=DEBUG_MODE)
    
    # Set environment variable to control debug in subprocesses
    import os
    os.environ['ORCHESTRATOR_DEBUG'] = 'true' if DEBUG_MODE else 'false'
    
    # Initialize core after logging is configured
    from core.initialize import initialize_core
    try:
        # Override debug setting in config
        os.environ['DEBUG'] = 'false'  # Always set to false to avoid config override
        initialize_core()
    except Exception as e:
        if DEBUG_MODE:
            print(f"Warning: Failed to initialize core infrastructure: {e}")
    
    # Create runner
    runner = DirectWorkflowRunner()
    
    # Store debug mode in runner for later use
    runner.debug_mode = DEBUG_MODE
    
    # Handle --no-orchestrator flag
    if hasattr(args, 'no_orchestrator') and args.no_orchestrator:
        runner.orchestrator_started = True  # Skip auto-start
        if DEBUG_MODE:
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
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())