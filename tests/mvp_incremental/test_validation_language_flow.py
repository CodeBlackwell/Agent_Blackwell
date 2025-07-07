#!/usr/bin/env python3
"""
Test the complete validation flow with mocked components
Ensures language detection and validation work correctly without full execution
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.validator.validator_agent import validator_agent, extract_code_files


class TestValidationLanguageFlow(unittest.TestCase):
    """Test complete validation flow with language awareness"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up event loop"""
        self.loop.close()
    
    def test_extract_code_files(self):
        """Test code file extraction from validator input"""
        # Test Python file extraction
        python_input = '''
Here's the implementation:

```python
# filename: calculator.py
class Calculator:
    def add(self, a, b):
        return a + b
```

```python
# filename: test_calculator.py
import unittest
from calculator import Calculator
```
'''
        
        files = extract_code_files(python_input)
        self.assertEqual(len(files), 2)
        self.assertIn('calculator.py', files)
        self.assertIn('test_calculator.py', files)
        self.assertIn('class Calculator:', files['calculator.py'])
        
        # Test JavaScript file extraction
        js_input = '''
Implementation:

```javascript
# filename: server.js
const express = require('express');
const app = express();
```

```js
# filename: routes/api.js
module.exports = (app) => {
    app.get('/api/users', getUsers);
};
```
'''
        
        files = extract_code_files(js_input)
        self.assertEqual(len(files), 2)
        self.assertIn('server.js', files)
        self.assertIn('routes/api.js', files)
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_python_validation_flow(self, mock_get_manager):
        """Test Python code validation flow"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock container
        mock_container_info = {'container_id': 'python_container', 'language': 'python'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (True, 'Tests passed', '')
        
        # Create validator input
        input_text = '''
SESSION_ID: test_python_123

Please validate this code implementation:

```python
# filename: calculator.py
class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
```
'''
        
        # Create message input
        message = Message(parts=[MessagePart(content=input_text)])
        
        # Run validator
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify results
        self.assertEqual(len(results), 1)
        output = results[0].parts[0].content
        
        self.assertIn('SESSION_ID: test_python_123', output)
        self.assertIn('VALIDATION_RESULT: PASS', output)
        
        # Verify Python container was requested
        mock_manager.get_or_create_container.assert_called_once()
        call_args = mock_manager.get_or_create_container.call_args
        self.assertEqual(call_args[0][0], 'test_python_123')
        
        # Verify correct files were executed
        mock_manager.execute_code.assert_called_once()
        executed_files = mock_manager.execute_code.call_args[0][1]
        self.assertIn('calculator.py', executed_files)
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_javascript_validation_flow(self, mock_get_manager):
        """Test JavaScript code validation flow with language hint"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock container
        mock_container_info = {'container_id': 'node_container', 'language': 'javascript'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (True, 'Server started', '')
        
        # Create validator input with language hint
        input_text = '''
SESSION_ID: test_js_456
LANGUAGE: javascript

Please validate this Express.js implementation:

```javascript
# filename: server.js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.json({ message: 'Hello World' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```
'''
        
        # Create message input
        message = Message(parts=[MessagePart(content=input_text)])
        
        # Run validator
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify results
        self.assertEqual(len(results), 1)
        output = results[0].parts[0].content
        
        self.assertIn('VALIDATION_RESULT: PASS', output)
        
        # Verify execute_code was called with JavaScript files
        mock_manager.execute_code.assert_called_once()
        executed_files = mock_manager.execute_code.call_args[0][1]
        self.assertIn('server.js', executed_files)
        self.assertIn('express', executed_files['server.js'])
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_typescript_validation_with_hint(self, mock_get_manager):
        """Test TypeScript validation with language hint"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock container
        mock_container_info = {'container_id': 'ts_container', 'language': 'typescript'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (True, 'Compiled successfully', '')
        
        # Create validator input with TypeScript hint
        input_text = '''
SESSION_ID: test_ts_789
LANGUAGE: typescript

Please validate this TypeScript implementation:

```typescript
# filename: app.ts
interface User {
    id: number;
    name: string;
    email: string;
}

class UserService {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }
    
    getUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}

export { UserService, User };
```
'''
        
        # Create message input
        message = Message(parts=[MessagePart(content=input_text)])
        
        # Run validator
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify results
        output = results[0].parts[0].content
        self.assertIn('VALIDATION_RESULT: PASS', output)
        
        # Verify TypeScript files were processed
        executed_files = mock_manager.execute_code.call_args[0][1]
        self.assertIn('index.ts', executed_files)  # Language hint adds index.ts
        self.assertIn('app.ts', executed_files)
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_validation_error_handling(self, mock_get_manager):
        """Test validation error handling and reporting"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock container with execution error
        mock_container_info = {'container_id': 'error_container', 'language': 'python'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (False, '', 'SyntaxError: invalid syntax')
        
        # Create validator input with syntax error
        input_text = '''
Please validate this code:

```python
# filename: broken.py
def broken_function(
    print("Missing closing parenthesis"
```
'''
        
        # Create message input
        message = Message(parts=[MessagePart(content=input_text)])
        
        # Run validator
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify error handling
        output = results[0].parts[0].content
        self.assertIn('VALIDATION_RESULT: FAIL', output)
        self.assertIn('SyntaxError', output)
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_no_python_file_error_avoided(self, mock_get_manager):
        """Test that JavaScript files don't trigger 'No Python file found' error"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock container
        mock_container_info = {'container_id': 'js_container', 'language': 'javascript'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (True, 'Running', '')
        
        # Create JavaScript-only input
        input_text = '''
LANGUAGE: javascript

Validate this Node.js code:

```javascript
# filename: index.js
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end('Hello World');
});
server.listen(3000);
```
'''
        
        # Create message input
        message = Message(parts=[MessagePart(content=input_text)])
        
        # Run validator
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify NO "No Python file found" error
        output = results[0].parts[0].content
        self.assertNotIn('No Python file found', output)
        self.assertIn('VALIDATION_RESULT: PASS', output)
        
        # Verify correct files were passed to execute_code
        executed_files = mock_manager.execute_code.call_args[0][1]
        self.assertIn('index.js', executed_files)
        self.assertNotIn('.py', str(executed_files))  # No Python files


if __name__ == '__main__':
    unittest.main()