#!/usr/bin/env python3
"""
Test suite for MVP Incremental Demo Script
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo_mvp_incremental import (
    MVPIncrementalDemo,
    EXAMPLES,
    run_cli
)
from shared.data_models import CodingTeamInput


class TestMVPIncrementalDemo:
    """Test the MVPIncrementalDemo class."""
    
    def test_init(self):
        """Test demo initialization."""
        demo = MVPIncrementalDemo()
        
        assert demo.selected_example is None
        assert demo.custom_requirements is None
        assert demo.config["run_tests"] == False
        assert demo.config["run_integration_verification"] == False
        
    def test_print_examples(self, capsys):
        """Test printing available examples."""
        demo = MVPIncrementalDemo()
        demo.print_examples()
        
        captured = capsys.readouterr()
        assert "Available Examples:" in captured.out
        assert "calculator" in captured.out
        assert "todo-api" in captured.out
        assert "auth-system" in captured.out
        assert "file-processor" in captured.out
        
    def test_examples_data(self):
        """Test the EXAMPLES dictionary."""
        assert "calculator" in EXAMPLES
        assert "todo-api" in EXAMPLES
        
        # Check calculator example
        calc = EXAMPLES["calculator"]
        assert calc["name"] == "Simple Calculator"
        assert "calculator module" in calc["requirements"]
        assert calc["config"]["run_tests"] == True
        assert calc["config"]["run_integration_verification"] == False
        
        # Check todo-api example
        todo = EXAMPLES["todo-api"]
        assert todo["name"] == "TODO REST API"
        assert "FastAPI" in todo["requirements"]
        assert todo["config"]["run_tests"] == True
        assert todo["config"]["run_integration_verification"] == True
        
    @patch('builtins.input', side_effect=['1'])
    def test_get_user_choice_valid(self, mock_input):
        """Test getting valid user choice."""
        demo = MVPIncrementalDemo()
        choice = demo.get_user_choice()
        assert choice == '1'
        
    @patch('builtins.input', side_effect=['invalid', '5', '2'])
    def test_get_user_choice_invalid_then_valid(self, mock_input):
        """Test handling invalid then valid choices."""
        demo = MVPIncrementalDemo()
        choice = demo.get_user_choice()
        assert choice == '2'
        
    @patch('builtins.input', side_effect=['calculator'])
    def test_select_example_valid(self, mock_input):
        """Test selecting a valid example."""
        demo = MVPIncrementalDemo()
        example = demo.select_example()
        assert example == 'calculator'
        
    @patch('builtins.input', side_effect=['invalid', 'back'])
    def test_select_example_back(self, mock_input):
        """Test going back from example selection."""
        demo = MVPIncrementalDemo()
        example = demo.select_example()
        assert example is None
        
    @patch('builtins.input', side_effect=['Create a calculator', 'with tests', 'END'])
    def test_get_custom_requirements(self, mock_input):
        """Test getting custom requirements."""
        demo = MVPIncrementalDemo()
        requirements = demo.get_custom_requirements()
        assert "Create a calculator" in requirements
        assert "with tests" in requirements
        
    @patch('builtins.input', side_effect=['y', 'n'])
    def test_configure_phases(self, mock_input):
        """Test configuring phases."""
        demo = MVPIncrementalDemo()
        demo.configure_phases()
        
        assert demo.config["run_tests"] == True
        assert demo.config["run_integration_verification"] == False
        
    def test_show_configuration_summary(self, capsys):
        """Test showing configuration summary."""
        demo = MVPIncrementalDemo()
        demo.config["run_tests"] = True
        demo.config["run_integration_verification"] = False
        
        demo.show_configuration_summary("Test requirements")
        
        captured = capsys.readouterr()
        assert "Configuration Summary" in captured.out
        assert "Test requirements" in captured.out
        assert "✅ Enabled" in captured.out  # For run_tests
        assert "❌ Disabled" in captured.out  # For integration
        
    @pytest.mark.asyncio
    @patch('demo_mvp_incremental.execute_workflow')
    async def test_run_workflow(self, mock_execute):
        """Test running the workflow."""
        demo = MVPIncrementalDemo()
        demo.config["run_tests"] = True
        
        # Mock the workflow execution
        mock_execute.return_value = {"status": "success"}
        
        result = await demo.run_workflow("Test requirements")
        
        assert result == {"status": "success"}
        mock_execute.assert_called_once()
        
        # Check the input data
        call_args = mock_execute.call_args
        input_data = call_args[0][1]
        assert isinstance(input_data, CodingTeamInput)
        assert input_data.requirements == "Test requirements"
        assert input_data.run_tests == True
        
    def test_save_results(self, tmp_path):
        """Test saving results."""
        demo = MVPIncrementalDemo()
        demo.selected_example = "calculator"
        
        # Change output directory to temp
        with patch('demo_mvp_incremental.Path', return_value=tmp_path):
            demo.save_results({"status": "success"})
            
        # Check that a file was created
        files = list(tmp_path.glob("mvp_demo_*_summary.json"))
        assert len(files) > 0


class TestCLIMode:
    """Test CLI mode functionality."""
    
    @pytest.mark.asyncio
    @patch('demo_mvp_incremental.execute_workflow')
    async def test_run_cli_with_preset(self, mock_execute):
        """Test CLI mode with preset."""
        mock_execute.return_value = {"status": "success"}
        
        # Create mock args
        args = MagicMock()
        args.preset = "calculator"
        args.requirements = None
        args.all_phases = False
        args.tests = None
        args.integration = None
        args.save_output = False
        
        result = await run_cli(args)
        assert result == 0
        
    @pytest.mark.asyncio
    @patch('demo_mvp_incremental.execute_workflow')
    async def test_run_cli_with_requirements(self, mock_execute):
        """Test CLI mode with custom requirements."""
        mock_execute.return_value = {"status": "success"}
        
        # Create mock args
        args = MagicMock()
        args.preset = None
        args.requirements = "Create a test app"
        args.all_phases = True
        args.tests = None
        args.integration = None
        args.save_output = False
        
        result = await run_cli(args)
        assert result == 0
        
    @pytest.mark.asyncio
    async def test_run_cli_invalid_preset(self):
        """Test CLI mode with invalid preset."""
        # Create mock args
        args = MagicMock()
        args.preset = "invalid"
        args.requirements = None
        
        result = await run_cli(args)
        assert result == 1
        
    @pytest.mark.asyncio
    async def test_run_cli_no_input(self):
        """Test CLI mode with no input."""
        # Create mock args
        args = MagicMock()
        args.preset = None
        args.requirements = None
        
        result = await run_cli(args)
        assert result == 1
        
    @pytest.mark.asyncio
    @patch('demo_mvp_incremental.execute_workflow')
    async def test_run_cli_with_error(self, mock_execute):
        """Test CLI mode with workflow error."""
        mock_execute.side_effect = Exception("Test error")
        
        # Create mock args
        args = MagicMock()
        args.preset = "calculator"
        args.requirements = None
        args.all_phases = False
        args.tests = None
        args.integration = None
        args.save_output = False
        
        result = await run_cli(args)
        assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])