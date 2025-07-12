"""
Feature parser for extracting implementation plans from designer output.
Follows ACP patterns for shared utilities.
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from shared.data_models import BaseModel

# Set up logging
logger = logging.getLogger(__name__)


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
    short_name: str  # Concise name for UI display (e.g., "API Foundation", "User Auth")
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
    FEATURE_PATTERN = r'FEATURE\[(\d+)\]:\s*([^\n]+)'
    FIELD_PATTERNS = {
        'description': r'Description:\s*([^\n]+(?:\n(?!(?:Files:|Validation:|Dependencies:|Complexity:|FEATURE\[))[^\n]+)*)',
        'files': r'Files:\s*([^\n]+)',
        'validation': r'Validation:\s*([^\n]+(?:\n(?!(?:Dependencies:|Complexity:|FEATURE\[))[^\n]+)*)',
        'dependencies': r'Dependencies:\s*([^\n]+)',
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
        
        logger.debug("Starting feature parsing...")
        
        # Try markdown format first (### Feature N: Title)
        if "### Feature" in designer_output:
            logger.debug("Detected markdown format")
            return self._parse_markdown_format(designer_output)
        
        # Check if implementation plan exists OR if FEATURE patterns exist
        if "IMPLEMENTATION PLAN" not in designer_output and not re.search(r'FEATURE\[\d+\]:', designer_output):
            logger.debug("No IMPLEMENTATION PLAN or FEATURE patterns found, using auto-generation")
            # Fallback to auto-generation
            return self._generate_default_features(designer_output)
        
        # Extract implementation plan section or use full output if no header
        if "IMPLEMENTATION PLAN" in designer_output:
            plan_start = designer_output.find("IMPLEMENTATION PLAN")
            plan_section = designer_output[plan_start:]
            logger.debug(f"Found IMPLEMENTATION PLAN at position {plan_start}")
        else:
            # No header, but we know there are FEATURE patterns, so use full output
            plan_section = designer_output
            logger.debug("No IMPLEMENTATION PLAN header, using full designer output")
        
        # Find all features - first get titles
        feature_matches = list(re.finditer(self.FEATURE_PATTERN, plan_section))
        logger.info(f"Found {len(feature_matches)} features to parse")
        
        for i, match in enumerate(feature_matches):
            feature_id = f"FEATURE[{match.group(1)}]"
            feature_title = match.group(2).strip()
            
            # Get full content from this feature to the next (or end)
            start_pos = match.start()
            if i + 1 < len(feature_matches):
                end_pos = feature_matches[i + 1].start()
            else:
                end_pos = len(plan_section)
            
            feature_content = plan_section[start_pos:end_pos]
            logger.debug(f"Parsing {feature_id}: {feature_title} (content length: {len(feature_content)})")
            
            # Extract feature fields
            feature = self._parse_feature(feature_id, feature_title, feature_content)
            self.features.append(feature)
            self.feature_map[feature_id] = feature
        
        logger.info(f"Successfully parsed {len(self.features)} features")
        
        # Validation: Check if suspiciously few features were detected
        if len(self.features) == 1 and len(designer_output) > 500:
            # Check if the single feature contains multiple FEATURE patterns
            feature_pattern_count = len(re.findall(r'FEATURE\[\d+\]:', designer_output))
            if feature_pattern_count > 1:
                logger.warning(f"WARNING: Found {feature_pattern_count} FEATURE patterns but only parsed 1 feature. "
                             "This may indicate a parsing issue.")
                # Log the first feature for debugging
                if self.features:
                    logger.warning(f"Single feature title: {self.features[0].title[:100]}...")
        
        # Sort by dependencies
        return self._topological_sort()
    
    def _parse_feature(self, feature_id: str, title: str, content: str) -> Feature:
        """Parse individual feature from content"""
        fields = {}
        
        for field_name, pattern in self.FIELD_PATTERNS.items():
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                fields[field_name] = match.group(1).strip()
                logger.debug(f"  {feature_id} - Found {field_name}: {fields[field_name][:50]}...")
            else:
                fields[field_name] = self._get_default_value(field_name)
                logger.debug(f"  {feature_id} - Using default for {field_name}: {fields[field_name]}")
        
        # Parse specific fields
        files = [f.strip() for f in fields['files'].split(',')]
        dependencies = self._parse_dependencies(fields['dependencies'])
        complexity = self._parse_complexity(fields['complexity'])
        
        # Generate short name from title
        short_name = self._generate_short_name(title, feature_id)
        
        return Feature(
            id=feature_id,
            title=title,
            short_name=short_name,
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
        # Check for "high" before other terms since "very high" contains "high"
        if 'high' in complexity_lower:
            return ComplexityLevel.HIGH
        elif 'low' in complexity_lower:
            return ComplexityLevel.LOW
        else:
            return ComplexityLevel.MEDIUM
    
    def _generate_short_name(self, title: str, feature_id: str) -> str:
        """Generate a short, meaningful name from the feature title"""
        # Common patterns to simplify
        title_lower = title.lower()
        
        # Map common feature patterns to short names
        name_mappings = {
            'project foundation': 'Foundation',
            'project setup': 'Setup',
            'api foundation': 'API Base',
            'hello world': 'Hello API',
            'greeting': 'Greeting',
            'data model': 'Data Models',
            'database': 'Database',
            'authentication': 'Auth',
            'authorization': 'Auth',
            'user management': 'User Mgmt',
            'testing': 'Tests',
            'test suite': 'Tests',
            'documentation': 'Docs',
            'api documentation': 'API Docs',
            'docker': 'Docker',
            'containerization': 'Container',
            'configuration': 'Config',
            'validation': 'Validation',
            'error handling': 'Error Handler',
            'middleware': 'Middleware',
            'routing': 'Routes',
            'endpoint': 'Endpoints',
            'service': 'Service',
            'business logic': 'Business',
            'api layer': 'API Layer',
            'rest api': 'REST API',
            'graphql': 'GraphQL',
            'websocket': 'WebSocket',
            'security': 'Security',
            'logging': 'Logging',
            'monitoring': 'Monitoring',
            'deployment': 'Deploy',
            'ci/cd': 'CI/CD',
            'integration': 'Integration'
        }
        
        # Check for exact matches first
        for pattern, short in name_mappings.items():
            if pattern in title_lower:
                return short
        
        # If no pattern matches, create from title
        # Remove common words and take first 2-3 significant words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'to', 'of', 'in', 'on', 'at'}
        words = [w for w in title.split() if w.lower() not in stop_words]
        
        if len(words) == 0:
            # Fallback to feature number
            return f"Feature {feature_id.replace('FEATURE[', '').replace(']', '')}"
        elif len(words) == 1:
            # Single word - use as is but truncate if too long
            return words[0][:15]
        elif len(words) == 2:
            # Two words - combine them
            return f"{words[0]} {words[1]}"[:20]
        else:
            # Multiple words - use first two or create acronym
            if len(words[0]) + len(words[1]) <= 15:
                return f"{words[0]} {words[1]}"
            else:
                # Create acronym from first 3-4 words
                acronym = ''.join(w[0].upper() for w in words[:4])
                return acronym
    
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
            short_name="Foundation",
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
                short_name="Data Models",
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
                short_name="Business",
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
                short_name="API Layer",
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
    
    def _parse_markdown_format(self, designer_output: str) -> List[Feature]:
        """Parse markdown format features (### Feature N: Title)"""
        # Pattern for markdown features
        md_pattern = r'### Feature (\d+):\s*([^\n]+)'
        feature_sections = re.split(r'(?=### Feature \d+:)', designer_output)
        
        for section in feature_sections:
            if not section.strip() or '### Feature' not in section:
                continue
                
            # Extract feature header
            header_match = re.match(md_pattern, section)
            if not header_match:
                continue
                
            feature_num = header_match.group(1)
            feature_title = header_match.group(2).strip()
            
            # Extract fields in markdown format
            id_match = re.search(r'\*\*ID\*\*:\s*([^\n]+)', section)
            desc_match = re.search(r'\*\*Description\*\*:\s*([^\n]+)', section)
            complex_match = re.search(r'\*\*Complexity\*\*:\s*([^\n]+)', section)
            files_match = re.search(r'\*\*Files\*\*:\s*([^\n]+)', section)
            valid_match = re.search(r'\*\*Validation\*\*:\s*([^\n]+)', section)
            deps_match = re.search(r'\*\*Dependencies\*\*:\s*([^\n]+)', section)
            
            feature_id = id_match.group(1).strip() if id_match else f"FEATURE[{feature_num}]"
            description = desc_match.group(1).strip() if desc_match else feature_title
            complexity_str = complex_match.group(1).strip() if complex_match else "medium"
            files_str = files_match.group(1).strip() if files_match else "implementation files"
            validation = valid_match.group(1).strip() if valid_match else "Code executes without errors"
            deps_str = deps_match.group(1).strip() if deps_match else "None"
            
            # Parse fields
            files = [f.strip() for f in files_str.split(',')]
            dependencies = self._parse_dependencies(deps_str)
            complexity = self._parse_complexity(complexity_str)
            
            feature = Feature(
                id=feature_id,
                title=feature_title,
                short_name=self._generate_short_name(feature_title, feature_id),
                description=description,
                files=files,
                validation_criteria=validation,
                dependencies=dependencies,
                complexity=complexity
            )
            
            self.features.append(feature)
            self.feature_map[feature_id] = feature
        
        return self._topological_sort()
