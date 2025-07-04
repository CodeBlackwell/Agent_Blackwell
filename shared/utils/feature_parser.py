"""
Feature parser for extracting implementation plans from designer output.
Follows ACP patterns for shared utilities.
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from shared.data_models import BaseModel


class ComplexityLevel(Enum):
    """Feature complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Feature(BaseModel):
    """Represents a single implementation feature following ACP data model patterns"""
    id: str
    title: str
    description: str
    files: List[str]
    validation_criteria: str
    dependencies: List[str]
    complexity: ComplexityLevel
    estimated_tokens: int = 2000
    
    def __post_init__(self):
        """Adjust token allocation based on complexity"""
        complexity_multipliers = {
            ComplexityLevel.LOW: 1.0,
            ComplexityLevel.MEDIUM: 1.5,
            ComplexityLevel.HIGH: 2.0
        }
        self.estimated_tokens = int(2000 * complexity_multipliers[self.complexity])


class FeatureParser:
    """
    Parses implementation plans from designer output.
    Follows ACP pattern for parser utilities.
    """
    
    # Regex patterns for feature extraction
    FEATURE_PATTERN = r'FEATURE\[(\d+)\]:\s*(.+?)(?=FEATURE\[\d+\]:|IMPLEMENTATION PLAN END|$)'
    FIELD_PATTERNS = {
        'description': r'Description:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
        'files': r'Files:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
        'validation': r'Validation:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
        'dependencies': r'Dependencies:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
        'complexity': r'(?:Estimated\s*)?Complexity:\s*(\w+)'
    }
    
    def __init__(self):
        self.features: List[Feature] = []
        self.feature_map: Dict[str, Feature] = {}
    
    def parse(self, designer_output: str) -> List[Feature]:
        """
        Parse designer output and extract features.
        Returns list of features in dependency order.
        """
        self.features = []
        self.feature_map = {}
        
        # Check if implementation plan exists
        if "IMPLEMENTATION PLAN" not in designer_output:
            # Fallback to auto-generation
            return self._generate_default_features(designer_output)
        
        # Extract implementation plan section
        plan_start = designer_output.find("IMPLEMENTATION PLAN")
        plan_section = designer_output[plan_start:]
        
        # Find all features
        feature_matches = re.finditer(self.FEATURE_PATTERN, plan_section, re.DOTALL)
        
        for match in feature_matches:
            feature_id = f"FEATURE[{match.group(1)}]"
            feature_title = match.group(2).strip()
            feature_content = match.group(0)
            
            # Extract feature fields
            feature = self._parse_feature(feature_id, feature_title, feature_content)
            self.features.append(feature)
            self.feature_map[feature_id] = feature
        
        # Sort by dependencies
        return self._topological_sort()
    
    def _parse_feature(self, feature_id: str, title: str, content: str) -> Feature:
        """Parse individual feature from content"""
        fields = {}
        
        for field_name, pattern in self.FIELD_PATTERNS.items():
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                fields[field_name] = match.group(1).strip()
            else:
                fields[field_name] = self._get_default_value(field_name)
        
        # Parse specific fields
        files = [f.strip() for f in fields['files'].split(',')]
        dependencies = self._parse_dependencies(fields['dependencies'])
        complexity = self._parse_complexity(fields['complexity'])
        
        return Feature(
            id=feature_id,
            title=title,
            description=fields['description'],
            files=files,
            validation_criteria=fields['validation'],
            dependencies=dependencies,
            complexity=complexity
        )
    
    def _parse_dependencies(self, deps_str: str) -> List[str]:
        """Parse dependency string into list"""
        if deps_str.lower() in ['none', 'n/a', '-']:
            return []
        
        # Extract FEATURE[N] patterns
        deps = re.findall(r'FEATURE\[\d+\]', deps_str)
        return deps
    
    def _parse_complexity(self, complexity_str: str) -> ComplexityLevel:
        """Parse complexity level"""
        complexity_lower = complexity_str.lower()
        if 'low' in complexity_lower:
            return ComplexityLevel.LOW
        elif 'high' in complexity_lower:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.MEDIUM
    
    def _topological_sort(self) -> List[Feature]:
        """Sort features by dependencies using topological sort"""
        sorted_features = []
        visited = set()
        
        def visit(feature: Feature):
            if feature.id in visited:
                return
            visited.add(feature.id)
            
            for dep_id in feature.dependencies:
                if dep_id in self.feature_map:
                    visit(self.feature_map[dep_id])
            
            sorted_features.append(feature)
        
        for feature in self.features:
            visit(feature)
        
        return sorted_features
    
    def _generate_default_features(self, designer_output: str) -> List[Feature]:
        """
        Generate default feature breakdown when not provided explicitly.
        Analyzes design content to create sensible features.
        """
        features = []
        
        # Always start with setup
        features.append(Feature(
            id="FEATURE[1]",
            title="Project Foundation",
            description="Set up project structure and configuration",
            files=["app.py", "config.py", "requirements.txt", "__init__.py"],
            validation_criteria="Application imports work, configuration loads",
            dependencies=[],
            complexity=ComplexityLevel.LOW
        ))
        
        # Detect models/schemas
        if any(keyword in designer_output.lower() for keyword in ['model', 'schema', 'database']):
            features.append(Feature(
                id="FEATURE[2]",
                title="Data Models",
                description="Implement core data models and schemas",
                files=["models/"],
                validation_criteria="Models instantiate correctly, relationships work",
                dependencies=["FEATURE[1]"],
                complexity=ComplexityLevel.MEDIUM
            ))
        
        # Detect services/business logic
        if any(keyword in designer_output.lower() for keyword in ['service', 'business', 'logic']):
            features.append(Feature(
                id="FEATURE[3]",
                title="Business Logic",
                description="Implement core services and business logic",
                files=["services/"],
                validation_criteria="Service methods execute without errors",
                dependencies=["FEATURE[2]"] if len(features) > 1 else ["FEATURE[1]"],
                complexity=ComplexityLevel.HIGH
            ))
        
        # Detect API/routes
        if any(keyword in designer_output.lower() for keyword in ['api', 'endpoint', 'route', 'rest']):
            features.append(Feature(
                id="FEATURE[4]",
                title="API Layer",
                description="Implement API endpoints and routing",
                files=["api/", "routes/"],
                validation_criteria="Endpoints respond correctly, proper status codes",
                dependencies=[f"FEATURE[{len(features)-1}]"],
                complexity=ComplexityLevel.MEDIUM
            ))
        
        return features
    
    def _get_default_value(self, field_name: str) -> str:
        """Get default value for missing fields"""
        defaults = {
            'description': "Implementation feature",
            'files': "implementation files",
            'validation': "Code executes without errors",
            'dependencies': "None",
            'complexity': "medium"
        }
        return defaults.get(field_name, "")
