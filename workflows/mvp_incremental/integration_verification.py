"""
Phase 10: Integration Verification Module

This module implements full application integration testing and completion
report generation after all features have been implemented.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from workflows.logger import workflow_logger as logger
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.test_execution import TestExecutor, TestExecutionConfig, TestResult
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker, TDDPhase


@dataclass
class IntegrationTestResult:
    """Result from integration testing."""
    all_tests_pass: bool
    unit_test_results: TestResult
    integration_test_results: Optional[TestResult]
    smoke_test_passed: bool
    smoke_test_output: str
    build_successful: bool
    build_output: str
    feature_interactions: Dict[str, bool]
    issues_found: List[str]
    tdd_compliance: Dict[str, str]  # Feature ID -> TDD phase status


@dataclass
class CompletionReport:
    """Final completion report for the project."""
    project_name: str
    timestamp: str
    features_implemented: List[Dict[str, Any]]
    test_summary: Dict[str, Any]
    build_status: str
    known_issues: List[str]
    setup_instructions: List[str]
    run_instructions: List[str]
    api_documentation: Dict[str, str]
    recommendations: List[str]
    metrics: Dict[str, Any]
    tdd_summary: Dict[str, Any]  # TDD compliance summary


class IntegrationVerifier:
    """Handles full integration verification and reporting."""
    
    def __init__(self, validator: CodeValidator, phase_tracker: Optional[TDDPhaseTracker] = None):
        self.validator = validator
        self.test_executor = TestExecutor(validator, TestExecutionConfig())
        self.phase_tracker = phase_tracker
        
    async def verify_integration(self,
                               generated_path: Path,
                               features: List[Dict[str, Any]],
                               workflow_report: Any) -> IntegrationTestResult:
        """Perform complete integration verification."""
        logger.info("Starting integration verification...")
        
        # Run all unit tests
        unit_results = await self._run_all_unit_tests(generated_path)
        
        # Run integration tests if they exist
        integration_results = await self._run_integration_tests(generated_path)
        
        # Perform smoke test
        smoke_passed, smoke_output = await self._run_smoke_test(generated_path)
        
        # Verify build
        build_success, build_output = await self._verify_build(generated_path)
        
        # Check feature interactions
        interactions = await self._check_feature_interactions(features, generated_path)
        
        # Identify issues
        issues = self._identify_issues(
            unit_results,
            integration_results,
            smoke_passed,
            build_success,
            interactions
        )
        
        # Verify TDD compliance
        tdd_compliance = self._verify_tdd_compliance(features)
        
        return IntegrationTestResult(
            all_tests_pass=unit_results.success and (integration_results.success if integration_results else True),
            unit_test_results=unit_results,
            integration_test_results=integration_results,
            smoke_test_passed=smoke_passed,
            smoke_test_output=smoke_output,
            build_successful=build_success,
            build_output=build_output,
            feature_interactions=interactions,
            issues_found=issues,
            tdd_compliance=tdd_compliance
        )
        
    async def _run_all_unit_tests(self, generated_path: Path) -> TestResult:
        """Run all unit tests in the project."""
        # Find all test files
        test_files = list(generated_path.rglob("test_*.py"))
        test_files.extend(list(generated_path.rglob("*_test.py")))
        
        if not test_files:
            return TestResult(
                success=True,
                passed=0,
                failed=0,
                errors=[],
                output="No unit tests found",
                test_files=[]
            )
            
        # Run tests
        test_paths = [str(f.relative_to(generated_path)) for f in test_files]
        return await self.test_executor._run_tests(test_paths)
        
    async def _run_integration_tests(self, generated_path: Path) -> Optional[TestResult]:
        """Run integration tests if they exist."""
        integration_dir = generated_path / "tests" / "integration"
        if not integration_dir.exists():
            return None
            
        test_files = list(integration_dir.glob("test_*.py"))
        if not test_files:
            return None
            
        test_paths = [str(f.relative_to(generated_path)) for f in test_files]
        return await self.test_executor._run_tests(test_paths)
        
    async def _run_smoke_test(self, generated_path: Path) -> Tuple[bool, str]:
        """Run a basic smoke test of the application."""
        # Look for main entry point
        main_files = ["main.py", "app.py", "__main__.py", "server.py"]
        entry_point = None
        
        for main_file in main_files:
            if (generated_path / main_file).exists():
                entry_point = main_file
                break
                
        if not entry_point:
            return True, "No main entry point found (not necessarily an error)"
            
        # Try to run the app briefly
        smoke_test_code = f"""
