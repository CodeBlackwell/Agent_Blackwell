#!/usr/bin/env python3
"""
🚀 Unified Runner for Multi-Agent Coding System

This is the main entry point for all demos, examples, workflows, and tests.
It provides both interactive and command-line interfaces for easy access to
all system functionality.

Usage:
    python run.py                    # Interactive mode
    python run.py example calculator # Run an example
    python run.py workflow tdd       # Run a workflow
    python run.py test unit          # Run tests
    python run.py --help            # Get help
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import helper modules
from demos.lib.config_loader import ConfigLoader
from demos.lib.interactive_menu import InteractiveMenu
from demos.lib.workflow_runner import WorkflowRunner
from demos.lib.preflight_checker import PreflightChecker
from demos.lib.output_formatter import OutputFormatter


class UnifiedRunner:
    """Main runner that combines all functionality."""
    
    def __init__(self):
        self.menu = InteractiveMenu()
        self.config_loader = ConfigLoader()
        self.workflow_runner = WorkflowRunner()
        self.preflight_checker = PreflightChecker()
        self.output_formatter = OutputFormatter()
        
    async def run_interactive(self):
        """Run in interactive mode with menus."""
        self.menu.print_banner(
            "🚀 MULTI-AGENT CODING SYSTEM",
            "Unified Runner - Interactive Mode"
        )
        
        # Run preflight checks
        if not self._run_preflight_checks(skip_optional=True):
            if not self.menu.get_yes_no("Continue anyway?", default=False):
                return
                
        while True:
            # Main menu
            options = [
                ("1", "Run an Example Project"),
                ("2", "Run a Workflow"),
                ("3", "Run Tests"),
                ("4", "API Demos"),
                ("5", "Advanced Options"),
                ("6", "Help & Documentation")
            ]
            
            choice = self.menu.show_menu("Main Menu", options)
            
            if choice == "0":  # Exit
                print("\n👋 Thanks for using the Multi-Agent Coding System!")
                break
            elif choice == "1":
                await self._interactive_example()
            elif choice == "2":
                await self._interactive_workflow()
            elif choice == "3":
                await self._interactive_tests()
            elif choice == "4":
                await self._interactive_api()
            elif choice == "5":
                await self._interactive_advanced()
            elif choice == "6":
                self._show_help()
                
    async def _interactive_example(self):
        """Interactive example selection and execution."""
        examples = self.config_loader.list_examples()
        
        if not examples:
            self.menu.show_error(
                "No examples found in demos/examples/",
                ["Create YAML files in demos/examples/", "Check the examples directory"]
            )
            return
            
        # Show available examples
        self.menu.print_section("Available Examples")
        example_infos = []
        
        for i, name in enumerate(examples, 1):
            info = self.config_loader.get_example_info(name)
            if info:
                print(f"  {i}. {info['name']} ({name})")
                print(f"     {info['description']}")
                print(f"     Difficulty: {info['difficulty']} | Time: {info['time_estimate']}")
                example_infos.append((name, info))
                
        # Get selection
        choice = self.menu.get_text_input(
            "\nSelect example number (or 0 to cancel)",
            required=True
        )
        
        try:
            idx = int(choice) - 1
            if idx == -1:  # Cancel
                return
            if 0 <= idx < len(examples):
                example_name = examples[idx]
                await self._run_example(example_name)
            else:
                self.menu.show_error("Invalid selection")
        except ValueError:
            self.menu.show_error("Please enter a number")
            
    async def _run_example(self, example_name: str):
        """Run a specific example."""
        # Load example configuration
        config = self.config_loader.load_example(example_name)
        if not config:
            self.menu.show_error(f"Could not load example: {example_name}")
            return
            
        # Show example details
        self.menu.print_section(f"Running Example: {config.name}")
        print(f"Requirements preview:")
        print("-" * 60)
        print(config.requirements[:200] + "..." if len(config.requirements) > 200 else config.requirements)
        print("-" * 60)
        
        # Configuration options
        run_config = config.config.copy()
        
        if self.menu.get_yes_no("\nCustomize configuration?", default=False):
            run_config['run_tests'] = self.menu.get_yes_no(
                "Enable test execution?",
                default=run_config.get('run_tests', False)
            )
            run_config['run_integration_verification'] = self.menu.get_yes_no(
                "Enable integration verification?",
                default=run_config.get('run_integration_verification', False)
            )
            
        # Confirm execution
        if not self.menu.confirm_action(
            f"Run {config.name} example",
            [
                f"Workflow: {run_config.get('workflow_type', 'tdd')}",
                f"Tests: {'Yes' if run_config.get('run_tests') else 'No'}",
                f"Integration: {'Yes' if run_config.get('run_integration_verification') else 'No'}",
                f"Estimated time: {config.time_estimate}"
            ]
        ):
            return
            
        # Run the workflow
        await self._execute_workflow(
            config.requirements,
            run_config.get('workflow_type', 'tdd'),
            run_config
        )
        
    async def _interactive_workflow(self):
        """Interactive workflow execution."""
        # List available workflows
        workflows = self.workflow_runner.list_workflows()
        
        self.menu.print_section("Available Workflows")
        for i, (key, name, desc) in enumerate(workflows, 1):
            print(f"  {i}. {name} ({key})")
            print(f"     {desc}")
            
        # Get selection
        choice = self.menu.get_text_input(
            "\nSelect workflow number (or 0 to cancel)",
            required=True
        )
        
        try:
            idx = int(choice) - 1
            if idx == -1:  # Cancel
                return
            if 0 <= idx < len(workflows):
                workflow_type = workflows[idx][0]
                
                # Get requirements
                print("\nEnter your requirements:")
                requirements = self.menu.get_multiline_input(
                    "Describe what you want to build:"
                )
                
                if not requirements.strip():
                    self.menu.show_error("Requirements cannot be empty")
                    return
                    
                # Run workflow
                await self._execute_workflow(requirements, workflow_type)
            else:
                self.menu.show_error("Invalid selection")
        except ValueError:
            self.menu.show_error("Please enter a number")
            
    async def _execute_workflow(self, requirements: str, workflow_type: str, 
                              config: Optional[Dict[str, Any]] = None):
        """Execute a workflow with progress tracking."""
        start_time = time.time()
        
        # Start message
        print(self.output_formatter.format_workflow_start(workflow_type, requirements))
        
        # Run workflow
        success, result = await self.workflow_runner.run_workflow(
            requirements,
            workflow_type,
            config
        )
        
        duration = time.time() - start_time
        
        # Show results
        if success:
            print(self.output_formatter.format_workflow_complete(
                True,
                duration,
                result.get('session_id'),
                result.get('generated_path')
            ))
            
            # Show next steps
            self.menu.print_section("Next Steps")
            print("1. Navigate to the generated code directory")
            print("2. Review the generated files")
            print("3. Install any dependencies")
            print("4. Run the application or tests")
            
            if result.get('generated_path'):
                print(f"\ncd {result['generated_path']}")
                
        else:
            print(self.output_formatter.format_error(
                result.get('error', 'Unknown error'),
                result.get('error_type'),
                result.get('traceback')
            ))
            
    async def _interactive_tests(self):
        """Interactive test runner."""
        # Import test runner functionality
        from test_runner import TEST_CATEGORIES, TestRunner
        
        self.menu.print_section("Test Runner")
        
        # Show test categories
        print("Available test categories:")
        for i, (key, info) in enumerate(TEST_CATEGORIES.items(), 1):
            print(f"  {i}. {info['emoji']} {info['name']} ({key})")
            print(f"     {info['description']}")
            
        # Get selection
        choice = self.menu.get_text_input(
            "\nSelect test category (or 'all' for all tests, 0 to cancel)",
            required=True
        )
        
        if choice == "0":
            return
        elif choice.lower() == "all":
            categories = list(TEST_CATEGORIES.keys())
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(TEST_CATEGORIES):
                    categories = [list(TEST_CATEGORIES.keys())[idx]]
                else:
                    self.menu.show_error("Invalid selection")
                    return
            except ValueError:
                # Try as category name
                if choice in TEST_CATEGORIES:
                    categories = [choice]
                else:
                    self.menu.show_error("Invalid category")
                    return
                    
        # Run tests
        runner = TestRunner(verbose=True)
        
        parallel = self.menu.get_yes_no("Run tests in parallel?", default=False)
        
        print(f"\nRunning tests: {', '.join(categories)}")
        results = runner.run_categories(categories, parallel=parallel)
        
        # Show summary
        runner.print_summary(results)
        
    async def _interactive_api(self):
        """Interactive API demos."""
        self.menu.print_section("API Demos")
        
        options = [
            ("1", "Check API Server Status"),
            ("2", "Run Simple API Demo"),
            ("3", "Submit Workflow via API"),
            ("4", "Monitor Workflow Status")
        ]
        
        choice = self.menu.show_menu("API Options", options)
        
        if choice == "1":
            await self._check_api_status()
        elif choice == "2":
            await self._run_api_demo()
        elif choice == "3":
            await self._api_submit_workflow()
        elif choice == "4":
            await self._api_monitor_workflow()
            
    async def _check_api_status(self):
        """Check if API server is running."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    self.menu.show_status("API server is running", "success")
                else:
                    self.menu.show_status(f"API returned status {response.status_code}", "warning")
        except Exception as e:
            self.menu.show_error(
                "API server not reachable",
                ["Start the API server with: python api/orchestrator_api.py"]
            )
            
    async def _run_api_demo(self):
        """Run the API demo script."""
        script_path = Path("api/demo_api_usage.py")
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)])
        else:
            self.menu.show_error("API demo script not found")
            
    async def _interactive_advanced(self):
        """Advanced options menu."""
        options = [
            ("1", "Run MVP Incremental Demo"),
            ("2", "Run Specific Agent Test"),
            ("3", "System Diagnostics"),
            ("4", "Export Configuration")
        ]
        
        choice = self.menu.show_menu("Advanced Options", options)
        
        if choice == "1":
            # Run the comprehensive MVP demo
            script_path = Path("demos/advanced/mvp_incremental_demo.py")
            if not script_path.exists():
                # Try the legacy location
                script_path = Path("demo_mvp_incremental.py")
                
            if script_path.exists():
                subprocess.run([sys.executable, str(script_path)])
            else:
                self.menu.show_error("MVP Incremental demo not found")
                
        elif choice == "2":
            await self._run_agent_test()
        elif choice == "3":
            self._run_diagnostics()
        elif choice == "4":
            self._export_configuration()
            
    def _run_diagnostics(self):
        """Run comprehensive system diagnostics."""
        results = self.preflight_checker.run_all_checks(skip_optional=False)
        self.preflight_checker.print_results(results)
        
        # Save report
        report_path = self.output_formatter.save_json_report({
            "timestamp": datetime.now().isoformat(),
            "diagnostics": results
        })
        print(f"\nDiagnostics report saved to: {report_path}")
        
    def _show_help(self):
        """Show help and documentation."""
        help_text = """
📚 HELP & DOCUMENTATION

🎯 Quick Start Guide:
1. Run 'python run.py' for interactive mode
2. Choose "Run an Example Project" for pre-configured examples
3. Start with the "calculator" example if you're new

📋 Command Line Usage:
  python run.py example <name>              # Run an example
  python run.py workflow <type> --task "..." # Run a workflow
  python run.py test <category>             # Run tests
  python run.py --help                      # Show CLI help

🔧 Available Workflows:
  - tdd: Test-Driven Development
  - full: Full development workflow
  - mvp_incremental: Build incrementally
  - planning: Planning only
  - design: Design only
  - implementation: Code only

📁 Project Structure:
  demos/
    examples/     # Example configurations
    lib/          # Helper modules
    legacy/       # Old demo scripts
    advanced/     # Advanced demos
  generated/      # Generated code output
  logs/           # Execution logs

🌐 Resources:
  - Documentation: docs/
  - Examples: demos/examples/
  - Tests: tests/

💡 Tips:
  - Enable verbose mode with -v for detailed output
  - Use --dry-run to preview without executing
  - Check logs in demo_outputs/logs/ for debugging
"""
        print(help_text)
        self.menu.wait_for_enter()
        
    def _run_preflight_checks(self, skip_optional: bool = True) -> bool:
        """Run preflight checks and return status."""
        results = self.preflight_checker.run_all_checks(skip_optional)
        self.preflight_checker.print_results(results)
        return results['all_passed']
        
    async def run_cli(self, args):
        """Run in CLI mode based on parsed arguments."""
        # Set output formatter mode
        if args.short:
            self.output_formatter = OutputFormatter(mode="short")
        elif args.verbose:
            self.output_formatter = OutputFormatter(mode="verbose")
            
        # Handle different commands
        if args.command == "example":
            await self._cli_example(args)
        elif args.command == "workflow":
            await self._cli_workflow(args)
        elif args.command == "test":
            await self._cli_test(args)
        elif args.command == "api":
            await self._cli_api(args)
        elif args.command == "list":
            self._cli_list(args)
        else:
            # No command specified, run interactive
            await self.run_interactive()
            
    async def _cli_example(self, args):
        """Handle CLI example command."""
        if args.list:
            # List examples
            examples = self.config_loader.list_examples()
            print("Available examples:")
            for name in examples:
                info = self.config_loader.get_example_info(name)
                if info:
                    print(f"  {name:<15} - {info['description']}")
            return
            
        if not args.name:
            print("Error: Example name required")
            print("Use 'run.py example --list' to see available examples")
            return
            
        # Load and run example
        config = self.config_loader.load_example(args.name)
        if not config:
            print(f"Error: Example '{args.name}' not found")
            return
            
        # Apply CLI overrides
        run_config = config.config.copy()
        if args.all_phases:
            run_config['run_tests'] = True
            run_config['run_integration_verification'] = True
        elif args.tests is not None:
            run_config['run_tests'] = args.tests
            
        # Run
        if not args.dry_run:
            await self._execute_workflow(
                config.requirements,
                run_config.get('workflow_type', 'tdd'),
                run_config
            )
        else:
            print(f"Would run example: {config.name}")
            print(f"Workflow: {run_config.get('workflow_type', 'tdd')}")
            print(f"Tests: {run_config.get('run_tests', False)}")
            print(f"Integration: {run_config.get('run_integration_verification', False)}")
            
    async def _cli_workflow(self, args):
        """Handle CLI workflow command."""
        if args.list:
            # List workflows
            workflows = self.workflow_runner.list_workflows()
            print("Available workflows:")
            for key, name, desc in workflows:
                print(f"  {key:<20} - {desc}")
            return
            
        if not args.type:
            print("Error: Workflow type required")
            print("Use 'run.py workflow --list' to see available workflows")
            return
            
        if not args.task and not args.requirements_file:
            print("Error: Task description required (--task or --requirements-file)")
            return
            
        # Get requirements
        if args.requirements_file:
            try:
                with open(args.requirements_file, 'r') as f:
                    requirements = f.read()
            except Exception as e:
                print(f"Error reading requirements file: {e}")
                return
        else:
            requirements = args.task
            
        # Run workflow
        if not args.dry_run:
            config = {}
            if args.all_phases:
                config['run_tests'] = True
                config['run_integration_verification'] = True
                
            await self._execute_workflow(requirements, args.type, config)
        else:
            print(f"Would run workflow: {args.type}")
            print(f"Requirements: {requirements[:100]}...")
            
    async def _cli_test(self, args):
        """Handle CLI test command."""
        from test_runner import TestRunner, TEST_CATEGORIES
        
        if args.list:
            print("Available test categories:")
            for key, info in TEST_CATEGORIES.items():
                print(f"  {key:<15} - {info['description']}")
            return
            
        # Determine categories
        if not args.categories:
            categories = ['all']
        else:
            categories = args.categories
            
        if 'all' in categories:
            categories = list(TEST_CATEGORIES.keys())
            
        # Run tests
        runner = TestRunner(verbose=args.verbose, ci_mode=args.ci)
        
        if not args.dry_run:
            results = runner.run_categories(categories, parallel=args.parallel)
            runner.print_summary(results)
            
            # Exit with appropriate code
            all_passed = all(r['status'] == 'passed' for r in results.values())
            sys.exit(0 if all_passed else 1)
        else:
            print(f"Would run tests: {', '.join(categories)}")
            print(f"Parallel: {args.parallel}")
            
    def _cli_list(self, args):
        """Handle list command."""
        if args.what == "examples":
            examples = self.config_loader.list_examples()
            print("Available examples:")
            for name in examples:
                info = self.config_loader.get_example_info(name)
                if info:
                    print(f"  {name:<15} - {info['description']}")
                    
        elif args.what == "workflows":
            workflows = self.workflow_runner.list_workflows()
            print("Available workflows:")
            for key, name, desc in workflows:
                print(f"  {key:<20} - {desc}")
                
        elif args.what == "tests":
            from test_runner import TEST_CATEGORIES
            print("Available test categories:")
            for key, info in TEST_CATEGORIES.items():
                print(f"  {key:<15} - {info['description']}")
                
    async def _cli_api(self, args):
        """Handle API commands."""
        if args.action == "demo":
            await self._run_api_demo()
        elif args.action == "status":
            await self._check_api_status()


