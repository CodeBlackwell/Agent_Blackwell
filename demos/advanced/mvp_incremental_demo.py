#!/usr/bin/env python3
"""
🚀 Interactive Demo for MVP Incremental Workflow
===============================================

This beginner-friendly demo helps you explore and test the MVP Incremental Workflow,
a sophisticated AI-powered system that builds software step-by-step with validation
and testing at each phase.

What is the MVP Incremental Workflow?
------------------------------------
It's a 10-phase process where specialized AI agents work together to:
1. Understand your requirements
2. Create a detailed plan
3. Design the architecture
4. Build features one by one
5. Write and run tests
6. Review and improve code
7. Ensure everything works together

Usage Examples:
--------------
    # 🎯 Interactive mode (RECOMMENDED for beginners)
    python demo_mvp_incremental.py
    
    # 🏃 Quick start with a preset example
    python demo_mvp_incremental.py --preset calculator
    
    # 💡 Custom requirements
    python demo_mvp_incremental.py --requirements "Create a REST API for managing tasks"
    
    # 🔧 Advanced: Enable all phases
    python demo_mvp_incremental.py --preset todo-api --all-phases
    
    # 📚 Get detailed help
    python demo_mvp_incremental.py --help
"""

import asyncio
import argparse
import sys
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import json
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from shared.data_models import CodingTeamInput
    from workflows.workflow_manager import execute_workflow
    from workflows.monitoring import WorkflowExecutionTracer
except ImportError as e:
    print("\n❌ ERROR: Missing required modules!")
    print(f"   Details: {e}")
    print("\n📋 Please ensure you've installed all dependencies:")
    print("   1. Activate your virtual environment: source .venv/bin/activate")
    print("   2. Install requirements: uv pip install -r requirements.txt")
    sys.exit(1)


# Pre-configured examples with detailed information
EXAMPLES = {
    "calculator": {
        "name": "📱 Simple Calculator",
        "difficulty": "Beginner",
        "time_estimate": "2-3 minutes",
        "description": "A basic Python calculator module with mathematical operations",
        "detailed_description": """This example creates a simple calculator that can:
        • Add, subtract, multiply, and divide numbers
        • Calculate square roots
        • Handle edge cases like division by zero
        • Include comprehensive unit tests
        
        Perfect for beginners to see the workflow in action!""",
        "requirements": """Create a Python calculator module with the following features:
1. Add two numbers
2. Subtract two numbers
3. Multiply two numbers
4. Divide two numbers (handle division by zero)
5. Calculate square root
6. Include unit tests for all operations""",
        "config": {
            "run_tests": True,
            "run_integration_verification": False
        },
        "expected_files": ["calculator.py", "test_calculator.py"]
    },
    "todo-api": {
        "name": "📝 TODO REST API",
        "difficulty": "Intermediate",
        "time_estimate": "5-7 minutes",
        "description": "A RESTful API for managing TODO items using FastAPI",
        "detailed_description": """This example builds a complete REST API including:
        • Full CRUD operations (Create, Read, Update, Delete)
        • Data validation and error handling
        • Pagination for listing items
        • Auto-generated API documentation
        • Comprehensive test suite
        
        Great for learning API development patterns!""",
        "requirements": """Create a REST API for managing TODO items using FastAPI:
1. Create a TODO item (title, description, completed status)
2. List all TODO items with pagination
3. Get a specific TODO by ID
4. Update a TODO item
5. Delete a TODO item
6. Add input validation
7. Include API documentation
8. Write tests for all endpoints""",
        "config": {
            "run_tests": True,
            "run_integration_verification": True
        },
        "expected_files": ["main.py", "models.py", "test_api.py", "requirements.txt"]
    },
    "auth-system": {
        "name": "🔐 User Authentication System",
        "difficulty": "Advanced",
        "time_estimate": "10-15 minutes",
        "description": "A complete authentication system with JWT tokens and role-based access",
        "detailed_description": """This example implements a production-ready auth system:
        • User registration and login
        • Secure password hashing (bcrypt)
        • JWT token generation and validation
        • Email verification flow
        • Password reset functionality
        • Role-based access control (RBAC)
        • Security best practices
        
        Ideal for understanding security implementations!""",
        "requirements": """Create a user authentication system with:
1. User registration with email and password
2. Password hashing using bcrypt
3. User login with JWT token generation
4. Token validation middleware
5. Password reset functionality
6. Email verification
7. User profile management
8. Role-based access control (admin, user)
9. Include comprehensive tests
10. Add security best practices""",
        "config": {
            "run_tests": True,
            "run_integration_verification": True
        },
        "expected_files": ["auth.py", "models.py", "middleware.py", "utils.py", "test_auth.py"]
    },
    "file-processor": {
        "name": "📊 CSV File Processor",
        "difficulty": "Intermediate",
        "time_estimate": "5-8 minutes",
        "description": "A tool for processing and analyzing CSV files with streaming support",
        "detailed_description": """This example creates a versatile CSV processor that:
        • Reads files with configurable delimiters
        • Validates data types in columns
        • Handles missing values gracefully
        • Filters data based on conditions
        • Performs aggregations (sum, average, count)
        • Exports to JSON or CSV
        • Supports large files via streaming
        
        Perfect for data processing workflows!""",
        "requirements": """Create a CSV file processing tool that:
1. Read CSV files with configurable delimiter
2. Validate data types in columns
3. Handle missing values
4. Filter rows based on conditions
5. Aggregate data (sum, average, count)
6. Export results to JSON or new CSV
7. Support large files with streaming
8. Include error handling and logging""",
        "config": {
            "run_tests": False,
            "run_integration_verification": True
        },
        "expected_files": ["csv_processor.py", "validators.py", "exporters.py", "test_processor.py"]
    }
}


