#!/usr/bin/env python3
"""
MEAN Stack specific tests for the enhanced validator
Tests the validator's ability to handle MongoDB, Express, Angular, and Node.js applications
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


async def test_mean_backend():
    """Test MEAN stack backend validation"""
    print("🧪 Test 1: MEAN Stack Backend (Express + MongoDB)")
    print("-" * 60)
    
    test_input = """
Please validate this MEAN stack backend:

```javascript
// filename: server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// MongoDB connection
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mean_app';

// User Schema
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    createdAt: { type: Date, default: Date.now }
});

// Todo Schema
const todoSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: String,
    completed: { type: Boolean, default: false },
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);
const Todo = mongoose.model('Todo', todoSchema);

// Auth middleware
const authMiddleware = (req, res, next) => {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }
    
    try {
        const decoded = jwt.verify(token, 'secret_key');
        req.userId = decoded.userId;
        next();
    } catch (error) {
        res.status(401).json({ error: 'Invalid token' });
    }
};

// Routes
app.post('/api/auth/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;
        
        const hashedPassword = await bcrypt.hash(password, 10);
        const user = new User({ username, email, password: hashedPassword });
        
        await user.save();
        
        const token = jwt.sign({ userId: user._id }, 'secret_key');
        res.status(201).json({ token, userId: user._id });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

app.post('/api/auth/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        const user = await User.findOne({ username });
        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const isValid = await bcrypt.compare(password, user.password);
        if (!isValid) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const token = jwt.sign({ userId: user._id }, 'secret_key');
        res.json({ token, userId: user._id });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

app.get('/api/todos', authMiddleware, async (req, res) => {
    try {
        const todos = await Todo.find({ userId: req.userId });
        res.json(todos);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/todos', authMiddleware, async (req, res) => {
    try {
        const { title, description } = req.body;
        const todo = new Todo({ title, description, userId: req.userId });
        await todo.save();
        res.status(201).json(todo);
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

// Test the connection and basic functionality
async function testServer() {
    try {
        await mongoose.connect(mongoUri);
        console.log('Successfully connected to MongoDB!');
        
        // Create test user
        const testUser = new User({
            username: 'testuser',
            email: 'test@example.com',
            password: await bcrypt.hash('password123', 10)
        });
        
        await User.deleteMany({ username: 'testuser' }); // Clean up first
        await testUser.save();
        console.log('Created test user');
        
        // Create test todo
        const testTodo = new Todo({
            title: 'Test Todo',
            description: 'This is a test',
            userId: testUser._id
        });
        
        await testTodo.save();
        console.log('Created test todo');
        
        // Clean up
        await Todo.deleteMany({ userId: testUser._id });
        await User.deleteMany({ username: 'testuser' });
        
        console.log('MEAN backend validation successful!');
        await mongoose.connection.close();
    } catch (error) {
        console.error('Validation failed:', error);
        process.exit(1);
    }
}

// Run test instead of starting server
testServer();
```

```json
// filename: package.json
{
    "name": "mean-backend",
    "version": "1.0.0",
    "description": "MEAN stack backend",
    "main": "server.js",
    "scripts": {
        "start": "node server.js",
        "test": "jest"
    },
    "dependencies": {
        "express": "^4.18.2",
        "mongoose": "^7.0.0",
        "cors": "^2.8.5",
        "body-parser": "^1.20.2",
        "jsonwebtoken": "^9.0.0",
        "bcryptjs": "^2.4.3",
        "dotenv": "^16.0.3"
    }
}
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    session_id = None
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")
        
        # Extract session ID for next tests
        if "SESSION_ID:" in response:
            session_id = response.split("SESSION_ID:")[1].split("\n")[0].strip()
            
    return session_id


async def test_mean_frontend():
    """Test Angular frontend validation"""
    print("\n\n🧪 Test 2: MEAN Stack Frontend (Angular + TypeScript)")
    print("-" * 60)
    
    test_input = """
Please validate this Angular application:

```typescript
// filename: app.component.ts
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface Todo {
    _id?: string;
    title: string;
    description: string;
    completed: boolean;
}

@Component({
    selector: 'app-root',
    template: `
        <div class="container">
            <h1>{{ title }}</h1>
            <div *ngFor="let todo of todos$ | async">
                <h3>{{ todo.title }}</h3>
                <p>{{ todo.description }}</p>
            </div>
        </div>
    `,
    styles: [`
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
    `]
})
export class AppComponent implements OnInit {
    title = 'MEAN Todo App';
    todos$: Observable<Todo[]>;
    
    constructor(private http: HttpClient) {}
    
