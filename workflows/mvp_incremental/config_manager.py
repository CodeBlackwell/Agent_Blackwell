"""
Configuration Manager for MVP Incremental Workflow

Handles environment configuration, validation, and management for generated applications.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from workflows.logger import setup_logger

logger = setup_logger(__name__)


class ConfigType(Enum):
    """Types of configuration values"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    URL = "url"
    PORT = "port"
    SECRET = "secret"
    FILE_PATH = "file_path"


@dataclass
class ConfigVariable:
    """Represents a configuration variable"""
    name: str
    value: Optional[str] = None
    default: Optional[str] = None
    description: Optional[str] = None
    config_type: ConfigType = ConfigType.STRING
    required: bool = True
    is_secret: bool = False
    validation_pattern: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    source_files: Set[str] = field(default_factory=set)


@dataclass
class ConfigurationReport:
    """Report of configuration analysis and generation"""
    env_variables: List[ConfigVariable]
    secrets: List[ConfigVariable]
    deployment_configs: Dict[str, Dict[str, Any]]
    validation_errors: List[str]
    warnings: List[str]
    generated_files: List[str]


class ConfigManager:
    """Manages configuration for generated applications"""
    
    # Common patterns for detecting environment variables
    ENV_PATTERNS = [
        r'process\.env\.(\w+)',  # Node.js
        r'os\.environ\.get\(["\'](\w+)["\']',  # Python
        r'os\.getenv\(["\'](\w+)["\']',  # Python
        r'ENV\[["\'](\w+)["\']\]',  # Ruby
        r'System\.getenv\("(\w+)"\)',  # Java
        r'\$\{(\w+)\}',  # Shell/Docker
        r'env\.(\w+)',  # Various frameworks
    ]
    
    # Patterns for detecting configuration types
    TYPE_PATTERNS = {
        ConfigType.PORT: [r'PORT', r'_PORT$', r'^PORT_'],
        ConfigType.URL: [r'URL', r'URI', r'ENDPOINT', r'HOST'],
        ConfigType.SECRET: [r'SECRET', r'KEY', r'TOKEN', r'PASSWORD', r'CREDENTIALS'],
        ConfigType.BOOLEAN: [r'ENABLE', r'DISABLE', r'IS_', r'HAS_', r'USE_'],
        ConfigType.FILE_PATH: [r'PATH', r'FILE', r'DIRECTORY', r'DIR'],
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_vars: Dict[str, ConfigVariable] = {}
        self.secrets: Set[str] = set()
        
    def analyze_project(self) -> ConfigurationReport:
        """Analyze project for configuration needs"""
        logger.info("🔍 Analyzing project for configuration requirements...")
        
        # Scan codebase for environment variables
        self._scan_for_env_vars()
        
        # Infer configuration types
        self._infer_config_types()
        
        # Validate configuration
        validation_errors = self._validate_configuration()
        
        # Generate configuration files
        generated_files = self._generate_config_files()
        
        # Prepare report
        env_vars = [var for var in self.config_vars.values() if not var.is_secret]
        secrets = [var for var in self.config_vars.values() if var.is_secret]
        
        return ConfigurationReport(
            env_variables=env_vars,
            secrets=secrets,
            deployment_configs=self._generate_deployment_configs(),
            validation_errors=validation_errors,
            warnings=self._generate_warnings(),
            generated_files=generated_files
        )
    
    def _scan_for_env_vars(self):
        """Scan codebase for environment variable usage"""
        logger.info("Scanning for environment variables...")
        
        # File extensions to scan
        extensions = ['.js', '.ts', '.py', '.java', '.rb', '.go', '.php', '.cs']
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    self._extract_env_vars(content, str(file_path.relative_to(self.project_path)))
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
    
    def _extract_env_vars(self, content: str, source_file: str):
        """Extract environment variables from file content"""
        found_vars = set()
        
        for pattern in self.ENV_PATTERNS:
            matches = re.findall(pattern, content, re.MULTILINE)
            found_vars.update(matches)
        
        # Add found variables to config
        for var_name in found_vars:
            if var_name not in self.config_vars:
                self.config_vars[var_name] = ConfigVariable(name=var_name)
            self.config_vars[var_name].source_files.add(source_file)
    
    def _infer_config_types(self):
        """Infer configuration types based on variable names"""
        for var_name, var_config in self.config_vars.items():
            # Check against type patterns
            for config_type, patterns in self.TYPE_PATTERNS.items():
                if any(re.search(pattern, var_name, re.IGNORECASE) for pattern in patterns):
                    var_config.config_type = config_type
                    if config_type == ConfigType.SECRET:
                        var_config.is_secret = True
                        self.secrets.add(var_name)
                    break
            
            # Set validation patterns based on type
            if var_config.config_type == ConfigType.PORT:
                var_config.validation_pattern = r'^\d{1,5}$'
                var_config.examples = ['3000', '8080', '5432']
            elif var_config.config_type == ConfigType.URL:
                var_config.validation_pattern = r'^https?://'
                var_config.examples = ['http://localhost:3000', 'https://api.example.com']
            elif var_config.config_type == ConfigType.BOOLEAN:
                var_config.validation_pattern = r'^(true|false|1|0|yes|no)$'
                var_config.examples = ['true', 'false']
    
    def _validate_configuration(self) -> List[str]:
        """Validate configuration setup"""
        errors = []
        
        # Check for missing required variables
        for var_name, var_config in self.config_vars.items():
            if var_config.required and not var_config.default:
                if not var_config.value:
                    errors.append(f"Required variable {var_name} has no default value")
        
        # Check for insecure patterns
        for var_name, var_config in self.config_vars.items():
            if var_config.is_secret and var_config.default:
                errors.append(f"Secret {var_name} should not have a default value")
        
        return errors
    
    def _generate_warnings(self) -> List[str]:
        """Generate configuration warnings"""
        warnings = []
        
        # Warn about variables without descriptions
        undocumented = [var.name for var in self.config_vars.values() if not var.description]
        if undocumented:
            warnings.append(f"Variables without descriptions: {', '.join(undocumented[:5])}...")
        
        # Warn about potential secrets not marked as such
        potential_secrets = []
        for var_name, var_config in self.config_vars.items():
            if not var_config.is_secret and any(
                keyword in var_name.upper() 
                for keyword in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD']
            ):
                potential_secrets.append(var_name)
        
        if potential_secrets:
            warnings.append(f"Potential secrets not marked as secure: {', '.join(potential_secrets)}")
        
        return warnings
    
    def _generate_config_files(self) -> List[str]:
        """Generate configuration files"""
        generated = []
        
        # Generate .env.example
        env_example_path = self.project_path / '.env.example'
        self._generate_env_example(env_example_path)
        generated.append(str(env_example_path))
        
        # Generate .env.local (for development)
        env_local_path = self.project_path / '.env.local'
        self._generate_env_local(env_local_path)
        generated.append(str(env_local_path))
        
        # Update .gitignore
        gitignore_path = self.project_path / '.gitignore'
        self._update_gitignore(gitignore_path)
        
        return generated
    
    def _generate_env_example(self, path: Path):
        """Generate .env.example file"""
        lines = ["# Environment Configuration", ""]
        
        # Group variables by type
        grouped = {}
        for var_config in sorted(self.config_vars.values(), key=lambda x: x.name):
            category = var_config.config_type.value.upper()
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(var_config)
        
        # Write grouped variables
        for category, vars in grouped.items():
            lines.append(f"# {category} Configuration")
            for var in vars:
                if var.description:
                    lines.append(f"# {var.description}")
                if var.examples:
                    lines.append(f"# Example: {var.examples[0]}")
                
                value = var.default if var.default else f"<{var.config_type.value}>"
                if var.is_secret:
                    value = "<secret>"
                
                lines.append(f"{var.name}={value}")
                lines.append("")
        
        path.write_text('\n'.join(lines))
        logger.info(f"Generated {path}")
    
    def _generate_env_local(self, path: Path):
        """Generate .env.local file for development"""
        if path.exists():
            logger.info(f"{path} already exists, skipping generation")
            return
        
        lines = ["# Local Development Configuration", "# Copy this file to .env and update values", ""]
        
        for var_config in sorted(self.config_vars.values(), key=lambda x: x.name):
            if var_config.default and not var_config.is_secret:
                lines.append(f"{var_config.name}={var_config.default}")
            else:
                placeholder = var_config.examples[0] if var_config.examples else "your_value_here"
                lines.append(f"# {var_config.name}={placeholder}")
        
        path.write_text('\n'.join(lines))
        logger.info(f"Generated {path}")
    
    def _update_gitignore(self, path: Path):
        """Update .gitignore to exclude sensitive files"""
        entries_to_add = [
            '.env',
            '.env.local',
            '.env.*.local',
            '*.secret',
            'secrets/',
        ]
        
        if path.exists():
            content = path.read_text()
            lines = content.strip().split('\n')
        else:
            lines = []
        
        # Add entries if not present
        added = False
        for entry in entries_to_add:
            if entry not in lines:
                if not added:
                    lines.extend(['', '# Environment and secrets'])
                    added = True
                lines.append(entry)
        
        if added:
            path.write_text('\n'.join(lines) + '\n')
            logger.info(f"Updated {path} with environment exclusions")
    
    def _generate_deployment_configs(self) -> Dict[str, Dict[str, Any]]:
        """Generate deployment-specific configurations"""
        configs = {}
        
        # Docker configuration
        configs['docker'] = {
            'env_file': '.env',
            'build_args': {
                var.name: f"${{{var.name}}}"
                for var in self.config_vars.values()
                if not var.is_secret
            }
        }
        
        # Kubernetes configuration
        configs['kubernetes'] = {
            'configmap': {
                var.name: var.default or ''
                for var in self.config_vars.values()
                if not var.is_secret and var.default
            },
            'secrets': [var.name for var in self.config_vars.values() if var.is_secret]
        }
        
        # Docker Compose configuration
        configs['docker-compose'] = {
            'environment': {
                var.name: f"${{{var.name}:-{var.default or ''}}}"
                for var in self.config_vars.values()
                if not var.is_secret
            }
        }
        
        return configs
    
    def apply_configuration(self, env_values: Dict[str, str]):
        """Apply configuration values"""
        for var_name, value in env_values.items():
            if var_name in self.config_vars:
                self.config_vars[var_name].value = value
    
    def validate_runtime_config(self) -> Tuple[bool, List[str]]:
        """Validate runtime configuration"""
        errors = []
        
        for var_name, var_config in self.config_vars.items():
            if var_config.required and not var_config.value and not var_config.default:
                errors.append(f"Missing required variable: {var_name}")
            
            if var_config.value and var_config.validation_pattern:
                if not re.match(var_config.validation_pattern, var_config.value):
                    errors.append(f"Invalid value for {var_name}: {var_config.value}")
        
        return len(errors) == 0, errors