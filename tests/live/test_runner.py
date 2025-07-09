"""
Live Test Runner for MVP Incremental TDD Workflow
Executes real tests without mocks, using actual agent interactions
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import docker
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.live.test_categories import TestCategory, TestLevel, get_tests_by_level
from orchestrator.orchestrator_agent import run_team_member
from shared.data_models import WorkflowType
from workflows.workflow_manager import execute_workflow


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    test_file: str
    level: TestLevel
    status: TestStatus
    duration: float
    output: str
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class TestSuiteResult:
    """Results of entire test suite execution"""
    start_time: datetime
    end_time: datetime
    total_duration: float
    test_results: List[TestResult]
    summary: Dict[str, int]
    performance_metrics: Dict[str, Any]


class LiveTestRunner:
    """Orchestrates live test execution"""
    
    def __init__(self, 
                 output_dir: Optional[Path] = None,
                 parallel: bool = False,
                 verbose: bool = True,
                 docker_client: Optional[docker.DockerClient] = None):
        """Initialize test runner
        
        Args:
            output_dir: Directory for test outputs
            parallel: Run tests in parallel
            verbose: Show detailed output
            docker_client: Docker client for container management
        """
        self.output_dir = output_dir or Path("tests/outputs/live_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parallel = parallel
        self.verbose = verbose
        self.docker_client = docker_client or docker.from_env()
        self.session_dir = self._create_session_dir()
        
    def _create_session_dir(self) -> Path:
        """Create timestamped session directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.output_dir / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
        
    async def run_all_tests(self, levels: Optional[List[TestLevel]] = None) -> TestSuiteResult:
        """Run all tests or specific levels
        
        Args:
            levels: Specific test levels to run (None = all)
            
        Returns:
            Complete test suite results
        """
        start_time = datetime.now()
        test_results = []
        
        # Get tests to run
        if levels is None:
            levels = list(TestLevel)
            
        all_tests = []
        for level in levels:
            tests = get_tests_by_level(level)
            all_tests.extend([(level, test) for test in tests])
            
        if self.verbose:
            print(f"\n🚀 Running {len(all_tests)} live tests across {len(levels)} levels")
            print(f"📁 Output directory: {self.session_dir}")
            print("=" * 80)
            
        # Run tests
        if self.parallel and len(all_tests) > 1:
            # Run in parallel using asyncio
            tasks = []
            for level, test_info in all_tests:
                task = self._run_single_test(level, test_info)
                tasks.append(task)
            test_results = await asyncio.gather(*tasks)
        else:
            # Run sequentially
            for level, test_info in all_tests:
                result = await self._run_single_test(level, test_info)
                test_results.append(result)
                
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = self._generate_summary(test_results)
        performance_metrics = self._calculate_performance_metrics(test_results)
        
        suite_result = TestSuiteResult(
            start_time=start_time,
            end_time=end_time,
            total_duration=duration,
            test_results=test_results,
            summary=summary,
            performance_metrics=performance_metrics
        )
        
        # Save results
        self._save_results(suite_result)
        
        # Print summary
        if self.verbose:
            self._print_summary(suite_result)
            
        return suite_result
        
    async def _run_single_test(self, level: TestLevel, test_info: Dict[str, Any]) -> TestResult:
        """Run a single test case
        
        Args:
            level: Test complexity level
            test_info: Test configuration
            
        Returns:
            Test execution result
        """
        test_name = test_info["name"]
        test_file = test_info["file"]
        
        if self.verbose:
            print(f"\n▶️  Running {level.value} test: {test_name}")
            
        start_time = time.time()
        test_dir = self.session_dir / test_name
        test_dir.mkdir(exist_ok=True)
        
        try:
            # Execute the test
            result = await self._execute_test(test_info, test_dir)
            
            duration = time.time() - start_time
            
            if result["success"]:
                status = TestStatus.PASSED
                if self.verbose:
                    print(f"✅ {test_name} PASSED in {duration:.2f}s")
            else:
                status = TestStatus.FAILED
                if self.verbose:
                    print(f"❌ {test_name} FAILED in {duration:.2f}s")
                    
            return TestResult(
                test_name=test_name,
                test_file=test_file,
                level=level,
                status=status,
                duration=duration,
                output=result.get("output", ""),
                error=result.get("error"),
                metrics=result.get("metrics", {}),
                artifacts=result.get("artifacts", [])
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            if self.verbose:
                print(f"⏱️  {test_name} TIMEOUT after {duration:.2f}s")
            return TestResult(
                test_name=test_name,
                test_file=test_file,
                level=level,
                status=TestStatus.TIMEOUT,
                duration=duration,
                output="Test execution timed out",
                error="Timeout exceeded"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            if self.verbose:
                print(f"💥 {test_name} ERROR: {str(e)}")
            return TestResult(
                test_name=test_name,
                test_file=test_file,
                level=level,
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error=str(e)
            )
            
    async def _execute_test(self, test_info: Dict[str, Any], test_dir: Path) -> Dict[str, Any]:
        """Execute a test using the workflow
        
        Args:
            test_info: Test configuration
            test_dir: Directory for test outputs
            
        Returns:
            Test execution results
        """
        requirements = test_info["requirements"]
        workflow_type = test_info.get("workflow_type", "mvp_incremental")
        timeout = test_info.get("timeout", 300)  # 5 minutes default
        
        # Run the workflow
        try:
            result = await asyncio.wait_for(
                execute_workflow(
                    requirements=requirements,
                    workflow_type=workflow_type,
                    session_id=test_info["name"],
                    output_dir=str(test_dir)
                ),
                timeout=timeout
            )
            
            # Validate the result
            validation = await self._validate_result(result, test_info, test_dir)
            
            # Collect metrics
            metrics = self._collect_metrics(result, test_dir)
            
            # List artifacts
            artifacts = self._list_artifacts(test_dir)
            
            return {
                "success": validation["passed"],
                "output": json.dumps(result, indent=2),
                "error": validation.get("error"),
                "metrics": metrics,
                "artifacts": artifacts
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "metrics": {},
                "artifacts": []
            }
            
    async def _validate_result(self, result: Dict[str, Any], test_info: Dict[str, Any], test_dir: Path) -> Dict[str, Any]:
        """Validate test results against expectations
        
        Args:
            result: Workflow execution result
            test_info: Test configuration with expectations
            test_dir: Test output directory
            
        Returns:
            Validation results
        """
        validations = test_info.get("validations", [])
        
        for validation in validations:
            val_type = validation["type"]
            
            if val_type == "file_exists":
                file_path = test_dir / validation["path"]
                if not file_path.exists():
                    return {
                        "passed": False,
                        "error": f"Expected file not found: {validation['path']}"
                    }
                    
            elif val_type == "file_contains":
                file_path = test_dir / validation["path"]
                if file_path.exists():
                    content = file_path.read_text()
                    if validation["content"] not in content:
                        return {
                            "passed": False,
                            "error": f"File {validation['path']} does not contain expected content"
                        }
                else:
                    return {
                        "passed": False,
                        "error": f"File not found: {validation['path']}"
                    }
                    
            elif val_type == "docker_test":
                # Run code in Docker container
                test_result = await self._run_docker_test(test_dir, validation)
                if not test_result["success"]:
                    return {
                        "passed": False,
                        "error": f"Docker test failed: {test_result['error']}"
                    }
                    
        return {"passed": True}
        
    async def _run_docker_test(self, test_dir: Path, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation test in Docker container
        
        Args:
            test_dir: Directory with generated code
            validation: Docker test configuration
            
        Returns:
            Test execution result
        """
        try:
            # Create container
            image = validation.get("image", "python:3.9-slim")
            container = self.docker_client.containers.create(
                image,
                command=validation["command"],
                volumes={str(test_dir): {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=True
            )
            
            # Run container
            container.start()
            result = container.wait(timeout=60)
            logs = container.logs(stdout=True, stderr=True).decode()
            
            # Cleanup
            container.remove()
            
            return {
                "success": result["StatusCode"] == 0,
                "output": logs,
                "error": logs if result["StatusCode"] != 0 else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
            
    def _collect_metrics(self, result: Dict[str, Any], test_dir: Path) -> Dict[str, Any]:
        """Collect performance metrics from test execution
        
        Args:
            result: Workflow result
            test_dir: Test output directory
            
        Returns:
            Performance metrics
        """
        metrics = {
            "files_generated": len(list(test_dir.glob("**/*.py"))),
            "total_size_bytes": sum(f.stat().st_size for f in test_dir.glob("**/*") if f.is_file()),
            "phases_completed": len(result.get("phases", [])),
        }
        
        # Add timing metrics if available
        if "execution_time" in result:
            metrics["execution_time"] = result["execution_time"]
            
        return metrics
        
    def _list_artifacts(self, test_dir: Path) -> List[str]:
        """List all artifacts generated by test
        
        Args:
            test_dir: Test output directory
            
        Returns:
            List of artifact paths
        """
        artifacts = []
        for file_path in test_dir.glob("**/*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(test_dir)
                artifacts.append(str(relative_path))
        return sorted(artifacts)
        
    def _generate_summary(self, test_results: List[TestResult]) -> Dict[str, int]:
        """Generate test summary statistics
        
        Args:
            test_results: All test results
            
        Returns:
            Summary counts by status
        """
        summary = {
            "total": len(test_results),
            "passed": sum(1 for r in test_results if r.status == TestStatus.PASSED),
            "failed": sum(1 for r in test_results if r.status == TestStatus.FAILED),
            "skipped": sum(1 for r in test_results if r.status == TestStatus.SKIPPED),
            "timeout": sum(1 for r in test_results if r.status == TestStatus.TIMEOUT),
        }
        return summary
        
    def _calculate_performance_metrics(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Calculate overall performance metrics
        
        Args:
            test_results: All test results
            
        Returns:
            Performance statistics
        """
        durations = [r.duration for r in test_results]
        
        metrics = {
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "total_files_generated": sum(r.metrics.get("files_generated", 0) for r in test_results),
        }
        
        # Group by level
        by_level = {}
        for level in TestLevel:
            level_results = [r for r in test_results if r.level == level]
            if level_results:
                level_durations = [r.duration for r in level_results]
                by_level[level.value] = {
                    "count": len(level_results),
                    "avg_duration": sum(level_durations) / len(level_durations),
                    "passed": sum(1 for r in level_results if r.status == TestStatus.PASSED),
                }
        metrics["by_level"] = by_level
        
        return metrics
        
    def _save_results(self, suite_result: TestSuiteResult):
        """Save test results to file
        
        Args:
            suite_result: Complete test suite results
        """
        # Convert to JSON-serializable format
        results_data = {
            "start_time": suite_result.start_time.isoformat(),
            "end_time": suite_result.end_time.isoformat(),
            "total_duration": suite_result.total_duration,
            "summary": suite_result.summary,
            "performance_metrics": suite_result.performance_metrics,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "test_file": r.test_file,
                    "level": r.level.value,
                    "status": r.status.value,
                    "duration": r.duration,
                    "error": r.error,
                    "metrics": r.metrics,
                    "artifacts": r.artifacts,
                }
                for r in suite_result.test_results
            ]
        }
        
        # Save JSON report
        report_path = self.session_dir / "test_results.json"
        with open(report_path, "w") as f:
            json.dump(results_data, f, indent=2)
            
        # Save markdown report
        self._save_markdown_report(suite_result)
        
    def _save_markdown_report(self, suite_result: TestSuiteResult):
        """Save human-readable markdown report
        
        Args:
            suite_result: Complete test suite results
        """
        report_path = self.session_dir / "test_report.md"
        
        with open(report_path, "w") as f:
            f.write("# Live Test Execution Report\n\n")
            f.write(f"**Date**: {suite_result.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duration**: {suite_result.total_duration:.2f} seconds\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- Total Tests: {suite_result.summary['total']}\n")
            f.write(f"- ✅ Passed: {suite_result.summary['passed']}\n")
            f.write(f"- ❌ Failed: {suite_result.summary['failed']}\n")
            f.write(f"- ⏭️  Skipped: {suite_result.summary['skipped']}\n")
            f.write(f"- ⏱️  Timeout: {suite_result.summary['timeout']}\n\n")
            
            # Performance
            f.write("## Performance Metrics\n\n")
            metrics = suite_result.performance_metrics
            f.write(f"- Average Duration: {metrics['avg_duration']:.2f}s\n")
            f.write(f"- Min Duration: {metrics['min_duration']:.2f}s\n")
            f.write(f"- Max Duration: {metrics['max_duration']:.2f}s\n")
            f.write(f"- Total Files Generated: {metrics['total_files_generated']}\n\n")
            
            # By Level
            f.write("### By Complexity Level\n\n")
            for level, stats in metrics.get("by_level", {}).items():
                f.write(f"**{level}**:\n")
                f.write(f"- Tests: {stats['count']}\n")
                f.write(f"- Passed: {stats['passed']}\n")
                f.write(f"- Avg Duration: {stats['avg_duration']:.2f}s\n\n")
                
            # Detailed Results
            f.write("## Detailed Results\n\n")
            for result in suite_result.test_results:
                status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
                f.write(f"### {status_icon} {result.test_name}\n\n")
                f.write(f"- **Level**: {result.level.value}\n")
                f.write(f"- **Status**: {result.status.value}\n")
                f.write(f"- **Duration**: {result.duration:.2f}s\n")
                
                if result.error:
                    f.write(f"- **Error**: {result.error}\n")
                    
                if result.metrics:
                    f.write("- **Metrics**:\n")
                    for key, value in result.metrics.items():
                        f.write(f"  - {key}: {value}\n")
                        
                if result.artifacts:
                    f.write("- **Artifacts**:\n")
                    for artifact in result.artifacts[:5]:  # Show first 5
                        f.write(f"  - {artifact}\n")
                    if len(result.artifacts) > 5:
                        f.write(f"  - ... and {len(result.artifacts) - 5} more\n")
                        
                f.write("\n")
                
    def _print_summary(self, suite_result: TestSuiteResult):
        """Print test summary to console
        
        Args:
            suite_result: Complete test suite results
        """
        print("\n" + "=" * 80)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        # Overall stats
        total = suite_result.summary["total"]
        passed = suite_result.summary["passed"]
        failed = suite_result.summary["failed"]
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        
        if suite_result.summary["timeout"] > 0:
            print(f"⏱️  Timeout: {suite_result.summary['timeout']}")
            
        print(f"\n⏱️  Total Duration: {suite_result.total_duration:.2f}s")
        print(f"📁 Results saved to: {self.session_dir}")
        
        # Failed tests
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in suite_result.test_results:
                if result.status == TestStatus.FAILED:
                    print(f"  - {result.test_name}: {result.error}")
                    
        print("\n" + "=" * 80)


async def main():
    """Run live tests from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run live tests for MVP Incremental TDD Workflow")
    parser.add_argument("--levels", nargs="+", choices=[l.value for l in TestLevel],
                       help="Test levels to run (default: all)")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--output-dir", type=str, help="Output directory for results")
    
    args = parser.parse_args()
    
    # Convert level strings to enums
    levels = None
    if args.levels:
        levels = [TestLevel(l) for l in args.levels]
        
    # Create runner
    runner = LiveTestRunner(
        output_dir=Path(args.output_dir) if args.output_dir else None,
        parallel=args.parallel,
        verbose=not args.quiet
    )
    
    # Run tests
    results = await runner.run_all_tests(levels=levels)
    
    # Exit with appropriate code
    sys.exit(0 if results.summary["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())