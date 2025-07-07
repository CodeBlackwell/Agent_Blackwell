"""
Configuration loader for demo examples.
Loads and validates YAML configuration files for predefined examples.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class ExampleConfig:
    """Represents a loaded example configuration."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get('name', 'Unnamed Example')
        self.description = data.get('description', '')
        self.difficulty = data.get('difficulty', 'Unknown')
        self.time_estimate = data.get('time_estimate', 'Unknown')
        self.requirements = data.get('requirements', '')
        self.config = data.get('config', {})
        self.expected_files = data.get('expected_files', [])
        self.detailed_description = data.get('detailed_description', '')
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility."""
        return {
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty,
            'time_estimate': self.time_estimate,
            'requirements': self.requirements,
            'config': self.config,
            'expected_files': self.expected_files,
            'detailed_description': self.detailed_description
        }


class ConfigLoader:
    """Loads example configurations from YAML files."""
    
    def __init__(self, examples_dir: Optional[Path] = None):
        """Initialize the config loader.
        
        Args:
            examples_dir: Path to examples directory. Defaults to demos/examples/
        """
        if examples_dir is None:
            # Find the examples directory relative to this file
            current_dir = Path(__file__).parent.parent
            examples_dir = current_dir / "examples"
        
        self.examples_dir = Path(examples_dir)
        self._cache: Dict[str, ExampleConfig] = {}
        
    def load_example(self, name: str) -> Optional[ExampleConfig]:
        """Load a specific example configuration.
        
        Args:
            name: Name of the example (without .yaml extension)
            
        Returns:
            ExampleConfig object or None if not found
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]
            
        # Try to load from file
        yaml_path = self.examples_dir / f"{name}.yaml"
        if not yaml_path.exists():
            # Try with .yml extension
            yaml_path = self.examples_dir / f"{name}.yml"
            
        if not yaml_path.exists():
            return None
            
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                
            config = ExampleConfig(data)
            self._cache[name] = config
            return config
            
        except Exception as e:
            print(f"Error loading example {name}: {e}")
            return None
            
    def list_examples(self) -> List[str]:
        """List all available examples.
        
        Returns:
            List of example names (without extensions)
        """
        examples = []
        
        if not self.examples_dir.exists():
            return examples
            
        for file in self.examples_dir.iterdir():
            if file.suffix in ['.yaml', '.yml']:
                examples.append(file.stem)
                
        return sorted(examples)
        
    def get_example_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get basic info about an example without fully loading it.
        
        Args:
            name: Name of the example
            
        Returns:
            Dictionary with name, description, difficulty, time_estimate
        """
        config = self.load_example(name)
        if config is None:
            return None
            
        return {
            'name': config.name,
            'description': config.description,
            'difficulty': config.difficulty,
            'time_estimate': config.time_estimate
        }
        
    def validate_config(self, config: ExampleConfig) -> List[str]:
        """Validate an example configuration.
        
        Args:
            config: ExampleConfig to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not config.name:
            errors.append("Missing 'name' field")
            
        if not config.requirements:
            errors.append("Missing 'requirements' field")
            
        if config.difficulty not in ['Beginner', 'Intermediate', 'Advanced', 'Unknown']:
            errors.append(f"Invalid difficulty: {config.difficulty}")
            
        if not isinstance(config.config, dict):
            errors.append("'config' field must be a dictionary")
            
        if not isinstance(config.expected_files, list):
            errors.append("'expected_files' must be a list")
            
        return errors


# Convenience function for quick loading
def load_example(name: str, examples_dir: Optional[Path] = None) -> Optional[ExampleConfig]:
    """Quick function to load an example configuration.
    
    Args:
        name: Name of the example
        examples_dir: Optional path to examples directory
        
    Returns:
        ExampleConfig object or None if not found
    """
    loader = ConfigLoader(examples_dir)
    return loader.load_example(name)