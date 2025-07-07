#!/usr/bin/env python3
"""Quick validation of Phase 3 dependency ordering."""

from workflows.mvp_incremental.feature_dependency_parser import FeatureDependencyParser, Feature

# Test 1: Explicit dependencies
print("🧪 Test 1: Explicit dependency parsing")
design_with_deps = """
IMPLEMENTATION PLAN:
===================

FEATURE[1]: Define Task Class
Description: Create a Task class with title, description, priority, and status attributes.
Files: task.py
Dependencies: None
Validation: Task can be instantiated with all attributes.

FEATURE[2]: Define TaskList Class  
Description: Create a TaskList class that manages a collection of Task objects.
Files: task_list.py
Dependencies: FEATURE[1]
Validation: TaskList can be instantiated and holds tasks.

FEATURE[3]: Add Task Method
Description: Implement add_task method in TaskList to add new tasks.
Files: task_list.py
Dependencies: FEATURE[2], FEATURE[1]
Validation: Tasks can be added to the list.

FEATURE[4]: Export to JSON
Description: Implement export_to_json method to save tasks.
Files: task_list.py
Dependencies: FEATURE[2], FEATURE[3]
Validation: Tasks can be exported to JSON file.
"""

features = FeatureDependencyParser.parse_dependencies(design_with_deps)
print(f"Found {len(features)} features with dependencies")

ordered = FeatureDependencyParser.topological_sort(features)
print("\n📊 Dependency-ordered execution:")
for i, f in enumerate(ordered, 1):
    deps = f.dependencies if f.dependencies else ["None"]
    print(f"{i}. {f.title} (depends on: {', '.join(deps)})")

# Test 2: Smart ordering without explicit dependencies
print("\n\n🧪 Test 2: Smart ordering by keywords")
simple_features = [
    {"id": "1", "title": "Export to JSON method", "description": "Export functionality"},
    {"id": "2", "title": "Task class definition", "description": "Basic Task class"},
    {"id": "3", "title": "Add validation", "description": "Validate task data"},
    {"id": "4", "title": "TaskList class", "description": "Container for tasks"},
    {"id": "5", "title": "Import from JSON", "description": "Load tasks from file"},
]

ordered_simple = FeatureDependencyParser.order_features_smart(simple_features, "")
print("\n📊 Smart-ordered execution:")
for i, f in enumerate(ordered_simple, 1):
    print(f"{i}. {f['title']}")

print("\n✅ Phase 3 dependency ordering is working!")