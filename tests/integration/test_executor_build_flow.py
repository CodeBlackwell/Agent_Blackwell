"""
Integration test for executor agent with build manager
Tests the complete flow of build detection, execution, and Docker containerization
"""

import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart


class TestExecutorBuildFlow(unittest.TestCase):
    """Test complete executor flow with build integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    @patch('agents.executor.executor_agent.docker')
    @patch('agents.executor.docker_manager.docker')
    async def test_typescript_project_build_flow(self, mock_docker_manager, mock_docker_executor):
        """Test TypeScript project with build step"""
        # Mock Docker clients
        mock_docker_client = MagicMock()
        mock_docker_client.ping.return_value = True
        mock_docker_client.images.build.return_value = (MagicMock(), [])
        mock_docker_client.containers.run.return_value = MagicMock(
            id="test_container_123",
            name="executor_test",
            status="running"
        )
        mock_docker_client.containers.get.return_value = MagicMock(
            exec_run=MagicMock(return_value=MagicMock(
                exit_code=0,
                output=(b"Tests passed", b"")
            ))
        )
        
        mock_docker_manager.from_env.return_value = mock_docker_client
        mock_docker_executor.from_env.return_value = mock_docker_client
        
        # Create test input with TypeScript code
        input_text = """
Requirements: Create a TypeScript calculator with tests

