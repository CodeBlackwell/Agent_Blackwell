#!/usr/bin/env python3
"""
Direct demo of the incremental workflow with feature orchestrator.
This doesn't require the main orchestrator service to be running.
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.incremental.incremental_workflow import execute_incremental_workflow
from workflows.monitoring import WorkflowExecutionTracer

# Blog Application Requirements with explicit feature breakdown
BLOG_REQUIREMENTS = """
Create a simple blog application with the following features:

IMPLEMENTATION PLAN:

FEATURE[1]: Database Models
Description: Create SQLAlchemy models for users, posts, and comments
Files: models/user.py, models/post.py, models/comment.py, models/__init__.py
Validation: All models should have proper fields and relationships defined
Dependencies: []
Complexity: low

FEATURE[2]: Authentication System
Description: Implement JWT-based authentication with user registration and login
Files: auth/jwt_handler.py, auth/password.py, api/auth_routes.py
Validation: Users can register, login, and receive valid JWT tokens
Dependencies: [FEATURE[1]]
Complexity: medium

FEATURE[3]: Blog Post CRUD API
Description: Create REST API endpoints for creating, reading, updating, and deleting blog posts
Files: api/post_routes.py, services/post_service.py
Validation: All CRUD operations work correctly with proper authorization
Dependencies: [FEATURE[1], FEATURE[2]]
Complexity: medium

FEATURE[4]: Comment System
Description: Implement threaded comments with moderation capabilities
Files: api/comment_routes.py, services/comment_service.py
Validation: Users can comment on posts, reply to comments, and authors can moderate
Dependencies: [FEATURE[1], FEATURE[2], FEATURE[3]]
Complexity: high

FEATURE[5]: Search and Filter
Description: Add search functionality for posts by title/content and filter by tags/author
Files: services/search_service.py, api/search_routes.py
Validation: Search returns relevant results and filters work correctly
Dependencies: [FEATURE[1], FEATURE[3]]
Complexity: medium

Technology Stack:
- Python with FastAPI
- SQLAlchemy for ORM
- Pydantic for validation
- JWT for authentication
"""

async def run_direct_incremental_demo():
    """Run the incremental workflow directly without external orchestrator."""
    
    print("🚀 Direct Incremental Blog Development Demo")
    print("=" * 80)
    print("\nThis demo uses the feature orchestrator directly within the workflow.")
    print("No external orchestrator service is required!\n")
    
    # Create input for the workflow
    input_data = CodingTeamInput(
        requirements=BLOG_REQUIREMENTS,
        workflow_type="incremental",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ]
    )
    
    # Create a tracer to monitor execution
    tracer = WorkflowExecutionTracer("direct_incremental_blog_demo")
    
    try:
        print("📋 Feature Plan:")
        print("-" * 40)
        print("1. Database Models (User, Post, Comment)")
        print("2. JWT Authentication System") 
        print("3. Blog Post CRUD API")
        print("4. Threaded Comment System")
        print("5. Search and Filter Functionality")
        print("-" * 40)
        
        print("\n⏳ Starting incremental workflow execution...\n")
        
        # Execute the incremental workflow directly
        # This will use the feature_orchestrator internally
        results = await execute_incremental_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed!")
        print("\n📊 Results Summary:")
        print("-" * 40)
        
        # Display results from each phase
        for result in results:
            if hasattr(result, 'team_member') and hasattr(result, 'output'):
                member_name = result.team_member.value if hasattr(result.team_member, 'value') else str(result.team_member)
                print(f"\n👤 {member_name.upper()}:")
                # Show first 300 chars of output
                output_preview = result.output[:300] + "..." if len(result.output) > 300 else result.output
                print(output_preview)
        
        # Get execution report
        report = tracer.get_report()
        if report:
            print("\n📈 Execution Metrics:")
            print(f"• Total Duration: {report.total_duration_seconds:.2f}s")
            print(f"• Total Steps: {report.total_steps}")
            
            # Show feature-specific metrics if available
            metadata = report.metadata
            if metadata and 'feature_count' in metadata:
                print(f"• Features Planned: {metadata['feature_count']}")
            if metadata and 'progress_report' in metadata:
                progress = metadata['progress_report']
                print(f"• Features Completed: {progress.get('completed', 0)}")
                print(f"• Success Rate: {progress.get('success_rate', 0):.1f}%")
        
        print("\n💡 The feature orchestrator has:")
        print("• Parsed the features from the requirements")
        print("• Implemented each feature incrementally")
        print("• Validated each feature before moving to the next")
        print("• Applied retry strategies for any failures")
        print("• Generated a complete codebase")
        
        return results, report
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

# Mock the agent functions for standalone testing
async def mock_run_team_member_with_tracking(agent: str, input_text: str, objective: str):
    """Mock agent for testing without the orchestrator service."""
    
    # Simple mock responses based on agent type
    if agent == "planner_agent":
        return [{
            "parts": [{
                "content": """
                Blog Application Development Plan:
                1. Set up database models for users, posts, and comments
                2. Implement authentication system with JWT
                3. Create CRUD API for blog posts
                4. Add comment system with threading
                5. Implement search and filtering
                
                This will be built incrementally with each feature validated before proceeding.
                """
            }]
        }]
    
    elif agent == "designer_agent":
        return [{
            "parts": [{
                "content": BLOG_REQUIREMENTS  # Use our pre-defined requirements with features
            }]
        }]
    
    elif agent == "coder_agent":
        # Return mock code for a feature
        return [{
            "parts": [{
                "content": """
                FILENAME: models/user.py
                ```python
                from sqlalchemy import Column, Integer, String, DateTime
                from sqlalchemy.ext.declarative import declarative_base
                from datetime import datetime

                Base = declarative_base()

                class User(Base):
                    __tablename__ = 'users'
                    
                    id = Column(Integer, primary_key=True)
                    email = Column(String(255), unique=True, nullable=False)
                    username = Column(String(100), unique=True, nullable=False)
                    password_hash = Column(String(255), nullable=False)
                    created_at = Column(DateTime, default=datetime.utcnow)
                    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
                ```
                """
            }]
        }]
    
    elif agent == "reviewer_agent":
        return [{
            "parts": [{
                "content": """
                Code Review Summary:
                - Database models are well-structured
                - Authentication implementation follows best practices
                - API endpoints are RESTful and secure
                - Good separation of concerns
                - Suggest adding more input validation
                """
            }]
        }]
    
    return [{"parts": [{"content": f"Mock response from {agent}"}]}]

def main():
    """Main entry point for the demo."""
    print("\n" + "="*80)
    print("🎯 DIRECT INCREMENTAL WORKFLOW DEMO: Feature Orchestrator")
    print("="*80 + "\n")
    
    # For testing, we can mock the agent calls
    if "--mock" in sys.argv:
        print("🧪 Running in mock mode (no external agents required)")
        # Monkey patch the import to use our mock
        import workflows.incremental.feature_orchestrator as fo
        fo.run_team_member_with_tracking = mock_run_team_member_with_tracking
    
    # Run the async demo
    asyncio.run(run_direct_incremental_demo())
    
    print("\n🎉 Demo completed!")
    print("\n📁 In a real run, generated code would be in ./generated/")
    print("\n💡 To run with real agents, start the orchestrator first:")
    print("   python orchestrator/orchestrator_agent.py")

if __name__ == "__main__":
    main()