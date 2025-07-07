#!/usr/bin/env python3
"""
Test script for the feature reviewer agent.
Tests feature-specific code review capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.orchestrator_agent import run_team_member

async def test_feature_reviewer_simple():
    """Test feature reviewer with a simple feature implementation"""
    print("🧪 Testing Feature Reviewer Agent - Simple Feature")
    print("=" * 60)
    
    # Test case: Simple feature implementation
    feature_input = """
Feature: Add method
Description: Implement an add method that returns the sum of two numbers

Current Implementation:
```python
# filename: calculator.py
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
```

This is the first feature being implemented for a calculator class.
"""
    
    result = await run_team_member("feature_reviewer_agent", feature_input)
    
    print("\n📝 Feature Reviewer Response:")
    print(result)
    print("=" * 60)
    
    return result

async def test_feature_reviewer_with_error():
    """Test feature reviewer with a feature that has issues"""
    print("\n🧪 Testing Feature Reviewer Agent - Feature with Issues")
    print("=" * 60)
    
    # Test case: Feature with error handling issues
    feature_input = """
Feature: Divide method
Description: Implement a divide method that safely handles division by zero

Current Implementation:
```python
# filename: calculator.py
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        return a / b  # Missing error handling for division by zero
```

Existing code already has an add method. This feature should handle edge cases.
"""
    
    result = await run_team_member("feature_reviewer_agent", feature_input)
    
    print("\n📝 Feature Reviewer Response:")
    print(result)
    print("=" * 60)
    
    return result

async def test_feature_reviewer_retry_context():
    """Test feature reviewer with retry context"""
    print("\n🧪 Testing Feature Reviewer Agent - Retry Context")
    print("=" * 60)
    
    # Test case: Retry attempt with previous feedback
    feature_input = """
Feature: Complete task method
Retry Attempt: 2

Previous Error:
NameError: name 'task' is not defined at line 15

Previous Feedback:
The variable 'task' is used before being defined. You need to retrieve the task from self.tasks using the task_id.

New Implementation:
```python
# filename: task_manager.py
class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1
    
    def add_task(self, title, priority="medium"):
        task_id = self.next_id
        self.tasks[task_id] = {
            'id': task_id,
            'title': title,
            'priority': priority,
            'completed': False
        }
        self.next_id += 1
        return task_id
    
    def complete_task(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] = True
            return True
        return False
```

Existing Code Context:
The TaskManager class already has add_task method implemented. This retry fixes the previous error.
"""
    
    result = await run_team_member("feature_reviewer_agent", feature_input)
    
    print("\n📝 Feature Reviewer Response:")
    print(result)
    print("=" * 60)
    
    return result

async def test_feature_reviewer_complex():
    """Test feature reviewer with a complex feature"""
    print("\n🧪 Testing Feature Reviewer Agent - Complex Feature")
    print("=" * 60)
    
    # Test case: Complex feature with multiple concerns
    feature_input = """
Feature: Get statistics method
Description: Return comprehensive statistics about tasks including completion rate and category breakdown

Current Implementation:
```python
# filename: task_manager.py
class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1
    
    def add_task(self, title, priority="medium", category="general"):
        task_id = self.next_id
        self.tasks[task_id] = {
            'id': task_id,
            'title': title,
            'priority': priority,
            'category': category,
            'completed': False,
            'created_at': time.time()
        }
        self.next_id += 1
        return task_id
    
    def complete_task(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] = True
            self.tasks[task_id]['completed_at'] = time.time()
            return True
        return False
    
    def get_statistics(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t['completed'])
        
        # Category breakdown
        categories = {}
        for task in self.tasks.values():
            cat = task['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'completed': 0}
            categories[cat]['total'] += 1
            if task['completed']:
                categories[cat]['completed'] += 1
        
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': completed / total if total > 0 else 0,
            'categories': categories
        }
```

This feature builds on existing task management functionality to provide analytics.
"""
    
    result = await run_team_member("feature_reviewer_agent", feature_input)
    
    print("\n📝 Feature Reviewer Response:")
    print(result)
    print("=" * 60)
    
    return result

async def main():
    """Run all feature reviewer tests"""
    print("🚀 Starting Feature Reviewer Agent Tests")
    print("Note: Make sure the orchestrator server is running on port 8080!")
    print()
    
    # Run tests
    await test_feature_reviewer_simple()
    await test_feature_reviewer_with_error()
    await test_feature_reviewer_retry_context()
    await test_feature_reviewer_complex()
    
    print("\n✅ All feature reviewer tests completed!")

if __name__ == "__main__":
    asyncio.run(main())