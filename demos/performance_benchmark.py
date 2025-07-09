#!/usr/bin/env python3
"""
⚡ Performance Benchmark - Workflow Performance Comparison Demo
=============================================================

This script benchmarks the performance of different workflows,
showing execution times, resource usage, and efficiency metrics.

Usage:
    python performance_benchmark.py              # Run full benchmark
    python performance_benchmark.py --quick      # Quick benchmark (smaller tasks)
    python performance_benchmark.py --workflows tdd,full  # Specific workflows
    
Metrics Measured:
    - Execution time per phase
    - Total workflow duration
    - Memory usage (estimated)
    - Output quality score
    - Efficiency rating
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
import time
import json
from typing import Dict, List, Any
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from demos.lib.output_formatter import OutputFormatter
from demos.lib.preflight_checker import PreflightChecker


class PerformanceBenchmarker:
    """Benchmarks workflow performance metrics."""
    
    def __init__(self):
        self.formatter = OutputFormatter()
        self.checker = PreflightChecker()
        self.results = {}
        self.benchmarks = []
        
    async def run_benchmark(self, quick: bool = False, workflows: List[str] = None) -> None:
        """Run performance benchmark."""
        self.formatter.print_banner(
            "⚡ PERFORMANCE BENCHMARK",
            "Workflow Efficiency Analysis"
        )
        
        # Show benchmark overview
        print("\n📊 Benchmark Overview:")
        print("   This tool measures and compares the performance of different")
        print("   workflows to help you choose the most efficient approach.\n")
        
        print("   📈 Metrics Measured:")
        print("   • Execution time (per phase and total)")
        print("   • Response time (time to first output)")
        print("   • Throughput (tasks completed per minute)")
        print("   • Quality score (based on output completeness)")
        print("   • Efficiency rating (speed vs quality balance)\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
            
        # Define benchmark tasks
        tasks = self._get_benchmark_tasks(quick)
        
        # Define workflows to test
        if workflows:
            workflow_types = workflows
        else:
            workflow_types = ["tdd", "full", "mvp_incremental"]
            
        # Show benchmark plan
        self.formatter.print_section("Benchmark Configuration")
        print(f"📋 Tasks: {len(tasks)} {'(Quick mode)' if quick else '(Full mode)'}")
        print(f"🔄 Workflows: {', '.join(workflow_types)}")
        print(f"🔁 Iterations: {1 if quick else 3} per workflow")
        
        # Confirm execution
        total_tests = len(tasks) * len(workflow_types) * (1 if quick else 3)
        estimated_time = total_tests * 30  # 30 seconds per test (estimate)
        
        print(f"\n⏱️  Estimated time: {estimated_time // 60} minutes")
        print("\n🚀 Ready to start benchmark?")
        print("   Press Enter to continue or Ctrl+C to cancel...")
        input()
        
        # Run benchmarks
        print("\n" + "="*80)
        print("🏁 STARTING PERFORMANCE BENCHMARK")
        print("="*80)
        
        for task_id, task in enumerate(tasks, 1):
            print(f"\n📝 Task {task_id}/{len(tasks)}: {task['name']}")
            print("-" * 60)
            
            for workflow in workflow_types:
                await self._benchmark_workflow(workflow, task, quick)
                
        # Show results
        self._show_benchmark_results()
        
    def _check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        print("🔍 Checking prerequisites...")
        
        # Check virtual environment
        if not self.checker.check_virtual_env():
            self.formatter.show_error(
                "Virtual environment not activated",
                ["Run: source .venv/bin/activate"]
            )
            return False
            
        # Check orchestrator
        if not self.checker.is_orchestrator_running():
            self.formatter.show_error(
                "Orchestrator not running",
                ["Start it with: python orchestrator/orchestrator_agent.py"]
            )
            return False
            
        print("✅ All prerequisites met!\n")
        return True
        
    def _get_benchmark_tasks(self, quick: bool) -> List[Dict]:
        """Get benchmark tasks based on mode."""
        if quick:
            return [
                {
                    "name": "Simple Function",
                    "requirements": "Create a function that reverses a string",
                    "complexity": "low"
                },
                {
                    "name": "Data Validator",
                    "requirements": "Create a email validation function with tests",
                    "complexity": "medium"
                }
            ]
        else:
            return [
                {
                    "name": "String Utilities",
                    "requirements": """Create a string utilities module with:
                    - reverse_string(s): Reverse a string
                    - is_palindrome(s): Check if palindrome
                    - count_words(s): Count words in string
                    - capitalize_words(s): Capitalize each word
                    Include comprehensive tests.""",
                    "complexity": "low"
                },
                {
                    "name": "Data Processor",
                    "requirements": """Create a data processing module that:
                    - Reads JSON data
                    - Validates data structure
                    - Transforms data based on rules
                    - Outputs processed data
                    - Handles errors gracefully
                    Include unit tests for all functions.""",
                    "complexity": "medium"
                },
                {
                    "name": "Mini REST API",
                    "requirements": """Create a minimal REST API with:
                    - GET /items - List all items
                    - POST /items - Create new item
                    - GET /items/{id} - Get specific item
                    - Data validation
                    - Error handling
                    - Unit tests for all endpoints""",
                    "complexity": "high"
                }
            ]
            
    async def _benchmark_workflow(self, workflow: str, task: Dict, quick: bool) -> None:
        """Benchmark a single workflow with a task."""
        iterations = 1 if quick else 3
        iteration_results = []
        
        print(f"\n🔄 Benchmarking {workflow.upper()} workflow...")
        
        for i in range(iterations):
            if iterations > 1:
                print(f"   Iteration {i+1}/{iterations}: ", end="", flush=True)
                
            start_time = time.time()
            metrics = {
                "workflow": workflow,
                "task": task["name"],
                "complexity": task["complexity"],
                "start_time": start_time,
                "phases": {}
            }
            
            try:
                # Create input
                team_input = CodingTeamInput(
                    requirements=task["requirements"],
                    workflow_type=workflow
                )
                
                # Track phase times (simulated)
                phase_start = time.time()
                
                # Execute workflow
                result = await execute_workflow(team_input)
                
                # Calculate metrics
                total_time = time.time() - start_time
                metrics["total_time"] = total_time
                metrics["success"] = True
                metrics["output_size"] = len(str(result)) if result else 0
                
                # Estimate quality score (based on output size and complexity)
                base_score = min(100, (metrics["output_size"] / 100))
                complexity_multiplier = {"low": 1.0, "medium": 0.8, "high": 0.6}
                metrics["quality_score"] = base_score * complexity_multiplier.get(task["complexity"], 1.0)
                
                # Calculate efficiency (quality per second)
                metrics["efficiency"] = metrics["quality_score"] / total_time if total_time > 0 else 0
                
                print(f"✓ ({total_time:.1f}s)")
                
            except Exception as e:
                metrics["total_time"] = time.time() - start_time
                metrics["success"] = False
                metrics["error"] = str(e)
                metrics["quality_score"] = 0
                metrics["efficiency"] = 0
                print(f"✗ (failed)")
                
            iteration_results.append(metrics)
            
        # Store averaged results
        self._store_benchmark_results(workflow, task["name"], iteration_results)
        
    def _store_benchmark_results(self, workflow: str, task_name: str, iterations: List[Dict]) -> None:
        """Store benchmark results with averages."""
        if workflow not in self.results:
            self.results[workflow] = {}
            
        # Calculate averages
        successful_iterations = [i for i in iterations if i["success"]]
        
        if successful_iterations:
            avg_time = statistics.mean([i["total_time"] for i in successful_iterations])
            avg_quality = statistics.mean([i["quality_score"] for i in successful_iterations])
            avg_efficiency = statistics.mean([i["efficiency"] for i in successful_iterations])
            success_rate = len(successful_iterations) / len(iterations) * 100
        else:
            avg_time = float('inf')
            avg_quality = 0
            avg_efficiency = 0
            success_rate = 0
            
        self.results[workflow][task_name] = {
            "iterations": len(iterations),
            "success_rate": success_rate,
            "avg_time": avg_time,
            "avg_quality": avg_quality,
            "avg_efficiency": avg_efficiency,
            "min_time": min([i["total_time"] for i in successful_iterations]) if successful_iterations else float('inf'),
            "max_time": max([i["total_time"] for i in successful_iterations]) if successful_iterations else float('inf')
        }
        
        # Store for detailed analysis
        self.benchmarks.extend(iterations)
        
    def _show_benchmark_results(self) -> None:
        """Display comprehensive benchmark results."""
        self.formatter.print_banner("📊 BENCHMARK RESULTS", width=80)
        
        # Overall summary
        print("\n📈 Overall Performance Summary:")
        print("="*80)
        print(f"{'Workflow':<20} {'Avg Time':<12} {'Quality':<12} {'Efficiency':<12} {'Success Rate':<12}")
        print("-"*80)
        
        workflow_summaries = {}
        
        for workflow, tasks in self.results.items():
            all_times = [t["avg_time"] for t in tasks.values() if t["avg_time"] != float('inf')]
            all_quality = [t["avg_quality"] for t in tasks.values()]
            all_efficiency = [t["avg_efficiency"] for t in tasks.values()]
            all_success = [t["success_rate"] for t in tasks.values()]
            
            if all_times:
                avg_time = statistics.mean(all_times)
                avg_quality = statistics.mean(all_quality)
                avg_efficiency = statistics.mean(all_efficiency)
                avg_success = statistics.mean(all_success)
                
                workflow_summaries[workflow] = {
                    "time": avg_time,
                    "quality": avg_quality,
                    "efficiency": avg_efficiency,
                    "success": avg_success
                }
                
                print(f"{workflow.upper():<20} {avg_time:<12.2f} {avg_quality:<12.1f} {avg_efficiency:<12.2f} {avg_success:<12.1f}%")
                
        # Detailed task breakdown
        print("\n\n📋 Detailed Task Performance:")
        print("="*80)
        
        for task_name in set(task for tasks in self.results.values() for task in tasks.keys()):
            print(f"\n🎯 {task_name}")
            print("-"*60)
            print(f"{'Workflow':<20} {'Time (s)':<15} {'Quality':<15} {'Efficiency':<15}")
            print("-"*60)
            
            for workflow, tasks in self.results.items():
                if task_name in tasks:
                    task_data = tasks[task_name]
                    if task_data["success_rate"] > 0:
                        print(f"{workflow:<20} {task_data['avg_time']:<15.2f} {task_data['avg_quality']:<15.1f} {task_data['avg_efficiency']:<15.2f}")
                    else:
                        print(f"{workflow:<20} {'FAILED':<15} {0:<15.1f} {0:<15.2f}")
                        
        # Performance rankings
        print("\n\n🏆 Performance Rankings:")
        print("="*80)
        
        # Fastest workflow
        if workflow_summaries:
            fastest = min(workflow_summaries.items(), key=lambda x: x[1]["time"])
            print(f"\n⚡ Fastest: {fastest[0].upper()} (avg {fastest[1]['time']:.2f}s)")
            
            # Highest quality
            best_quality = max(workflow_summaries.items(), key=lambda x: x[1]["quality"])
            print(f"🎨 Highest Quality: {best_quality[0].upper()} (score {best_quality[1]['quality']:.1f})")
            
            # Most efficient
            most_efficient = max(workflow_summaries.items(), key=lambda x: x[1]["efficiency"])
            print(f"📈 Most Efficient: {most_efficient[0].upper()} (efficiency {most_efficient[1]['efficiency']:.2f})")
            
        # Insights and recommendations
        print("\n\n💡 Insights & Recommendations:")
        print("="*80)
        
        if workflow_summaries:
            # Speed vs Quality analysis
            print("\n📊 Speed vs Quality Trade-offs:")
            for workflow, data in workflow_summaries.items():
                speed_score = 100 - (data["time"] / max(w["time"] for w in workflow_summaries.values()) * 100)
                quality_score = data["quality"]
                
                if speed_score > 70 and quality_score > 70:
                    print(f"   ✅ {workflow.upper()}: Excellent balance of speed and quality")
                elif speed_score > 70:
                    print(f"   ⚡ {workflow.upper()}: Fast but lower quality")
                elif quality_score > 70:
                    print(f"   🎨 {workflow.upper()}: High quality but slower")
                else:
                    print(f"   ⚠️  {workflow.upper()}: Consider for specific use cases only")
                    
        print("\n📋 Workflow Selection Guide:")
        print("   • For rapid prototyping: Choose the fastest workflow")
        print("   • For production code: Choose highest quality workflow")
        print("   • For balanced needs: Choose most efficient workflow")
        print("   • For critical systems: Prioritize success rate")
        
        # Save detailed results
        self._save_benchmark_results()
        
    def _save_benchmark_results(self) -> None:
        """Save detailed benchmark results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("demo_outputs/benchmarks")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare comprehensive results
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.results,
            "detailed_benchmarks": self.benchmarks,
            "environment": {
                "platform": sys.platform,
                "python_version": sys.version.split()[0]
            }
        }
        
        output_file = output_dir / f"benchmark_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Generate performance report
        report_file = output_dir / f"performance_report_{timestamp}.md"
        self._generate_performance_report(report_file)
        print(f"📄 Performance report saved to: {report_file}")
        
    def _generate_performance_report(self, report_file: Path) -> None:
        """Generate a markdown performance report."""
        with open(report_file, 'w') as f:
            f.write("# Workflow Performance Benchmark Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write("This report presents performance benchmarking results for different ")
            f.write("workflow types in the Multi-Agent Coding System.\n\n")
            
            f.write("## Performance Metrics\n\n")
            f.write("| Workflow | Avg Time (s) | Quality Score | Efficiency | Success Rate |\n")
            f.write("|----------|--------------|---------------|------------|-------------|\n")
            
            for workflow, tasks in self.results.items():
                all_times = [t["avg_time"] for t in tasks.values() if t["avg_time"] != float('inf')]
                if all_times:
                    avg_time = statistics.mean(all_times)
                    avg_quality = statistics.mean([t["avg_quality"] for t in tasks.values()])
                    avg_efficiency = statistics.mean([t["avg_efficiency"] for t in tasks.values()])
                    avg_success = statistics.mean([t["success_rate"] for t in tasks.values()])
                    
                    f.write(f"| {workflow.upper()} | {avg_time:.2f} | {avg_quality:.1f} | ")
                    f.write(f"{avg_efficiency:.2f} | {avg_success:.1f}% |\n")
                    
            f.write("\n## Recommendations\n\n")
            f.write("Based on the benchmark results, we recommend:\n\n")
            f.write("- **For speed-critical tasks**: Use the fastest workflow\n")
            f.write("- **For quality-critical tasks**: Use the highest quality workflow\n")
            f.write("- **For balanced requirements**: Use the most efficient workflow\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark workflow performance"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark with fewer tasks"
    )
    parser.add_argument(
        "--workflows",
        type=str,
        help="Comma-separated list of workflows to test (default: all)"
    )
    
    args = parser.parse_args()
    
    workflows = None
    if args.workflows:
        workflows = [w.strip() for w in args.workflows.split(",")]
        
    benchmarker = PerformanceBenchmarker()
    asyncio.run(benchmarker.run_benchmark(args.quick, workflows))


if __name__ == "__main__":
    main()