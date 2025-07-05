"""
Environment Specification Data Class

Shared data structure for Docker environment specifications.
"""

from typing import List
from dataclasses import dataclass

@dataclass
class EnvironmentSpec:
    """Specification for a Docker environment"""
    language: str
    version: str
    base_image: str
    dependencies: List[str]
    system_packages: List[str]
    build_commands: List[str]
    execution_commands: List[str]
    working_dir: str = "/app"