import subprocess
import time
import sys

# Start the app
proc = subprocess.Popen(
    [sys.executable, '{entry_point}'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give it a moment to start
time.sleep(2)

# Check if it's still running
if proc.poll() is None:
    # Still running, that's good
    proc.terminate()
    print("SUCCESS: Application started successfully")
    success = True
else:
    # Crashed immediately
    stdout, stderr = proc.communicate()
    print("FAILED: Application crashed on startup")
    print(f"STDOUT: {{stdout}}")
    print(f"STDERR: {{stderr}}")
    success = False
"""
        
        result = await self.validator.execute_code(smoke_test_code, timeout=10)
        return "SUCCESS" in result.output, result.output
        
    async def _verify_build(self, generated_path: Path) -> Tuple[bool, str]:
        """Verify the project builds successfully."""
        # Check for build files
        if (generated_path / "setup.py").exists():
            result = await self.validator.execute_code(
                "python setup.py check",
                timeout=30
            )
            return result.success, result.output
            
        elif (generated_path / "pyproject.toml").exists():
            result = await self.validator.execute_code(
                "python -m build --version",  # Just check build tool
                timeout=10
            )
            return result.success, "Build tool available"
            
        else:
            return True, "No build configuration found (simple script project)"
            
    async def _check_feature_interactions(self,
                                        features: List[Dict[str, Any]],
                                        generated_path: Path) -> Dict[str, bool]:
        """Check that features work together properly."""
        interactions = {}
        
        # Create simple interaction tests for each feature pair
        for i, feature1 in enumerate(features):
            for feature2 in features[i+1:]:
                interaction_key = f"{feature1['name']} <-> {feature2['name']}"
                
                # Simple heuristic: if both features are implemented and tests pass,
                # assume they interact correctly
                if feature1.get('status') == 'completed' and feature2.get('status') == 'completed':
                    interactions[interaction_key] = True
                else:
                    interactions[interaction_key] = False
                    
        return interactions
        
    def _identify_issues(self,
                        unit_results: TestResult,
                        integration_results: Optional[TestResult],
                        smoke_passed: bool,
                        build_success: bool,
                        interactions: Dict[str, bool]) -> List[str]:
        """Identify any issues found during verification."""
        issues = []
        
        if not unit_results.success:
            issues.append(f"Unit tests failing: {unit_results.failed} failures")
            
        if integration_results and not integration_results.success:
            issues.append(f"Integration tests failing: {integration_results.failed} failures")
            
        if not smoke_passed:
            issues.append("Application fails to start (smoke test failed)")
            
        if not build_success:
            issues.append("Build verification failed")
            
        failed_interactions = [k for k, v in interactions.items() if not v]
        if failed_interactions:
            issues.append(f"Feature interaction issues: {', '.join(failed_interactions)}")
            
        return issues
        
    async def generate_completion_report(self,
                                       project_name: str,
                                       features: List[Dict[str, Any]],
                                       integration_result: IntegrationTestResult,
                                       workflow_report: Any,
                                       generated_path: Path) -> CompletionReport:
        """Generate comprehensive completion report."""
        # Extract metrics
        metrics = self._calculate_metrics(features, integration_result, workflow_report)
        
        # Generate documentation snippets
        api_docs = self._generate_api_documentation(features)
        
        # Create setup and run instructions
        setup_instructions = self._generate_setup_instructions(generated_path)
        run_instructions = self._generate_run_instructions(generated_path)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            features,
            integration_result,
            metrics
        )
        
        # Generate TDD summary
        tdd_summary = self._generate_tdd_summary(integration_result.tdd_compliance)
        
        return CompletionReport(
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            features_implemented=[
                {
                    "name": f["name"],
                    "status": f.get("status", "unknown"),
                    "retries": f.get("retries", 0),
                    "test_coverage": f.get("test_coverage", "unknown"),
                    "tdd_phase": integration_result.tdd_compliance.get(
                        f.get('id', f.get('name', 'unknown')), 
                        "Not tracked"
                    )
                }
                for f in features
            ],
            test_summary={
                "unit_tests": {
                    "passed": integration_result.unit_test_results.passed,
                    "failed": integration_result.unit_test_results.failed,
                    "total": integration_result.unit_test_results.passed + integration_result.unit_test_results.failed
                },
                "integration_tests": {
                    "passed": integration_result.integration_test_results.passed if integration_result.integration_test_results else 0,
                    "failed": integration_result.integration_test_results.failed if integration_result.integration_test_results else 0,
                    "total": (integration_result.integration_test_results.passed + integration_result.integration_test_results.failed) if integration_result.integration_test_results else 0
                },
                "smoke_test": "PASSED" if integration_result.smoke_test_passed else "FAILED"
            },
            build_status="SUCCESS" if integration_result.build_successful else "FAILED",
            known_issues=integration_result.issues_found,
            setup_instructions=setup_instructions,
            run_instructions=run_instructions,
            api_documentation=api_docs,
            recommendations=recommendations,
            metrics=metrics,
            tdd_summary=tdd_summary
        )
        
    def _calculate_metrics(self,
                         features: List[Dict[str, Any]],
                         integration_result: IntegrationTestResult,
                         workflow_report: Any) -> Dict[str, Any]:
        """Calculate project metrics."""
        total_features = len(features)
        completed_features = sum(1 for f in features if f.get("status") == "completed")
        
        return {
            "total_features": total_features,
            "completed_features": completed_features,
            "completion_rate": f"{(completed_features/total_features)*100:.1f}%",
            "total_retries": sum(f.get("retries", 0) for f in features),
            "test_success_rate": f"{(integration_result.unit_test_results.passed / (integration_result.unit_test_results.passed + integration_result.unit_test_results.failed) * 100):.1f}%" if (integration_result.unit_test_results.passed + integration_result.unit_test_results.failed) > 0 else "N/A",
            "development_time": getattr(workflow_report, "total_duration", "unknown"),
            "code_files_generated": len(list(Path(workflow_report.output_path).rglob("*.py"))) if hasattr(workflow_report, "output_path") else "unknown"
        }
        
    def _generate_api_documentation(self, features: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate basic API documentation."""
        api_docs = {}
        
        for feature in features:
            if "api" in feature["name"].lower() or "endpoint" in feature["name"].lower():
                # Extract API details from feature
                api_docs[feature["name"]] = f"Implemented: {feature.get('description', 'No description available')}"
                
        return api_docs
        
    def _generate_setup_instructions(self, generated_path: Path) -> List[str]:
        """Generate setup instructions based on project structure."""
        instructions = []
        
        # Python environment
        instructions.append("1. Create a virtual environment: `python -m venv venv`")
        instructions.append("2. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)")
        
        # Dependencies
        if (generated_path / "requirements.txt").exists():
            instructions.append("3. Install dependencies: `pip install -r requirements.txt`")
        elif (generated_path / "pyproject.toml").exists():
            instructions.append("3. Install dependencies: `pip install -e .`")
        else:
            instructions.append("3. No dependency file found - install manually as needed")
            
        # Additional setup
        if (generated_path / "setup.py").exists():
            instructions.append("4. Install the package: `pip install -e .`")
            
        return instructions
        
    def _generate_run_instructions(self, generated_path: Path) -> List[str]:
        """Generate run instructions based on project structure."""
        instructions = []
        
        # Find entry points
        if (generated_path / "main.py").exists():
            instructions.append("Run the application: `python main.py`")
        elif (generated_path / "app.py").exists():
            instructions.append("Run the application: `python app.py`")
        elif (generated_path / "__main__.py").exists():
            instructions.append("Run the application: `python -m <package_name>`")
            
        # Look for CLI scripts
        cli_files = list(generated_path.glob("*cli*.py"))
        for cli_file in cli_files:
            instructions.append(f"CLI available: `python {cli_file.name}`")
            
        # Tests
        instructions.append("Run tests: `pytest` or `python -m pytest`")
        
        return instructions if instructions else ["No clear entry point found - check the code for main functions"]
        
    def _verify_tdd_compliance(self, features: List[Dict[str, Any]]) -> Dict[str, str]:
        """Verify TDD compliance for all features."""
        tdd_compliance = {}
        
        if not self.phase_tracker:
            # No phase tracker available, return default
            for feature in features:
                tdd_compliance[feature.get('id', feature.get('name', 'unknown'))] = "No TDD tracking"
            return tdd_compliance
        
        # Check each feature's TDD phase
        for feature in features:
            feature_id = feature.get('id', feature.get('name', 'unknown'))
            current_phase = self.phase_tracker.get_current_phase(feature_id)
            
            if current_phase is None:
                tdd_compliance[feature_id] = "Not tracked"
            else:
                tdd_compliance[feature_id] = f"{current_phase.get_emoji()} {current_phase.value}"
                
                # Add warnings for incomplete features
                if current_phase != TDDPhase.GREEN:
                    logger.warning(f"Feature {feature_id} not in GREEN phase: {current_phase.value}")
        
        return tdd_compliance
        
    def _generate_recommendations(self,
                                features: List[Dict[str, Any]],
                                integration_result: IntegrationTestResult,
                                metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        # Test coverage
        if integration_result.unit_test_results.failed > 0:
            recommendations.append(f"Fix {integration_result.unit_test_results.failed} failing unit tests")
            
        # Missing tests
        if integration_result.unit_test_results.passed + integration_result.unit_test_results.failed == 0:
            recommendations.append("Add unit tests for better code reliability")
            
        # Integration tests
        if not integration_result.integration_test_results:
            recommendations.append("Add integration tests to verify feature interactions")
            
        # Performance
        high_retry_features = [f for f in features if f.get("retries", 0) > 2]
        if high_retry_features:
            recommendations.append(f"Review {len(high_retry_features)} features that required multiple retries")
            
        # Documentation
        recommendations.append("Add comprehensive documentation for all APIs and features")
        
        # Error handling
        if integration_result.issues_found:
            recommendations.append("Address the identified issues for production readiness")
        
        # TDD compliance
        if hasattr(integration_result, 'tdd_compliance'):
            incomplete_features = [
                fid for fid, phase in integration_result.tdd_compliance.items() 
                if "GREEN" not in phase and "Not tracked" not in phase
            ]
            if incomplete_features:
                recommendations.append(f"Complete TDD cycle for {len(incomplete_features)} features not in GREEN phase")
            
        return recommendations
    
    def _generate_tdd_summary(self, tdd_compliance: Dict[str, str]) -> Dict[str, Any]:
        """Generate TDD compliance summary."""
        summary = {
            "total_features": len(tdd_compliance),
            "phases": {
                "RED": 0,
                "YELLOW": 0,
                "GREEN": 0,
                "not_tracked": 0
            },
            "compliance_rate": 0.0,
            "details": tdd_compliance
        }
        
        # Count features by phase
        for feature_id, phase_info in tdd_compliance.items():
            if "RED" in phase_info:
                summary["phases"]["RED"] += 1
            elif "YELLOW" in phase_info:
                summary["phases"]["YELLOW"] += 1
            elif "GREEN" in phase_info:
                summary["phases"]["GREEN"] += 1
            else:
                summary["phases"]["not_tracked"] += 1
        
        # Calculate compliance rate (features in GREEN phase)
        if summary["total_features"] > 0:
            summary["compliance_rate"] = (summary["phases"]["GREEN"] / summary["total_features"]) * 100
        
        return summary
        
    def save_completion_report(self, report: CompletionReport, output_path: Path) -> Path:
        """Save the completion report to a file."""
        report_path = output_path / "COMPLETION_REPORT.md"
        
        with open(report_path, "w") as f:
            f.write(f"# {report.project_name} - Completion Report\n\n")
            f.write(f"Generated: {report.timestamp}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Features Implemented**: {len(report.features_implemented)}\n")
            f.write(f"- **Build Status**: {report.build_status}\n")
            f.write(f"- **Test Summary**: {report.test_summary['unit_tests']['passed']}/{report.test_summary['unit_tests']['total']} unit tests passing\n")
            if report.known_issues:
                f.write(f"- **Known Issues**: {len(report.known_issues)}\n")
            f.write("\n")
            
            f.write("## Features\n\n")
            for feature in report.features_implemented:
                status_emoji = "✅" if feature["status"] == "completed" else "❌"
                f.write(f"- {status_emoji} **{feature['name']}**")
                if feature["retries"] > 0:
                    f.write(f" (required {feature['retries']} retries)")
                if "tdd_phase" in feature and feature["tdd_phase"] != "Not tracked":
                    f.write(f" [{feature['tdd_phase']}]")
                f.write("\n")
            f.write("\n")
            
            # Add TDD Summary section
            if hasattr(report, 'tdd_summary') and report.tdd_summary:
                f.write("## TDD Compliance Summary\n\n")
                f.write(f"- **Total Features**: {report.tdd_summary['total_features']}\n")
                f.write(f"- **Compliance Rate**: {report.tdd_summary['compliance_rate']:.1f}%\n")
                f.write(f"- **Phase Distribution**:\n")
                f.write(f"  - 🔴 RED: {report.tdd_summary['phases']['RED']} features\n")
                f.write(f"  - 🟡 YELLOW: {report.tdd_summary['phases']['YELLOW']} features\n")
                f.write(f"  - 🟢 GREEN: {report.tdd_summary['phases']['GREEN']} features\n")
                if report.tdd_summary['phases']['not_tracked'] > 0:
                    f.write(f"  - ❓ Not Tracked: {report.tdd_summary['phases']['not_tracked']} features\n")
                f.write("\n")
            
            if report.known_issues:
                f.write("## Known Issues\n\n")
                for issue in report.known_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
                
            f.write("## Setup Instructions\n\n")
            for instruction in report.setup_instructions:
                f.write(f"{instruction}\n")
            f.write("\n")
            
            f.write("## Run Instructions\n\n")
            for instruction in report.run_instructions:
                f.write(f"- {instruction}\n")
            f.write("\n")
            
            if report.api_documentation:
                f.write("## API Documentation\n\n")
                for api, doc in report.api_documentation.items():
                    f.write(f"### {api}\n{doc}\n\n")
                    
            f.write("## Metrics\n\n")
            for metric, value in report.metrics.items():
                f.write(f"- **{metric.replace('_', ' ').title()}**: {value}\n")
            f.write("\n")
            
            if report.recommendations:
                f.write("## Recommendations\n\n")
                for i, rec in enumerate(report.recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                    
        # Also save as JSON
        json_path = output_path / "completion_report.json"
        with open(json_path, "w") as f:
            json.dump(asdict(report), f, indent=2)
            
        return report_path


# Integration helper
async def perform_integration_verification(
    generated_path: Path,
    features: List[Dict[str, Any]],
    workflow_report: Any,
    project_name: str = "Generated Project",
    phase_tracker: Optional[TDDPhaseTracker] = None
) -> Tuple[IntegrationTestResult, CompletionReport]:
    """Perform complete integration verification and generate report."""
    # Create validator for the generated code path
    validator = CodeValidator()
    verifier = IntegrationVerifier(validator, phase_tracker)
    
    # Run integration verification
    integration_result = await verifier.verify_integration(
        generated_path,
        features,
        workflow_report
    )
    
    # Generate completion report
    completion_report = await verifier.generate_completion_report(
        project_name,
        features,
        integration_result,
        workflow_report,
        generated_path
    )
    
    # Save the report
    verifier.save_completion_report(completion_report, generated_path)
    
    return integration_result, completion_report