"""
Feature Dependency Parser for MVP Incremental Workflow
Parses feature dependencies and orders them for execution
"""
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Feature:
    """Represents a feature with its dependencies"""
    id: str
    title: str
    description: str
    dependencies: List[str]  # List of feature IDs this depends on
    
    def __hash__(self):
        return hash(self.id)


class FeatureDependencyParser:
    """Parses and orders features based on dependencies"""
    
    @staticmethod
    def parse_dependencies(design_output: str) -> List[Feature]:
        """
        Parse features with dependencies from design output.
        Looks for FEATURE[n] blocks with Dependencies field.
        """
        features = []
        
        # Pattern to match FEATURE blocks
        feature_pattern = r'FEATURE\[(\d+)\]:\s*([^\n]+)\nDescription:\s*([^\n]+)(?:\n[^\n]*)*?\nDependencies:\s*([^\n]+)'
        matches = re.findall(feature_pattern, design_output, re.MULTILINE | re.DOTALL)
        
        if matches:
            for match in matches:
                feature_num, title, description, deps_str = match
                feature_id = f"feature_{feature_num}"
                
                # Parse dependencies
                dependencies = []
                if deps_str.strip().upper() != "NONE":
                    # Look for FEATURE[n] references
                    dep_matches = re.findall(r'FEATURE\[(\d+)\]', deps_str)
                    dependencies = [f"feature_{dep}" for dep in dep_matches]
                
                features.append(Feature(
                    id=feature_id,
                    title=title.strip(),
                    description=description.strip(),
                    dependencies=dependencies
                ))
        
        return features
    
    @staticmethod
    def topological_sort(features: List[Feature]) -> List[Feature]:
        """
        Order features using topological sort based on dependencies.
        Returns ordered list where dependencies come before dependents.
        """
        # Build adjacency list and in-degree count
        graph = {f.id: f.dependencies for f in features}
        in_degree = {f.id: 0 for f in features}
        feature_map = {f.id: f for f in features}
        
        # Calculate in-degrees (count how many features depend on each feature)
        for feature_id, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[feature_id] += 1  # This feature depends on dep
        
        # Find all features with no dependencies
        queue = [f_id for f_id, degree in in_degree.items() if degree == 0]
        ordered = []
        
        while queue:
            # Process feature with no remaining dependencies
            current_id = queue.pop(0)
            ordered.append(feature_map[current_id])
            
            # Remove this feature from dependencies of others
            for feature_id, deps in graph.items():
                if current_id in deps:
                    in_degree[feature_id] -= 1
                    if in_degree[feature_id] == 0:
                        queue.append(feature_id)
        
        # Check for cycles
        if len(ordered) != len(features):
            # If we have a cycle, return features in original order
            print("⚠️  Warning: Circular dependencies detected, using original order")
            return features
        
        return ordered
    
    @staticmethod
    def extract_simple_dependencies(feature_description: str) -> List[str]:
        """
        Extract implicit dependencies from feature description.
        Looks for phrases like "uses", "requires", "depends on", etc.
        """
        dependencies = []
        
        # Patterns that indicate dependencies
        dependency_patterns = [
            r'uses?\s+(?:the\s+)?(\w+)',
            r'requires?\s+(?:the\s+)?(\w+)',
            r'depends?\s+on\s+(?:the\s+)?(\w+)',
            r'extends?\s+(?:the\s+)?(\w+)',
            r'based\s+on\s+(?:the\s+)?(\w+)',
            r'from\s+(?:the\s+)?(\w+)\s+(?:class|method|function)',
        ]
        
        for pattern in dependency_patterns:
            matches = re.findall(pattern, feature_description, re.IGNORECASE)
            dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    @staticmethod
    def order_features_smart(features_list: List[Dict[str, str]], design_output: str) -> List[Dict[str, str]]:
        """
        Smart ordering of features based on both explicit and implicit dependencies.
        Falls back to original order if no dependencies found.
        """
        # First try to parse explicit FEATURE blocks with dependencies
        parsed_features = FeatureDependencyParser.parse_dependencies(design_output)
        
        if parsed_features:
            # We have explicit dependencies, use topological sort
            ordered_features = FeatureDependencyParser.topological_sort(parsed_features)
            
            # Map back to original feature dict format
            feature_map = {f['title']: f for f in features_list}
            result = []
            
            for feature in ordered_features:
                # Find matching feature in original list
                for orig_feature in features_list:
                    if feature.title in orig_feature.get('title', '') or \
                       feature.title in orig_feature.get('description', ''):
                        result.append(orig_feature)
                        break
            
            # Add any features we didn't match
            for f in features_list:
                if f not in result:
                    result.append(f)
            
            return result
        
        # No explicit dependencies, try implicit ordering
        # Common patterns: class definition -> methods, basic -> complex
        ordered = []
        remaining = features_list.copy()
        
        # Phase 1: Class/structure definitions
        for i, feature in enumerate(remaining):
            title = feature.get('title', '').lower()
            desc = feature.get('description', '').lower()
            if any(keyword in title + desc for keyword in ['class', 'structure', 'schema', 'model', 'interface']):
                ordered.append(feature)
                remaining[i] = None
        
        # Phase 2: Basic methods/functions
        remaining = [f for f in remaining if f is not None]
        for i, feature in enumerate(remaining):
            title = feature.get('title', '').lower()
            desc = feature.get('description', '').lower()
            if any(keyword in title + desc for keyword in ['add', 'get', 'set', 'init', 'constructor', 'basic']):
                ordered.append(feature)
                remaining[i] = None
        
        # Phase 3: Complex methods/functions
        remaining = [f for f in remaining if f is not None]
        for i, feature in enumerate(remaining):
            title = feature.get('title', '').lower()
            desc = feature.get('description', '').lower()
            if any(keyword in title + desc for keyword in ['complex', 'advanced', 'process', 'calculate']):
                ordered.append(feature)
                remaining[i] = None
        
        # Phase 4: Error handling/validation
        remaining = [f for f in remaining if f is not None]
        for i, feature in enumerate(remaining):
            title = feature.get('title', '').lower()
            desc = feature.get('description', '').lower()
            if any(keyword in title + desc for keyword in ['error', 'exception', 'validate', 'check']):
                ordered.append(feature)
                remaining[i] = None
        
        # Phase 5: Testing/documentation
        remaining = [f for f in remaining if f is not None]
        for i, feature in enumerate(remaining):
            title = feature.get('title', '').lower()
            desc = feature.get('description', '').lower()
            if any(keyword in title + desc for keyword in ['test', 'document', 'example']):
                ordered.append(feature)
                remaining[i] = None
        
        # Add any remaining features
        remaining = [f for f in remaining if f is not None]
        ordered.extend(remaining)
        
        return ordered if ordered else features_list