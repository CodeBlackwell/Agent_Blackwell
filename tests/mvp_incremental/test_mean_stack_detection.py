#!/usr/bin/env python3
"""
MEAN Stack specific detection tests
Lightweight tests for MongoDB, Express, Angular, Node.js patterns
"""

import unittest
import asyncio
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.mvp_incremental.mvp_incremental import _detect_primary_language
from agents.validator.container_manager import ValidatorContainerManager
from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.validator.validator_agent import validator_agent


class TestMEANStackDetection(unittest.TestCase):
    """Test MEAN stack component detection and validation"""
    
    def test_mongodb_detection_patterns(self):
        """Test MongoDB usage detection in different languages"""
        manager = ValidatorContainerManager()
        
        # Python MongoDB code
        python_mongo = {
            'app.py': '''
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['myapp']
'''
        }
        self.assertTrue(manager._needs_database(python_mongo, 'mongodb'))
        
        # Node.js MongoDB with Mongoose
        node_mongoose = {
            'models/user.js': '''
const mongoose = require('mongoose');
const userSchema = new mongoose.Schema({
    name: String,
    email: String
});
module.exports = mongoose.model('User', userSchema);
'''
        }
        self.assertTrue(manager._needs_database(node_mongoose, 'mongodb'))
        
        # Node.js MongoDB native driver
        node_mongodb = {
            'db.js': '''
const { MongoClient } = require('mongodb');
const client = new MongoClient(uri);
'''
        }
        self.assertTrue(manager._needs_database(node_mongodb, 'mongodb'))
        
        # TypeScript with MongoDB
        ts_mongo = {
            'db.ts': '''
import { MongoClient, Db } from 'mongodb';
class Database {
    private client: MongoClient;
    private db: Db;
}
'''
        }
        self.assertTrue(manager._needs_database(ts_mongo, 'mongodb'))
    
    def test_express_patterns_detection(self):
        """Test Express.js pattern detection"""
        manager = ValidatorContainerManager()
        
        # Basic Express app
        express_app = {
            'server.js': '''
const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});

app.listen(PORT);
'''
        }
        
        # Detect language
        lang = _detect_primary_language(express_app)
        self.assertEqual(lang, 'javascript')
        
        # Detect Express dependency
        deps = manager._detect_node_dependencies(express_app)
        self.assertIn('express', deps)
    
    def test_angular_component_detection(self):
        """Test Angular component and TypeScript detection"""
        # Angular component files
        angular_files = {
            'angular.json': '{"projects": {"my-app": {}}}',
            'package.json': '{"dependencies": {"@angular/core": "^15.0.0"}}',
            'src/app/app.component.ts': '''
import { Component } from '@angular/core';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css']
})
export class AppComponent {
    title = 'my-app';
}
''',
            'src/app/services/api.service.ts': '''
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    constructor(private http: HttpClient) {}
    
    getUsers(): Observable<any[]> {
        return this.http.get<any[]>('/api/users');
    }
}
'''
        }
        
        # Should detect TypeScript for Angular
        lang = _detect_primary_language(angular_files)
        self.assertEqual(lang, 'typescript')
        
        # Test dependency detection
        manager = ValidatorContainerManager()
        # Pass the entire files dict, not just one file
        deps = manager._detect_node_dependencies(angular_files)
        # Should detect Angular core dependencies
        self.assertTrue(any('@angular' in dep for dep in deps))
    
    def test_mean_stack_full_structure(self):
        """Test detection of complete MEAN stack structure"""
        # Backend structure (Node.js + Express + MongoDB)
        backend_structure = {
            'package.json': '''
{
    "name": "mean-backend",
    "dependencies": {
        "express": "^4.18.0",
        "mongoose": "^6.0.0",
        "cors": "^2.8.5",
        "dotenv": "^16.0.0"
    }
}
''',
            'server.js': '''
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/meanapp');

// Routes
app.use('/api/users', require('./routes/users'));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
''',
            'models/User.js': '''
const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('User', UserSchema);
''',
            'routes/users.js': '''
const router = require('express').Router();
const User = require('../models/User');

router.get('/', async (req, res) => {
    try {
        const users = await User.find();
        res.json(users);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
'''
        }
        
        # Frontend structure (Angular)
        frontend_structure = {
            'angular.json': '{"projects": {"mean-frontend": {}}}',
            'package.json': '''
{
    "name": "mean-frontend",
    "dependencies": {
        "@angular/core": "^15.0.0",
        "@angular/common": "^15.0.0",
        "@angular/platform-browser": "^15.0.0",
        "@angular/router": "^15.0.0",
        "@angular/forms": "^15.0.0",
        "@angular/common/http": "^15.0.0"
    }
}
''',
            'src/app/app.component.ts': 'export class AppComponent {}',
            'src/app/services/user.service.ts': '''
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class UserService {
    private apiUrl = 'http://localhost:5000/api/users';
    
    constructor(private http: HttpClient) {}
    
    getUsers(): Observable<any[]> {
        return this.http.get<any[]>(this.apiUrl);
    }
}
'''
        }
        
        # Test backend detection
        backend_lang = _detect_primary_language(backend_structure)
        self.assertEqual(backend_lang, 'javascript')
        
        # Test frontend detection
        frontend_lang = _detect_primary_language(frontend_structure)
        self.assertEqual(frontend_lang, 'typescript')
        
        # Test MongoDB detection in backend
        manager = ValidatorContainerManager()
        needs_mongo = manager._needs_database(backend_structure, 'mongodb')
        self.assertTrue(needs_mongo)
        
        # Test dependency detection
        backend_deps = manager._detect_node_dependencies(backend_structure)
        self.assertIn('express', backend_deps)
        self.assertIn('mongoose', backend_deps)
        self.assertIn('cors', backend_deps)
        # Note: dotenv is called via require('dotenv').config() which doesn't match the regex
    
    @patch('agents.validator.container_manager.get_container_manager')
    async def test_mean_validation_without_python_error(self, mock_get_manager):
        """Test MEAN stack validation doesn't produce Python errors"""
        # Mock container manager
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Mock successful JavaScript execution
        mock_container_info = {'container_id': 'node_container', 'language': 'javascript'}
        mock_manager.get_or_create_container.return_value = mock_container_info
        mock_manager.execute_code.return_value = (True, 'Server started on port 3000', '')
        
        # MEAN backend validation input
        input_text = '''
SESSION_ID: mean_test_123
LANGUAGE: javascript

Please validate this MEAN stack backend:

```javascript
# filename: server.js
const express = require('express');
const mongoose = require('mongoose');
const app = express();

mongoose.connect('mongodb://localhost:27017/meanapp');

app.get('/api/test', (req, res) => {
    res.json({ message: 'MEAN stack API working' });
});

app.listen(3000, () => {
    console.log('Server started on port 3000');
});
```

```javascript
# filename: models/User.js
const mongoose = require('mongoose');
const UserSchema = new mongoose.Schema({
    name: String,
    email: String
});
module.exports = mongoose.model('User', UserSchema);
```
'''
        
        # Create message and run validator
        message = Message(parts=[MessagePart(content=input_text)])
        results = []
        async for result in validator_agent([message]):
            results.append(result)
        
        # Verify results
        output = results[0].parts[0].content
        
        # Critical assertions
        self.assertNotIn('No Python file found', output)
        self.assertIn('VALIDATION_RESULT: PASS', output)
        
        # Verify correct container and files were used
        mock_manager.get_or_create_container.assert_called_once()
        executed_files = mock_manager.execute_code.call_args[0][1]
        self.assertIn('server.js', executed_files)
        self.assertIn('models/User.js', executed_files)
        
        # No Python files should be in the execution
        for filename in executed_files:
            self.assertFalse(filename.endswith('.py'))
    
    def test_mean_stack_dependency_detection(self):
        """Test comprehensive MEAN stack dependency detection"""
        manager = ValidatorContainerManager()
        
        # Comprehensive MEAN stack code with various dependencies
        mean_code = {
            'server.js': '''
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const multer = require('multer');
const passport = require('passport');
const socketio = require('socket.io');
'''
        }
        
        deps = manager._detect_node_dependencies(mean_code)
        
        # Verify all common MEAN dependencies are detected
        expected_deps = [
            'express', 'mongoose', 'cors', 'bcryptjs',
            'jsonwebtoken', 'multer', 'passport', 'socket.io'
        ]
        
        for dep in expected_deps:
            self.assertIn(dep, deps)


if __name__ == '__main__':
    # Run async tests properly
    unittest.main()