#!/usr/bin/env python3
"""
Standalone example of using the Feature Orchestrator.
This demonstrates the core functionality without needing any external services.
"""

import asyncio
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.incremental.feature_orchestrator import (
    FeatureOrchestrator,
    FeatureImplementationResult,
    prepare_feature_context,
    parse_code_files
)
from workflows.monitoring import WorkflowExecutionTracer
from shared.utils.feature_parser import FeatureParser, Feature, ComplexityLevel


# Blog requirements with features
BLOG_DESIGN = """
Blog Application Technical Design

IMPLEMENTATION PLAN:

FEATURE[1]: Database Models
Description: Create the core database models for users and posts
Files: models.py
Validation: Models should have all required fields
Dependencies: []
Complexity: low

FEATURE[2]: Authentication
Description: Implement user authentication
Files: auth.py
Validation: Login and registration functions work
Dependencies: [FEATURE[1]]
Complexity: medium

FEATURE[3]: API Routes
Description: Create REST API endpoints
Files: api.py
Validation: All CRUD operations functional
Dependencies: [FEATURE[1], FEATURE[2]]
Complexity: medium
"""


class MockAgentSystem:
    """Mock agent system for standalone demonstration."""
    
    async def code_feature(self, context: str, feature: Feature) -> str:
        """Mock coder that generates code based on the feature."""
        
        # Simple mock implementations based on feature
        if "Database Models" in feature.title:
            return """
FILENAME: models.py
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Post:
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
```
"""
        
        elif "Authentication" in feature.title:
            return """
FILENAME: auth.py
```python
import hashlib
import secrets
from models import User

class AuthSystem:
    def __init__(self):
        self.users = {}  # In-memory storage for demo
        self.sessions = {}
    
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        return salt + hashlib.sha256((salt + password).encode()).hexdigest()
    
    def verify_password(self, password: str, hash: str) -> bool:
        salt = hash[:32]
        return hash == salt + hashlib.sha256((salt + password).encode()).hexdigest()
    
    def register(self, username: str, email: str, password: str) -> User:
        if username in self.users:
            raise ValueError("Username already exists")
        
        user = User(
            id=len(self.users) + 1,
            username=username,
            email=email,
            password_hash=self.hash_password(password)
        )
        self.users[username] = user
        return user
    
    def login(self, username: str, password: str) -> str:
        user = self.users.get(username)
        if not user or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        token = secrets.token_urlsafe(32)
        self.sessions[token] = user.id
        return token
```
"""
        
        elif "API" in feature.title:
            return """
FILENAME: api.py
```python
from typing import List, Optional
from models import Post, User
from auth import AuthSystem

class BlogAPI:
    def __init__(self, auth: AuthSystem):
        self.auth = auth
        self.posts = []
    
    def create_post(self, token: str, title: str, content: str) -> Post:
        user_id = self.auth.sessions.get(token)
        if not user_id:
            raise ValueError("Invalid auth token")
        
        post = Post(
            id=len(self.posts) + 1,
            title=title,
            content=content,
            author_id=user_id
        )
        self.posts.append(post)
        return post
    
    def get_posts(self) -> List[Post]:
        return self.posts
    
    def get_post(self, post_id: int) -> Optional[Post]:
        for post in self.posts:
            if post.id == post_id:
                return post
        return None
    
    def update_post(self, token: str, post_id: int, title: str = None, content: str = None) -> Post:
        user_id = self.auth.sessions.get(token)
        if not user_id:
            raise ValueError("Invalid auth token")
        
        post = self.get_post(post_id)
        if not post:
            raise ValueError("Post not found")
        if post.author_id != user_id:
            raise ValueError("Not authorized")
        
        if title:
            post.title = title
        if content:
            post.content = content
        return post
```
"""
        
        return f"# Mock implementation for {feature.title}"
    
    async def validate_feature(self, feature: Feature, files: Dict[str, str]) -> bool:
        """Mock validation - just check if files were created."""
        return len(files) > 0