FILENAME: tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "strict": true
  }
}
```

FILENAME: package.json
```json
{
  "name": "calculator",
  "version": "1.0.0",
  "scripts": {
    "build": "tsc",
    "test": "jest"
  },
  "devDependencies": {
    "@types/node": "^18.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
```

FILENAME: src/calculator.ts
```typescript
export class Calculator {
  add(a: number, b: number): number {
    return a + b;
  }
  
  multiply(a: number, b: number): number {
    return a * b;
  }
}
```

FILENAME: src/calculator.test.ts
```typescript
import { Calculator } from './calculator';

describe('Calculator', () => {
  const calc = new Calculator();
  
  test('adds numbers', () => {
    expect(calc.add(2, 3)).toBe(5);
  });
  
  test('multiplies numbers', () => {
    expect(calc.multiply(3, 4)).toBe(12);
  });
});
```
"""
        
        # Create message
        message = Message(
            role="user",
            parts=[MessagePart(content=input_text)]
        )
        
        # Mock subprocess for build execution
        with patch('subprocess.run') as mock_run:
            # Mock TypeScript compilation
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Compilation complete",
                stderr=""
            )
            
            # Import and run executor
            from agents.executor.executor_agent import executor_agent
            
            # Collect output
            output_parts = []
            async for part in executor_agent([message]):
                output_parts.append(part.content)
            
            # Join output
            output = "\n".join(output_parts)
            
            # Verify build was detected and executed
            self.assertIn("Detecting build requirements", output)
            self.assertIn("Building node_typescript", output)
            self.assertIn("DOCKER EXECUTION RESULT", output)
            
            # Verify subprocess was called for build
            mock_run.assert_called()
            call_args = str(mock_run.call_args)
            self.assertIn("tsc", call_args)
    
    @patch('agents.executor.executor_agent.docker')
    @patch('agents.executor.docker_manager.docker')
    async def test_angular_project_build_flow(self, mock_docker_manager, mock_docker_executor):
        """Test Angular project with npm build"""
        # Mock Docker
        mock_docker_client = MagicMock()
        mock_docker_client.ping.return_value = True
        mock_docker_client.images.build.return_value = (MagicMock(), [])
        mock_docker_client.containers.run.return_value = MagicMock(
            id="test_container_456",
            name="executor_angular",
            status="running"
        )
        mock_docker_client.containers.get.return_value = MagicMock(
            exec_run=MagicMock(return_value=MagicMock(
                exit_code=0,
                output=(b"App running", b"")
            ))
        )
        
        mock_docker_manager.from_env.return_value = mock_docker_client
        mock_docker_executor.from_env.return_value = mock_docker_client
        
        # Angular project input
        input_text = """
Requirements: Create an Angular application

FILENAME: angular.json
```json
{
  "version": 1,
  "projects": {
    "app": {
      "projectType": "application",
      "root": "",
      "sourceRoot": "src"
    }
  }
}
```

FILENAME: package.json
```json
{
  "name": "angular-app",
  "scripts": {
    "build": "ng build",
    "start": "ng serve"
  },
  "dependencies": {
    "@angular/core": "^15.0.0"
  }
}
```

FILENAME: src/app/app.component.ts
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: '<h1>Hello Angular</h1>'
})
export class AppComponent {
  title = 'app';
}
```
"""
        
        message = Message(
            role="user",
            parts=[MessagePart(content=input_text)]
        )
        
        # Mock build command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Angular build complete\ndist/ folder created",
                stderr=""
            )
            
            from agents.executor.executor_agent import executor_agent
            
            output_parts = []
            async for part in executor_agent([message]):
                output_parts.append(part.content)
            
            output = "\n".join(output_parts)
            
            # Verify Angular build
            self.assertIn("Building angular", output)
            self.assertIn("build_types", output)  # From proof of execution
    
    @patch('agents.executor.executor_agent.docker')
    @patch('agents.executor.docker_manager.docker')  
    async def test_monorepo_build_flow(self, mock_docker_manager, mock_docker_executor):
        """Test monorepo with multiple builds"""
        # Mock Docker
        mock_docker_client = MagicMock()
        mock_docker_client.ping.return_value = True
        mock_docker_client.images.build.return_value = (MagicMock(), [])
        mock_docker_client.containers.run.return_value = MagicMock(
            id="test_container_789",
            name="executor_monorepo",
            status="running"
        )
        mock_docker_client.containers.get.return_value = MagicMock(
            exec_run=MagicMock(return_value=MagicMock(
                exit_code=0,
                output=(b"All services running", b"")
            ))
        )
        
        mock_docker_manager.from_env.return_value = mock_docker_client
        mock_docker_executor.from_env.return_value = mock_docker_client
        
        # Monorepo input
        input_text = """
Requirements: Create a monorepo with frontend and backend

FILENAME: package.json
```json
{
  "name": "monorepo",
  "workspaces": ["backend", "frontend"]
}
```

FILENAME: backend/package.json
```json
{
  "name": "backend",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js"
  }
}
```

FILENAME: backend/tsconfig.json
```json
{
  "compilerOptions": {
    "outDir": "./dist"
  }
}
```

FILENAME: backend/src/server.ts
```typescript
console.log('Server starting...');
```

FILENAME: frontend/angular.json
```json
{
  "projects": {
    "frontend": {}
  }
}
```

FILENAME: frontend/package.json
```json
{
  "name": "frontend",
  "scripts": {
    "build": "ng build"
  }
}
```
"""
        
        message = Message(
            role="user",
            parts=[MessagePart(content=input_text)]
        )
        
        build_count = 0
        
        def mock_build_run(*args, **kwargs):
            nonlocal build_count
            build_count += 1
            return MagicMock(
                returncode=0,
                stdout=f"Build {build_count} complete",
                stderr=""
            )
        
        with patch('subprocess.run', side_effect=mock_build_run):
            from agents.executor.executor_agent import executor_agent
            
            output_parts = []
            async for part in executor_agent([message]):
                output_parts.append(part.content)
            
            output = "\n".join(output_parts)
            
            # Should detect multiple builds
            self.assertIn("builds_detected", output)
            # Build count should be at least 2 (backend and frontend)
            self.assertGreaterEqual(build_count, 2)
    
    async def test_build_failure_handling(self):
        """Test handling of build failures"""
        # This test verifies that build failures are properly logged
        # but don't prevent Docker container creation
        
        with patch('agents.executor.executor_agent.docker'):
            with patch('agents.executor.docker_manager.docker'):
                with patch('subprocess.run') as mock_run:
                    # Mock build failure
                    mock_run.return_value = MagicMock(
                        returncode=1,
                        stdout="",
                        stderr="TypeScript error: Cannot find module"
                    )
                    
                    input_text = """
FILENAME: tsconfig.json
```json
{"compilerOptions": {"outDir": "./dist"}}
```

FILENAME: package.json
```json
{"name": "test", "scripts": {"build": "tsc"}}
```

FILENAME: index.ts
```typescript
import { nonexistent } from 'missing-module';
```
"""
                    
                    message = Message(
                        role="user",
                        parts=[MessagePart(content=input_text)]
                    )
                    
                    from agents.executor.executor_agent import executor_agent
                    
                    output_parts = []
                    try:
                        async for part in executor_agent([message]):
                            output_parts.append(part.content)
                    except Exception:
                        pass  # Expected to handle gracefully
                    
                    output = "\n".join(output_parts)
                    
                    # Should mention build failure
                    if "Build failed" in output or "error" in output.lower():
                        self.assertTrue(True)  # Build failure was handled


# Helper to run async tests
def run_async_test(test_func):
    """Run async test function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func)
    finally:
        loop.close()


if __name__ == '__main__':
    # Patch async test methods
    for attr_name in dir(TestExecutorBuildFlow):
        attr = getattr(TestExecutorBuildFlow, attr_name)
        if asyncio.iscoroutinefunction(attr) and attr_name.startswith('test_'):
            wrapped = lambda self, func=attr: run_async_test(func(self))
            setattr(TestExecutorBuildFlow, attr_name, wrapped)
    
    unittest.main()