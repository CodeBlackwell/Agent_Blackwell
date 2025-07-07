"""
Enhanced Feature Parser with Testable Criteria Extraction
Parses features from design output and extracts testable acceptance criteria
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from workflows.logger import workflow_logger as logger


@dataclass
class TestCriteria:
    """Represents testable criteria for a feature"""
    description: str
    input_examples: List[Dict[str, Any]] = field(default_factory=list)
    expected_outputs: List[Any] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    error_conditions: List[str] = field(default_factory=list)


@dataclass
class TestableFeature:
    """Feature with testable criteria"""
    id: str
    title: str
    description: str
    test_criteria: TestCriteria
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "test_criteria": {
                "description": self.test_criteria.description,
                "input_examples": self.test_criteria.input_examples,
                "expected_outputs": self.test_criteria.expected_outputs,
                "edge_cases": self.test_criteria.edge_cases,
                "error_conditions": self.test_criteria.error_conditions
            },
            "dependencies": self.dependencies
        }


class TestableFeatureParser:
    """Parser that extracts testable criteria from feature descriptions"""
    
    @staticmethod
    def parse_features_with_criteria(design_output: str) -> List[TestableFeature]:
        """
        Parse features and extract testable criteria from design output.
        
        Looks for patterns like:
        - FEATURE[n]: Title
        - Description: ...
        - Input/Output: ...
        - Edge cases: ...
        - Error handling: ...
        """
        features = []
        
        # Enhanced pattern to capture more structure
        # Split the text into sections starting with FEATURE[n]
        feature_blocks = re.split(r'(?=^FEATURE\[\d+\]:)', design_output, flags=re.MULTILINE)
        feature_blocks = [block for block in feature_blocks if block.strip()]
        
        matches = []
        for block in feature_blocks:
            match = re.match(r'^FEATURE\[(\d+)\]:\s*([^\n]+)(.*)', block, re.DOTALL)
            if match:
                matches.append(match.groups())
        
        logger.debug(f"Standard pattern found {len(matches)} matches")
        
        if matches:
            for match in matches:
                feature_num, title, content = match
                feature_id = f"feature_{feature_num}"
                
                # Extract sections from content
                description = TestableFeatureParser._extract_section(content, "Description")
                dependencies = TestableFeatureParser._extract_dependencies(content)
                
                # Extract test criteria
                test_criteria = TestableFeatureParser._extract_test_criteria(content, description)
                
                features.append(TestableFeature(
                    id=feature_id,
                    title=title.strip(),
                    description=description,
                    test_criteria=test_criteria,
                    dependencies=dependencies
                ))
        else:
            # Fallback to simple parsing with inferred criteria
            features = TestableFeatureParser._parse_simple_features(design_output)
            
        return features
    
    @staticmethod
    def _extract_section(content: str, section_name: str) -> str:
        """Extract a specific section from feature content"""
        pattern = rf'{section_name}:\s*([^\n]+(?:\n(?![A-Z][a-z]*:)[^\n]+)*)'
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    @staticmethod
    def _extract_dependencies(content: str) -> List[str]:
        """Extract feature dependencies"""
        deps_str = TestableFeatureParser._extract_section(content, "Dependencies")
        dependencies = []
        
        if deps_str and deps_str.upper() != "NONE":
            # Look for FEATURE[n] references
            dep_matches = re.findall(r'FEATURE\[(\d+)\]', deps_str)
            dependencies = [f"feature_{dep}" for dep in dep_matches]
            
        return dependencies
    
    @staticmethod
    def _extract_test_criteria(content: str, description: str) -> TestCriteria:
        """Extract testable criteria from feature content"""
        criteria = TestCriteria(description=description)
        
        # Extract input/output examples
        io_section = TestableFeatureParser._extract_section(content, "Input/Output|Examples?|Usage")
        if io_section:
            criteria.input_examples, criteria.expected_outputs = \
                TestableFeatureParser._parse_io_examples(io_section)
        
        # Extract edge cases
        edge_section = TestableFeatureParser._extract_section(content, "Edge Cases?|Boundary")
        if edge_section:
            criteria.edge_cases = TestableFeatureParser._parse_list_items(edge_section)
        
        # Extract error conditions
        error_section = TestableFeatureParser._extract_section(content, "Error|Exception|Validation")
        if error_section:
            criteria.error_conditions = TestableFeatureParser._parse_list_items(error_section)
        
        # If no explicit criteria found, infer from description
        if not any([criteria.input_examples, criteria.edge_cases, criteria.error_conditions]):
            criteria = TestableFeatureParser._infer_criteria(description)
            
        return criteria
    
    @staticmethod
    def _parse_io_examples(text: str) -> Tuple[List[Dict[str, Any]], List[Any]]:
        """Parse input/output examples from text"""
        inputs = []
        outputs = []
        
        # Look for patterns like "Input: X, Output: Y"
        io_pattern = r'Input:\s*([^,\n]+),?\s*Output:\s*([^\n]+)'
        matches = re.findall(io_pattern, text, re.IGNORECASE)
        
        for inp, out in matches:
            inputs.append({"raw": inp.strip()})
            outputs.append(out.strip())
            
        # Also look for function call examples
        func_pattern = r'(\w+)\(([^)]*)\)\s*(?:->|returns?|=)\s*([^\n]+)'
        func_matches = re.findall(func_pattern, text)
        
        for func, args, result in func_matches:
            inputs.append({"function": func, "args": args.strip()})
            outputs.append(result.strip())
            
        return inputs, outputs
    
    @staticmethod
    def _parse_list_items(text: str) -> List[str]:
        """Parse bullet points or numbered items from text"""
        items = []
        
        # Match various list formats
        list_pattern = r'(?:^|\n)\s*(?:[-*•·]|\d+\.)\s+([^\n]+)'
        matches = re.findall(list_pattern, text, re.MULTILINE)
        
        items.extend(match.strip() for match in matches)
        
        # If no list items found, split by common separators
        if not items and text:
            # Try splitting by commas or semicolons
            if ',' in text or ';' in text:
                items = [item.strip() for item in re.split(r'[,;]', text) if item.strip()]
            else:
                # Use the whole text as a single item
                items = [text.strip()]
                
        return items
    
    @staticmethod
    def _infer_criteria(description: str) -> TestCriteria:
        """Infer test criteria from feature description"""
        criteria = TestCriteria(description=description)
        
        # Common patterns for different types of features
        lower_desc = description.lower()
        
        # Math/calculation features
        if any(word in lower_desc for word in ['add', 'subtract', 'multiply', 'divide', 'calculate']):
            criteria.input_examples = [
                {"args": "2, 3"},
                {"args": "0, 5"},
                {"args": "-1, 1"}
            ]
            criteria.edge_cases = ["Zero inputs", "Negative numbers", "Large numbers"]
            if 'divide' in lower_desc:
                criteria.error_conditions = ["Division by zero"]
                
        # CRUD operations
        elif any(word in lower_desc for word in ['create', 'add', 'insert', 'save']):
            criteria.input_examples = [{"data": "Valid object"}]
            criteria.edge_cases = ["Empty data", "Duplicate entries"]
            criteria.error_conditions = ["Invalid data format", "Missing required fields"]
            
        elif any(word in lower_desc for word in ['get', 'fetch', 'retrieve', 'find']):
            criteria.input_examples = [{"id": "existing_id"}]
            criteria.edge_cases = ["Non-existent ID", "Invalid ID format"]
            criteria.error_conditions = ["Not found error"]
            
        elif any(word in lower_desc for word in ['update', 'modify', 'edit']):
            criteria.input_examples = [{"id": "existing_id", "data": "Updated data"}]
            criteria.edge_cases = ["Partial updates", "No changes"]
            criteria.error_conditions = ["Not found", "Invalid update data"]
            
        elif any(word in lower_desc for word in ['delete', 'remove']):
            criteria.input_examples = [{"id": "existing_id"}]
            criteria.edge_cases = ["Already deleted", "Non-existent"]
            criteria.error_conditions = ["Not found", "Cannot delete"]
            
        # Validation features
        elif any(word in lower_desc for word in ['validate', 'check', 'verify']):
            criteria.input_examples = [{"input": "Valid data"}, {"input": "Invalid data"}]
            criteria.edge_cases = ["Empty input", "Boundary values"]
            criteria.error_conditions = ["Validation failure"]
            
        # API endpoints
        elif any(word in lower_desc for word in ['endpoint', 'api', 'route']):
            criteria.input_examples = [{"method": "GET/POST", "path": "/resource"}]
            criteria.edge_cases = ["Missing parameters", "Invalid auth"]
            criteria.error_conditions = ["400 Bad Request", "401 Unauthorized", "404 Not Found"]
            
        # Generic fallback
        else:
            criteria.input_examples = [{"input": "Sample input"}]
            criteria.edge_cases = ["Empty input", "Invalid input"]
            criteria.error_conditions = ["Error handling"]
            
        return criteria
    
    @staticmethod
    def _parse_simple_features(design_output: str) -> List[TestableFeature]:
        """Fallback parser for simple feature lists"""
        features = []
        
        # Look for numbered features or bullet points
        pattern = r'(?:^|\n)\s*(?:\d+\.|-|\*|•)\s+([^\n]+(?:\n(?!\s*(?:\d+\.|-|\*|•))[^\n]+)*)'
        matches = re.findall(pattern, design_output, re.MULTILINE)
        
        if not matches:
            # Ultra-fallback: treat the whole output as one feature
            matches = [design_output[:500]]
            
        for i, match in enumerate(matches, 1):
            title = match.strip().split('\n')[0][:100]
            description = match.strip()
            
            # Infer criteria based on description
            criteria = TestableFeatureParser._infer_criteria(description)
            
            features.append(TestableFeature(
                id=f"feature_{i}",
                title=title,
                description=description,
                test_criteria=criteria,
                dependencies=[]
            ))
            
        return features
    
    @staticmethod
    def _force_extract_all_features(design_output: str) -> List[TestableFeature]:
        """
        Force extract all features when the standard pattern fails.
        Uses multiple strategies to ensure all features are captured.
        """
        features = []
        
        # Strategy 1: Split by FEATURE[ and process each block
        feature_blocks = re.split(r'(?=FEATURE\[\d+\])', design_output)
        
        for block in feature_blocks:
            if 'FEATURE[' not in block:
                continue
                
            # Extract feature number and title
            feature_match = re.match(r'FEATURE\[(\d+)\]:\s*([^\n]+)', block)
            if feature_match:
                feature_num, title = feature_match.groups()
                feature_id = f"feature_{feature_num}"
                
                # Get the rest of the block content
                content = block[feature_match.end():]
                
                # Extract sections
                description = TestableFeatureParser._extract_section(content, "Description")
                if not description:
                    # Use first few lines as description
                    lines = content.strip().split('\n')
                    description = '\n'.join(lines[:3])
                
                # Extract dependencies from the entire block (not just content)
                dependencies = TestableFeatureParser._extract_dependencies(block)
                test_criteria = TestableFeatureParser._extract_test_criteria(content, description)
                
                features.append(TestableFeature(
                    id=feature_id,
                    title=title.strip(),
                    description=description,
                    test_criteria=test_criteria,
                    dependencies=dependencies
                ))
        
        # If still no features, try line-by-line extraction
        if not features:
            lines = design_output.split('\n')
            current_feature = None
            
            for line in lines:
                feature_match = re.match(r'FEATURE\[(\d+)\]:\s*(.+)', line)
                if feature_match:
                    # Save previous feature if exists
                    if current_feature:
                        features.append(current_feature)
                    
                    # Start new feature
                    feature_num, title = feature_match.groups()
                    current_feature = TestableFeature(
                        id=f"feature_{feature_num}",
                        title=title.strip(),
                        description="",
                        test_criteria=TestCriteria(description=""),
                        dependencies=[]
                    )
                elif current_feature and line.strip():
                    # Add to current feature description
                    if not current_feature.description:
                        current_feature.description = line.strip()
                    else:
                        current_feature.description += f"\n{line.strip()}"
            
            # Add last feature
            if current_feature:
                features.append(current_feature)
        
        # Ensure test criteria for all features
        for feature in features:
            if not feature.test_criteria.description:
                feature.test_criteria = TestableFeatureParser._infer_criteria(feature.description)
        
        return features


def parse_testable_features(design_output: str) -> List[Dict[str, Any]]:
    """
    Main entry point for parsing features with testable criteria.
    Returns list of feature dictionaries for compatibility.
    """
    testable_features = TestableFeatureParser.parse_features_with_criteria(design_output)
    
    # Log feature extraction results
    logger.info(f"Extracted {len(testable_features)} features from design output")
    
    # Validate we got a reasonable number of features
    if len(testable_features) == 1:
        logger.warning("Only extracted 1 feature - checking if expansion is needed")
        
        # Check if design output mentions multiple features but we only extracted one
        feature_count = design_output.count("FEATURE[")
        if feature_count > 1:
            logger.error(f"Design contains {feature_count} FEATURE blocks but only extracted 1")
            # Try alternative parsing
            testable_features = TestableFeatureParser._force_extract_all_features(design_output)
            logger.info(f"Force extraction found {len(testable_features)} features")
    
    return [f.to_dict() for f in testable_features]