async def demonstrate_feature_orchestrator():
    """Demonstrate the feature orchestrator with mock agents."""
    
    print("🎯 Standalone Feature Orchestrator Demonstration")
    print("=" * 70)
    print("\nThis shows how the feature orchestrator works without external dependencies.\n")
    
    # Create components
    tracer = WorkflowExecutionTracer("standalone_demo")
    orchestrator = FeatureOrchestrator(tracer)
    mock_agents = MockAgentSystem()
    
    # Parse features
    print("1️⃣ Parsing features from design document...")
    parser = FeatureParser()
    features = parser.parse(BLOG_DESIGN)
    
    print(f"\n📋 Found {len(features)} features:")
    for i, feature in enumerate(features, 1):
        print(f"   {i}. {feature.title}")
        print(f"      - Files: {', '.join(feature.files)}")
        print(f"      - Complexity: {feature.complexity.value}")
        if feature.dependencies:
            print(f"      - Depends on: {', '.join(feature.dependencies)}")
    
    # Simulate incremental implementation
    print("\n2️⃣ Simulating incremental implementation...")
    print("-" * 50)
    
    implemented_features = []
    codebase = {}
    
    for feature in features:
        print(f"\n🔨 Implementing {feature.title}...")
        
        # Prepare context
        context = prepare_feature_context(
            feature=feature,
            requirements="Create a blog application",
            design=BLOG_DESIGN,
            existing_code=codebase,
            tests=None
        )
        
        # Generate code (mock)
        code_output = await mock_agents.code_feature(context, feature)
        files = parse_code_files(code_output)
        
        # Validate (mock)
        if await mock_agents.validate_feature(feature, files):
            print(f"   ✅ Validation passed!")
            codebase.update(files)
            implemented_features.append(feature)
            
            # Show generated files
            for filename in files:
                print(f"   📄 Created: {filename}")
        else:
            print(f"   ❌ Validation failed!")
    
    # Summary
    print("\n3️⃣ Implementation Summary")
    print("-" * 50)
    print(f"✅ Successfully implemented: {len(implemented_features)}/{len(features)} features")
    print(f"📁 Files created: {len(codebase)}")
    
    print("\n📂 Final codebase structure:")
    for filename in sorted(codebase.keys()):
        print(f"   └── {filename}")
    
    # Show how this would work with real orchestrator
    print("\n4️⃣ How this works with the real system:")
    print("-" * 50)
    print("""
    In the real system:
    1. The planner agent creates a development plan
    2. The designer agent outputs features (like our BLOG_DESIGN)
    3. The feature orchestrator:
       - Parses features from the designer output
       - For each feature:
         - Sends context to the coder agent
         - Gets generated code back
         - Validates with the executor agent
         - Retries if validation fails
       - Tracks progress throughout
    4. The reviewer agent reviews the final implementation
    
    The feature orchestrator handles:
    - Dependency management (features built in correct order)
    - Retry logic with different strategies
    - Progress tracking and visualization
    - Stagnation detection
    - Error analysis and recovery
    """)
    
    return implemented_features, codebase


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("FEATURE ORCHESTRATOR - STANDALONE DEMONSTRATION")
    print("="*70 + "\n")
    
    # Run the demonstration
    features, codebase = asyncio.run(demonstrate_feature_orchestrator())
    
    print("\n✅ Demonstration complete!")
    print("\n💡 Key Insights:")
    print("• The feature orchestrator is the engine of incremental development")
    print("• It manages feature-by-feature implementation with validation")
    print("• Each feature builds upon previously implemented features")
    print("• Failed features are retried with intelligent strategies")
    print("• Progress is tracked and reported throughout execution")
    
    print("\n📚 Next Steps:")
    print("1. Explore the full workflow: workflows/incremental/incremental_workflow.py")
    print("2. Run with real agents: python orchestrator/orchestrator_agent.py")
    print("3. Try the blog demo: python examples/direct_incremental_blog_demo.py")


if __name__ == "__main__":
    main()