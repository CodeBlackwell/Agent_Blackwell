"""
Configuration loader for examples and presets.
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class ExampleConfig:
    """Configuration for an example project."""
    name: str
    description: str
    requirements: str
    config: Dict[str, Any]
    difficulty: str = "beginner"
    time_estimate: str = "5-10 minutes"


class ConfigLoader:
    """Loads example configurations from YAML files."""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent.parent / "examples"
        self.examples_cache = {}
        
    def list_examples(self) -> List[str]:
        """List all available examples."""
        if not self.examples_dir.exists():
            return []
            
        examples = []
        for file in self.examples_dir.glob("*.yaml"):
            examples.append(file.stem)
        return sorted(examples)
        
    def load_example(self, name: str) -> Optional[ExampleConfig]:
        """Load a specific example configuration."""
        if name in self.examples_cache:
            return self.examples_cache[name]
            
        yaml_path = self.examples_dir / f"{name}.yaml"
        if not yaml_path.exists():
            return None
            
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                
            config = ExampleConfig(
                name=data.get('name', name),
                description=data.get('description', ''),
                requirements=data.get('requirements', ''),
                config=data.get('config', {}),
                difficulty=data.get('difficulty', 'beginner'),
                time_estimate=data.get('time_estimate', '5-10 minutes')
            )
            
            self.examples_cache[name] = config
            return config
            
        except Exception as e:
            print(f"Error loading example {name}: {e}")
            return None
            
    def get_example_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get basic info about an example without full load."""
        config = self.load_example(name)
        if not config:
            return None
            
        return {
            'name': config.name,
            'description': config.description,
            'difficulty': config.difficulty,
            'time_estimate': config.time_estimate
        }