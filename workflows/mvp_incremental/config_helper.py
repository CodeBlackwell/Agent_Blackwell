"""
Configuration Helper for MVP Incremental Workflow

This module provides utilities for managing workflow configurations,
loading presets, and validating settings.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from workflows.mvp_incremental.retry_strategy import RetryConfig
from workflows.mvp_incremental.test_execution import TestExecutionConfig


@dataclass
class MVPIncrementalConfig:
    """Complete configuration for MVP Incremental workflow."""
    
    # Basic settings
    name: str = "Custom Configuration"
    description: str = ""
    
    # Retry configuration
    max_retries: int = 2
    extract_error_context: bool = True
    modify_prompt_on_retry: bool = True
    
    # Test execution configuration
    run_tests: bool = False
    test_command: str = "pytest"
    test_timeout: int = 30
    fix_on_failure: bool = True
    max_fix_attempts: int = 2
    
    # Integration verification
    run_integration_verification: bool = False
    
    # Validation settings
    strict_validation: bool = True
    check_imports: bool = True
    check_syntax: bool = True
    
    def to_retry_config(self) -> RetryConfig:
        """Convert to RetryConfig instance."""
        return RetryConfig(
            max_retries=self.max_retries,
            extract_error_context=self.extract_error_context,
            modify_prompt_on_retry=self.modify_prompt_on_retry
        )
        
    def to_test_config(self) -> TestExecutionConfig:
        """Convert to TestExecutionConfig instance."""
        return TestExecutionConfig(
            run_tests=self.run_tests,
            test_command=self.test_command,
            test_timeout=self.test_timeout,
            fix_on_failure=self.fix_on_failure,
            max_fix_attempts=self.max_fix_attempts
        )


class ConfigHelper:
    """Helper class for managing MVP Incremental configurations."""
    
    def __init__(self):
        self.presets_dir = Path(__file__).parent / "presets"
        self.available_presets = self._load_available_presets()
        
    def _load_available_presets(self) -> Dict[str, str]:
        """Load list of available presets."""
        presets = {}
        
        if self.presets_dir.exists():
            for preset_file in self.presets_dir.glob("*.yaml"):
                preset_name = preset_file.stem
                try:
                    with open(preset_file, 'r') as f:
                        data = yaml.safe_load(f)
                        presets[preset_name] = data.get('name', preset_name)
                except Exception:
                    # Skip invalid preset files
                    pass
                    
        return presets
        
    def load_preset(self, preset_name: str) -> MVPIncrementalConfig:
        """Load a preset configuration."""
        preset_file = self.presets_dir / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise ValueError(f"Preset '{preset_name}' not found")
            
        with open(preset_file, 'r') as f:
            data = yaml.safe_load(f)
            
        # Map preset data to config
        config = MVPIncrementalConfig(
            name=data.get('name', preset_name),
            description=data.get('description', '')
        )
        
        # Load retry config
        if 'retry_config' in data:
            retry = data['retry_config']
            config.max_retries = retry.get('max_retries', config.max_retries)
            config.extract_error_context = retry.get('extract_error_context', config.extract_error_context)
            config.modify_prompt_on_retry = retry.get('modify_prompt_on_retry', config.modify_prompt_on_retry)
            
        # Load test config
        if 'test_execution' in data:
            test = data['test_execution']
            config.run_tests = test.get('run_tests', config.run_tests)
            config.test_command = test.get('test_command', config.test_command)
            config.test_timeout = test.get('test_timeout', config.test_timeout)
            config.fix_on_failure = test.get('fix_on_failure', config.fix_on_failure)
            config.max_fix_attempts = test.get('max_fix_attempts', config.max_fix_attempts)
            
        # Load phase config
        if 'phases' in data:
            phases = data['phases']
            config.run_tests = phases.get('run_tests', config.run_tests)
            config.run_integration_verification = phases.get('run_integration_verification', config.run_integration_verification)
            
        # Load validation settings
        if 'validation' in data:
            val = data['validation']
            config.strict_validation = val.get('strict_mode', config.strict_validation)
            config.check_imports = val.get('check_imports', config.check_imports)
            config.check_syntax = val.get('check_syntax', config.check_syntax)
            
        return config
        
    def validate_config(self, config: MVPIncrementalConfig) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Validate retry settings
        if config.max_retries < 0:
            issues.append("max_retries must be >= 0")
        if config.max_retries > 10:
            issues.append("max_retries > 10 may cause long execution times")
            
        # Validate test settings
        if config.test_timeout < 1:
            issues.append("test_timeout must be >= 1 second")
        if config.test_timeout > 300:
            issues.append("test_timeout > 300 seconds is not recommended")
            
        if config.max_fix_attempts < 0:
            issues.append("max_fix_attempts must be >= 0")
            
        # Validate combinations
        if config.run_integration_verification and not config.run_tests:
            issues.append("Integration verification without tests may have limited value")
            
        return issues
        
    def get_performance_recommendations(self, project_type: str) -> Dict[str, Any]:
        """Get performance recommendations based on project type."""
        recommendations = {
            "simple": {
                "max_retries": 1,
                "test_timeout": 30,
                "run_tests": False,
                "run_integration_verification": False,
                "reason": "Simple projects usually work on first attempt"
            },
            "api": {
                "max_retries": 3,
                "test_timeout": 60,
                "run_tests": True,
                "run_integration_verification": True,
                "reason": "APIs benefit from thorough testing and validation"
            },
            "complex": {
                "max_retries": 5,
                "test_timeout": 90,
                "run_tests": True,
                "run_integration_verification": True,
                "reason": "Complex projects need more iterations and testing"
            },
            "data": {
                "max_retries": 4,
                "test_timeout": 120,
                "run_tests": False,
                "run_integration_verification": True,
                "reason": "Data projects need validation but not always unit tests"
            }
        }
        
        return recommendations.get(project_type, recommendations["simple"])
        
    def save_config(self, config: MVPIncrementalConfig, filepath: Path):
        """Save configuration to file."""
        data = asdict(config)
        
        if filepath.suffix == '.yaml' or filepath.suffix == '.yml':
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
    def interactive_wizard(self) -> MVPIncrementalConfig:
        """Interactive configuration wizard."""
        print("\n🧙 MVP Incremental Configuration Wizard")
        print("=" * 50)
        
        # Start with preset or custom?
        print("\n1. Start with a preset")
        print("2. Create custom configuration")
        choice = input("\nChoice (1-2): ").strip()
        
        if choice == '1' and self.available_presets:
            # Show presets
            print("\nAvailable presets:")
            for key, name in self.available_presets.items():
                print(f"  {key:<15} - {name}")
                
            preset = input("\nSelect preset: ").strip()
            if preset in self.available_presets:
                config = self.load_preset(preset)
                print(f"\n✅ Loaded preset: {config.name}")
            else:
                print("❌ Invalid preset, starting with defaults")
                config = MVPIncrementalConfig()
        else:
            config = MVPIncrementalConfig()
            
        # Customize settings
        print("\n📝 Customize settings (press Enter to keep defaults)")
        
        # Retry settings
        print(f"\n🔄 Retry Configuration")
        max_retries = input(f"  Max retries [{config.max_retries}]: ").strip()
        if max_retries.isdigit():
            config.max_retries = int(max_retries)
            
        # Test settings
        print(f"\n🧪 Test Execution")
        run_tests = input(f"  Run tests (y/n) [{'y' if config.run_tests else 'n'}]: ").strip().lower()
        if run_tests in ['y', 'n']:
            config.run_tests = run_tests == 'y'
            
        if config.run_tests:
            test_command = input(f"  Test command [{config.test_command}]: ").strip()
            if test_command:
                config.test_command = test_command
                
        # Integration verification
        run_int = input(f"\n🔍 Run integration verification (y/n) [{'y' if config.run_integration_verification else 'n'}]: ").strip().lower()
        if run_int in ['y', 'n']:
            config.run_integration_verification = run_int == 'y'
            
        # Validate
        issues = self.validate_config(config)
        if issues:
            print("\n⚠️  Configuration issues:")
            for issue in issues:
                print(f"  - {issue}")
                
        return config
        
    def get_preset_info(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a preset."""
        preset_file = self.presets_dir / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            return None
            
        with open(preset_file, 'r') as f:
            return yaml.safe_load(f)


# Convenience functions
def load_preset(preset_name: str) -> MVPIncrementalConfig:
    """Load a preset configuration."""
    helper = ConfigHelper()
    return helper.load_preset(preset_name)


def create_config_interactive() -> MVPIncrementalConfig:
    """Create configuration interactively."""
    helper = ConfigHelper()
    return helper.interactive_wizard()


def validate_config(config: MVPIncrementalConfig) -> List[str]:
    """Validate a configuration."""
    helper = ConfigHelper()
    return helper.validate_config(config)