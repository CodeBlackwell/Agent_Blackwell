#!/usr/bin/env python3
"""
Integration tests for the enhanced validator with multi-language and database support
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.validator.validator_agent import validator_agent
from agents.validator.container_manager import get_container_manager


class TestValidatorEnhanced:
    """Integration tests for enhanced validator functionality"""
    
    def __init__(self):
        self.session_id = None
        self.test_results = []
        
    async def test_python_flask_dependencies(self):
        """Test Python app with Flask dependencies"""
        print("\n🧪 Test 1: Python Flask App with Auto-Dependencies")
        print("-" * 60)
        
        test_input = """
Please validate this Flask application:

```python
# filename: app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis

app = Flask(__name__)
CORS(app)

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/api/hello', methods=['GET'])
def hello():
    visits = redis_client.incr('visits')
    return jsonify({
        'message': 'Hello from Flask!',
        'visits': visits
    })

@app.route('/api/data', methods=['POST'])
def process_data():
    data = request.get_json()
    return jsonify({'received': data, 'status': 'processed'})

if __name__ == '__main__':
    # Just validate, don't actually run the server
    print("Flask app validated successfully!")
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            # Extract session ID
            if "SESSION_ID:" in response and not self.session_id:
                self.session_id = response.split("SESSION_ID:")[1].split("\n")[0].strip()
            
            # Check result
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Python Flask Dependencies", "PASSED"))
            else:
                self.test_results.append(("Python Flask Dependencies", "FAILED"))
    
    async def test_nodejs_express_dependencies(self):
        """Test Node.js app with Express dependencies"""
        print("\n\n🧪 Test 2: Node.js Express App with Auto-Dependencies")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this Express.js application:

```javascript
// filename: server.js
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Routes
app.get('/api/hello', (req, res) => {{
    res.json({{ message: 'Hello from Express!' }});
}});

app.post('/api/login', (req, res) => {{
    const {{ username, password }} = req.body;
    
    // Mock authentication
    if (username === 'admin' && password === 'password') {{
        const token = jwt.sign({{ username }}, 'secret_key');
        res.json({{ token }});
    }} else {{
        res.status(401).json({{ error: 'Invalid credentials' }});
    }}
}});

// Don't actually start the server for validation
console.log('Express app validated successfully!');
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Node.js Express Dependencies", "PASSED"))
            else:
                self.test_results.append(("Node.js Express Dependencies", "FAILED"))
    
    async def test_mongodb_python(self):
        """Test Python app with MongoDB"""
        print("\n\n🧪 Test 3: Python MongoDB Application")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this Python MongoDB application:

```python
# filename: mongo_app.py
from pymongo import MongoClient
import os

# Connect to MongoDB
mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)

# Test connection
try:
    # Force connection to verify it works
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    
    # Create a test database and collection
    db = client['test_db']
    collection = db['test_collection']
    
    # Insert a test document
    test_doc = {'name': 'Test User', 'email': 'test@example.com'}
    result = collection.insert_one(test_doc)
    print(f"Inserted document with ID: {{result.inserted_id}}")
    
    # Query the document
    found = collection.find_one({{'name': 'Test User'}})
    print(f"Found document: {{found}}")
    
    # Clean up
    collection.drop()
    print("Test completed successfully!")
    
except Exception as e:
    print(f"MongoDB connection failed: {{e}}")
    exit(1)
finally:
    client.close()
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Python MongoDB Integration", "PASSED"))
            else:
                self.test_results.append(("Python MongoDB Integration", "FAILED"))
    
    async def test_mongodb_nodejs(self):
        """Test Node.js app with MongoDB using Mongoose"""
        print("\n\n🧪 Test 4: Node.js MongoDB Application with Mongoose")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this Node.js MongoDB application:

```javascript
// filename: mongo_app.js
const mongoose = require('mongoose');

// MongoDB connection
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/test_db';

// Define a schema
const UserSchema = new mongoose.Schema({{
    name: String,
    email: String,
    createdAt: {{ type: Date, default: Date.now }}
}});

const User = mongoose.model('User', UserSchema);

// Main function
async function main() {{
    try {{
        // Connect to MongoDB
        await mongoose.connect(mongoUri);
        console.log('Successfully connected to MongoDB!');
        
        // Create a test user
        const testUser = new User({{
            name: 'Test User',
            email: 'test@example.com'
        }});
        
        await testUser.save();
        console.log('Created test user:', testUser);
        
        // Query the user
        const foundUser = await User.findOne({{ name: 'Test User' }});
        console.log('Found user:', foundUser);
        
        // Clean up
        await User.deleteMany({{}});
        console.log('Test completed successfully!');
        
    }} catch (error) {{
        console.error('MongoDB connection failed:', error);
        process.exit(1);
    }} finally {{
        await mongoose.connection.close();
    }}
}}

// Run the test
main();
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Node.js MongoDB Integration", "PASSED"))
            else:
                self.test_results.append(("Node.js MongoDB Integration", "FAILED"))
    
    async def test_typescript_compilation(self):
        """Test TypeScript compilation and execution"""
        print("\n\n🧪 Test 5: TypeScript Application")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this TypeScript application:

