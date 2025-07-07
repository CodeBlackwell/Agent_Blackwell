"""
Unit tests for workflow configuration with project structures
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.workflow_config import PROJECT_STRUCTURES, BUILD_CONFIGS


class TestWorkflowConfig(unittest.TestCase):
    """Test workflow configuration"""
    
    def test_project_structures_defined(self):
        """Test that project structures are properly defined"""
        # Should have at least these structures
        expected_structures = ['mean_stack', 'microservices', 'modular_monolith', 'simple_api']
        
        for structure in expected_structures:
            self.assertIn(structure, PROJECT_STRUCTURES)
            
            # Each structure should have required fields
            struct_def = PROJECT_STRUCTURES[structure]
            self.assertIn('name', struct_def)
            self.assertIn('description', struct_def)
            self.assertIn('structure', struct_def)
            
            # Structure should be a dict
            self.assertIsInstance(struct_def['structure'], dict)
    
    def test_mean_stack_structure(self):
        """Test MEAN stack structure is complete"""
        mean_structure = PROJECT_STRUCTURES['mean_stack']['structure']
        
        # Check backend structure
        self.assertIn('backend/', mean_structure)
        self.assertIn('src/', mean_structure['backend/'])
        self.assertIn('package.json', mean_structure['backend/'])
        
        # Check frontend structure
        self.assertIn('frontend/', mean_structure)
        self.assertIn('src/', mean_structure['frontend/'])
        self.assertIn('package.json', mean_structure['frontend/'])
        self.assertIn('angular.json', mean_structure['frontend/'])
        
        # Check shared and infrastructure
        self.assertIn('shared/', mean_structure)
        self.assertIn('docker-compose.yml', mean_structure)
        self.assertIn('.env.example', mean_structure)
    
    def test_microservices_structure(self):
        """Test microservices structure"""
        ms_structure = PROJECT_STRUCTURES['microservices']['structure']
        
        # Check services
        self.assertIn('services/', ms_structure)
        services = ms_structure['services/']
        
        # Should have multiple services
        self.assertIn('api-gateway/', services)
        self.assertIn('user-service/', services)
        self.assertIn('auth-service/', services)
        
        # Each service should have src and package.json
        for service_name, service_struct in services.items():
            if isinstance(service_struct, dict):
                self.assertIn('src/', service_struct)
                self.assertIn('package.json', service_struct)
    
    def test_modular_monolith_structure(self):
        """Test modular monolith structure"""
        mm_structure = PROJECT_STRUCTURES['modular_monolith']['structure']
        
        # Check src structure
        self.assertIn('src/', mm_structure)
        self.assertIn('modules/', mm_structure['src/'])
        
        # Check modules
        modules = mm_structure['src/']['modules/']
        self.assertIn('auth/', modules)
        self.assertIn('users/', modules)
        
        # Check auth module structure
        auth_module = modules['auth/']
        self.assertIn('controllers/', auth_module)
        self.assertIn('services/', auth_module)
        self.assertIn('models/', auth_module)
        
        # Check tests structure
        self.assertIn('tests/', mm_structure)
        tests = mm_structure['tests/']
        self.assertIn('unit/', tests)
        self.assertIn('integration/', tests)
        self.assertIn('e2e/', tests)
    
    def test_build_configs(self):
        """Test build configurations"""
        # Check required build configs exist
        expected_configs = ['angular', 'react', 'node_typescript', 'python']
        
        for config in expected_configs:
            self.assertIn(config, BUILD_CONFIGS)
            
            # Each config should have basic commands
            build_conf = BUILD_CONFIGS[config]
            if config != 'python':
                self.assertIn('install', build_conf)
                self.assertIn('build', build_conf)
                self.assertIn('serve', build_conf)
            else:
                # Python doesn't always have build step
                self.assertIn('install', build_conf)
                self.assertIn('serve', build_conf)
    
    def test_angular_build_config(self):
        """Test Angular specific build config"""
        angular_config = BUILD_CONFIGS['angular']
        
        self.assertEqual(angular_config['install'], 'npm install')
        self.assertEqual(angular_config['build'], 'npm run build')
        self.assertEqual(angular_config['test'], 'npm run test')
        self.assertEqual(angular_config['serve'], 'npm run start')
    
    def test_python_build_config(self):
        """Test Python build config"""
        python_config = BUILD_CONFIGS['python']
        
        self.assertEqual(python_config['install'], 'pip install -r requirements.txt')
        self.assertEqual(python_config['test'], 'pytest')
        self.assertEqual(python_config['serve'], 'python main.py')
    
    def test_structure_can_be_used_as_template(self):
        """Test that structures can be used as templates for project generation"""
        # Get MEAN stack structure
        mean_template = PROJECT_STRUCTURES['mean_stack']
        
        # Simulate using it as a template
        def generate_file_list(structure, prefix=''):
            """Recursively generate file list from structure"""
            files = []
            
            for key, value in structure.items():
                path = prefix + key
                
                if isinstance(value, dict):
                    # It's a directory, recurse
                    files.extend(generate_file_list(value, path))
                else:
                    # It's a file or description
                    if not key.endswith('/'):
                        files.append(path)
            
            return files
        
        # Generate file list
        files = generate_file_list(mean_template['structure'])
        
        # Should generate multiple files
        self.assertGreater(len(files), 5)
        
        # Should include key files
        self.assertIn('backend/package.json', files)
        self.assertIn('frontend/package.json', files)
        self.assertIn('docker-compose.yml', files)


if __name__ == '__main__':
    unittest.main()