def create_parser():
    """Create argument parser for CLI mode."""
    parser = argparse.ArgumentParser(
        description="Unified runner for Multi-Agent Coding System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                           # Interactive mode
  python run.py example calculator        # Run calculator example
  python run.py workflow tdd --task "..." # Run TDD workflow
  python run.py test unit integration     # Run specific tests
  python run.py list examples             # List available examples
"""
    )
    
    # Global options
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("-s", "--short", action="store_true",
                       help="Enable short output mode")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview actions without executing")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Example command
    example_parser = subparsers.add_parser("example", help="Run an example project")
    example_parser.add_argument("name", nargs="?", help="Example name")
    example_parser.add_argument("--list", action="store_true",
                               help="List available examples")
    example_parser.add_argument("--all-phases", action="store_true",
                               help="Enable all optional phases")
    example_parser.add_argument("--tests", action="store_true",
                               help="Enable test execution")
    example_parser.add_argument("--no-tests", dest="tests", action="store_false",
                               help="Disable test execution")
    
    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run a workflow")
    workflow_parser.add_argument("type", nargs="?", help="Workflow type")
    workflow_parser.add_argument("--task", help="Task description")
    workflow_parser.add_argument("--requirements-file", help="File with requirements")
    workflow_parser.add_argument("--list", action="store_true",
                                help="List available workflows")
    workflow_parser.add_argument("--all-phases", action="store_true",
                                help="Enable all optional phases")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("categories", nargs="*", help="Test categories to run")
    test_parser.add_argument("--list", action="store_true",
                            help="List available test categories")
    test_parser.add_argument("-p", "--parallel", action="store_true",
                            help="Run tests in parallel")
    test_parser.add_argument("--ci", action="store_true",
                            help="CI mode (no emojis)")
    
    # API command
    api_parser = subparsers.add_parser("api", help="API operations")
    api_parser.add_argument("action", choices=["demo", "status"],
                           help="API action to perform")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available options")
    list_parser.add_argument("what", choices=["examples", "workflows", "tests"],
                            help="What to list")
    
    return parser


async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    runner = UnifiedRunner()
    
    try:
        await runner.run_cli(args)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"\n❌ Error: {e}")
            print("Use -v for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())