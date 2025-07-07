#!/usr/bin/env python3
"""
Test suite for MVP Incremental Config Helper
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path

from workflows.mvp_incremental.config_helper import (
    MVPIncrementalConfig,
    ConfigHelper,
    load_preset,
    validate_config
)


class TestMVPIncrementalConfig:
    """Test the MVPIncrementalConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MVPIncrementalConfig()
        
        assert config.name == "Custom Configuration"
        assert config.max_retries == 2
        assert config.run_tests == False
        assert config.test_command == "pytest"
        assert config.test_timeout == 30
        
    def test_to_retry_config(self):
        """Test conversion to RetryConfig."""
        config = MVPIncrementalConfig(
            max_retries=5,
            extract_error_context=True,
            modify_prompt_on_retry=False
        )
        
        retry_config = config.to_retry_config()
        assert retry_config.max_retries == 5
        assert retry_config.extract_error_context == True
        assert retry_config.modify_prompt_on_retry == False
        
    def test_to_test_config(self):
        """Test conversion to TestExecutionConfig."""
        config = MVPIncrementalConfig(
            run_tests=True,
            test_command="python -m pytest",
            test_timeout=60,
            fix_on_failure=False,
            max_fix_attempts=3
        )
        
        test_config = config.to_test_config()
        assert test_config.run_tests == True
        assert test_config.test_command == "python -m pytest"
        assert test_config.test_timeout == 60
        assert test_config.fix_on_failure == False
        assert test_config.max_fix_attempts == 3


class TestConfigHelper:
    """Test the ConfigHelper class."""
    
    def test_load_available_presets(self):
        """Test loading available presets."""
        helper = ConfigHelper()
        
        # Should have at least the presets we created
        assert "basic_api" in helper.available_presets
        assert "cli_tool" in helper.available_presets
        assert "data_processor" in helper.available_presets
        assert "web_scraper" in helper.available_presets
        
    def test_load_preset_basic_api(self):
        """Test loading the basic_api preset."""
        helper = ConfigHelper()
        config = helper.load_preset("basic_api")
        
        assert config.name == "Basic REST API"
        assert config.max_retries == 3
        assert config.run_tests == True
        assert config.test_timeout == 60
        assert config.run_integration_verification == True
        
    def test_load_preset_cli_tool(self):
        """Test loading the cli_tool preset."""
        helper = ConfigHelper()
        config = helper.load_preset("cli_tool")
        
        assert config.name == "CLI Tool"
        assert config.max_retries == 2
        assert config.run_tests == True
        assert config.run_integration_verification == False
        
    def test_load_preset_not_found(self):
        """Test loading a non-existent preset."""
        helper = ConfigHelper()
        
        with pytest.raises(ValueError, match="Preset 'nonexistent' not found"):
            helper.load_preset("nonexistent")
            
    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        helper = ConfigHelper()
        config = MVPIncrementalConfig(
            max_retries=3,
            test_timeout=30
        )
        
        issues = helper.validate_config(config)
        assert len(issues) == 0
        
    def test_validate_config_invalid(self):
        """Test validating an invalid configuration."""
        helper = ConfigHelper()
        config = MVPIncrementalConfig(
            max_retries=-1,
            test_timeout=0,
            max_fix_attempts=-5
        )
        
        issues = helper.validate_config(config)
        assert len(issues) >= 3
        assert any("max_retries must be >= 0" in issue for issue in issues)
        assert any("test_timeout must be >= 1" in issue for issue in issues)
        assert any("max_fix_attempts must be >= 0" in issue for issue in issues)
        
    def test_validate_config_warnings(self):
        """Test configuration warnings."""
        helper = ConfigHelper()
        config = MVPIncrementalConfig(
            max_retries=15,
            test_timeout=400,
            run_integration_verification=True,
            run_tests=False
        )
        
        issues = helper.validate_config(config)
        assert any("max_retries > 10" in issue for issue in issues)
        assert any("test_timeout > 300" in issue for issue in issues)
        assert any("Integration verification without tests" in issue for issue in issues)
        
    def test_get_performance_recommendations(self):
        """Test performance recommendations."""
        helper = ConfigHelper()
        
        # Test simple project
        simple = helper.get_performance_recommendations("simple")
        assert simple["max_retries"] == 1
        assert simple["run_tests"] == False
        
        # Test API project
        api = helper.get_performance_recommendations("api")
        assert api["max_retries"] == 3
        assert api["run_tests"] == True
        assert api["run_integration_verification"] == True
        
        # Test complex project
        complex_proj = helper.get_performance_recommendations("complex")
        assert complex_proj["max_retries"] == 5
        assert complex_proj["test_timeout"] == 90
        
        # Test unknown project type
        unknown = helper.get_performance_recommendations("unknown")
        assert unknown == helper.get_performance_recommendations("simple")
        
    def test_save_config_yaml(self):
        """Test saving configuration to YAML."""
        helper = ConfigHelper()
        config = MVPIncrementalConfig(
            name="Test Config",
            max_retries=3,
            run_tests=True
        )
        
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            filepath = Path(f.name)
            
        try:
            helper.save_config(config, filepath)
            
            # Load and verify
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            assert data["name"] == "Test Config"
            assert data["max_retries"] == 3
            assert data["run_tests"] == True
        finally:
            filepath.unlink()
            
    def test_save_config_json(self):
        """Test saving configuration to JSON."""
        helper = ConfigHelper()
        config = MVPIncrementalConfig(
            name="Test Config",
            max_retries=3,
            run_tests=True
        )
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = Path(f.name)
            
        try:
            helper.save_config(config, filepath)
            
            # Load and verify
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            assert data["name"] == "Test Config"
            assert data["max_retries"] == 3
            assert data["run_tests"] == True
        finally:
            filepath.unlink()
            
    def test_get_preset_info(self):
        """Test getting preset information."""
        helper = ConfigHelper()
        
        # Test existing preset
        info = helper.get_preset_info("basic_api")
        assert info is not None
        assert info["name"] == "Basic REST API"
        assert "retry_config" in info
        assert "test_execution" in info
        
        # Test non-existent preset
        info = helper.get_preset_info("nonexistent")
        assert info is None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_load_preset_function(self):
        """Test the load_preset convenience function."""
        config = load_preset("basic_api")
        assert config.name == "Basic REST API"
        assert config.max_retries == 3
        
    def test_validate_config_function(self):
        """Test the validate_config convenience function."""
        config = MVPIncrementalConfig(max_retries=-1)
        issues = validate_config(config)
        assert len(issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])