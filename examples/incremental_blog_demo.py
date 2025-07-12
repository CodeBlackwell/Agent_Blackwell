#!/usr/bin/env python3
"""
Demo: How to use the Incremental Workflow to build a Blog application
This demonstrates the feature-based incremental development approach.
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer
from examples.simple_orchestrator_manager import ensure_orchestrator

# Port configuration
ORCHESTRATOR_PORT = 8080

# Blog Application Requirements
BLOG_REQUIREMENTS = """
Create a simple blog application with the following features:

1. Blog Post Management:
   - Create, read, update, and delete blog posts
   - Each post should have: title, content, author, created_at, updated_at, tags
   - Posts should support markdown content

2. User Management:
   - User registration and authentication
   - User profiles with name, email, bio
   - Authors can only edit their own posts

3. Comment System:
   - Users can comment on posts
   - Comments are threaded (replies to comments)
   - Comment moderation for authors

4. Search and Filter:
   - Search posts by title or content
   - Filter posts by author or tags
   - Pagination for post lists

5. API Design:
   - RESTful API endpoints
   - JSON responses
   - Basic authentication

Technology Stack:
- Python with FastAPI for the backend
- SQLAlchemy for database ORM
- Pydantic for data validation
- JWT for authentication

The implementation should be modular with clear separation of concerns.
Create a feature-based implementation plan that can be developed incrementally.
"""

async def run_incremental_blog_demo():
    """Run the incremental workflow to build a blog application."""
    
    print("🚀 Starting Incremental Blog Development Demo")
    print("=" * 80)
    print("\nThis demo shows how the incremental workflow breaks down a complex")
    print("project into manageable features and implements them one by one.\n")
    
    # Create input for the workflow
    input_data = CodingTeamInput(
        requirements=BLOG_REQUIREMENTS,
        workflow_type="incremental",  # Use incremental workflow
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ]
    )
    
    # Create a tracer to monitor execution
    tracer = WorkflowExecutionTracer("incremental_blog_demo")
    
    try:
        print("📋 Requirements Overview:")
        print("-" * 40)
        print("• Blog Post Management (CRUD operations)")
        print("• User Management (auth & profiles)")
        print("• Comment System (threaded comments)")
        print("• Search and Filter capabilities")
        print("• RESTful API with FastAPI")
        print("-" * 40)
        print("\n⏳ Starting workflow execution...\n")
        
        # Execute the incremental workflow
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed!")
        print("\n📊 Execution Summary:")
        print("-" * 40)
        
        # Display results from each phase
        for result in results:
            if hasattr(result, 'team_member') and hasattr(result, 'output'):
                print(f"\n👤 {result.team_member.value.upper()} Output:")
                # Show first 500 chars of output
                output_preview = result.output[:500] + "..." if len(result.output) > 500 else result.output
                print(output_preview)
                print("-" * 40)
        
        # Show execution report if available
        if hasattr(report, 'get_summary'):
            summary = report.get_summary()
            print("\n📈 Detailed Execution Report:")
            print(f"• Total Duration: {summary.get('total_duration', 'N/A')}")
            print(f"• Features Planned: {summary.get('features_planned', 'N/A')}")
            print(f"• Features Implemented: {summary.get('features_implemented', 'N/A')}")
            print(f"• Success Rate: {summary.get('success_rate', 'N/A')}%")
        
        print("\n💡 Key Benefits of Incremental Workflow:")
        print("• Features are implemented one at a time")
        print("• Each feature is validated before moving to the next")
        print("• Failed features can be retried with smart strategies")
        print("• Progress is tracked and visualized throughout")
        print("• Stagnation detection prevents getting stuck")
        
        return results, report
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main entry point for the demo."""
    print("\n" + "="*80)
    print("🎯 INCREMENTAL WORKFLOW DEMO: Building a Blog Application")
    print("="*80 + "\n")
    
    # Ensure orchestrator is running
    if not ensure_orchestrator():
        print("\n❌ Failed to start orchestrator. Please try manually:")
        print("   python orchestrator/orchestrator_agent.py")
        return
    
    print("\n✅ Orchestrator is ready!\n")
    
    try:
        # Run the async demo
        asyncio.run(run_incremental_blog_demo())
        
        print("\n🎉 Demo completed!")
        print("\n📁 Generated code can be found in the ./generated/ directory")
        print("\n📝 Note: The orchestrator is still running in the background.")
        print("   To stop it: pkill -f orchestrator_agent.py")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()