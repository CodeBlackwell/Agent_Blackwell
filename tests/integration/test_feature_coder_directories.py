#!/usr/bin/env python3
"""
Integration tests for feature_coder_agent directory structure support
Tests the agent's actual ability to generate files with nested paths
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.feature_coder.feature_coder_agent import feature_coder_agent


async def test_mean_stack_structure():
    """Test MEAN stack directory structure generation"""
    print("🧪 Test 1: MEAN Stack Directory Structure")
    print("-" * 60)
    
    test_input = """
    Create a MEAN stack user authentication system with the following structure:
    
    Backend (Node.js/Express):
    - backend/src/server.js - Express server setup
    - backend/src/routes/auth.js - Authentication routes
    - backend/src/models/User.js - User model with Mongoose
    - backend/src/middleware/auth.js - JWT authentication middleware
    - backend/package.json - Backend dependencies
    
    Frontend (Angular):
    - frontend/src/app/app.module.ts - Angular app module
    - frontend/src/app/components/login/login.component.ts - Login component
    - frontend/src/app/services/auth.service.ts - Authentication service
    - frontend/package.json - Frontend dependencies
    
    Shared:
    - docker-compose.yml - Docker setup for all services
    """
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    result = ""
    async for message in feature_coder_agent(messages):
        result += message.parts[0].content
    
    print("\n📥 Response preview (first 500 chars):")
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # Parse the result to check for nested paths
    files = parse_output(result)
    
    print(f"\n📁 Files detected: {len(files)}")
    for filepath in sorted(files.keys()):
        print(f"   - {filepath}")
    
    # Verify expected structure
    expected_files = [
        'backend/src/server.js',
        'backend/src/routes/auth.js',
        'backend/src/models/User.js',
        'backend/src/middleware/auth.js',
        'backend/package.json',
        'frontend/src/app/app.module.ts',
        'frontend/src/app/components/login/login.component.ts',
        'frontend/src/app/services/auth.service.ts',
        'frontend/package.json',
        'docker-compose.yml'
    ]
    
    missing_files = [f for f in expected_files if f not in files]
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
    else:
        print("\n✅ All expected files generated with correct paths!")
    
    return len(missing_files) == 0


async def test_microservices_structure():
    """Test microservices architecture structure"""
    print("\n\n🧪 Test 2: Microservices Architecture")
    print("-" * 60)
    
    test_input = """
    Create a microservices e-commerce system with:
    
    User Service:
    - services/user-service/src/index.js - User service main file
    - services/user-service/src/models/user.js - User model
    - services/user-service/package.json - Dependencies
    
    Order Service:
    - services/order-service/src/index.js - Order service main file
    - services/order-service/src/models/order.js - Order model
    - services/order-service/package.json - Dependencies
    
    API Gateway:
    - services/api-gateway/src/index.js - Gateway routing
    - services/api-gateway/package.json - Dependencies
    
    Infrastructure:
    - docker-compose.yml - All services orchestration
    - .env.example - Environment variables template
    """
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    result = ""
    async for message in feature_coder_agent(messages):
        result += message.parts[0].content
    
    files = parse_output(result)
    
    print(f"\n📁 Files detected: {len(files)}")
    for filepath in sorted(files.keys()):
        print(f"   - {filepath}")
    
    # Check for service structure
    services = set()
    for filepath in files.keys():
        if filepath.startswith('services/'):
            service = filepath.split('/')[1]
            services.add(service)
    
    print(f"\n🎯 Services detected: {services}")
    
    expected_services = {'user-service', 'order-service', 'api-gateway'}
    missing_services = expected_services - services
    
    if missing_services:
        print(f"❌ Missing services: {missing_services}")
    else:
        print("✅ All microservices created successfully!")
    
    return len(missing_services) == 0


async def test_deeply_nested_structure():
    """Test deeply nested directory structures"""
    print("\n\n🧪 Test 3: Deeply Nested Structure")
    print("-" * 60)
    
    test_input = """
    Create a modular authentication system with deeply nested structure:
    
    - src/modules/auth/controllers/auth.controller.js - Authentication controller
    - src/modules/auth/services/auth.service.js - Business logic
    - src/modules/auth/repositories/user.repository.js - Data access
    - src/modules/auth/middleware/validate.middleware.js - Input validation
    - src/modules/auth/dto/login.dto.js - Data transfer objects
    - tests/unit/modules/auth/services/auth.service.test.js - Unit tests
    - tests/integration/modules/auth/auth.integration.test.js - Integration tests
    """
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    result = ""
    async for message in feature_coder_agent(messages):
        result += message.parts[0].content
    
    files = parse_output(result)
    
    print(f"\n📁 Files detected: {len(files)}")
    
    # Check nesting depth
    max_depth = 0
    for filepath in files.keys():
        depth = len(filepath.split('/'))
        max_depth = max(max_depth, depth)
        print(f"   - {filepath} (depth: {depth})")
    
    print(f"\n📏 Maximum nesting depth: {max_depth}")
    
    if max_depth >= 5:
        print("✅ Deep nesting handled correctly!")
        return True
    else:
        print("❌ Deep nesting not properly supported")
        return False


def parse_output(output: str) -> dict:
    """Parse agent output to extract files with paths"""
    import re
    
    files = {}
    
    # Multiple patterns to catch different formats
    patterns = [
        r'```(?:\w+)?\s*\n#\s*filename:\s*([^\n]+)\n(.*?)```',  # New format
        r'```(?:\w+)\s+([^\n]+)\n(.*?)```',  # Old format with filename after language
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, output, re.DOTALL)
        for filename, content in matches:
            filename = filename.strip().replace('\\', '/')
            files[filename] = content.strip()
    
    return files


async def main():
    """Run all integration tests"""
    print("🚀 Feature Coder Directory Structure Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("MEAN Stack Structure", await test_mean_stack_structure()))
    results.append(("Microservices Structure", await test_microservices_structure()))
    results.append(("Deeply Nested Structure", await test_deeply_nested_structure()))
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Directory structure support is working.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Feature coder needs enhancement.")
        
        # Provide specific enhancement needed
        print("\nRequired enhancement to feature_coder_agent.py:")
        print("- Update the instructions to explicitly mention directory support")
        print("- Ensure the output format example shows nested paths")
        print("- Test with the actual orchestrator server running")


if __name__ == "__main__":
    # Check if orchestrator is running
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        
        if result != 0:
            print("⚠️  WARNING: Orchestrator server not running on port 8080")
            print("   Please start it with: python orchestrator/orchestrator_agent.py")
            print("")
    except:
        pass
    
    asyncio.run(main())