"""
Unit tests for _parse_code_files function in mvp_incremental workflow
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.mvp_incremental.mvp_incremental import _parse_code_files


class TestParseCodeFiles(unittest.TestCase):
    """Test the _parse_code_files function"""
    
    def test_parse_nested_paths(self):
        """Test parsing files with nested directory paths"""
        code_output = """
```javascript
# filename: backend/src/server.js
const express = require('express');
const app = express();
```

```typescript
# filename: frontend/src/app/app.component.ts
import { Component } from '@angular/core';
```

```json
# filename: backend/package.json
{
  "name": "backend",
  "version": "1.0.0"
}
```
"""
        
        files = _parse_code_files(code_output)
        
        # Should have 3 files
        self.assertEqual(len(files), 3)
        
        # Check correct paths
        self.assertIn('backend/src/server.js', files)
        self.assertIn('frontend/src/app/app.component.ts', files)
        self.assertIn('backend/package.json', files)
        
        # Check content
        self.assertIn('express', files['backend/src/server.js'])
        self.assertIn('@angular/core', files['frontend/src/app/app.component.ts'])
        self.assertIn('"name": "backend"', files['backend/package.json'])
    
    def test_parse_flat_structure(self):
        """Test parsing files without subdirectories"""
        code_output = """
```python
# filename: main.py
def main():
    print("Hello")
```

```python
# filename: utils.py
def helper():
    pass
```
"""
        
        files = _parse_code_files(code_output)
        
        self.assertEqual(len(files), 2)
        self.assertIn('main.py', files)
        self.assertIn('utils.py', files)
    
    def test_parse_mixed_languages(self):
        """Test parsing files with different languages"""
        code_output = """
```javascript
# filename: server.js
const app = express();
```

```python
# filename: scripts/process.py
import pandas as pd
```

```yaml
# filename: docker-compose.yml
version: '3.8'
```

```typescript
# filename: src/types/user.ts
export interface User {}
```
"""
        
        files = _parse_code_files(code_output)
        
        self.assertEqual(len(files), 4)
        self.assertIn('server.js', files)
        self.assertIn('scripts/process.py', files)
        self.assertIn('docker-compose.yml', files)
        self.assertIn('src/types/user.ts', files)
    
    def test_parse_deeply_nested(self):
        """Test parsing deeply nested paths"""
        code_output = """
```javascript
# filename: src/modules/auth/controllers/auth.controller.js
class AuthController {}
```

```javascript
# filename: tests/unit/modules/auth/controllers/auth.controller.test.js
describe('AuthController', () => {});
```
"""
        
        files = _parse_code_files(code_output)
        
        self.assertIn('src/modules/auth/controllers/auth.controller.js', files)
        self.assertIn('tests/unit/modules/auth/controllers/auth.controller.test.js', files)
    
    def test_parse_structured_format(self):
        """Test parsing the old structured format"""
        code_output = """
--- IMPLEMENTATION DETAILS ---

FILENAME: calculator.py
```python
class Calculator:
    pass
```

FILENAME: test_calculator.py
```python
import unittest
```
"""
        
        files = _parse_code_files(code_output)
        
        self.assertEqual(len(files), 2)
        self.assertIn('calculator.py', files)
        self.assertIn('test_calculator.py', files)
    
    def test_fallback_parsing(self):
        """Test fallback parsing for old formats"""
        code_output = """
```python calculator.py
def add(a, b):
    return a + b
```

```javascript
console.log("No filename specified");
```
"""
        
        files = _parse_code_files(code_output)
        
        # Should have calculator.py from explicit name
        self.assertIn('calculator.py', files)
        self.assertIn('def add', files['calculator.py'])
        
        # Should have module_1.py as default for unnamed file (second file)
        self.assertIn('module_1.py', files)
        self.assertIn('console.log', files['module_1.py'])
    
    def test_no_code_blocks(self):
        """Test handling when no code blocks are found"""
        code_output = "This is just plain text without any code blocks"
        
        files = _parse_code_files(code_output)
        
        # Should treat entire output as main.py
        self.assertEqual(len(files), 1)
        self.assertIn('main.py', files)
        self.assertEqual(files['main.py'], code_output.strip())
    
    def test_skip_project_created_output(self):
        """Test that PROJECT CREATED output is skipped"""
        code_output = """
✅ PROJECT CREATED
📁 Location: /some/path
📄 Files created: 5
"""
        
        files = _parse_code_files(code_output)
        
        # Should be empty since this is metadata, not code
        self.assertEqual(len(files), 0)
    
    def test_windows_paths(self):
        """Test handling Windows-style paths"""
        code_output = r"""
```python
# filename: backend\src\main.py
print("Windows path")
```
"""
        
        files = _parse_code_files(code_output)
        
        # Should normalize to forward slashes
        self.assertIn('backend\\src\\main.py', files)
        # Note: Path normalization happens in code_saver, not parser


if __name__ == '__main__':
    unittest.main()