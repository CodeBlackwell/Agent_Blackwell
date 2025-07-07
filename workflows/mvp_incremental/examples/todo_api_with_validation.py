#!/usr/bin/env python3
"""
Example: TODO API with Validation
Demonstrates retry mechanisms and validation features
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.mvp_incremental.config_helper import load_preset


async def run_todo_api_example():
    """Run TODO API example with validation and retries."""
    
    print("📝 TODO API with Validation Example")
    print("=" * 60)
    print("This example demonstrates:")
    print("- Complex feature dependencies")
    print("- Automatic validation and retry")
    print("- API endpoint implementation")
    print("- Using presets for configuration")
    print()
    
    # Requirements for a TODO API
    requirements = """
Create a REST API for managing TODO items using FastAPI:

1. Data Model:
   - TODO item with: id, title, description, completed, created_at, updated_at
   - Use Pydantic for validation
   - Use SQLite for persistence

2. API Endpoints:
   - POST /todos - Create a new TODO
   - GET /todos - List all TODOs with pagination (limit, offset)
   - GET /todos/{id} - Get specific TODO
   - PUT /todos/{id} - Update TODO
   - DELETE /todos/{id} - Delete TODO
   - GET /todos/search - Search TODOs by title

3. Features:
   - Input validation with meaningful error messages
   - Automatic API documentation (Swagger/OpenAPI)
   - CORS support for web clients
   - Request/response logging
   - Error handling with proper HTTP status codes

4. Testing:
   - Unit tests for all endpoints
   - Test validation rules
   - Test error scenarios
   - Test pagination
"""
    
    # Load the basic_api preset
    print("🔧 Loading 'basic_api' preset configuration...")
    config = load_preset("basic_api")
    
    # Create input with preset config
    input_data = CodingTeamInput(
        requirements=requirements,
        run_tests=config.run_tests,
        run_integration_verification=config.run_integration_verification
    )
    
    print("📋 Configuration (from preset):")
    print(f"   Max retries: {config.max_retries}")
    print(f"   Test execution: {'✅' if config.run_tests else '❌'}")
    print(f"   Integration verification: {'✅' if config.run_integration_verification else '❌'}")
    print()
    print("🚀 Starting workflow...")
    print("-" * 60)
    
    try:
        # Execute the workflow
        result = await execute_workflow(
            "mvp_incremental",
            input_data
        )
        
        print()
        print("✅ Workflow completed successfully!")
        print()
        print("📊 Results:")
        print("   - FastAPI application with all endpoints")
        print("   - SQLite database integration")
        print("   - Comprehensive validation")
        print("   - Auto-generated API documentation")
        print()
        print("💡 Key Features Demonstrated:")
        print("   - Validation caught and fixed import errors")
        print("   - Retry mechanism handled missing dependencies")
        print("   - All endpoints tested and verified")
        print()
        print("🔗 To run the API:")
        print("   cd generated/app_generated_*")
        print("   pip install -r requirements.txt")
        print("   uvicorn main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_todo_api_example())
    sys.exit(exit_code)