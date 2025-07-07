"""
Unit tests for the enhanced container manager with multi-language support
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.validator.container_manager import ValidatorContainerManager


class TestContainerManager(unittest.TestCase):
    """Test container manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ValidatorContainerManager()
        self.manager._initialized = True
        self.manager.docker_client = Mock()
        self.manager.network = Mock()
        self.manager._containers = {}
        
    def test_detect_language_python(self):
        """Test language detection for Python files"""
        code_files = {
            'main.py': 'print("Hello")',
            'utils.py': 'def helper(): pass',
            'requirements.txt': 'flask==2.0.0'
        }
        
        language = self.manager._detect_language(code_files)
        self.assertEqual(language, 'python')
        
    def test_detect_language_javascript(self):
        """Test language detection for JavaScript files"""
        code_files = {
            'index.js': 'console.log("Hello")',
            'app.js': 'const express = require("express")',
            'package.json': '{"name": "test"}'
        }
        
        language = self.manager._detect_language(code_files)
        self.assertEqual(language, 'javascript')
        
    def test_detect_language_typescript(self):
        """Test language detection for TypeScript files"""
        code_files = {
            'index.ts': 'const x: string = "Hello"',
            'app.ts': 'interface User { name: string }'
        }
        
        language = self.manager._detect_language(code_files)
        self.assertEqual(language, 'typescript')
        
    def test_detect_language_mixed_prefers_majority(self):
        """Test language detection with mixed files prefers majority"""
        code_files = {
            'main.py': 'print("Hello")',
            'app.js': 'console.log("World")',
            'utils.js': 'module.exports = {}',
            'server.js': 'const http = require("http")'
        }
        
        language = self.manager._detect_language(code_files)
        self.assertEqual(language, 'javascript')
        
    def test_detect_python_dependencies(self):
        """Test Python dependency detection"""
        code_files = {
            'main.py': '''
import flask
from fastapi import FastAPI
import numpy as np
from pymongo import MongoClient
import requests
'''
        }
        
        deps = self.manager._detect_python_dependencies(code_files)
        self.assertIn('flask', deps)
        self.assertIn('fastapi', deps)
        self.assertIn('numpy', deps)
        self.assertIn('pymongo', deps)
        self.assertIn('requests', deps)
        
    def test_detect_node_dependencies(self):
        """Test Node.js dependency detection"""
        code_files = {
            'app.js': '''
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
import axios from 'axios';
import { Socket } from 'socket.io';
'''
        }
        
        deps = self.manager._detect_node_dependencies(code_files)
        self.assertIn('express', deps)
        self.assertIn('mongoose', deps)
        self.assertIn('cors', deps)
        self.assertIn('axios', deps)
        self.assertIn('socket.io', deps)
        
    def test_detect_node_dependencies_angular(self):
        """Test Angular dependency detection"""
        code_files = {
            'app.component.ts': '''
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
'''
        }
        
        deps = self.manager._detect_node_dependencies(code_files)
        # Should include all basic Angular packages
        self.assertIn('@angular/core', deps)
        self.assertIn('@angular/common', deps)
        
    def test_needs_database_python(self):
        """Test MongoDB detection for Python"""
        code_files = {
            'main.py': '''
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
'''
        }
        
        needs_db = self.manager._needs_database(code_files, 'mongodb')
        self.assertTrue(needs_db)
        
    def test_needs_database_nodejs(self):
        """Test MongoDB detection for Node.js"""
        code_files = {
            'app.js': '''
const mongoose = require('mongoose');
mongoose.connect('mongodb://localhost:27017/myapp');
'''
        }
        
        needs_db = self.manager._needs_database(code_files, 'mongodb')
        self.assertTrue(needs_db)
        
    def test_create_container_python(self):
        """Test Python container creation"""
        mock_container = Mock()
        mock_container.id = 'test_container_id'
        mock_container.reload = Mock()
        
        self.manager.docker_client.containers.run.return_value = mock_container
        
        container_info = self.manager._create_container('test_session', 'python')
        
        # Verify correct image was used
        self.manager.docker_client.containers.run.assert_called_once()
        call_args = self.manager.docker_client.containers.run.call_args
        self.assertEqual(call_args[0][0], 'python:3.9-slim')
        
        # Verify container info
        self.assertEqual(container_info['language'], 'python')
        self.assertEqual(container_info['session_id'], 'test_session')
        
    def test_create_container_nodejs(self):
        """Test Node.js container creation"""
        mock_container = Mock()
        mock_container.id = 'test_container_id'
        mock_container.reload = Mock()
        mock_container.exec_run = Mock()
        
        self.manager.docker_client.containers.run.return_value = mock_container
        
        container_info = self.manager._create_container('test_session', 'javascript')
        
        # Verify correct image was used
        self.manager.docker_client.containers.run.assert_called_once()
        call_args = self.manager.docker_client.containers.run.call_args
        self.assertEqual(call_args[0][0], 'node:18-alpine')
        
        # Verify setup commands were run
        mock_container.exec_run.assert_called_with('apk add --no-cache python3 make g++')
        
        # Verify container info
        self.assertEqual(container_info['language'], 'javascript')
        
    @patch('time.sleep')
    def test_mongodb_container_creation(self, mock_sleep):
        """Test MongoDB container creation"""
        mock_container = Mock()
        mock_container.id = 'mongo_container_id'
        
        self.manager.docker_client.containers.run.return_value = mock_container
        self.manager.docker_client.containers.get.side_effect = docker.errors.NotFound('Not found')
        
        # Import docker.errors for the test
        import docker.errors
        
        db_info = self.manager.get_or_create_db_container('test_session', 'mongodb')
        
        # Verify MongoDB container was created
        self.manager.docker_client.containers.run.assert_called_once()
        call_args = self.manager.docker_client.containers.run.call_args
        self.assertEqual(call_args[0][0], 'mongo:5.0')
        
        # Verify connection string
        self.assertEqual(db_info['connection_string'], 'mongodb://validator_db_test_session:27017/')
        
    def test_cleanup_containers(self):
        """Test container cleanup"""
        # Set up mock containers
        mock_app_container = Mock()
        mock_db_container = Mock()
        
        self.manager._containers['test_session'] = {
            'container_id': 'app_container_id'
        }
        
        def get_container(container_id):
            if container_id == 'app_container_id':
                return mock_app_container
            elif container_id == 'validator_db_test_session':
                return mock_db_container
            raise docker.errors.NotFound('Not found')
            
        self.manager.docker_client.containers.get.side_effect = get_container
        
        # Import docker.errors for the test
        import docker.errors
        
        # Run cleanup
        self.manager.cleanup_container('test_session')
        
        # Verify both containers were stopped and removed
        mock_app_container.stop.assert_called_once()
        mock_app_container.remove.assert_called_once()
        mock_db_container.stop.assert_called_once()
        mock_db_container.remove.assert_called_once()
        
        # Verify session was removed from tracking
        self.assertNotIn('test_session', self.manager._containers)
        
    def test_network_initialization(self):
        """Test network creation during initialization"""
        mock_network = Mock()
        self.manager.docker_client = Mock()
        self.manager.docker_client.ping = Mock()
        self.manager.docker_client.networks.get.side_effect = docker.errors.NotFound('Not found')
        self.manager.docker_client.networks.create.return_value = mock_network
        
        # Import docker.errors for the test
        import docker.errors
        
        # Reset initialization flag to test
        self.manager._initialized = False
        self.manager.network = None
        
        # Initialize
        self.manager.initialize()
        
        # Verify network was created
        self.manager.docker_client.networks.create.assert_called_once_with(
            "validator_network",
            driver="bridge",
            labels={"validator": "true"}
        )
        
        self.assertEqual(self.manager.network, mock_network)


if __name__ == '__main__':
    unittest.main()