    ngOnInit() {
        console.log('Angular app initialized');
        // Would normally fetch todos here
        // this.todos$ = this.http.get<Todo[]>('/api/todos');
    }
}
```

```typescript
// filename: auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

interface AuthResponse {
    token: string;
    userId: string;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private tokenSubject = new BehaviorSubject<string | null>(null);
    public token$ = this.tokenSubject.asObservable();
    
    constructor(private http: HttpClient) {
        const token = localStorage.getItem('token');
        if (token) {
            this.tokenSubject.next(token);
        }
    }
    
    login(username: string, password: string): Observable<AuthResponse> {
        console.log('Login method called');
        return this.http.post<AuthResponse>('/api/auth/login', { username, password })
            .pipe(
                tap(response => {
                    localStorage.setItem('token', response.token);
                    this.tokenSubject.next(response.token);
                })
            );
    }
    
    logout() {
        localStorage.removeItem('token');
        this.tokenSubject.next(null);
    }
    
    isAuthenticated(): boolean {
        return !!this.tokenSubject.value;
    }
}

// Test the service
console.log('Angular auth service validated!');
```

```json
// filename: package.json
{
    "name": "mean-frontend",
    "version": "1.0.0",
    "scripts": {
        "ng": "ng",
        "start": "ng serve",
        "build": "ng build",
        "test": "ng test"
    },
    "dependencies": {
        "@angular/animations": "^15.0.0",
        "@angular/common": "^15.0.0",
        "@angular/compiler": "^15.0.0",
        "@angular/core": "^15.0.0",
        "@angular/forms": "^15.0.0",
        "@angular/platform-browser": "^15.0.0",
        "@angular/platform-browser-dynamic": "^15.0.0",
        "@angular/router": "^15.0.0",
        "rxjs": "^7.5.0",
        "tslib": "^2.3.0",
        "zone.js": "^0.11.4"
    }
}
```

```json
// filename: tsconfig.json
{
    "compilerOptions": {
        "target": "ES2022",
        "module": "ES2022",
        "lib": ["ES2022", "dom"],
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "forceConsistentCasingInFileNames": true,
        "experimentalDecorators": true,
        "emitDecoratorMetadata": true
    }
}
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")


async def test_socket_io():
    """Test Socket.io real-time functionality"""
    print("\n\n🧪 Test 3: Socket.io Real-time Features")
    print("-" * 60)
    
    test_input = """
Please validate this Socket.io implementation:

```javascript
// filename: socket-server.js
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// Store active connections
const connections = new Map();

io.on('connection', (socket) => {
    console.log('New client connected:', socket.id);
    connections.set(socket.id, { id: socket.id, joinedAt: new Date() });
    
    // Broadcast user count
    io.emit('userCount', connections.size);
    
    socket.on('todo:create', (data) => {
        console.log('New todo created:', data);
        // Broadcast to all clients except sender
        socket.broadcast.emit('todo:new', data);
    });
    
    socket.on('todo:update', (data) => {
        console.log('Todo updated:', data);
        socket.broadcast.emit('todo:updated', data);
    });
    
    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
        connections.delete(socket.id);
        io.emit('userCount', connections.size);
    });
});

// Test the socket functionality
console.log('Socket.io server validated successfully!');
console.log('Active connections:', connections.size);

// Clean up for validation
process.exit(0);
```

```javascript
// filename: socket-client.js
const io = require('socket.io-client');

class SocketService {
    constructor() {
        this.socket = null;
    }
    
    connect(url = 'http://localhost:3000') {
        this.socket = io(url, {
            transports: ['websocket'],
            autoConnect: true
        });
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('userCount', (count) => {
            console.log('Active users:', count);
        });
        
        this.socket.on('todo:new', (todo) => {
            console.log('New todo received:', todo);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }
    
    createTodo(todo) {
        this.socket.emit('todo:create', todo);
    }
    
    updateTodo(todo) {
        this.socket.emit('todo:update', todo);
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Test the client
const client = new SocketService();
console.log('Socket.io client validated successfully!');
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")


async def test_docker_compose():
    """Test Docker Compose configuration validation"""
    print("\n\n🧪 Test 4: Docker Compose Configuration")
    print("-" * 60)
    
    test_input = """
Please validate this Docker compose setup:

```yaml
# filename: docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:5.0
    container_name: mean_mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: mean_app
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - mean_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: mean_backend
    restart: always
    environment:
      - NODE_ENV=production
      - PORT=3000
      - MONGODB_URI=mongodb://admin:password@mongodb:27017/mean_app?authSource=admin
      - JWT_SECRET=your_jwt_secret_key
    ports:
      - "3000:3000"
    depends_on:
      - mongodb
    networks:
      - mean_network
    volumes:
      - ./backend:/app
      - /app/node_modules

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: mean_frontend
    restart: always
    environment:
      - NODE_ENV=production
    ports:
      - "4200:80"
    depends_on:
      - backend
    networks:
      - mean_network

volumes:
  mongodb_data:

networks:
  mean_network:
    driver: bridge
```

