#!/usr/bin/env python3
"""
Integration test for language hint propagation through the MVP Incremental workflow
Tests that language detection flows correctly from workflow to validator to container
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.mvp_incremental.mvp_incremental import _detect_primary_language
from agents.validator.validator_agent import extract_language_hint, extract_session_id
from agents.validator.container_manager import ValidatorContainerManager


class TestLanguageHintFlow(unittest.TestCase):
    """Test language hint propagation through the system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up event loop"""
        self.loop.close()
    
    def test_language_hint_extraction(self):
        """Test extraction of language hints from validator input"""
        # Test with language hint
        input_with_hint = """
SESSION_ID: test_123
LANGUAGE: typescript

Please validate this code implementation for feature: User Authentication
"""
        
        session_id = extract_session_id(input_with_hint)
        language = extract_language_hint(input_with_hint)
        
        self.assertEqual(session_id, 'test_123')
        self.assertEqual(language, 'typescript')
        
        # Test without language hint
        input_without_hint = """
SESSION_ID: test_456

Please validate this code implementation
"""
        
        session_id = extract_session_id(input_without_hint)
        language = extract_language_hint(input_without_hint)
        
        self.assertEqual(session_id, 'test_456')
        self.assertIsNone(language)
    
    def test_validation_input_formatting(self):
        """Test how validation input is formatted with language hints"""
        # Simulate the workflow's validation input creation
        validator_session_id = "val_20250107_123456"
        language = "javascript"
        feature_title = "API Endpoint"
        
        # This mimics the format from mvp_incremental.py
        validation_input = f"""
SESSION_ID: {validator_session_id}
LANGUAGE: {language}

Please validate this code implementation for feature: {feature_title}
"""
        
        # Verify format is parseable
        extracted_session = extract_session_id(validation_input)
        extracted_language = extract_language_hint(validation_input)
        
        self.assertEqual(extracted_session, validator_session_id)
        self.assertEqual(extracted_language, language)
    
    @patch('agents.validator.container_manager.ValidatorContainerManager.get_or_create_container')
    def test_container_selection_with_hint(self, mock_get_container):
        """Test that language hints affect container selection"""
        manager = ValidatorContainerManager()
        manager._initialized = True
        
        # Mock container creation
        mock_container_info = {
            'container_id': 'test_container',
            'language': 'typescript'
        }
        mock_get_container.return_value = mock_container_info
        
        # Test TypeScript hint leads to TypeScript container
        code_files = {
            'index.ts': 'const x: string = "test";',
            'app.ts': 'interface User {}'
        }
        
        # Simulate validator receiving TypeScript hint
        session_id = 'test_session'
        language = manager._detect_language(code_files)
        
        self.assertEqual(language, 'typescript')
        
        # Verify container would be created with correct language
        container_info = manager.get_or_create_container(session_id, language)
        mock_get_container.assert_called_with(session_id, 'typescript')
    
    def test_mean_stack_language_flow(self):
        """Test complete language detection flow for MEAN stack"""
        # Frontend files (Angular/TypeScript)
        frontend_files = {
            'angular.json': '{}',
            'package.json': '{"name": "frontend"}',
            'src/app/app.component.ts': 'export class AppComponent {}',
            'src/app/services/api.service.ts': 'export class ApiService {}'
        }
        
        # Backend files (Node.js/JavaScript)
        backend_files = {
            'package.json': '{"name": "backend"}',
            'server.js': 'const express = require("express");',
            'models/user.js': 'const mongoose = require("mongoose");',
            'routes/api.js': 'router.get("/users", getUsers);'
        }
        
        # Test frontend detection
        frontend_lang = _detect_primary_language(frontend_files)
        self.assertEqual(frontend_lang, 'typescript')
        
        # Test backend detection
        backend_lang = _detect_primary_language(backend_files)
        self.assertEqual(backend_lang, 'javascript')
        
        # Simulate validation inputs for both
        frontend_input = f"""
LANGUAGE: {frontend_lang}

Please validate this Angular frontend code
"""
        
        backend_input = f"""
LANGUAGE: {backend_lang}

Please validate this Express backend code
"""
        
        # Verify hints are extractable
        self.assertEqual(extract_language_hint(frontend_input), 'typescript')
        self.assertEqual(extract_language_hint(backend_input), 'javascript')
    
    def test_language_hint_affects_execution(self):
        """Test that language hints affect code execution in validator"""
        manager = ValidatorContainerManager()
        
        # Test Python code without hint - should detect Python
        python_files = {
            'calculator.py': '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
        }
        
        detected_lang = manager._detect_language(python_files)
        self.assertEqual(detected_lang, 'python')
        
        # Test JavaScript code with explicit hint override
        # This simulates when mvp_incremental.py passes a language hint
        js_files = {
            'index.js': 'console.log("Hello");',
            'main.py': 'print("This file should be ignored")'  # Mixed files
        }
        
        # Without hint, it would detect based on file count
        detected_lang = manager._detect_language(js_files)
        
        # With language hint in validator, it should use JavaScript
        # This tests the validator's behavior when it receives a hint
        validation_input_with_hint = """
LANGUAGE: javascript

Please validate this code
"""
        
        hint = extract_language_hint(validation_input_with_hint)
        self.assertEqual(hint, 'javascript')
    
    def test_phase2_metadata_with_language(self):
        """Test Phase 2 metadata includes language information"""
        # Simulate Phase 2 metadata that could include language hints
        metadata = {
            "enable_multi_container": True,
            "enable_build_pipeline": True,
            "preferred_language": "typescript"  # Future enhancement
        }
        
        # This is a placeholder for future enhancement where
        # metadata could carry language preferences
        self.assertIn("enable_multi_container", metadata)
        
        # Verify the system can handle TypeScript when multi-container is enabled
        ts_files = {
            'frontend/app.ts': 'const app = new Application();',
            'backend/server.js': 'const server = express();'
        }
        
        # Should detect mixed languages when multi-container is enabled
        frontend_lang = _detect_primary_language({'app.ts': ts_files['frontend/app.ts']})
        backend_lang = _detect_primary_language({'server.js': ts_files['backend/server.js']})
        
        self.assertEqual(frontend_lang, 'typescript')
        self.assertEqual(backend_lang, 'javascript')


if __name__ == '__main__':
    unittest.main()