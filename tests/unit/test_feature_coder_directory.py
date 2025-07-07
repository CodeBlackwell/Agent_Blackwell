"""
Unit tests for feature_coder_agent directory structure support
Tests the agent's ability to handle nested file paths and project structures
"""

import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.feature_coder.feature_coder_agent import feature_coder_agent


class TestFeatureCoderDirectory(unittest.TestCase):
    """Test feature coder's directory structure handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up"""
        self.loop.close()
    
    def test_parse_nested_file_paths(self):
        """Test parsing of nested file paths from agent output"""
        test_output = """
```javascript
# filename: backend/src/server.js
const express = require('express');
const app = express();
app.listen(3000);
```

```javascript
# filename: frontend/src/app.js
console.log('Frontend app');
```

```json
# filename: backend/package.json
{
  "name": "backend",
  "version": "1.0.0"
}
```
"""
        
        # Parse the output to extract file paths
        files = self._parse_agent_output(test_output)
        
        # Verify nested paths are correctly parsed
        self.assertIn('backend/src/server.js', files)
        self.assertIn('frontend/src/app.js', files)
        self.assertIn('backend/package.json', files)
        
        # Verify content is preserved
        self.assertIn("const express", files['backend/src/server.js'])
        self.assertIn("console.log", files['frontend/src/app.js'])
        self.assertIn('"name": "backend"', files['backend/package.json'])
    
    def test_mean_stack_structure(self):
        """Test MEAN stack project structure generation"""
        test_output = """
```typescript
# filename: backend/src/app.ts
import express from 'express';
import mongoose from 'mongoose';

const app = express();
export default app;
```

```typescript
# filename: frontend/src/app/app.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: '<h1>MEAN App</h1>'
})
export class AppComponent {}
```

```yaml
# filename: docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
  frontend:
    build: ./frontend
  mongodb:
    image: mongo:5.0
```
"""
        
        files = self._parse_agent_output(test_output)
        
        # Verify proper MEAN structure
        self.assertIn('backend/src/app.ts', files)
        self.assertIn('frontend/src/app/app.component.ts', files)
        self.assertIn('docker-compose.yml', files)
        
        # Verify TypeScript content
        self.assertIn("import express from 'express'", files['backend/src/app.ts'])
        self.assertIn("@Component", files['frontend/src/app/app.component.ts'])
    
    def test_deeply_nested_paths(self):
        """Test handling of deeply nested directory structures"""
        test_output = """
```javascript
# filename: src/modules/auth/controllers/auth.controller.js
class AuthController {
  login() { return 'login'; }
}
module.exports = AuthController;
```

```javascript
# filename: src/modules/auth/services/auth.service.js
class AuthService {
  authenticate() { return true; }
}
module.exports = AuthService;
```

```javascript
# filename: tests/unit/modules/auth/auth.test.js
describe('Auth', () => {
  test('should work', () => {});
});
```
"""
        
        files = self._parse_agent_output(test_output)
        
        # Verify deep nesting works
        self.assertIn('src/modules/auth/controllers/auth.controller.js', files)
        self.assertIn('src/modules/auth/services/auth.service.js', files)
        self.assertIn('tests/unit/modules/auth/auth.test.js', files)
    
    def test_windows_style_paths(self):
        """Test handling of Windows-style paths"""
        test_output = """
```python
# filename: backend\\src\\main.py
print("Windows path test")
```

```python
# filename: backend\\tests\\test_main.py
def test_main():
    pass
```
"""
        
        files = self._parse_agent_output(test_output)
        
        # Should normalize to forward slashes
        self.assertIn('backend/src/main.py', files)
        self.assertIn('backend/tests/test_main.py', files)
    
    @patch('agents.feature_coder.feature_coder_agent.ChatModel')
    @patch('agents.feature_coder.feature_coder_agent.ReActAgent')
    def test_agent_handles_mean_requirements(self, mock_react_agent, mock_chat_model):
        """Test that agent correctly processes MEAN stack requirements"""
        # Mock the agent response
        mock_agent_instance = AsyncMock()
        mock_react_agent.return_value = mock_agent_instance
        
        # Create a mock response that includes directory structure
        mock_response = Mock()
        mock_response.result.text = """
```javascript
# filename: backend/server.js
const express = require('express');
const app = express();
```

```typescript
# filename: frontend/src/app/app.module.ts
import { NgModule } from '@angular/core';
```
"""
        mock_agent_instance.run.return_value = mock_response
        
        # Test input simulating MEAN stack requirements
        test_input = [Message(parts=[MessagePart(content="""
        Create a MEAN stack application with:
        - Backend API in backend/ directory
        - Frontend Angular app in frontend/ directory
        - Shared types in shared/ directory
        """)])]
        
        # Run the agent
        result = self.loop.run_until_complete(
            self._run_agent_async(test_input)
        )
        
        # Verify the response includes directory structure
        self.assertIn('backend/server.js', result)
        self.assertIn('frontend/src/app/app.module.ts', result)
    
    async def _run_agent_async(self, input_messages):
        """Helper to run agent and collect output"""
        result = ""
        async for message in feature_coder_agent(input_messages):
            result += message.parts[0].content
        return result
    
    def _parse_agent_output(self, output: str) -> dict:
        """
        Parse agent output to extract files with paths.
        This simulates what the enhanced code_saver will do.
        """
        import re
        
        files = {}
        
        # Pattern to match code blocks with filenames
        pattern = r'```\w*\s*\n#\s*filename:\s*([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, output, re.DOTALL)
        
        for filename, content in matches:
            # Normalize path separators
            filename = filename.strip().replace('\\', '/')
            files[filename] = content.strip()
        
        return files


class TestFeatureCoderIntegration(unittest.TestCase):
    """Integration tests for feature coder with real workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up"""
        self.loop.close()
    
    def test_microservices_structure(self):
        """Test microservices architecture structure"""
        test_output = """
```javascript
# filename: services/user-service/src/index.js
const express = require('express');
const app = express();
app.listen(3001);
```

```javascript
# filename: services/order-service/src/index.js
const express = require('express');
const app = express();
app.listen(3002);
```

```javascript
# filename: services/api-gateway/src/index.js
const gateway = require('express-gateway');
gateway.load('/config/gateway.config.yml');
```

```yaml
# filename: docker-compose.yml
version: '3.8'
services:
  user-service:
    build: ./services/user-service
  order-service:
    build: ./services/order-service
  api-gateway:
    build: ./services/api-gateway
```
"""
        
        files = self._parse_output(test_output)
        
        # Verify microservices structure
        self.assertEqual(len(files), 4)
        self.assertIn('services/user-service/src/index.js', files)
        self.assertIn('services/order-service/src/index.js', files)
        self.assertIn('services/api-gateway/src/index.js', files)
        self.assertIn('docker-compose.yml', files)
    
    def _parse_output(self, output: str) -> dict:
        """Parse output helper"""
        import re
        
        files = {}
        pattern = r'```\w*\s*\n#\s*filename:\s*([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, output, re.DOTALL)
        
        for filename, content in matches:
            filename = filename.strip().replace('\\', '/')
            files[filename] = content.strip()
        
        return files


if __name__ == '__main__':
    unittest.main()