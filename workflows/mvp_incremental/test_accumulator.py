"""
Test Accumulator for MVP Incremental TDD Workflow

This module manages the accumulation and organization of tests as features are added.
It ensures tests are properly combined, dependencies are handled, and test suites grow incrementally.
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from workflows.logger import workflow_logger as logger


@dataclass
class TestFile:
    """Represents a test file with its contents and metadata"""
    filename: str
    content: str
    feature_id: str
    imports: Set[str] = field(default_factory=set)
    test_functions: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)


@dataclass
class TestSuite:
    """Represents the complete test suite for the project"""
    unit_tests: Dict[str, TestFile] = field(default_factory=dict)
    integration_tests: Dict[str, TestFile] = field(default_factory=dict)
    feature_map: Dict[str, List[str]] = field(default_factory=dict)  # feature_id -> test files
    test_order: List[str] = field(default_factory=list)  # Execution order


class TestAccumulator:
    """Manages the growing test suite as features are implemented"""
    
    def __init__(self):
        self.test_suite = TestSuite()
        self.framework_imports = {
            'python': {'import pytest', 'import unittest', 'from unittest.mock import'},
            'javascript': {'const { expect }', 'describe(', 'it(', 'test('},
        }
    
    def add_feature_tests(self, 
                         feature_id: str, 
                         test_code: str,
                         feature_dependencies: Optional[List[str]] = None) -> List[TestFile]:
        """
        Add tests for a new feature to the test suite.
        
        Args:
            feature_id: Unique identifier for the feature
            test_code: Generated test code for the feature
            feature_dependencies: List of feature IDs this feature depends on
            
        Returns:
            List of TestFile objects created
        """
        # Parse test files from the code
        test_files = self._parse_test_files(test_code, feature_id)
        
        # Analyze dependencies
        for test_file in test_files:
            test_file.dependencies = self._analyze_dependencies(
                test_file, 
                feature_dependencies or []
            )
        
        # Categorize and add tests
        for test_file in test_files:
            if self._is_integration_test(test_file):
                self.test_suite.integration_tests[test_file.filename] = test_file
            else:
                self.test_suite.unit_tests[test_file.filename] = test_file
            
            # Update feature map
            if feature_id not in self.test_suite.feature_map:
                self.test_suite.feature_map[feature_id] = []
            self.test_suite.feature_map[feature_id].append(test_file.filename)
        
        # Update test execution order
        self._update_test_order(test_files)
        
        logger.info(f"Added {len(test_files)} test files for feature {feature_id}")
        return test_files
    
    def get_combined_test_suite(self, test_type: str = "all") -> str:
        """
        Generate a combined test suite file.
        
        Args:
            test_type: "unit", "integration", or "all"
            
        Returns:
            Combined test code as string
        """
        if test_type == "unit":
            test_files = self.test_suite.unit_tests.values()
        elif test_type == "integration":
            test_files = self.test_suite.integration_tests.values()
        else:
            test_files = list(self.test_suite.unit_tests.values()) + \
                        list(self.test_suite.integration_tests.values())
        
        # Group by test file to avoid duplicates
        unique_files = {}
        for test_file in test_files:
            unique_files[test_file.filename] = test_file
        
        # Generate combined output
        output_parts = []
        
        for filename in self.test_suite.test_order:
            if filename in unique_files:
                test_file = unique_files[filename]
                output_parts.append(f"# {'-' * 60}")
                output_parts.append(f"# Tests from: {filename}")
                output_parts.append(f"# Feature: {test_file.feature_id}")
                output_parts.append(f"# {'-' * 60}")
                output_parts.append("")
                output_parts.append(test_file.content)
                output_parts.append("")
        
        return "\n".join(output_parts)
    
    def get_test_command(self, feature_id: Optional[str] = None) -> str:
        """
        Get the command to run tests.
        
        Args:
            feature_id: Optional feature ID to run specific feature tests
            
        Returns:
            Test execution command
        """
        if feature_id and feature_id in self.test_suite.feature_map:
            # Run tests for specific feature
            test_files = self.test_suite.feature_map[feature_id]
            return f"pytest {' '.join(test_files)} -v"
        else:
            # Run all tests
            all_files = list(self.test_suite.unit_tests.keys()) + \
                       list(self.test_suite.integration_tests.keys())
            if all_files:
                return f"pytest {' '.join(all_files)} -v"
            else:
                return "echo 'No tests to run'"
    
    def get_test_coverage_config(self) -> Dict[str, any]:
        """Generate test coverage configuration"""
        return {
            'minimum_coverage': 80,
            'coverage_paths': self._get_source_paths(),
            'omit_paths': ['tests/*', 'test_*', '*_test.py'],
            'coverage_command': 'pytest --cov=. --cov-report=html --cov-report=term'
        }
    
    def generate_test_runner_script(self) -> str:
        """Generate a test runner script"""
        script = '''#!/usr/bin/env python
"""
Automated Test Runner for TDD Workflow
Generated by MVP Incremental TDD
"""

import subprocess
import sys
import json
from pathlib import Path

def run_tests(test_type="all"):
    """Run tests with coverage reporting"""
    
    # Test commands based on type
    commands = {
        "unit": "pytest tests/unit -v --cov=src --cov-report=term-missing",
        "integration": "pytest tests/integration -v",
        "all": "pytest -v --cov=src --cov-report=html --cov-report=term"
    }
    
    command = commands.get(test_type, commands["all"])
    
    print(f"Running {test_type} tests...")
    print(f"Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        # Parse coverage if available
        if "--cov" in command and result.returncode == 0:
            print("\n" + "=" * 60)
            print("COVERAGE SUMMARY")
            print("=" * 60)
            # Coverage details would be parsed here
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    success = run_tests(test_type)
    sys.exit(0 if success else 1)
'''
        return script
    
    def _parse_test_files(self, test_code: str, feature_id: str) -> List[TestFile]:
        """Parse test files from generated test code"""
        test_files = []
        
        # Pattern to match test file blocks
        file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
        matches = re.findall(file_pattern, test_code, re.DOTALL)
        
        for filename, content in matches:
            test_file = TestFile(
                filename=filename,
                content=content.strip(),
                feature_id=feature_id
            )
            
            # Extract imports
            test_file.imports = self._extract_imports(content)
            
            # Extract test functions
            test_file.test_functions = self._extract_test_functions(content)
            
            test_files.append(test_file)
        
        # Fallback if no proper file markers found
        if not test_files and test_code.strip():
            # Assume it's a single test file
            filename = f"test_feature_{feature_id}.py"
            test_file = TestFile(
                filename=filename,
                content=test_code.strip(),
                feature_id=feature_id
            )
            test_file.imports = self._extract_imports(test_code)
            test_file.test_functions = self._extract_test_functions(test_code)
            test_files.append(test_file)
        
        return test_files
    
    def _extract_imports(self, content: str) -> Set[str]:
        """Extract import statements from code"""
        imports = set()
        
        # Python imports
        import_patterns = [
            r'^import\s+(\S+)',
            r'^from\s+(\S+)\s+import',
            r'^const\s+\{[^}]+\}\s*=\s*require\([\'"]([^\'"]+)[\'"]\)',
            r'^import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.update(matches)
        
        return imports
    
    def _extract_test_functions(self, content: str) -> List[str]:
        """Extract test function names"""
        functions = []
        
        # Python test functions
        py_patterns = [
            r'def\s+(test_\w+)\s*\(',
            r'async\s+def\s+(test_\w+)\s*\('
        ]
        
        # JavaScript test functions
        js_patterns = [
            r'test\s*\(\s*[\'"]([^\'"]]+)[\'"]',
            r'it\s*\(\s*[\'"]([^\'"]]+)[\'"]',
            r'describe\s*\(\s*[\'"]([^\'"]]+)[\'"]'
        ]
        
        for pattern in py_patterns + js_patterns:
            matches = re.findall(pattern, content)
            functions.extend(matches)
        
        return functions
    
    def _is_integration_test(self, test_file: TestFile) -> bool:
        """Determine if a test file contains integration tests"""
        indicators = [
            'integration' in test_file.filename.lower(),
            'e2e' in test_file.filename.lower(),
            'end_to_end' in test_file.filename.lower(),
            any('integration' in func.lower() for func in test_file.test_functions),
            'mock' not in test_file.content.lower() and len(test_file.imports) > 5
        ]
        
        return any(indicators)
    
    def _analyze_dependencies(self, 
                            test_file: TestFile, 
                            feature_dependencies: List[str]) -> Set[str]:
        """Analyze test dependencies"""
        dependencies = set(feature_dependencies)
        
        # Check imports for dependencies on other features
        for imp in test_file.imports:
            for feature_id in self.test_suite.feature_map:
                if feature_id.lower() in imp.lower():
                    dependencies.add(feature_id)
        
        return dependencies
    
    def _update_test_order(self, new_test_files: List[TestFile]):
        """Update test execution order based on dependencies"""
        # Add new files to order
        for test_file in new_test_files:
            if test_file.filename not in self.test_suite.test_order:
                # Find correct position based on dependencies
                insert_pos = len(self.test_suite.test_order)
                
                for i, existing_file in enumerate(self.test_suite.test_order):
                    # Check if new file depends on existing file
                    existing_features = self._get_features_for_file(existing_file)
                    if any(feat in test_file.dependencies for feat in existing_features):
                        insert_pos = max(insert_pos, i + 1)
                
                self.test_suite.test_order.insert(insert_pos, test_file.filename)
    
    def _get_features_for_file(self, filename: str) -> Set[str]:
        """Get feature IDs associated with a test file"""
        features = set()
        for feature_id, files in self.test_suite.feature_map.items():
            if filename in files:
                features.add(feature_id)
        return features
    
    def _get_source_paths(self) -> List[str]:
        """Get source code paths for coverage"""
        # Infer source paths from imports
        source_paths = {'src', 'lib', 'app'}
        
        for test_file in self.test_suite.unit_tests.values():
            for imp in test_file.imports:
                if '.' in imp:
                    path_parts = imp.split('.')
                    source_paths.add(path_parts[0])
        
        return list(source_paths)
    
    def generate_test_report(self) -> str:
        """Generate a summary report of the test suite"""
        report = f"""
# Test Suite Summary
==================

## Overview
- Total test files: {len(self.test_suite.unit_tests) + len(self.test_suite.integration_tests)}
- Unit test files: {len(self.test_suite.unit_tests)}
- Integration test files: {len(self.test_suite.integration_tests)}
- Features covered: {len(self.test_suite.feature_map)}

## Test Files by Feature
"""
        for feature_id, files in self.test_suite.feature_map.items():
            report += f"\n### {feature_id}\n"
            for file in files:
                test_type = "integration" if file in self.test_suite.integration_tests else "unit"
                report += f"- {file} ({test_type})\n"
        
        report += "\n## Test Execution Order\n"
        for i, filename in enumerate(self.test_suite.test_order, 1):
            report += f"{i}. {filename}\n"
        
        return report