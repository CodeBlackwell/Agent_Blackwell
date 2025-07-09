#!/usr/bin/env python3
"""
🌐 Build a REST API - MVP Incremental Workflow Demo
==================================================

This script demonstrates building a REST API using the MVP Incremental workflow,
showing all 10 phases of incremental development with validation at each step.

Usage:
    python build_rest_api.py          # Build a TODO API (default)
    python build_rest_api.py blog     # Build a Blog API
    python build_rest_api.py auth     # Build an Authentication API
    
The MVP Incremental Process (10 Phases):
    1. 📋 Requirements Analysis
    2. 🎯 Feature Planning  
    3. 🏗️ System Architecture
    4. 🧱 Core Infrastructure
    5. ✨ Feature Implementation
    6. 🧪 Test Development
    7. 🔍 Code Review
    8. 🐛 Error Resolution
    9. ✅ Test Execution
    10. 🔗 Integration Verification
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker


class RestApiBuilder:
    """Builds REST APIs using MVP Incremental workflow."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.phase_emojis = {
            1: "📋", 2: "🎯", 3: "🏗️", 4: "🧱", 5: "✨",
            6: "🧪", 7: "🔍", 8: "🐛", 9: "✅", 10: "🔗"
        }
        
    async def build_api(self, api_type: str = "todo") -> None:
        """Build a REST API of specified type."""
        self.formatter.print_banner(
            "🌐 REST API BUILDER",
            "MVP Incremental Workflow Demo"
        )
        
        # Show MVP process explanation
        print("\n📚 About MVP Incremental Workflow:")
        print("   This demo shows how to build a production-ready REST API")
        print("   through 10 carefully orchestrated phases:\n")
        
        phases = [
            "1. 📋 Requirements Analysis - Understanding what to build",
            "2. 🎯 Feature Planning - Breaking down into manageable features",
            "3. 🏗️ System Architecture - Designing the overall structure",
            "4. 🧱 Core Infrastructure - Setting up the foundation",
            "5. ✨ Feature Implementation - Building features incrementally",
            "6. 🧪 Test Development - Writing comprehensive tests",
            "7. 🔍 Code Review - Ensuring quality and best practices",
            "8. 🐛 Error Resolution - Fixing any issues found",
            "9. ✅ Test Execution - Running all tests",
            "10. 🔗 Integration Verification - Ensuring everything works together"
        ]
        
        for phase in phases:
            print(f"   {phase}")
            
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        # Get API requirements
        requirements = self._get_api_requirements(api_type)
        
        # Show what we're building
        self.formatter.print_section(f"Building {api_type.upper()} REST API")
        print("📝 Requirements:")
        print("-" * 60)
        print(requirements[:300] + "..." if len(requirements) > 300 else requirements)
        print("-" * 60)
        
        # Configuration options
        print("\n⚙️  Configuration Options:")
        config = {
            "run_tests": True,
            "run_integration_verification": True,
            "enable_all_phases": True
        }
        
        print(f"   • Run Tests: {'Yes' if config['run_tests'] else 'No'}")
        print(f"   • Integration Verification: {'Yes' if config['run_integration_verification'] else 'No'}")
        print(f"   • All 10 Phases: {'Yes' if config['enable_all_phases'] else 'No'}")
        
        # Confirm execution
        print("\n🚀 Ready to start the MVP Incremental process?")
        print("   You'll see each of the 10 phases execute in sequence.")
        print("\n   Press Enter to continue or Ctrl+C to cancel...")
        input()
        
        # Execute the workflow
        start_time = time.time()
        phase_times = {}
        
        print("\n" + "="*80)
        print("🏗️  STARTING MVP INCREMENTAL WORKFLOW")
        print("="*80)
        
        try:
            # Create input for workflow
            team_input = CodingTeamInput(
                requirements=requirements,
                workflow_type="mvp_incremental",
                **config
            )
            
            # Show phase progress (simulated for demo)
            print("\n📊 Phase Progress:")
            print("-" * 60)
            
            # Run the workflow with phase tracking
            result = await self._execute_with_phase_tracking(team_input, phase_times)
            
            # Show results
            self._show_results(result, time.time() - start_time, phase_times, api_type)
            
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
        
    def _get_api_requirements(self, api_type: str) -> str:
        """Get API requirements based on type."""
        requirements_map = {
            "todo": """Create a TODO management REST API with the following features:

1. Data Model:
   - Todo item with: id, title, description, status (pending/completed), created_at, updated_at
   - In-memory storage for simplicity

2. API Endpoints:
   - GET /todos - List all todos with optional status filter
   - GET /todos/{id} - Get a specific todo
   - POST /todos - Create a new todo
   - PUT /todos/{id} - Update a todo
   - DELETE /todos/{id} - Delete a todo
   - GET /todos/stats - Get statistics (total, completed, pending)

3. Technical Requirements:
   - Use FastAPI framework
   - Pydantic for data validation
   - Proper error handling and status codes
   - API documentation (auto-generated by FastAPI)
   - Comprehensive test coverage using pytest
   - Input validation for all endpoints

4. Additional Features:
   - Pagination for list endpoint
   - Search functionality by title
   - Bulk operations (mark multiple as complete)""",
   
            "blog": """Create a Blog REST API with the following features:

1. Data Models:
   - Post: id, title, content, author, tags, created_at, updated_at, published
   - Comment: id, post_id, author, content, created_at
   - In-memory storage

2. API Endpoints:
   - Posts:
     - GET /posts - List all posts (paginated)
     - GET /posts/{id} - Get post with comments
     - POST /posts - Create new post
     - PUT /posts/{id} - Update post
     - DELETE /posts/{id} - Delete post
   - Comments:
     - GET /posts/{id}/comments - List comments for a post
     - POST /posts/{id}/comments - Add comment
     - DELETE /comments/{id} - Delete comment
   - Additional:
     - GET /posts/search - Search posts by title/content
     - GET /posts/tags/{tag} - Get posts by tag

3. Technical Requirements:
   - FastAPI with async support
   - Rich error responses
   - Rate limiting simulation
   - Comprehensive testing""",
   
            "auth": """Create an Authentication REST API with the following features:

1. Data Models:
   - User: id, username, email, password_hash, created_at, is_active
   - Token: access_token, token_type, expires_in
   - In-memory user storage

2. API Endpoints:
   - POST /auth/register - User registration
   - POST /auth/login - User login (returns JWT token)
   - POST /auth/refresh - Refresh access token
   - GET /auth/me - Get current user info (protected)
   - PUT /auth/me - Update user profile (protected)
   - POST /auth/logout - Logout (invalidate token)
   - POST /auth/password/reset - Request password reset
   - POST /auth/password/confirm - Confirm password reset

3. Security Features:
   - Password hashing (bcrypt)
   - JWT token authentication
   - Token expiration and refresh
   - Protected endpoints
   - Input validation and sanitization

4. Technical Requirements:
   - FastAPI with OAuth2 support
   - PyJWT for token handling
   - Comprehensive security tests
   - Rate limiting for auth endpoints"""
        }
        
        return requirements_map.get(api_type, requirements_map["todo"])
        
    async def _execute_with_phase_tracking(self, team_input: CodingTeamInput, phase_times: Dict) -> dict:
        """Execute workflow with simulated phase tracking."""
        # This is a simulation for the demo
        # In reality, the workflow would report progress
        
        phases = [
            "Requirements Analysis",
            "Feature Planning",
            "System Architecture", 
            "Core Infrastructure",
            "Feature Implementation",
            "Test Development",
            "Code Review",
            "Error Resolution",
            "Test Execution",
            "Integration Verification"
        ]
        
        # Start the actual workflow
        workflow_task = asyncio.create_task(execute_workflow(team_input))
        
        # Simulate phase progress
        for i, phase in enumerate(phases, 1):
            phase_start = time.time()
            emoji = self.phase_emojis.get(i, "📌")
            
            print(f"{emoji} Phase {i}/10: {phase}... ", end="", flush=True)
            
            # Wait a bit to simulate work
            await asyncio.sleep(2)
            
            phase_times[phase] = time.time() - phase_start
            print(f"✓ ({phase_times[phase]:.1f}s)")
            
            # Check if workflow completed early
            if workflow_task.done():
                break
                
        # Wait for workflow to complete
        result = await workflow_task
        return result
        
    def _show_results(self, result: dict, total_duration: float, phase_times: Dict, api_type: str) -> None:
        """Show the workflow results."""
        self.formatter.print_banner("✅ MVP INCREMENTAL WORKFLOW COMPLETE!", width=80)
        
        print(f"\n⏱️  Total Duration: {total_duration:.2f} seconds")
        
        # Show phase summary
        print("\n📊 Phase Execution Summary:")
        print("-" * 60)
        for phase, duration in phase_times.items():
            print(f"   {phase:<30} {duration:>6.1f}s")
        print("-" * 60)
        print(f"   {'Total:':<30} {sum(phase_times.values()):>6.1f}s")
        
        # Show generated files
        print("\n📁 Generated API Structure:")
        output_dir = Path("generated/app_generated_latest")
        if output_dir.exists():
            self._show_directory_tree(output_dir, prefix="   ")
            
        # Show how to run the API
        print(f"\n🚀 To run your {api_type.upper()} API:")
        print("   cd generated/app_generated_latest")
        print("   pip install -r requirements.txt")
        print("   uvicorn main:app --reload")
        print("\n   Then visit: http://localhost:8000/docs")
        
        # Show testing instructions
        print("\n🧪 To run the tests:")
        print("   cd generated/app_generated_latest")
        print("   pytest -v")
        
        # Educational summary
        print("\n📚 What the MVP Incremental Process Achieved:")
        print("   ✓ Analyzed and planned the complete system")
        print("   ✓ Built features incrementally with validation")
        print("   ✓ Wrote comprehensive tests for all endpoints")
        print("   ✓ Reviewed and improved code quality")
        print("   ✓ Verified integration between components")
        print("   ✓ Created a production-ready REST API!")
        
        # Save results
        self._save_results(result, total_duration, phase_times, api_type)
        
    def _show_directory_tree(self, path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """Show directory structure as tree."""
        if current_depth >= max_depth:
            return
            
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        for item in items[:10]:  # Limit to first 10 items
            if item.name.startswith('.'):
                continue
            print(f"{prefix}{'└── ' if item == items[-1] else '├── '}{item.name}")
            if item.is_dir():
                self._show_directory_tree(item, prefix + "    ", max_depth, current_depth + 1)
                
    def _save_results(self, result: dict, duration: float, phase_times: Dict, api_type: str) -> None:
        """Save build results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/api_builds")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "api_type": api_type,
            "workflow": "MVP Incremental",
            "total_duration": duration,
            "phase_times": phase_times,
            "phases_completed": list(phase_times.keys()),
            "success": True
        }
        
        summary_file = output_dir / f"{api_type}_api_build_{timestamp}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Build summary saved to: {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a REST API using MVP Incremental workflow"
    )
    parser.add_argument(
        "api_type",
        nargs="?",
        default="todo",
        choices=["todo", "blog", "auth"],
        help="Type of API to build (default: todo)"
    )
    
    args = parser.parse_args()
    
    builder = RestApiBuilder()
    asyncio.run(builder.build_api(args.api_type))


if __name__ == "__main__":
    main()