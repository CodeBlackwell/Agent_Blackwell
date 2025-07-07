#!/usr/bin/env python3
"""
Unit tests for language detection in MVP Incremental workflow
Tests the _detect_primary_language function without requiring full workflow execution
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the function directly from the workflow
from workflows.mvp_incremental.mvp_incremental import _detect_primary_language


class TestLanguageDetection(unittest.TestCase):
    """Test language detection functionality"""
    
    def test_empty_files(self):
        """Test with empty file dictionary"""
        result = _detect_primary_language({})
        self.assertEqual(result, 'python')  # Default
    
    def test_pure_python_project(self):
        """Test detection of pure Python project"""
        code_files = {
            'main.py': 'print("Hello World")',
            'utils.py': 'def helper(): pass',
            'test_main.py': 'import unittest'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'python')
    
    def test_pure_javascript_project(self):
        """Test detection of pure JavaScript project"""
        code_files = {
            'index.js': 'console.log("Hello");',
            'server.js': 'const express = require("express");',
            'utils.js': 'module.exports = {};'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'javascript')
    
    def test_pure_typescript_project(self):
        """Test detection of pure TypeScript project"""
        code_files = {
            'index.ts': 'const x: string = "Hello";',
            'app.ts': 'interface User { name: string; }',
            'types.ts': 'export type ID = string | number;'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'typescript')
    
    def test_node_project_with_package_json(self):
        """Test Node.js project detection via package.json"""
        code_files = {
            'package.json': '{"name": "my-app", "version": "1.0.0"}',
            'index.js': 'console.log("Hello");'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'javascript')
    
    def test_angular_project_detection(self):
        """Test Angular project detection (TypeScript)"""
        code_files = {
            'package.json': '{"name": "angular-app"}',
            'angular.json': '{"projects": {}}',
            'app.component.ts': 'export class AppComponent {}',
            'app.module.ts': 'import { NgModule } from "@angular/core";'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'typescript')
    
    def test_typescript_with_package_json(self):
        """Test TypeScript detection when package.json exists"""
        code_files = {
            'package.json': '{"name": "ts-app"}',
            'index.ts': 'const x: number = 42;',
            'server.ts': 'import express from "express";'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'typescript')
    
    def test_mixed_language_majority_wins(self):
        """Test mixed language project - majority wins"""
        code_files = {
            'main.py': 'print("Python")',
            'server.js': 'console.log("JS");',
            'app.js': 'const app = express();',
            'utils.js': 'module.exports = {};'
        }
        result = _detect_primary_language(code_files)
        self.assertEqual(result, 'javascript')  # 3 JS files vs 1 Python
    
    def test_config_files_ignored(self):
        """Test that config files are ignored in language detection"""
        # Test 1: Python project with requirements.txt
        python_files = {
            'requirements.txt': 'flask==2.0',
            'main.py': 'print("Hello")',
            'app.py': 'from flask import Flask'
        }
        result = _detect_primary_language(python_files)
        self.assertEqual(result, 'python')  # 2 Python files
        
        # Test 2: Mixed project with package.json takes precedence
        mixed_files = {
            'package.json': '{}',
            'tsconfig.json': '{}',
            'requirements.txt': 'flask==2.0',
            'main.py': 'print("Hello")',
            'app.py': 'from flask import Flask'
        }
        result = _detect_primary_language(mixed_files)
        self.assertEqual(result, 'javascript')  # package.json indicates Node.js project
    
    def test_mean_stack_components(self):
        """Test MEAN stack component detection"""
        # MongoDB + Express (Node.js backend)
        backend_files = {
            'server.js': 'const mongoose = require("mongoose");',
            'app.js': 'const express = require("express");',
            'models/user.js': 'const Schema = mongoose.Schema;'
        }
        result = _detect_primary_language(backend_files)
        self.assertEqual(result, 'javascript')
        
        # Angular frontend
        frontend_files = {
            'angular.json': '{}',
            'package.json': '{}',
            'src/app/app.component.ts': 'export class AppComponent {}',
            'src/app/app.module.ts': 'import { NgModule } from "@angular/core";'
        }
        result = _detect_primary_language(frontend_files)
        self.assertEqual(result, 'typescript')
    
    def test_other_languages(self):
        """Test detection of other languages"""
        # Java
        java_files = {
            'Main.java': 'public class Main {}',
            'Utils.java': 'public class Utils {}'
        }
        result = _detect_primary_language(java_files)
        self.assertEqual(result, 'java')
        
        # Go
        go_files = {
            'main.go': 'package main',
            'utils.go': 'package utils'
        }
        result = _detect_primary_language(go_files)
        self.assertEqual(result, 'go')
        
        # Ruby
        ruby_files = {
            'app.rb': 'puts "Hello"',
            'server.rb': 'require "sinatra"'
        }
        result = _detect_primary_language(ruby_files)
        self.assertEqual(result, 'ruby')
    
    def test_react_jsx_detection(self):
        """Test React JSX file detection"""
        react_files = {
            'App.jsx': 'export default function App() {}',
            'index.js': 'ReactDOM.render(<App />, root);',
            'components/Button.jsx': 'export const Button = () => {}'
        }
        result = _detect_primary_language(react_files)
        self.assertEqual(result, 'javascript')
        
        # React with TypeScript
        react_ts_files = {
            'App.tsx': 'const App: React.FC = () => {}',
            'index.tsx': 'ReactDOM.render(<App />, root);'
        }
        result = _detect_primary_language(react_ts_files)
        self.assertEqual(result, 'typescript')


if __name__ == '__main__':
    unittest.main()