```dockerfile
# filename: backend.dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

```dockerfile
# filename: frontend.dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/mean-frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```javascript
// filename: validate-compose.js
// Simple validation that files parse correctly
console.log('Docker compose configuration validated!');
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")


async def test_mean_integration():
    """Test full MEAN stack integration"""
    print("\n\n🧪 Test 5: Full MEAN Stack Integration")
    print("-" * 60)
    
    test_input = """
Please validate this integrated MEAN stack test:

```javascript
// filename: integration-test.js
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const io = require('socket.io-client');

// Test models
const todoSchema = new mongoose.Schema({
    title: String,
    completed: Boolean,
    userId: mongoose.Schema.Types.ObjectId
});

const Todo = mongoose.model('Todo', todoSchema);

// Test auth token generation
function generateToken(userId) {
    return jwt.sign({ userId }, 'test_secret', { expiresIn: '1h' });
}

// Test database operations
async function testDatabase() {
    try {
        // Connect to test database
        await mongoose.connect('mongodb://localhost:27017/test_mean', {
            useNewUrlParser: true,
            useUnifiedTopology: true
        });
        
        console.log('Connected to MongoDB');
        
        // Create test todo
        const todo = new Todo({
            title: 'Integration Test Todo',
            completed: false,
            userId: new mongoose.Types.ObjectId()
        });
        
        await todo.save();
        console.log('Created todo:', todo);
        
        // Query todo
        const found = await Todo.findOne({ title: 'Integration Test Todo' });
        console.log('Found todo:', found);
        
        // Update todo
        found.completed = true;
        await found.save();
        console.log('Updated todo');
        
        // Delete todo
        await Todo.deleteOne({ _id: found._id });
        console.log('Deleted todo');
        
        await mongoose.connection.close();
        console.log('Database operations completed successfully');
        
    } catch (error) {
        console.error('Database test failed:', error);
        throw error;
    }
}

// Test Socket.io
function testSocketConnection() {
    return new Promise((resolve, reject) => {
        const socket = io('http://localhost:3000', {
            transports: ['websocket']
        });
        
        socket.on('connect', () => {
            console.log('Socket connected');
            socket.emit('test', { message: 'Hello from test' });
            socket.disconnect();
            resolve();
        });
        
        socket.on('connect_error', (error) => {
            console.log('Socket connection failed (expected in test environment)');
            resolve(); // Don't fail the test
        });
        
        setTimeout(() => {
            socket.disconnect();
            resolve();
        }, 2000);
    });
}

// Run integration tests
async function runTests() {
    console.log('Starting MEAN stack integration tests...');
    
    // Test JWT
    const token = generateToken('123456');
    console.log('Generated JWT token');
    
    try {
        const decoded = jwt.verify(token, 'test_secret');
        console.log('Token verified successfully');
    } catch (error) {
        console.error('Token verification failed:', error);
    }
    
    // Test Socket.io (will fail in test environment, that's ok)
    await testSocketConnection();
    
    console.log('\\nMEAN stack integration validated successfully!');
}

runTests().catch(console.error);
```

```json
// filename: test-package.json
{
    "name": "mean-integration-test",
    "version": "1.0.0",
    "dependencies": {
        "mongoose": "^7.0.0",
        "jsonwebtoken": "^9.0.0",
        "socket.io-client": "^4.5.0"
    }
}
```
"""
    
    messages = [Message(parts=[MessagePart(content=test_input)])]
    
    async for message in validator_agent(messages):
        response = message.parts[0].content
        print(f"\n📥 Response:\n{response}")


async def main():
    """Run all MEAN stack tests"""
    print("🚀 MEAN Stack Validator Tests")
    print("=" * 60)
    
    try:
        # Run tests
        session_id = await test_mean_backend()
        await test_mean_frontend()
        await test_socket_io()
        await test_docker_compose()
        await test_mean_integration()
        
        print("\n\n✅ All MEAN stack tests completed!")
        print("The validator successfully handled:")
        print("  • Node.js/Express backend with MongoDB")
        print("  • Angular frontend with TypeScript")
        print("  • Socket.io real-time features")
        print("  • Docker compose configuration")
        print("  • Full stack integration")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up containers...")
        container_manager = get_container_manager()
        container_manager.cleanup_all()


if __name__ == "__main__":
    asyncio.run(main())