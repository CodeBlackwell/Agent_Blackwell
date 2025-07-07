#!/usr/bin/env python3
"""
Test suite for MVP Incremental Presets
"""

import pytest
import yaml
from pathlib import Path


class TestPresetFiles:
    """Test the preset YAML files."""
    
    @pytest.fixture
    def presets_dir(self):
        """Get the presets directory."""
        return Path(__file__).parent.parent.parent / "workflows" / "mvp_incremental" / "presets"
        
    def test_presets_directory_exists(self, presets_dir):
        """Test that presets directory exists."""
        assert presets_dir.exists()
        assert presets_dir.is_dir()
        
    def test_all_presets_exist(self, presets_dir):
        """Test that all expected preset files exist."""
        expected_presets = [
            "basic_api.yaml",
            "cli_tool.yaml",
            "data_processor.yaml",
            "web_scraper.yaml"
        ]
        
        for preset_file in expected_presets:
            filepath = presets_dir / preset_file
            assert filepath.exists(), f"Preset file {preset_file} not found"
            
    def test_preset_yaml_valid(self, presets_dir):
        """Test that all preset files are valid YAML."""
        for yaml_file in presets_dir.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None, f"{yaml_file.name} is empty"
                except yaml.YAMLError as e:
                    pytest.fail(f"{yaml_file.name} has invalid YAML: {e}")
                    
    def test_preset_required_fields(self, presets_dir):
        """Test that all presets have required fields."""
        required_fields = ["name", "description"]
        
        for yaml_file in presets_dir.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                
            for field in required_fields:
                assert field in data, f"{yaml_file.name} missing required field: {field}"
                assert data[field], f"{yaml_file.name} has empty {field}"
                
    def test_basic_api_preset(self, presets_dir):
        """Test the basic_api preset content."""
        with open(presets_dir / "basic_api.yaml", 'r') as f:
            data = yaml.safe_load(f)
            
        assert data["name"] == "Basic REST API"
        assert "CRUD" in data["description"]
        
        # Check retry config
        assert "retry_config" in data
        assert data["retry_config"]["max_retries"] == 3
        
        # Check test config
        assert "test_execution" in data
        assert data["test_execution"]["run_tests"] == True
        assert data["test_execution"]["test_timeout"] == 60
        
        # Check phases
        assert "phases" in data
        assert data["phases"]["run_tests"] == True
        assert data["phases"]["run_integration_verification"] == True
        
        # Check feature hints
        assert "feature_hints" in data
        assert len(data["feature_hints"]) >= 4
        
    def test_cli_tool_preset(self, presets_dir):
        """Test the cli_tool preset content."""
        with open(presets_dir / "cli_tool.yaml", 'r') as f:
            data = yaml.safe_load(f)
            
        assert data["name"] == "CLI Tool"
        assert "command-line" in data["description"]
        
        # Check retry config
        assert data["retry_config"]["max_retries"] == 2
        
        # Check test config
        assert data["test_execution"]["test_timeout"] == 30
        
        # Check phases
        assert data["phases"]["run_tests"] == True
        assert data["phases"]["run_integration_verification"] == False
        
    def test_data_processor_preset(self, presets_dir):
        """Test the data_processor preset content."""
        with open(presets_dir / "data_processor.yaml", 'r') as f:
            data = yaml.safe_load(f)
            
        assert data["name"] == "Data Processor"
        assert "data processing" in data["description"]
        
        # Check unique settings
        assert data["retry_config"]["max_retries"] == 4
        assert data["test_execution"]["run_tests"] == False
        assert data["test_execution"]["test_timeout"] == 90
        
        # Check validation settings
        assert "validation" in data
        assert data["validation"]["validate_with_sample_data"] == True
        
    def test_web_scraper_preset(self, presets_dir):
        """Test the web_scraper preset content."""
        with open(presets_dir / "web_scraper.yaml", 'r') as f:
            data = yaml.safe_load(f)
            
        assert data["name"] == "Web Scraper"
        assert "web scraping" in data["description"]
        
        # Check unique settings
        assert data["retry_config"]["max_retries"] == 5  # Highest retry count
        assert data["validation"]["strict_mode"] == False
        
        # Check expected errors
        assert "expected_errors" in data
        error_patterns = [e["pattern"] for e in data["expected_errors"]]
        assert any("ConnectionError" in p for p in error_patterns)
        assert any("403" in p for p in error_patterns)
        
    def test_preset_error_patterns(self, presets_dir):
        """Test that error patterns in presets are valid."""
        for yaml_file in presets_dir.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                
            if "expected_errors" in data:
                for error in data["expected_errors"]:
                    assert "pattern" in error, f"{yaml_file.name} error missing pattern"
                    assert "hint" in error, f"{yaml_file.name} error missing hint"
                    assert isinstance(error["pattern"], str), f"{yaml_file.name} pattern must be string"
                    assert isinstance(error["hint"], str), f"{yaml_file.name} hint must be string"
                    
    def test_preset_project_structure(self, presets_dir):
        """Test that project structure suggestions are valid."""
        for yaml_file in presets_dir.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                
            if "project_structure" in data:
                assert isinstance(data["project_structure"], list)
                assert len(data["project_structure"]) > 0
                
                for item in data["project_structure"]:
                    assert isinstance(item, str)
                    # Check for basic format (filename and description)
                    assert len(item.split()) >= 2  # At least filename and one word


if __name__ == "__main__":
    pytest.main([__file__, "-v"])