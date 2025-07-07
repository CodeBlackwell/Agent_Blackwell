#!/usr/bin/env python3
"""
Mock container tests for runtime selection in MVP Incremental workflow
Tests container selection logic without requiring actual Docker
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.validator.container_manager import ValidatorContainerManager


class TestRuntimeContainerSelection(unittest.TestCase):
    """Test container selection and runtime management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ValidatorContainerManager()
        self.manager._initialized = True
        self.manager.docker_client = Mock()
        self.manager.network = Mock()
        self.manager._containers = {}
    
    @patch('docker.from_env')
    def test_container_image_selection(self, mock_docker):
        """Test that correct Docker images are selected for each language"""
        # Mock Docker client
        mock_client = Mock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True
        
        # Test cases for different languages
        test_cases = [
            ('python', 'python:3.9-slim', []),
            ('javascript', 'node:18-alpine', ['apk add --no-cache python3 make g++']),
            ('nodejs', 'node:18-alpine', ['apk add --no-cache python3 make g++']),
            ('typescript', 'node:18-alpine', ['apk add --no-cache python3 make g++']),
            ('java', 'openjdk:11-slim', []),
            ('go', 'golang:1.19-alpine', []),
            ('unknown', 'python:3.9-slim', [])  # Default fallback
        ]
        
        for language, expected_image, expected_setup_cmds in test_cases:
            with self.subTest(language=language):
                # Mock container creation
                mock_container = Mock()
                mock_container.id = f'container_{language}'
                mock_container.reload = Mock()
                mock_container.exec_run = Mock()
                
                self.manager.docker_client.containers.run.return_value = mock_container
                
                # Create container
                container_info = self.manager._create_container('test_session', language)
                
                # Verify correct image was used
                call_args = self.manager.docker_client.containers.run.call_args
                self.assertEqual(call_args[0][0], expected_image)
                
                # Verify setup commands
                if expected_setup_cmds:
                    for cmd in expected_setup_cmds:
                        mock_container.exec_run.assert_any_call(cmd)
                
                # Verify container info
                self.assertEqual(container_info['language'], 
                               language if language != 'unknown' else 'python')
    
    def test_container_reuse_same_language(self):
        """Test container reuse when language matches"""
        # Create initial container
        mock_container = Mock()
        mock_container.status = 'running'
        
        self.manager._containers['session1'] = {
            'container_id': 'container1',
            'language': 'javascript'
        }
        
        self.manager.docker_client.containers.get.return_value = mock_container
        
        # Request container with same language
        result = self.manager.get_or_create_container('session1', 'javascript')
        
        # Should reuse existing container
        self.assertEqual(result['container_id'], 'container1')
        self.manager.docker_client.containers.run.assert_not_called()
    
    def test_container_recreation_different_language(self):
        """Test container recreation when language changes"""
        # Create initial Python container
        mock_old_container = Mock()
        mock_old_container.status = 'running'
        
        self.manager._containers['session1'] = {
            'container_id': 'python_container',
            'language': 'python'
        }
        
        # Mock new container for JavaScript
        mock_new_container = Mock()
        mock_new_container.id = 'js_container'
        mock_new_container.reload = Mock()
        mock_new_container.exec_run = Mock()
        
        self.manager.docker_client.containers.get.return_value = mock_old_container
        self.manager.docker_client.containers.run.return_value = mock_new_container
        
        # Request container with different language
        result = self.manager.get_or_create_container('session1', 'javascript')
        
        # Should cleanup old container (might be called multiple times during cleanup)
        mock_old_container.stop.assert_called()
        mock_old_container.remove.assert_called()
        
        # Should create new container with Node.js image
        call_args = self.manager.docker_client.containers.run.call_args
        self.assertEqual(call_args[0][0], 'node:18-alpine')
        self.assertEqual(result['language'], 'javascript')
    
    def test_execution_command_selection(self):
        """Test that correct execution commands are selected for each language"""
        # Mock container and Docker operations
        mock_container = Mock()
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b'Success', b'')
        mock_container.exec_run.return_value = mock_exec_result
        mock_container.put_archive = Mock()
        
        self.manager.docker_client.containers.get.return_value = mock_container
        self.manager._containers['test'] = {
            'container_id': 'test_container',
            'language': 'python'
        }
        
        # Test Python execution
        python_files = {'main.py': 'print("Hello")'}
        success, stdout, stderr = self.manager.execute_code('test', python_files)
        
        # Verify Python execution command
        exec_calls = [call[0][0] for call in mock_container.exec_run.call_args_list]
        self.assertIn('python main.py', exec_calls)
        
        # Reset mocks
        mock_container.exec_run.reset_mock()
        
        # Test JavaScript execution
        js_files = {'index.js': 'console.log("Hello");'}
        self.manager._containers['test']['language'] = 'javascript'
        success, stdout, stderr = self.manager.execute_code('test', js_files)
        
        # Verify Node.js execution command
        exec_calls = [call[0][0] for call in mock_container.exec_run.call_args_list]
        self.assertIn('node index.js', exec_calls)
    
    def test_typescript_compilation_flow(self):
        """Test TypeScript compilation before execution"""
        # Mock container
        mock_container = Mock()
        mock_compile_result = Mock()
        mock_compile_result.exit_code = 0
        mock_compile_result.output = (b'', b'')
        
        mock_run_result = Mock()
        mock_run_result.exit_code = 0
        mock_run_result.output = (b'Hello from TypeScript', b'')
        
        # Set up exec_run to return different results for compile and run
        mock_container.exec_run.side_effect = [mock_compile_result, mock_run_result]
        mock_container.put_archive = Mock()
        
        self.manager.docker_client.containers.get.return_value = mock_container
        self.manager._containers['test'] = {
            'container_id': 'test_container',
            'language': 'typescript'
        }
        
        # Test TypeScript execution
        ts_files = {'index.ts': 'const msg: string = "Hello"; console.log(msg);'}
        success, stdout, stderr = self.manager.execute_code('test', ts_files)
        
        # Verify TypeScript compilation was called first
        self.assertEqual(mock_container.exec_run.call_count, 2)
        compile_call = mock_container.exec_run.call_args_list[0]
        run_call = mock_container.exec_run.call_args_list[1]
        
        self.assertEqual(compile_call[0][0], 'npx tsc')
        self.assertEqual(run_call[0][0], 'node index.js')
    
    def test_dependency_installation(self):
        """Test automatic dependency installation for different languages"""
        # Mock container
        mock_container = Mock()
        mock_install_result = Mock()
        mock_install_result.exit_code = 0
        mock_install_result.output = (b'Dependencies installed', b'')
        
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b'Success', b'')
        
        mock_container.exec_run.side_effect = [mock_install_result, mock_exec_result]
        mock_container.put_archive = Mock()
        
        self.manager.docker_client.containers.get.return_value = mock_container
        
        # Test Python with detected dependencies
        self.manager._containers['test'] = {
            'container_id': 'test_container',
            'language': 'python'
        }
        
        python_files = {
            'app.py': '''
import flask
from fastapi import FastAPI
import requests
'''
        }
        
        success, stdout, stderr = self.manager.execute_code('test', python_files)
        
        # Verify pip install was called with detected packages
        install_call = mock_container.exec_run.call_args_list[0]
        self.assertIn('pip install', install_call[0][0])
        self.assertIn('flask', install_call[0][0])
        self.assertIn('fastapi', install_call[0][0])
        self.assertIn('requests', install_call[0][0])
    
    def test_mongodb_container_creation(self):
        """Test MongoDB container creation when needed"""
        # Mock main container
        mock_container = Mock()
        self.manager._containers['test'] = {
            'container_id': 'test_container',
            'language': 'javascript'
        }
        
        # Mock MongoDB container creation
        mock_mongo_container = Mock()
        mock_mongo_container.id = 'mongo_container'
        
        # First call returns NotFound, second creates container
        import docker.errors
        self.manager.docker_client.containers.get.side_effect = [
            mock_container,  # Main container exists
            docker.errors.NotFound('Not found'),  # MongoDB container doesn't exist
        ]
        self.manager.docker_client.containers.run.return_value = mock_mongo_container
        
        # Test with code that needs MongoDB
        js_files = {
            'server.js': '''
const mongoose = require('mongoose');
mongoose.connect('mongodb://localhost:27017/myapp');
'''
        }
        
        # Execute code (which should trigger MongoDB container creation)
        mock_container.exec_run.return_value = Mock(exit_code=0, output=(b'', b''))
        mock_container.put_archive = Mock()
        
        # Check if MongoDB is needed
        needs_mongo = self.manager._needs_database(js_files, 'mongodb')
        self.assertTrue(needs_mongo)
        
        # Get or create MongoDB container
        db_info = self.manager.get_or_create_db_container('test', 'mongodb')
        
        # Verify MongoDB container was created with correct image
        create_call = self.manager.docker_client.containers.run.call_args
        self.assertEqual(create_call[0][0], 'mongo:5.0')
        self.assertEqual(db_info['connection_string'], 'mongodb://validator_db_test:27017/')
    
    def test_mean_stack_container_setup(self):
        """Test complete MEAN stack container setup"""
        # Mock containers
        mock_node_container = Mock()
        mock_node_container.id = 'node_container'
        mock_node_container.reload = Mock()
        mock_node_container.exec_run = Mock(return_value=Mock(exit_code=0, output=(b'', b'')))
        mock_node_container.put_archive = Mock()
        
        mock_mongo_container = Mock()
        mock_mongo_container.id = 'mongo_container'
        
        self.manager.docker_client.containers.run.side_effect = [
            mock_node_container,  # Node.js container
            mock_mongo_container  # MongoDB container
        ]
        
        # MEAN stack backend files
        mean_files = {
            'server.js': '''
const express = require('express');
const mongoose = require('mongoose');
const app = express();
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/myapp');
''',
            'package.json': '{"name": "mean-backend", "dependencies": {}}'
        }
        
        # Create Node.js container for MEAN backend
        session_id = 'mean_session'
        language = self.manager._detect_language(mean_files)
        self.assertEqual(language, 'javascript')
        
        container_info = self.manager.get_or_create_container(session_id, language)
        
        # Verify Node.js container was created
        node_create_call = self.manager.docker_client.containers.run.call_args_list[0]
        self.assertEqual(node_create_call[0][0], 'node:18-alpine')
        
        # Check if MongoDB is needed
        needs_mongo = self.manager._needs_database(mean_files, 'mongodb')
        self.assertTrue(needs_mongo)


if __name__ == '__main__':
    unittest.main()