class ConsoleLogger:
    """Captures and logs console output to file while displaying it."""
    
    def __init__(self, log_file_path: Path):
        self.log_file_path = log_file_path
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.log_file = None
        
    def __enter__(self):
        """Start capturing console output."""
        # Ensure directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open log file
        self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
        
        # Create a custom stream that writes to both console and file
        self.tee_stdout = TeeStream(self.original_stdout, self.log_file)
        self.tee_stderr = TeeStream(self.original_stderr, self.log_file)
        
        # Redirect stdout and stderr
        sys.stdout = self.tee_stdout
        sys.stderr = self.tee_stderr
        
        # Write header
        print(f"{'='*80}")
        print(f"MVP Incremental Demo Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing and restore original streams."""
        # Write footer
        print(f"\n{'='*80}")
        print(f"Log ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Restore original streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # Close log file
        if self.log_file:
            self.log_file.close()


class TeeStream:
    """Stream that writes to multiple destinations."""
    
    def __init__(self, *streams):
        self.streams = streams
        
    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()
            
    def flush(self):
        for stream in self.streams:
            stream.flush()
            
    def fileno(self):
        # Return the fileno of the first stream (usually stdout)
        return self.streams[0].fileno()
    
    def isatty(self):
        # Return True if the first stream is a tty
        return hasattr(self.streams[0], 'isatty') and self.streams[0].isatty()


class PreflightChecker:
    """Performs system checks before running the workflow."""
    
    @staticmethod
    def check_python_version() -> Tuple[bool, str]:
        """Check if Python version meets requirements."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            return False, f"Python 3.8+ required (you have {version.major}.{version.minor}.{version.micro})"
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    
    @staticmethod
    def check_virtual_env() -> Tuple[bool, str]:
        """Check if running in a virtual environment."""
        # Check multiple ways to detect virtual environment
        in_venv = (
            # Standard venv/virtualenv check
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            # Check for VIRTUAL_ENV environment variable
            os.environ.get('VIRTUAL_ENV') is not None or
            # Check if we're in a .venv directory
            '.venv' in sys.executable or
            'venv' in sys.executable
        )
        
        if not in_venv:
            return False, "Not in virtual environment"
        
        # Try to get the venv name/path
        venv_path = os.environ.get('VIRTUAL_ENV', '')
        if venv_path:
            venv_name = os.path.basename(venv_path)
            return True, f"✓ Virtual environment active ({venv_name})"
        return True, "✓ Virtual environment active"
    
    @staticmethod
    def check_dependencies() -> Tuple[bool, str]:
        """Check if required dependencies are installed."""
        required = ['pydantic', 'requests', 'fastapi', 'uvicorn']
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            return False, f"Missing packages: {', '.join(missing)}"
        return True, "✓ All dependencies installed"
    
    @staticmethod
    def check_orchestrator_server() -> Tuple[bool, str]:
        """Check if orchestrator server is running on port 8080."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            if result == 0:
                return True, "✓ Orchestrator server is running"
            else:
                return False, "Orchestrator server not running on port 8080"
        except Exception:
            return False, "Cannot check orchestrator server status"
    
    @staticmethod
    def run_all_checks() -> bool:
        """Run all preflight checks and display results."""
        print("\n🔍 Running Preflight Checks...")
        print("=" * 60)
        
        checks = [
            ("Python Version", PreflightChecker.check_python_version),
            ("Virtual Environment", PreflightChecker.check_virtual_env),
            ("Dependencies", PreflightChecker.check_dependencies),
            ("Orchestrator Server", PreflightChecker.check_orchestrator_server),
        ]
        
        all_passed = True
        for name, check_func in checks:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {name:.<40} {message}")
            if not passed:
                all_passed = False
        
        print("=" * 60)
        
        if not all_passed:
            print("\n⚠️  Some checks failed! Here's how to fix them:\n")
            
            _, venv_msg = PreflightChecker.check_virtual_env()
            if "Not in virtual environment" in venv_msg:
                print("📌 To activate virtual environment:")
                print("   uv venv")
                print("   source .venv/bin/activate")
                print()
            
            _, deps_msg = PreflightChecker.check_dependencies()
            if "Missing packages" in deps_msg:
                print("📌 To install dependencies:")
                print("   uv pip install -r requirements.txt")
                print()
            
            _, server_msg = PreflightChecker.check_orchestrator_server()
            if "not running" in server_msg:
                print("📌 To start the orchestrator server:")
                print("   python orchestrator/orchestrator_agent.py")
                print("   (Run this in a separate terminal)")
                print()
            
            return False
        
        print("\n✅ All checks passed! Ready to proceed.\n")
        return True


class MVPIncrementalDemo:
    """Interactive demo for MVP Incremental workflow."""
    
    def __init__(self):
        self.selected_example = None
        self.custom_requirements = None
        self.config = {
            "run_tests": False,
            "run_integration_verification": False
        }
        self.tutorial_mode = False
        self.verbose_mode = False
        self.short_mode = False
        
    def print_banner(self):
        """Print welcome banner with detailed information."""
        print("\n" + "🌟" * 35)
        print("🚀 Welcome to the MVP Incremental Workflow Demo! 🚀".center(70))
        print("🌟" * 35)
        print("\nThis demo helps you create production-ready code using AI agents.")
        print("Our specialized team of agents will work together to understand")
        print("your requirements and build your application step by step.")
        print("\n🤖 Meet the Team:")
        print("   • Planner Agent - Breaks down your requirements")
        print("   • Designer Agent - Creates the architecture")
        print("   • Coder Agent - Implements each feature")
        print("   • Test Writer Agent - Creates comprehensive tests")
        print("   • Reviewer Agent - Ensures code quality")
        print("   • Executor Agent - Runs and validates the code")
        
    def print_workflow_phases(self):
        """Display information about the 10 workflow phases."""
        print("\n📋 The 10-Phase MVP Incremental Workflow:")
        print("=" * 60)
        phases = [
            ("1. Planning", "Analyze requirements and create a project plan"),
            ("2. Design", "Create architecture and database schemas"),
            ("3. Feature Parsing", "Break down into implementable features"),
            ("4. Implementation", "Build features one by one"),
            ("5. Validation", "Check each feature works correctly"),
            ("6. Error Analysis", "Fix any issues that arise"),
            ("7. Progress Tracking", "Monitor the development progress"),
            ("8. Review", "Ensure code quality and best practices"),
            ("9. Test Execution", "Run all tests (optional)"),
            ("10. Integration", "Verify everything works together (optional)")
        ]
        
        for phase, desc in phases:
            print(f"  {phase:<20} {desc}")
        print("=" * 60)
        
    def print_examples(self):
        """Display available examples with detailed information."""
        print("\n📚 Available Examples:")
        print("=" * 70)
        
        for key, example in EXAMPLES.items():
            print(f"\n🔹 {key} - {example['name']}")
            print(f"   Difficulty: {example['difficulty']} | Time: {example['time_estimate']}")
            print(f"   {example['description']}")
            
        print("\n💡 Tip: Start with 'calculator' if you're new to the system!")
        print("=" * 70)
        
    def show_example_details(self, example_key: str):
        """Show detailed information about a specific example."""
        example = EXAMPLES[example_key]
        print(f"\n📋 Detailed Information: {example['name']}")
        print("=" * 60)
        print(example['detailed_description'])
        print(f"\n📁 Expected output files:")
        for file in example['expected_files']:
            print(f"   • {file}")
        print("=" * 60)
        
    def get_user_choice(self) -> str:
        """Get user's choice for example or custom."""
        print("\n🎯 How would you like to proceed?")
        print("  1. 📚 Use a pre-configured example (recommended)")
        print("  2. ✏️  Enter custom requirements")
        print("  3. 🎓 Start tutorial mode (for beginners)")
        print("  4. ❓ Learn more about the workflow")
        print("  5. 🚪 Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print("❌ Invalid choice. Please enter a number between 1 and 5.")
            
    def select_example(self) -> Optional[str]:
        """Let user select an example with detailed information."""
        self.print_examples()
        
        while True:
            print("\n💡 Type an example name to see more details, or choose one to use.")
            choice = input("Enter example name (or 'back' to return): ").strip().lower()
            
            if choice == 'back':
                return None
                
            if choice in EXAMPLES:
                self.show_example_details(choice)
                use_it = input("\n➡️  Use this example? (Y/n): ").strip().lower()
                if use_it != 'n':
                    return choice
            else:
                print(f"❌ Invalid example. Choose from: {', '.join(EXAMPLES.keys())}")
                
    def get_custom_requirements(self) -> str:
        """Get custom requirements from user with guidance."""
        print("\n✏️  Custom Requirements Input")
        print("=" * 60)
        print("📝 Tips for writing good requirements:")
        print("   • Be specific about what you want")
        print("   • List features as numbered items")
        print("   • Include technical details if needed")
        print("   • Mention any specific libraries or frameworks")
        print("\nExample:")
        print("   Create a web scraper that:")
        print("   1. Fetches product data from e-commerce sites")
        print("   2. Stores data in SQLite database")
        print("   3. Exports to CSV format")
        print("   4. Includes error handling")
        print("=" * 60)
        print("\n📝 Enter your requirements below:")
        print("(Type 'END' on a new line when finished)")
        
        lines = []
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
            
        return '\n'.join(lines)
        
    def configure_phases(self):
        """Let user configure which phases to run with detailed explanations."""
        print("\n⚙️  Phase Configuration")
        print("=" * 60)
        print("The workflow always runs phases 1-8. You can optionally enable:")
        print()
        
        # Phase 9
        print("📍 Phase 9 - Test Execution")
        print("   What it does:")
        print("   • Runs unit tests after each feature")
        print("   • Catches bugs early in development")
        print("   • Ensures each feature works correctly")
        print("   • Adds ~20% to execution time")
        print("   Recommended for: Production code, APIs, complex logic")
        
        choice = input("\n   Enable Phase 9? (y/N): ").strip().lower()
        self.config["run_tests"] = choice == 'y'
        
        # Phase 10
        print("\n📍 Phase 10 - Integration Verification")
        print("   What it does:")
        print("   • Runs full test suite after all features")
        print("   • Verifies components work together")
        print("   • Checks for integration issues")
        print("   • Generates completion report")
        print("   • Adds ~30% to execution time")
        print("   Recommended for: Multi-component systems, APIs, full applications")
        
        choice = input("\n   Enable Phase 10? (y/N): ").strip().lower()
        self.config["run_integration_verification"] = choice == 'y'
        
        # TDD mode option
        print("\n📍 Test-Driven Development (TDD) Mode")
        print("   What it does:")
        print("   • Writes tests BEFORE implementing each feature")
        print("   • Ensures tests fail first (red phase)")
        print("   • Implements code to make tests pass (green phase)")
        print("   • Optional refactoring phase")
        print("   • Adds ~40% to execution time but improves quality")
        print("   Recommended for: Production code, critical features, learning TDD")
        
        choice = input("\n   Enable TDD mode? (y/N): ").strip().lower()
        if choice == 'y':
            self.config["workflow_type"] = "mvp_incremental_tdd"
        else:
            self.config["workflow_type"] = "mvp_incremental"
        
        # Short mode option
        print("\n📍 Output Display Mode")
        print("   Short mode shows minimal output with emoji status indicators")
        print("   • Shows only agent names and pass/fail status")
        print("   • Full logs are still saved to files")
        print("   • Reduces console clutter significantly")
        print("   Recommended for: Experienced users, CI/CD environments")
        
        choice = input("\n   Enable short mode? (y/N): ").strip().lower()
        self.short_mode = choice == 'y'
        
    def show_configuration_summary(self, requirements: str):
        """Display configuration summary before running."""
        print("\n📋 Configuration Summary")
        print("=" * 70)
        
        # Show requirements preview
        req_preview = requirements[:200] + "..." if len(requirements) > 200 else requirements
        req_lines = req_preview.split('\n')
        print("📝 Requirements:")
        for line in req_lines[:5]:  # Show first 5 lines
            print(f"   {line}")
        if len(req_lines) > 5:
            print("   ...")
            
        print(f"\n⚙️  Configuration:")
        tdd_enabled = self.config.get("workflow_type", "mvp_incremental") == "mvp_incremental_tdd"
        print(f"   TDD Mode: {'✅ Enabled' if tdd_enabled else '❌ Disabled'}")
        print(f"   Phase 9 (Test Execution): {'✅ Enabled' if self.config['run_tests'] else '❌ Disabled'}")
        print(f"   Phase 10 (Integration): {'✅ Enabled' if self.config['run_integration_verification'] else '❌ Disabled'}")
        print(f"   Output Mode: {'🚀 Short Mode' if self.short_mode else '📝 Detailed Mode'}")
        
        # Estimate time
        base_time = 3  # minutes
        if self.selected_example:
            example = EXAMPLES[self.selected_example]
            if "2-3 minutes" in example["time_estimate"]:
                base_time = 2.5
            elif "5-7 minutes" in example["time_estimate"]:
                base_time = 6
            elif "10-15 minutes" in example["time_estimate"]:
                base_time = 12
            elif "5-8 minutes" in example["time_estimate"]:
                base_time = 6.5
        
        if tdd_enabled:
            base_time *= 1.4  # TDD adds significant time
        if self.config["run_tests"]:
            base_time *= 1.2
        if self.config["run_integration_verification"]:
            base_time *= 1.3
            
        print(f"\n⏱️  Estimated time: {int(base_time)}-{int(base_time * 1.2)} minutes")
        print("=" * 70)
        
    async def run_workflow(self, requirements: str) -> Dict:
        """Execute the MVP incremental workflow with progress updates."""
        print("\n🏃 Starting MVP Incremental Workflow...")
        if self.short_mode:
            print("Running in short mode - minimal output with status indicators\n")
        else:
            print("This will take a few minutes. Watch the progress below:\n")
        
        # Create progress indicator
        phases = ["Planning", "Design", "Implementation", "Validation", "Review", "Completion"]
        current_phase = 0
        
        def update_progress(phase_name: str):
            nonlocal current_phase
            print(f"\n{'─' * 60}")
            print(f"🔄 Phase {current_phase + 1}/6: {phase_name}")
            print(f"{'─' * 60}")
            current_phase += 1
        
        # Show initial progress
        update_progress("Planning")
        
        # Determine workflow type
        workflow_type = self.config.get("workflow_type", "mvp_incremental")
        
        # Create input
        input_data = CodingTeamInput(
            requirements=requirements,
            workflow_type=workflow_type,  # Add workflow type to input
            run_tests=self.config["run_tests"],
            run_integration_verification=self.config["run_integration_verification"]
        )
        
        # Create tracer for monitoring
        session_id = f"mvp_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tracer = WorkflowExecutionTracer(session_id)
        
        # Configure output handler for short mode if needed
        if self.short_mode:
            from workflows.agent_output_handler import RealTimeOutputHandler, set_output_handler
            short_handler = RealTimeOutputHandler(display_mode="minimal")
            set_output_handler(short_handler)
        
        try:
            # Execute workflow
            result = await execute_workflow(
                input_data,
                tracer
            )
            
            # Show completion
            print(f"\n{'─' * 60}")
            print("✅ Workflow completed successfully!")
            print(f"{'─' * 60}")
            
            return result
            
        except Exception as e:
            print(f"\n{'─' * 60}")
            print(f"❌ Error during workflow execution")
            print(f"{'─' * 60}")
            raise e
        
    def show_output_structure(self, output_dir: Path):
        """Display the structure of generated files."""
        print("\n📁 Generated Project Structure:")
        print("=" * 60)
        
        if output_dir.exists():
            # Find the most recent generated directory
            generated_dir = Path("generated")
            if generated_dir.exists():
                app_dirs = [d for d in generated_dir.iterdir() if d.is_dir() and d.name.startswith("app_generated_")]
                if app_dirs:
                    latest_dir = max(app_dirs, key=lambda d: d.stat().st_mtime)
                    print(f"📂 {latest_dir.name}/")
                    
                    # Show file tree (simplified)
                    for item in sorted(latest_dir.rglob("*")):
                        if item.is_file():
                            relative = item.relative_to(latest_dir)
                            indent = "  " * len(relative.parts[:-1])
                            print(f"{indent}├── {relative.name}")
                    
                    print(f"\n📍 Full path: {latest_dir.absolute()}")
                else:
                    print("No generated files found yet.")
        
        print("=" * 60)
        
    def show_next_steps(self):
        """Display what users can do with their generated code."""
        print("\n🎯 Next Steps:")
        print("=" * 60)
        print("1. 📂 Navigate to the generated directory")
        print("2. 🔍 Review the generated code")
        print("3. 📦 Install any dependencies (check requirements.txt)")
        print("4. 🏃 Run the application or tests")
        print("5. ✏️  Customize and extend as needed")
        print("\n💡 Tips:")
        print("   • Generated code follows best practices")
        print("   • All code includes comprehensive documentation")
        print("   • Tests are included when Phase 9 is enabled")
        print("   • Check COMPLETION_REPORT.md for detailed info")
        print("=" * 60)
        
    def save_results(self, result: Dict, log_file_path: Optional[Path] = None):
        """Save results to file with helpful information."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Save result summary
        summary_file = output_dir / f"mvp_demo_{timestamp}_summary.json"
        summary = {
            "timestamp": timestamp,
            "example": self.selected_example,
            "config": self.config,
            "success": True,
            "session_id": result.get("session_id", "unknown"),
            "generated_path": str(Path("generated").absolute()),
            "console_log": str(log_file_path) if log_file_path else None
        }
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Results saved to: {summary_file}")
        
        # Show comprehensive output locations
        self.show_output_locations(result, summary_file, log_file_path)
        
        # Show output structure
        self.show_output_structure(output_dir)
        
        # Show next steps
        self.show_next_steps()
    
    def show_output_locations(self, result: Dict, summary_file: Path, log_file_path: Optional[Path] = None):
        """Display comprehensive information about where all outputs are located."""
        print("\n" + "="*80)
        print("📍 OUTPUT LOCATIONS - Where to find everything from this run")
        print("="*80)
        
        # Console log
        if log_file_path and log_file_path.exists():
            print(f"\n📝 Console Output Log:")
            print(f"   Location: {log_file_path}")
            print(f"   Size: {log_file_path.stat().st_size / 1024:.1f} KB")
            print(f"   Contains: Complete console output from this demo run")
        
        # Summary file
        print(f"\n📊 Run Summary (JSON):")
        print(f"   Location: {summary_file}")
        print(f"   Contains: Configuration, timestamps, and paths")
        
        # Generated code
        generated_dir = Path("generated")
        if generated_dir.exists():
            app_dirs = [d for d in generated_dir.iterdir() if d.is_dir() and d.name.startswith("app_generated_")]
            if app_dirs:
                latest_dir = max(app_dirs, key=lambda d: d.stat().st_mtime)
                print(f"\n💻 Generated Code:")
                print(f"   Location: {latest_dir}")
                file_count = len(list(latest_dir.rglob("*")))
                print(f"   Files: {file_count} files generated")
                
                # List key files
                key_files = []
                for pattern in ["*.py", "*.md", "*.txt", "*.json"]:
                    key_files.extend(latest_dir.rglob(pattern))
                
                if key_files:
                    print(f"   Key files:")
                    for f in sorted(key_files)[:5]:  # Show first 5
                        print(f"     - {f.name}")
                    if len(key_files) > 5:
                        print(f"     ... and {len(key_files) - 5} more files")
        
        # Workflow logs
        logs_dir = Path("logs")
        if logs_dir.exists():
            session_id = result.get("session_id", "")
            if session_id:
                # Look for logs with this session ID
                session_logs = list(logs_dir.glob(f"*{session_id}*"))
                if not session_logs and app_dirs:
                    # Try to find logs by timestamp
                    latest_timestamp = latest_dir.name.split("_")[-1]
                    session_logs = list(logs_dir.glob(f"*{latest_timestamp}*"))
                
                if session_logs:
                    print(f"\n📋 Workflow Execution Logs:")
                    for log in session_logs[:3]:  # Show up to 3 logs
                        print(f"   - {log}")
                    if len(session_logs) > 3:
                        print(f"   ... and {len(session_logs) - 3} more log files")
        
        # Test outputs if tests were run
        if self.config.get("run_tests") or self.config.get("run_integration_verification"):
            test_outputs = Path("tests/outputs")
            if test_outputs.exists():
                recent_sessions = sorted(
                    [d for d in test_outputs.iterdir() if d.is_dir() and d.name.startswith("session_")],
                    key=lambda d: d.stat().st_mtime,
                    reverse=True
                )
                if recent_sessions:
                    print(f"\n🧪 Test Outputs:")
                    print(f"   Location: {recent_sessions[0]}")
                    print(f"   Contains: Test results, agent outputs, execution reports")
        
        # Completion report
        if generated_dir.exists() and app_dirs:
            latest_dir = max(app_dirs, key=lambda d: d.stat().st_mtime)
            completion_report = latest_dir / "COMPLETION_REPORT.md"
            if completion_report.exists():
                print(f"\n📄 Completion Report:")
                print(f"   Location: {completion_report}")
                print(f"   Contains: Detailed workflow execution summary")
        
        print("\n" + "="*80)
        print("💡 Quick Commands:")
        if log_file_path:
            print(f"   View console log:        cat {log_file_path}")
        
        # Get the latest generated directory
        latest_gen_dir = None
        if generated_dir.exists():
            app_dirs_cmd = [d for d in generated_dir.iterdir() if d.is_dir() and d.name.startswith("app_generated_")]
            if app_dirs_cmd:
                latest_gen_dir = max(app_dirs_cmd, key=lambda d: d.stat().st_mtime)
        
        print(f"   View generated code:     cd {latest_gen_dir if latest_gen_dir else 'generated/'}")
        print(f"   View summary:            cat {summary_file}")
        print("="*80)
        
    def run_tutorial_mode(self):
        """Run an interactive tutorial for beginners."""
        print("\n🎓 Welcome to Tutorial Mode!")
        print("=" * 60)
        print("I'll guide you through using the MVP Incremental Workflow step by step.")
        
        input("\nPress Enter to continue...")
        
        print("\n📚 Step 1: Understanding the System")
        print("The MVP Incremental Workflow uses AI agents to build software for you.")
        print("Think of it as having a team of expert programmers at your disposal!")
        
        input("\nPress Enter to continue...")
        
        print("\n📚 Step 2: Choosing an Example")
        print("For your first run, we'll use the 'calculator' example.")
        print("It's simple, quick, and shows all the key features.")
        
        input("\nPress Enter to continue...")
        
        print("\n📚 Step 3: Configuration")
        print("We'll enable Phase 9 (Test Execution) to see how the system")
        print("automatically creates and runs tests for your code.")
        
        input("\nPress Enter to start the demo...")
        
        # Set up tutorial configuration
        self.selected_example = "calculator"
        self.config["run_tests"] = True
        self.config["run_integration_verification"] = False
        
        print("\n✅ Tutorial configuration set!")
        print("Now let's run the workflow and see what happens...")
        
        return EXAMPLES["calculator"]["requirements"]
        
    async def run_interactive(self):
        """Run in interactive mode with enhanced user experience."""
        # Set up console logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("demo_outputs/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / f"mvp_demo_{timestamp}_console.log"
        
        with ConsoleLogger(log_file_path):
            self.print_banner()
            
            # Run preflight checks
            if not PreflightChecker.run_all_checks():
                print("\n⚠️  Please fix the issues above before continuing.")
                return
            
            while True:
                choice = self.get_user_choice()
            
                if choice == '5':  # Exit
                    print("\n👋 Thanks for using MVP Incremental Demo!")
                    print("   Happy coding! 🚀")
                    break
                    
                elif choice == '4':  # Learn more
                    self.print_workflow_phases()
                    input("\nPress Enter to continue...")
                    continue
                    
                elif choice == '3':  # Tutorial mode
                    requirements = self.run_tutorial_mode()
                    
                elif choice == '1':  # Pre-configured example
                    example_key = self.select_example()
                    if example_key:
                        self.selected_example = example_key
                        example = EXAMPLES[example_key]
                        requirements = example["requirements"]
                        
                        # Use example's default config
                        self.config = example["config"].copy()
                        
                        # Ask if user wants to modify phases
                        print("\n🔧 Configuration Options:")
                        print("1. Use recommended settings")
                        print("2. Customize phase configuration")
                        
                        config_choice = input("\nYour choice (1-2): ").strip()
                        if config_choice == '2':
                            self.configure_phases()
                    else:
                        continue
                        
                else:  # Custom requirements
                    requirements = self.get_custom_requirements()
                    if not requirements.strip():
                        print("❌ Requirements cannot be empty. Please try again.")
                        continue
                        
                    self.configure_phases()
                
                # Show summary and confirm
                self.show_configuration_summary(requirements)
                
                print("\n▶️  Ready to start?")
                print("   The workflow will now create your application.")
                print("   This typically takes a few minutes.")
                
                confirm = input("\n   Proceed? (Y/n): ").strip().lower()
                
                if confirm != 'n':
                    try:
                        start_time = time.time()
                        result = await self.run_workflow(requirements)
                        end_time = time.time()
                        
                        print(f"\n⏱️  Total time: {int(end_time - start_time)} seconds")
                        
                        # Save results with log file path
                        self.save_results(result, log_file_path)
                        
                    except Exception as e:
                        print(f"\n❌ Error during workflow execution:")
                        print(f"   {str(e)}")
                        print("\n💡 Troubleshooting tips:")
                        print("   1. Check if the orchestrator server is still running")
                        print("   2. Try with a simpler example first")
                        print("   3. Check the logs in the 'logs' directory")
                        print("   4. Report issues at: https://github.com/anthropics/claude-code/issues")
                        
                # Ask if user wants to run another
                print("\n🔄 Would you like to:")
                print("   1. Run another workflow")
                print("   2. Exit the demo")
                
                another = input("\nYour choice (1-2): ").strip()
                if another != '1':
                    print("\n👋 Thanks for using MVP Incremental Demo!")
                    print("   Your generated code is in the 'generated' directory.")
                    print("   Happy coding! 🚀")
                    break


async def run_cli(args):
    """Run in CLI mode with enhanced features."""
    demo = MVPIncrementalDemo()
    
    # Set up console logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("demo_outputs/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / f"mvp_demo_cli_{timestamp}_console.log"
    
    # Set short mode if specified
    if args.short:
        demo.short_mode = True
    
    with ConsoleLogger(log_file_path):
        # Determine workflow type
        workflow_type = "mvp_incremental"
        if args.workflow:
            workflow_type = args.workflow
        elif args.tdd:
            workflow_type = "mvp_incremental_tdd"
        
        demo.config["workflow_type"] = workflow_type
        
        # Handle dry-run mode
        if args.dry_run:
            print("🔍 Dry Run Mode - Showing what would happen:\n")
        
            if args.preset:
                example = EXAMPLES[args.preset]
                print(f"Would use preset: {example['name']}")
                print(f"Requirements: {example['requirements'][:100]}...")
            elif args.requirements:
                print(f"Would use custom requirements: {args.requirements[:100]}...")
            
            print(f"\nConfiguration:")
            print(f"  Workflow: {workflow_type}")
            print(f"  TDD Mode: {'✅' if 'tdd' in workflow_type else '❌'}")
            print(f"  All phases: {args.all_phases}")
            print(f"  Tests: {args.tests if args.tests is not None else 'default'}")
            print(f"  Integration: {args.integration if args.integration is not None else 'default'}")
            print(f"  Save output: {args.save_output}")
            print(f"  Short mode: {args.short}")
            
            print("\n✅ Dry run complete. No changes were made.")
            return 0
        
        # Run preflight checks unless skipped
        if not args.skip_checks:
            if not PreflightChecker.run_all_checks():
                print("\n⚠️  Use --skip-checks to bypass preflight checks (not recommended)")
                return 1
        
        # Determine requirements
        if args.preset:
            if args.preset not in EXAMPLES:
                print(f"❌ Invalid preset: {args.preset}")
                print(f"Available presets: {', '.join(EXAMPLES.keys())}")
                return 1
                
            example = EXAMPLES[args.preset]
            requirements = example["requirements"]
            demo.config = example["config"].copy()
            
        elif args.requirements:
            requirements = args.requirements
        else:
            print("❌ Either --preset or --requirements must be specified")
            print("Use --help for more information")
            return 1
        
        # Override config if specified
        if args.all_phases:
            demo.config["run_tests"] = True
            demo.config["run_integration_verification"] = True
        else:
            if args.tests is not None:
                demo.config["run_tests"] = args.tests
            if args.integration is not None:
                demo.config["run_integration_verification"] = args.integration
                
        # Show configuration
        workflow_desc = "MVP Incremental Workflow"
        if 'tdd' in workflow_type:
            workflow_desc += " with TDD"
        print(f"🚀 Running {workflow_desc}")
        print(f"📋 Requirements: {requirements[:100]}...")
        print(f"🧪 TDD Mode: {'✅ Tests written before implementation' if 'tdd' in workflow_type else '❌ Standard implementation'}")
        print(f"⚙️  Phase 9 (Tests): {'✅' if demo.config['run_tests'] else '❌'}")
        print(f"⚙️  Phase 10 (Integration): {'✅' if demo.config['run_integration_verification'] else '❌'}")
        print(f"📊 Output Mode: {'🚀 Short' if demo.short_mode else '📝 Detailed'}")
        
        if args.verbose:
            print(f"\n📝 Full requirements:")
            print(requirements)
        
        print()
        
        try:
            start_time = time.time()
            result = await demo.run_workflow(requirements)
            end_time = time.time()
            
            print(f"\n⏱️  Total time: {int(end_time - start_time)} seconds")
            
            # Always save results in CLI mode to show log location
            demo.save_results(result, log_file_path)
                
            return 0
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main():
    """Main entry point with comprehensive argument parsing."""
    parser = argparse.ArgumentParser(
        description="🚀 MVP Incremental Workflow Demo - Build software with AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📚 Examples:
  
  # Interactive mode (recommended for beginners)
  python demo_mvp_incremental.py
  
  # Use a preset example
  python demo_mvp_incremental.py --preset calculator
  
  # Custom requirements with all phases
  python demo_mvp_incremental.py --requirements "Create a web scraper" --all-phases
  
  # Preset with custom phase configuration
  python demo_mvp_incremental.py --preset todo-api --tests --no-integration
  
  # Dry run to see what would happen
  python demo_mvp_incremental.py --preset auth-system --dry-run
  
  # Verbose mode with output saving
  python demo_mvp_incremental.py --preset file-processor --verbose --save-output
  
  # Short mode for minimal output
  python demo_mvp_incremental.py --preset calculator --short

🎯 Available Presets:
  calculator     - Simple calculator with basic operations (Beginner)
  todo-api       - REST API for TODO management (Intermediate)
  auth-system    - Complete authentication system (Advanced)
  file-processor - CSV file processing tool (Intermediate)

💡 Tips:
  • Use interactive mode if you're new to the system
  • Start with the 'calculator' preset to see how it works
  • Enable Phase 9 (--tests) for test-driven development
  • Enable Phase 10 (--integration) for complex systems
  • Use --dry-run to preview without executing
        """
    )
    
    # Main arguments
    parser.add_argument(
        "--preset",
        choices=list(EXAMPLES.keys()),
        help="Use a pre-configured example project"
    )
    
    parser.add_argument(
        "--requirements",
        help="Custom requirements for your project (alternative to preset)"
    )
    
    # Phase configuration
    parser.add_argument(
        "--all-phases",
        action="store_true",
        help="Enable all phases (9 and 10) for comprehensive testing"
    )
    
    parser.add_argument(
        "--tests",
        action="store_true",
        default=None,
        help="Enable Phase 9 (test execution after each feature)"
    )
    
    parser.add_argument(
        "--no-tests",
        dest="tests",
        action="store_false",
        help="Disable Phase 9 (test execution)"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        default=None,
        help="Enable Phase 10 (full integration verification)"
    )
    
    parser.add_argument(
        "--no-integration",
        dest="integration",
        action="store_false",
        help="Disable Phase 10 (integration verification)"
    )
    
    # Output options
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save execution results and summary to file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output during execution"
    )
    
    parser.add_argument(
        "--short", "-s",
        action="store_true",
        help="Enable short mode - minimal output with emoji status indicators"
    )
    
    # TDD options
    parser.add_argument(
        "--tdd",
        action="store_true",
        help="Use Test-Driven Development approach (write tests before implementation)"
    )
    
    parser.add_argument(
        "--workflow",
        type=str,
        choices=["mvp_incremental", "mvp_incremental_tdd", "mvp_tdd"],
        default=None,
        help="Workflow type to use (default: mvp_incremental, or mvp_incremental_tdd if --tdd)"
    )
    
    # Utility options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip preflight checks (not recommended)"
    )
    
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available presets with details"
    )
    
    args = parser.parse_args()
    
    # Handle --list-presets
    if args.list_presets:
        print("\n📚 Available Presets:")
        print("=" * 70)
        for key, example in EXAMPLES.items():
            print(f"\n🔹 {key}")
            print(f"   Name: {example['name']}")
            print(f"   Difficulty: {example['difficulty']}")
            print(f"   Time: {example['time_estimate']}")
            print(f"   Description: {example['description']}")
            print(f"   Files: {', '.join(example['expected_files'])}")
        print("\n" + "=" * 70)
        sys.exit(0)
    
    # Check if running without arguments (interactive mode)
    if not any(vars(args).values()) or (
        not args.preset and not args.requirements and not args.list_presets
    ):
        asyncio.run(MVPIncrementalDemo().run_interactive())
    else:
        # CLI mode
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)


if __name__ == "__main__":
    main()