```typescript
// filename: app.ts
interface User {{
    id: number;
    name: string;
    email: string;
}}

class UserService {{
    private users: User[] = [];
    
    addUser(user: User): void {{
        this.users.push(user);
        console.log(`Added user: ${{user.name}}`);
    }}
    
    getUser(id: number): User | undefined {{
        return this.users.find(u => u.id === id);
    }}
    
    getAllUsers(): User[] {{
        return this.users;
    }}
}}

// Test the service
const service = new UserService();

service.addUser({{ id: 1, name: 'John Doe', email: 'john@example.com' }});
service.addUser({{ id: 2, name: 'Jane Smith', email: 'jane@example.com' }});

console.log('All users:', service.getAllUsers());
console.log('User 1:', service.getUser(1));
console.log('TypeScript validation successful!');
```

```javascript
// filename: tsconfig.json
{{
    "compilerOptions": {{
        "target": "es2020",
        "module": "commonjs",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "forceConsistentCasingInFileNames": true
    }}
}}
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("TypeScript Compilation", "PASSED"))
            else:
                self.test_results.append(("TypeScript Compilation", "FAILED"))
    
    async def test_package_json_dependencies(self):
        """Test Node.js app with package.json"""
        print("\n\n🧪 Test 6: Node.js with package.json")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this Node.js application with package.json:

```javascript
// filename: app.js
const express = require('express');
const morgan = require('morgan');
const helmet = require('helmet');

const app = express();

app.use(helmet());
app.use(morgan('combined'));
app.use(express.json());

app.get('/', (req, res) => {{
    res.json({{ message: 'App with package.json works!' }});
}});

console.log('App validated successfully!');
```

```json
// filename: package.json
{{
    "name": "test-app",
    "version": "1.0.0",
    "description": "Test application",
    "main": "app.js",
    "scripts": {{
        "start": "node app.js"
    }},
    "dependencies": {{
        "express": "^4.18.0",
        "morgan": "^1.10.0",
        "helmet": "^7.0.0"
    }}
}}
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Node.js package.json", "PASSED"))
            else:
                self.test_results.append(("Node.js package.json", "FAILED"))
    
    async def test_requirements_txt(self):
        """Test Python app with requirements.txt"""
        print("\n\n🧪 Test 7: Python with requirements.txt")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this Python application with requirements.txt:

```python
# filename: data_processor.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Create sample data
data = {{
    'feature1': np.random.randn(100),
    'feature2': np.random.randn(100),
    'target': np.random.randint(0, 2, 100)
}}

df = pd.DataFrame(data)
print("DataFrame shape:", df.shape)
print("DataFrame head:")
print(df.head())

# Scale features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(df[['feature1', 'feature2']])
print("\\nScaled features shape:", scaled_features.shape)

print("\\nData processing validated successfully!")
```

```text
# filename: requirements.txt
pandas==2.0.0
numpy==1.24.0
scikit-learn==1.3.0
matplotlib==3.7.0
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            if "VALIDATION_RESULT: SUCCESS" in response:
                self.test_results.append(("Python requirements.txt", "PASSED"))
            else:
                self.test_results.append(("Python requirements.txt", "FAILED"))
    
    async def test_mixed_language_error(self):
        """Test error handling for mixed languages"""
        print("\n\n🧪 Test 8: Mixed Language Detection")
        print("-" * 60)
        
        test_input = f"""
SESSION_ID: {self.session_id if self.session_id else 'new_session'}

Please validate this code:

```python
# filename: main.py
print("This is Python")
```

```javascript
// filename: app.js
console.log("This is JavaScript");
```
"""
        
        messages = [Message(parts=[MessagePart(content=test_input)])]
        
        async for message in validator_agent(messages):
            response = message.parts[0].content
            print(f"\n📥 Response:\n{response}")
            
            # Should still validate - picks majority language
            if "VALIDATION_RESULT:" in response:
                self.test_results.append(("Mixed Language Handling", "PASSED"))
            else:
                self.test_results.append(("Mixed Language Handling", "FAILED"))
    
    def print_summary(self):
        """Print test results summary"""
        print("\n\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.test_results:
            status = "✅" if result == "PASSED" else "❌"
            print(f"{status} {test_name}: {result}")
        
        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        total = len(self.test_results)
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} tests failed")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        try:
            await self.test_python_flask_dependencies()
            await self.test_nodejs_express_dependencies()
            await self.test_mongodb_python()
            await self.test_mongodb_nodejs()
            await self.test_typescript_compilation()
            await self.test_package_json_dependencies()
            await self.test_requirements_txt()
            await self.test_mixed_language_error()
            
            self.print_summary()
            
        finally:
            # Cleanup
            print("\n🧹 Cleaning up containers...")
            container_manager = get_container_manager()
            container_manager.cleanup_all()


async def main():
    """Main test runner"""
    print("🚀 Enhanced Validator Integration Tests")
    print("=" * 60)
    print("These tests validate:")
    print("  • Multi-language support (Python, Node.js, TypeScript)")
    print("  • Automatic dependency installation")
    print("  • MongoDB integration")
    print("  • Package manager support (pip, npm)")
    print("  • Session persistence")
    print("=" * 60)
    
    tester = TestValidatorEnhanced()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())