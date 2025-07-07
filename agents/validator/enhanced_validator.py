"""
Enhanced Validator with Multi-Container Support
Supports both single container and docker-compose based validation
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.validator.container_manager import get_container_manager
from agents.validator.docker_compose_manager import DockerComposeManager
from workflows.logger import workflow_logger as logger


class EnhancedValidator:
    """Enhanced validator that supports both single and multi-container validation"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.container_manager = get_container_manager()
        self.compose_manager = None
        self.temp_dir = None
        
    def validate_code(self, code_files: Dict[str, str], 
                     test_commands: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Validate code with automatic detection of single vs multi-container setup
        
        Args:
            code_files: Dictionary mapping filenames to content
            test_commands: Optional list of test commands to run
            
        Returns:
            Tuple of (success, output)
        """
        # Create temporary directory for code
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"validator_{self.session_id}_"))
        
        try:
            # Write files to temp directory
            self._write_files_to_temp(code_files)
            
            # Check for docker-compose.yml
            compose_path = DockerComposeManager.detect_compose_file(self.temp_dir)
            
            if compose_path:
                # Use multi-container validation
                logger.info("Detected docker-compose.yml - using multi-container validation")
                return self._validate_with_compose(compose_path, test_commands)
            else:
                # Use single container validation
                logger.info("No docker-compose.yml - using single container validation")
                return self._validate_with_single_container(code_files, test_commands)
                
        finally:
            # Cleanup temp directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
    
    def _write_files_to_temp(self, code_files: Dict[str, str]):
        """Write code files to temporary directory preserving structure"""
        for filepath, content in code_files.items():
            # Create full path
            full_path = self.temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content)
            logger.debug(f"Wrote file: {filepath}")
    
    def _validate_with_single_container(self, code_files: Dict[str, str], 
                                      test_commands: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Validate using single container approach"""
        try:
            # Execute code in container
            success, stdout, stderr = self.container_manager.execute_code(
                self.session_id,
                code_files
            )
            
            if not success:
                return False, f"Code execution failed:\n{stderr}"
            
            output = [f"Code execution successful:\n{stdout}"]
            
            # Run test commands if provided
            if test_commands:
                container = self.container_manager.get_container(self.session_id)
                if container:
                    for cmd in test_commands:
                        logger.info(f"Running test command: {cmd}")
                        exit_code, cmd_output = container.exec_run(cmd, workdir="/code")
                        
                        if exit_code != 0:
                            return False, f"Test command failed: {cmd}\n{cmd_output.decode()}"
                        
                        output.append(f"Test '{cmd}' passed:\n{cmd_output.decode()}")
            
            return True, "\n\n".join(output)
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _validate_with_compose(self, compose_path: Path, 
                             test_commands: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Validate using docker-compose approach"""
        self.compose_manager = DockerComposeManager(self.session_id)
        
        try:
            # Parse compose file
            config = self.compose_manager.parse_compose_file(compose_path)
            logger.info(f"Parsed compose file with {len(config.services)} services")
            
            # Start services
            self.compose_manager.start_services(self.temp_dir)
            
            # Wait for services to be healthy
            if not self.compose_manager.wait_for_healthy(timeout=120):
                return False, "Services failed to become healthy"
            
            output = ["All services started successfully"]
            
            # Get service status
            status = self.compose_manager.get_service_status()
            for service, info in status.items():
                output.append(f"Service '{service}': {info['status']} (health: {info['health']})")
            
            # Run test commands if provided
            if test_commands:
                # Determine which service to run tests in
                test_service = self._find_test_service(config.services)
                
                for cmd in test_commands:
                    logger.info(f"Running test command in {test_service}: {cmd}")
                    exit_code, cmd_output = self.compose_manager.execute_in_service(
                        test_service, cmd
                    )
                    
                    if exit_code != 0:
                        # Get logs from failed service
                        logs = self.compose_manager.get_service_logs(test_service, lines=50)
                        return False, f"Test command failed: {cmd}\nOutput: {cmd_output}\nLogs:\n{logs}"
                    
                    output.append(f"Test '{cmd}' passed:\n{cmd_output}")
            
            return True, "\n\n".join(output)
            
        except Exception as e:
            # Get logs from all services on failure
            error_output = [f"Compose validation failed: {str(e)}"]
            
            if self.compose_manager and hasattr(self.compose_manager, 'containers'):
                for service_name in self.compose_manager.containers:
                    try:
                        logs = self.compose_manager.get_service_logs(service_name, lines=30)
                        error_output.append(f"\nLogs from {service_name}:\n{logs}")
                    except:
                        pass
            
            return False, "\n".join(error_output)
            
        finally:
            # Cleanup compose resources
            if self.compose_manager:
                self.compose_manager.cleanup()
    
    def _find_test_service(self, services: Dict) -> str:
        """Find the appropriate service to run tests in"""
        # Priority order for test execution
        priority_names = ['app', 'backend', 'api', 'web', 'server']
        
        # Check for services with these names
        for name in priority_names:
            if name in services:
                return name
        
        # Check for services with test-related environment
        for name, service in services.items():
            env = service.environment or {}
            if any(key.lower() in ['node_env', 'environment'] for key in env):
                return name
        
        # Default to first service
        return list(services.keys())[0] if services else None
    
    def cleanup_session(self):
        """Clean up resources for this session"""
        # Clean up single container
        self.container_manager.cleanup_container(self.session_id)
        
        # Clean up compose if used
        if self.compose_manager:
            self.compose_manager.cleanup()


def create_validator(session_id: str) -> EnhancedValidator:
    """Factory function to create validator instance"""
    return EnhancedValidator(session_id)