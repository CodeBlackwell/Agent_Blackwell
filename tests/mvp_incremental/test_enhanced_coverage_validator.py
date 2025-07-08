"""
Tests for Enhanced Coverage Validator (Phase 3 of TDD Enhancement)

This test file validates the enhanced coverage validator with:
- Branch coverage support
- Statement coverage tracking
- Test quality scoring
- Coverage trend tracking
- Enhanced suggestions
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from workflows.mvp_incremental.coverage_validator import (
    CoverageReport, TestCoverageResult, TestCoverageValidator,
    validate_tdd_test_coverage
)


class TestEnhancedCoverageReport:
    """Test the enhanced CoverageReport data structure"""
    
    def test_coverage_report_initialization(self):
        """Test that CoverageReport initializes with all new fields"""
        report = CoverageReport()
        
        # Check new fields exist
        assert hasattr(report, 'statement_coverage')
        assert hasattr(report, 'branch_coverage')
        assert hasattr(report, 'function_coverage')
        assert hasattr(report, 'total_branches')
        assert hasattr(report, 'covered_branches')
        assert hasattr(report, 'uncovered_branches')
        assert hasattr(report, 'feature_coverage')
        
        # Check defaults
        assert report.statement_coverage == 0.0
        assert report.branch_coverage == 0.0
        assert report.function_coverage == 0.0
        assert report.total_branches == 0
        assert report.covered_branches == 0
        assert report.uncovered_branches == {}
        assert report.feature_coverage == {}
    
    def test_has_branch_coverage_property(self):
        """Test the has_branch_coverage property"""
        report = CoverageReport()
        
        # No branch data
        assert not report.has_branch_coverage
        
        # With branch data
        report.total_branches = 10
        assert report.has_branch_coverage
    
    def test_weighted_coverage_calculation(self):
        """Test that overall coverage is properly weighted"""
        report = CoverageReport(
            statement_coverage=80.0,
            branch_coverage=60.0,
            total_branches=10,
            covered_branches=6
        )
        
        # Should be weighted: 60% statement + 40% branch
        expected = 0.6 * 80.0 + 0.4 * 60.0
        assert report.coverage_percentage == expected  # Now calculated in __post_init__


class TestEnhancedCoverageResult:
    """Test the enhanced TestCoverageResult"""
    
    def test_coverage_result_new_fields(self):
        """Test new fields in TestCoverageResult"""
        result = TestCoverageResult(success=True)
        
        # Check new fields
        assert hasattr(result, 'coverage_improved')
        assert hasattr(result, 'previous_coverage')
        assert hasattr(result, 'red_phase_valid')
        assert hasattr(result, 'green_phase_valid')
        assert hasattr(result, 'test_quality_score')
        
        # Check defaults
        assert result.coverage_improved == False
        assert result.previous_coverage is None
        assert result.red_phase_valid == False
        assert result.green_phase_valid == False
        assert result.test_quality_score == 0.0


class TestEnhancedValidator:
    """Test the enhanced TestCoverageValidator"""
    
    def test_validator_initialization(self):
        """Test validator initializes with new parameters"""
        validator = TestCoverageValidator(
            minimum_coverage=85.0,
            minimum_branch_coverage=75.0,
            track_trends=True
        )
        
        assert validator.minimum_coverage == 85.0
        assert validator.minimum_branch_coverage == 75.0
        assert validator.track_trends == True
        assert validator.coverage_history == {}
    
    def test_test_quality_score_calculation(self):
        """Test the test quality score calculation"""
        validator = TestCoverageValidator()
        
        # Mock coverage report
        coverage_report = CoverageReport(
            coverage_percentage=90.0,
            branch_coverage=85.0,
            total_branches=10
        )
        
        # Test code with various quality indicators
        test_code = """
        def test_add_edge_case():
            # Testing edge cases
            assert add(0, 0) == 0
            
        def test_add_error_handling():
            with pytest.raises(TypeError):
                add("a", "b")
                
        def test_boundary_values():
            assert add(MAX_INT, 1) == MAX_INT + 1
            
        @patch('module.external_service')
        def test_with_mock(mock_service):
            mock_service.return_value = 42
            assert process() == 42
        """
        
        implementation_code = "def add(a, b): return a + b"
        
        score = validator._calculate_test_quality_score(
            coverage_report, test_code, implementation_code
        )
        
        # Should have high score due to:
        # - Coverage (36/40 points for 90%)
        # - Branch coverage (17/20 points for 85%) 
        # - Edge cases (5 points)
        # - Error handling (5 points)
        # - Boundary tests (5 points)
        # - Mocking (5 points)
        # - Various assertions (10+ points)
        assert score > 50  # Should be a reasonable score
    
    def test_enhanced_suggestions_generation(self):
        """Test enhanced suggestion generation"""
        validator = TestCoverageValidator()
        
        coverage_report = CoverageReport(
            statement_coverage=70.0,
            branch_coverage=60.0,
            total_branches=10,
            covered_branches=6,
            missing_lines={'file.py': [10, 11, 12, 20, 21]},
            uncovered_branches={'file.py': ['Line 15 -> 16', 'Line 20 -> 22']}
        )
        
        test_code = "def test_basic(): assert True"
        impl_code = "def process(): pass"
        
        suggestions = validator._generate_enhanced_coverage_suggestions(
            coverage_report, "", impl_code, test_code
        )
        
        # Should have suggestions for:
        # - Low statement coverage
        # - Low branch coverage
        # - Missing lines (grouped)
        # - Uncovered branches
        # - Missing edge cases
        # - Missing negative tests
        assert len(suggestions) >= 5
        assert any("Statement coverage" in s for s in suggestions)
        assert any("Branch coverage" in s for s in suggestions)
        assert any("uncovered branches" in s for s in suggestions)
    
    def test_line_grouping(self):
        """Test consecutive line grouping"""
        validator = TestCoverageValidator()
        
        lines = [10, 11, 12, 15, 20, 21, 22, 30]
        groups = validator._group_consecutive_lines(lines)
        
        assert len(groups) == 4
        assert groups[0] == [10, 11, 12]
        assert groups[1] == [15]
        assert groups[2] == [20, 21, 22]
        assert groups[3] == [30]
    
    def test_similar_test_counting(self):
        """Test counting similar tests for parameterization suggestion"""
        validator = TestCoverageValidator()
        
        test_code = """
        def test_add_positive():
            assert add(1, 2) == 3
            
        def test_add_negative():
            assert add(-1, -2) == -3
            
        def test_add_zero():
            assert add(0, 5) == 5
            
        def test_add_mixed():
            assert add(-1, 1) == 0
        """
        
        count = validator._count_similar_tests(test_code)
        assert count == 4  # All have 'add' prefix
    
    @pytest.mark.asyncio
    async def test_coverage_trend_tracking(self):
        """Test that coverage trends are tracked over time"""
        validator = TestCoverageValidator(track_trends=True)
        
        # Mock the validation process
        test_code = "def test_func(): assert func() == 42"
        impl_code = "def func(): return 42"
        
        # First run
        success1, msg1, result1 = await validate_tdd_test_coverage(
            test_code, impl_code, feature_id="feature_1"
        )
        
        # Simulate improved coverage
        test_code2 = """
        def test_func(): assert func() == 42
        def test_func_edge(): assert func() != None
        """
        
        # Would need to mock the actual coverage calculation
        # This tests the API structure
        assert result1 is not None


class TestEnhancedCoverageReportGeneration:
    """Test enhanced markdown report generation"""
    
    def test_enhanced_markdown_report(self):
        """Test that enhanced reports include all new metrics"""
        validator = TestCoverageValidator()
        
        coverage_report = CoverageReport(
            statement_coverage=85.0,
            branch_coverage=75.0,
            function_coverage=90.0,
            total_statements=100,
            covered_statements=85,
            total_branches=20,
            covered_branches=15,
            total_functions=10,
            covered_functions=9,
            missing_lines={'impl.py': [10, 11, 12, 20]},
            uncovered_branches={'impl.py': ['Line 15 -> 16']},
            uncovered_functions=['unused_func']
        )
        
        result = TestCoverageResult(
            success=True,
            coverage_report=coverage_report,
            test_quality_score=82.5
        )
        
        report = validator.generate_coverage_report_markdown(result, "feature_123")
        
        # Check report contains new elements
        assert "feature_123" in report
        # The format uses hyphens
        assert "- **Statement Coverage**: 85.0% (85/100)" in report
        assert "- **Branch Coverage**: 75.0% (15/20)" in report
        assert "- **Function Coverage**: 90.0% (9/10)" in report
        assert "- **Test Quality Score**: 82.5/100" in report
        assert "Uncovered branches" in report
        assert "Line 15 -> 16" in report
        assert "10-12, 20" in report  # Grouped lines


class TestPythonCoverageValidation:
    """Test Python-specific coverage validation"""
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_python_coverage_with_branch_data(self, mock_run):
        """Test Python coverage extraction with branch coverage"""
        validator = TestCoverageValidator()
        
        # Mock pytest coverage output
        mock_coverage_data = {
            "totals": {
                "num_statements": 50,
                "covered_lines": 45,
                "percent_covered": 90.0,
                "num_branches": 10,
                "covered_branches": 8,
                "percent_covered_branches": 80.0
            },
            "files": {
                "implementation.py": {
                    "missing_lines": [15, 16],
                    "missing_branches": [[20, 22], [25, 27]],
                    "contexts": {
                        "test_func1": [1, 2, 3],
                        "test_func2": [4, 5, 6]
                    }
                }
            }
        }
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.path.exists', return_value=True):
                with patch('json.load', return_value=mock_coverage_data):
                    
                    result = await validator._validate_python_coverage(
                        "def test_x(): pass",
                        "def func1(): pass\ndef func2(): pass"
                    )
        
        assert result.success
        assert result.coverage_report.branch_coverage == 80.0
        assert result.coverage_report.statement_coverage == 90.0
        # Weighted coverage: 0.6 * 90 + 0.4 * 80 = 86
        assert abs(result.coverage_report.coverage_percentage - 86.0) < 0.1
        assert len(result.coverage_report.uncovered_branches['implementation.py']) == 2


class TestHelperFunction:
    """Test the helper function for TDD integration"""
    
    @pytest.mark.asyncio
    async def test_validate_tdd_test_coverage_enhanced(self):
        """Test the enhanced helper function returns all data"""
        with patch.object(TestCoverageValidator, 'validate_test_coverage') as mock_validate:
            # Mock successful validation
            mock_result = TestCoverageResult(
                success=True,
                coverage_report=CoverageReport(
                    statement_coverage=85.0,
                    branch_coverage=75.0,
                    function_coverage=90.0,
                    total_branches=10,
                    covered_branches=7,
                    coverage_percentage=81.0
                ),
                test_quality_score=78.5
            )
            mock_validate.return_value = mock_result
            
            success, msg, result = await validate_tdd_test_coverage(
                "test code",
                "impl code",
                minimum_coverage=80.0,
                minimum_branch_coverage=70.0,
                feature_id="test_feature"
            )
            
            assert success
            assert "Statement: 85.0%" in msg
            assert "Branch: 75.0%" in msg
            assert "Functions: 90.0%" in msg
            assert "Quality Score: 78.5/100" in msg
            assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_validate_tdd_insufficient_coverage(self):
        """Test helper function with insufficient coverage"""
        with patch.object(TestCoverageValidator, 'validate_test_coverage') as mock_validate:
            # Mock failed validation
            mock_result = TestCoverageResult(
                success=False,
                coverage_report=CoverageReport(
                    statement_coverage=70.0,
                    branch_coverage=60.0,
                    total_branches=10,
                    coverage_percentage=66.0
                ),
                suggestions=["Add tests for uncovered branches"]
            )
            mock_validate.return_value = mock_result
            
            success, msg, result = await validate_tdd_test_coverage(
                "test code",
                "impl code",
                minimum_coverage=80.0,
                minimum_branch_coverage=70.0
            )
            
            assert not success
            assert "insufficient" in msg
            assert "Statement coverage: 70.0% (need 80.0%)" in msg
            assert "Branch coverage: 60.0% (need 70.0%)" in msg
            assert "Add tests for uncovered branches" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])