"""
Progress Monitor for MVP Incremental Workflow
Provides real-time visibility into workflow execution progress
"""
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    # TDD-specific states
    WRITING_TESTS = "writing_tests"
    TESTS_WRITTEN = "tests_written"
    TESTS_FAILING = "tests_failing"  # Red phase
    IMPLEMENTING = "implementing"
    TESTS_PASSING = "tests_passing"   # Yellow phase (was Green)
    AWAITING_REVIEW = "awaiting_review"  # Yellow phase
    APPROVED = "approved"              # Green phase
    REFACTORING = "refactoring"       # Refactor phase


@dataclass
class StepProgress:
    """Progress information for a single step"""
    step_name: str
    step_type: str  # planning, design, feature, validation
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if step is complete (either succeeded or failed)"""
        return self.status in [StepStatus.COMPLETED, StepStatus.FAILED]


@dataclass
class FeatureProgress:
    """Progress tracking for a specific feature"""
    feature_id: str
    feature_title: str
    total_attempts: int = 0
    validation_passed: bool = False
    current_status: StepStatus = StepStatus.PENDING
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    # TDD-specific tracking
    tests_written: bool = False
    tests_initial_run: bool = False
    tests_passing: bool = False
    test_file_count: int = 0
    test_function_count: int = 0
    code_coverage: Optional[float] = None
    # TDD phase tracking
    tdd_phase: Optional[str] = None  # RED, YELLOW, GREEN
    time_entered_yellow: Optional[datetime] = None
    review_attempts: int = 0
    # Enhanced TDD tracking
    phase_durations: Dict[str, float] = field(default_factory=dict)  # Phase -> duration in seconds
    phase_transitions: List[Tuple[str, str, datetime]] = field(default_factory=list)  # (from, to, timestamp)
    test_execution_times: List[float] = field(default_factory=list)  # Test run times in seconds
    time_entered_red: Optional[datetime] = None
    time_entered_green: Optional[datetime] = None
    test_failure_counts: Dict[int, int] = field(default_factory=dict)  # attempt -> failure count
    test_fix_iterations: int = 0  # Number of times tests were fixed


class ProgressMonitor:
    """
    Monitor and report progress of MVP incremental workflow execution.
    Provides real-time updates and summary statistics.
    """
    
    def __init__(self):
        self.workflow_start_time = None
        self.workflow_end_time = None
        self.steps: List[StepProgress] = []
        self.features: Dict[str, FeatureProgress] = {}
        self.current_phase = None
        self.total_features = 0
        
    def start_workflow(self, total_features: int = 0):
        """Mark workflow start"""
        self.workflow_start_time = datetime.now()
        self.total_features = total_features
        self._print_header()
        
    def end_workflow(self):
        """Mark workflow end and print summary"""
        self.workflow_end_time = datetime.now()
        self._print_summary()
        
        # Print enhanced TDD visualizations
        self.print_tdd_phase_timeline()
        self.print_test_progression()
        self.print_phase_progress_bars()
        
    def start_phase(self, phase_name: str):
        """Start a new phase (planning, design, implementation)"""
        self.current_phase = phase_name
        print(f"\n{'='*60}")
        print(f"📍 PHASE: {phase_name.upper()}")
        print(f"{'='*60}")
        
    def start_step(self, step_name: str, step_type: str, metadata: Dict[str, Any] = None):
        """Start tracking a new step"""
        step = StepProgress(
            step_name=step_name,
            step_type=step_type,
            status=StepStatus.IN_PROGRESS,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        self.steps.append(step)
        
        # Print progress indicator
        if step_type == "feature":
            feature_num = metadata.get("feature_num", "?")
            feature_title = metadata.get("feature_title", "Unknown")
            print(f"\n⚙️  Feature {feature_num}/{self.total_features}: {feature_title}")
            print(f"   Status: Starting implementation...")
        else:
            print(f"\n⚙️  {step_type.title()}: Starting...")
            
    def update_step(self, step_name: str, status: StepStatus, error_message: str = None):
        """Update step status"""
        step = self._find_step(step_name)
        if step:
            step.status = status
            if error_message:
                step.error_message = error_message
            
            # Print status update
            if status == StepStatus.RETRYING:
                print(f"   🔄 Retrying (attempt {step.retry_count + 1})...")
                step.retry_count += 1
            elif status == StepStatus.FAILED:
                print(f"   ❌ Failed: {error_message or 'Unknown error'}")
            elif status == StepStatus.COMPLETED:
                duration = (datetime.now() - step.start_time).total_seconds()
                print(f"   ✅ Completed in {duration:.1f}s")
            # TDD-specific status updates
            elif status == StepStatus.WRITING_TESTS:
                print(f"   ✍️  Writing tests...")
            elif status == StepStatus.TESTS_WRITTEN:
                print(f"   📝 Tests written")
            elif status == StepStatus.TESTS_FAILING:
                print(f"   🔴 Tests failing (expected - TDD red phase)")
            elif status == StepStatus.IMPLEMENTING:
                print(f"   🔨 Implementing code to pass tests...")
            elif status == StepStatus.TESTS_PASSING:
                print(f"   🟡 Tests passing - awaiting review (TDD yellow phase)")
            elif status == StepStatus.AWAITING_REVIEW:
                print(f"   🟡 Implementation awaiting review...")
            elif status == StepStatus.APPROVED:
                print(f"   🟢 Implementation approved (TDD green phase)")
            elif status == StepStatus.REFACTORING:
                print(f"   🔧 Refactoring code...")
                
    def complete_step(self, step_name: str, success: bool = True, metadata: Dict[str, Any] = None):
        """Mark step as complete"""
        step = self._find_step(step_name)
        if step:
            step.end_time = datetime.now()
            step.status = StepStatus.COMPLETED if success else StepStatus.FAILED
            if metadata:
                step.metadata.update(metadata)
                
    def start_feature(self, feature_id: str, feature_title: str, feature_num: int):
        """Start tracking a new feature"""
        feature = FeatureProgress(
            feature_id=feature_id,
            feature_title=feature_title,
            start_time=datetime.now()
        )
        self.features[feature_id] = feature
        
        # Start the feature step
        self.start_step(
            f"feature_{feature_id}",
            "feature",
            {
                "feature_num": feature_num,
                "feature_title": feature_title
            }
        )
        
    def update_feature_validation(self, feature_id: str, passed: bool, error: str = None):
        """Update feature validation status"""
        if feature_id in self.features:
            feature = self.features[feature_id]
            feature.validation_passed = passed
            if error:
                feature.errors.append(error)
            
            status_icon = "✅" if passed else "❌"
            print(f"   {status_icon} Validation: {'PASSED' if passed else 'FAILED'}")
            
    def update_tdd_phase(self, feature_id: str, phase: str, status: Optional[StepStatus] = None):
        """Update TDD phase for a feature with enhanced tracking"""
        if feature_id in self.features:
            feature = self.features[feature_id]
            previous_phase = feature.tdd_phase
            current_time = datetime.now()
            
            # Track phase transition
            if previous_phase and previous_phase != phase:
                feature.phase_transitions.append((previous_phase, phase, current_time))
                
                # Calculate duration of previous phase
                if previous_phase == "RED" and feature.time_entered_red:
                    duration = (current_time - feature.time_entered_red).total_seconds()
                    feature.phase_durations["RED"] = feature.phase_durations.get("RED", 0) + duration
                elif previous_phase == "YELLOW" and feature.time_entered_yellow:
                    duration = (current_time - feature.time_entered_yellow).total_seconds()
                    feature.phase_durations["YELLOW"] = feature.phase_durations.get("YELLOW", 0) + duration
                elif previous_phase == "GREEN" and feature.time_entered_green:
                    duration = (current_time - feature.time_entered_green).total_seconds()
                    feature.phase_durations["GREEN"] = feature.phase_durations.get("GREEN", 0) + duration
            
            # Update phase and timestamps
            feature.tdd_phase = phase
            
            if phase == "RED" and feature.time_entered_red is None:
                feature.time_entered_red = current_time
            elif phase == "YELLOW":
                if feature.time_entered_yellow is None:
                    feature.time_entered_yellow = current_time
                else:
                    # Re-entering YELLOW (from RED after fixes)
                    feature.test_fix_iterations += 1
            elif phase == "GREEN" and feature.time_entered_green is None:
                feature.time_entered_green = current_time
                
            if status:
                feature.current_status = status
                
            # Print enhanced phase transition
            phase_icons = {
                "RED": "🔴",
                "YELLOW": "🟡", 
                "GREEN": "🟢"
            }
            icon = phase_icons.get(phase, "⚪")
            
            # Show transition if applicable
            if previous_phase and previous_phase != phase:
                prev_icon = phase_icons.get(previous_phase, "⚪")
                print(f"   {prev_icon}→{icon} TDD Phase Transition: {previous_phase} → {phase}")
            else:
                print(f"   {icon} TDD Phase: {phase}")
            
    def increment_review_attempts(self, feature_id: str):
        """Increment review attempts for a feature in YELLOW phase"""
        if feature_id in self.features:
            self.features[feature_id].review_attempts += 1
            
    def complete_feature(self, feature_id: str, success: bool):
        """Mark feature as complete"""
        if feature_id in self.features:
            feature = self.features[feature_id]
            feature.end_time = datetime.now()
            feature.current_status = StepStatus.COMPLETED if success else StepStatus.FAILED
            
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        if self.total_features == 0:
            return 0.0
            
        completed_features = sum(1 for f in self.features.values() if f.current_status == StepStatus.COMPLETED)
        return (completed_features / self.total_features) * 100
        
    def get_elapsed_time(self) -> str:
        """Get elapsed time since workflow start"""
        if not self.workflow_start_time:
            return "0:00"
            
        elapsed = datetime.now() - self.workflow_start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        return f"{minutes}:{seconds:02d}"
        
    def print_progress_bar(self):
        """Print a visual progress bar"""
        percentage = self.get_progress_percentage()
        bar_length = 40
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        elapsed = self.get_elapsed_time()
        print(f"\n📊 Progress: [{bar}] {percentage:.0f}% | Time: {elapsed}")
        
    def _find_step(self, step_name: str) -> Optional[StepProgress]:
        """Find a step by name"""
        for step in reversed(self.steps):  # Search from most recent
            if step.step_name == step_name:
                return step
        return None
        
    def _print_header(self):
        """Print workflow start header"""
        print("\n" + "="*60)
        print("🚀 MVP INCREMENTAL WORKFLOW")
        print("="*60)
        print(f"⏰ Started at: {self.workflow_start_time.strftime('%H:%M:%S')}")
        if self.total_features > 0:
            print(f"📋 Total features to implement: {self.total_features}")
        print("="*60)
        
    def _print_summary(self):
        """Print workflow summary"""
        if not self.workflow_end_time:
            self.workflow_end_time = datetime.now()
            
        total_duration = (self.workflow_end_time - self.workflow_start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📈 WORKFLOW SUMMARY")
        print("="*60)
        
        # Overall stats
        print(f"\n⏱️  Total Duration: {total_duration:.1f} seconds")
        print(f"📊 Total Steps: {len(self.steps)}")
        
        # Phase breakdown
        phase_times = self._calculate_phase_times()
        if phase_times:
            print("\n📋 Phase Breakdown:")
            for phase, duration in phase_times.items():
                print(f"   - {phase}: {duration:.1f}s")
                
        # Feature stats
        if self.features:
            successful_features = sum(1 for f in self.features.values() if f.validation_passed)
            failed_features = len(self.features) - successful_features
            retried_features = sum(1 for f in self.features.values() if f.total_attempts > 1)
            
            print(f"\n🔧 Feature Implementation:")
            print(f"   - Total: {len(self.features)}")
            print(f"   - Successful: {successful_features}")
            print(f"   - Failed: {failed_features}")
            print(f"   - Required Retry: {retried_features}")
            
            # TDD stats
            features_with_tests = sum(1 for f in self.features.values() if f.tests_written)
            features_tests_passing = sum(1 for f in self.features.values() if f.tests_passing)
            features_in_yellow = sum(1 for f in self.features.values() if f.tdd_phase == "YELLOW")
            features_in_green = sum(1 for f in self.features.values() if f.tdd_phase == "GREEN")
            total_review_attempts = sum(f.review_attempts for f in self.features.values())
            total_test_files = sum(f.test_file_count for f in self.features.values())
            total_test_functions = sum(f.test_function_count for f in self.features.values())
            avg_coverage = self._calculate_average_coverage()
            
            print(f"\n🧪 TDD Metrics:")
            print(f"   - Features with tests: {features_with_tests}/{len(self.features)}")
            print(f"   - Features with passing tests: {features_tests_passing}/{len(self.features)}")
            print(f"   - Total test files: {total_test_files}")
            print(f"   - Total test functions: {total_test_functions}")
            if avg_coverage is not None:
                print(f"   - Average code coverage: {avg_coverage:.1f}%")
                
            print(f"\n🚦 TDD Phase Status:")
            print(f"   - 🔴 RED (implementing): {len(self.features) - features_in_yellow - features_in_green}")
            print(f"   - 🟡 YELLOW (awaiting review): {features_in_yellow}")
            print(f"   - 🟢 GREEN (approved): {features_in_green}")
            if total_review_attempts > 0:
                print(f"   - Total review attempts: {total_review_attempts}")
            
            # Enhanced TDD metrics
            phase_metrics = self.get_phase_metrics()
            
            print(f"\n⏱️  TDD Phase Timing:")
            for phase in ["RED", "YELLOW", "GREEN"]:
                phase_data = phase_metrics["phase_summary"][phase]
                if phase_data["total_duration"] > 0:
                    avg_mins = int(phase_data["avg_duration"] // 60)
                    avg_secs = int(phase_data["avg_duration"] % 60)
                    total_mins = int(phase_data["total_duration"] // 60)
                    total_secs = int(phase_data["total_duration"] % 60)
                    print(f"   - {phase}: avg {avg_mins}m {avg_secs}s, total {total_mins}m {total_secs}s")
            
            test_metrics = phase_metrics["test_metrics"]
            if test_metrics["avg_test_execution_time"] > 0:
                print(f"\n📊 Test Execution Metrics:")
                print(f"   - Average test execution time: {test_metrics['avg_test_execution_time']:.1f}s")
                if test_metrics["total_fix_iterations"] > 0:
                    print(f"   - Total test fix iterations: {test_metrics['total_fix_iterations']}")
                    avg_fix_iterations = test_metrics["total_fix_iterations"] / len([f for f in self.features.values() if f.test_fix_iterations > 0])
                    print(f"   - Average fix iterations per feature: {avg_fix_iterations:.1f}")
            
        # Error summary
        all_errors = []
        for feature in self.features.values():
            all_errors.extend(feature.errors)
            
        if all_errors:
            print(f"\n⚠️  Errors Encountered: {len(all_errors)}")
            # Show unique error types
            error_types = {}
            for error in all_errors:
                error_type = error.split(':')[0] if ':' in error else 'Unknown'
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            print("   Error Types:")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {error_type}: {count}")
                
        print("\n" + "="*60)
        
    def _calculate_phase_times(self) -> Dict[str, float]:
        """Calculate time spent in each phase"""
        phase_times = {}
        
        for step in self.steps:
            if step.duration_seconds:
                phase = step.step_type
                if phase not in phase_times:
                    phase_times[phase] = 0
                phase_times[phase] += step.duration_seconds
                
        return phase_times
        
    def update_tdd_progress(self, feature_id: str, tdd_phase: str, metadata: Dict[str, Any] = None):
        """Update TDD-specific progress for a feature"""
        if feature_id in self.features:
            feature = self.features[feature_id]
            
            if tdd_phase == "tests_written":
                feature.tests_written = True
                feature.test_file_count = metadata.get("test_files", 0) if metadata else 0
                feature.test_function_count = metadata.get("test_functions", 0) if metadata else 0
                print(f"   📝 Tests written: {feature.test_file_count} files, {feature.test_function_count} test functions")
            elif tdd_phase == "tests_initial_run":
                feature.tests_initial_run = True
                passed = metadata.get("passed", 0) if metadata else 0
                failed = metadata.get("failed", 0) if metadata else 0
                print(f"   🔴 Initial test run: {passed} passed, {failed} failed (expected failures)")
                # Track failure count
                attempt = metadata.get("attempt", 0) if metadata else 0
                if attempt >= 0:
                    feature.test_failure_counts[attempt] = failed
                # Track execution time
                exec_time = metadata.get("execution_time", None) if metadata else None
                if exec_time:
                    feature.test_execution_times.append(exec_time)
            elif tdd_phase == "tests_passing":
                feature.tests_passing = True
                feature.code_coverage = metadata.get("coverage", None) if metadata else None
                if feature.code_coverage:
                    print(f"   🟢 All tests passing! Coverage: {feature.code_coverage:.1f}%")
                else:
                    print(f"   🟢 All tests passing!")
                # Track final test run
                exec_time = metadata.get("execution_time", None) if metadata else None
                if exec_time:
                    feature.test_execution_times.append(exec_time)
                    
    def export_metrics(self) -> Dict[str, Any]:
        """Export progress metrics for analysis with enhanced TDD metrics"""
        # Get phase metrics
        phase_metrics = self.get_phase_metrics()
        
        # Calculate TDD metrics
        tdd_metrics = {
            "features_with_tests": sum(1 for f in self.features.values() if f.tests_written),
            "features_tests_passing": sum(1 for f in self.features.values() if f.tests_passing),
            "total_test_files": sum(f.test_file_count for f in self.features.values()),
            "total_test_functions": sum(f.test_function_count for f in self.features.values()),
            "average_coverage": self._calculate_average_coverage(),
            "phase_metrics": phase_metrics["phase_summary"],
            "test_execution_metrics": phase_metrics["test_metrics"]
        }
        
        return {
            "workflow_duration": (self.workflow_end_time - self.workflow_start_time).total_seconds() if self.workflow_end_time else None,
            "total_steps": len(self.steps),
            "total_features": len(self.features),
            "successful_features": sum(1 for f in self.features.values() if f.validation_passed),
            "failed_features": sum(1 for f in self.features.values() if not f.validation_passed),
            "retried_features": sum(1 for f in self.features.values() if f.total_attempts > 1),
            "phase_times": self._calculate_phase_times(),
            "tdd_metrics": tdd_metrics,
            "feature_details": {
                fid: {
                    "title": f.feature_title,
                    "passed": f.validation_passed,
                    "attempts": f.total_attempts,
                    "errors": f.errors,
                    "tests_written": f.tests_written,
                    "tests_passing": f.tests_passing,
                    "test_files": f.test_file_count,
                    "test_functions": f.test_function_count,
                    "coverage": f.code_coverage,
                    "tdd_phase": f.tdd_phase,
                    "phase_durations": f.phase_durations,
                    "phase_transitions": [(from_p, to_p, ts.isoformat()) for from_p, to_p, ts in f.phase_transitions],
                    "test_fix_iterations": f.test_fix_iterations,
                    "review_attempts": f.review_attempts,
                    "test_execution_times": f.test_execution_times,
                    "test_failure_counts": f.test_failure_counts
                }
                for fid, f in self.features.items()
            }
        }
    
    def _calculate_average_coverage(self) -> Optional[float]:
        """Calculate average code coverage across features"""
        coverages = [f.code_coverage for f in self.features.values() if f.code_coverage is not None]
        if coverages:
            return sum(coverages) / len(coverages)
        return None
    
    def print_tdd_phase_timeline(self):
        """Print a visual timeline of TDD phase transitions"""
        if not self.features:
            return
            
        print("\n🕒 TDD PHASE TIMELINE")
        print("="*60)
        
        for feature_id, feature in self.features.items():
            if not feature.phase_transitions:
                continue
                
            print(f"\n📋 {feature.feature_title}")
            
            # Show initial phase
            if feature.time_entered_red:
                print(f"   🔴 RED started at {feature.time_entered_red.strftime('%H:%M:%S')}")
            
            # Show transitions
            for from_phase, to_phase, timestamp in feature.phase_transitions:
                print(f"   ↓  {from_phase} → {to_phase} at {timestamp.strftime('%H:%M:%S')}")
            
            # Show phase durations
            if feature.phase_durations:
                print("   ⏱️  Phase Durations:")
                for phase, duration in feature.phase_durations.items():
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    print(f"      {phase}: {mins}m {secs}s")
            
            # Show test metrics
            if feature.test_fix_iterations > 0:
                print(f"   🔧 Test fix iterations: {feature.test_fix_iterations}")
            if feature.review_attempts > 0:
                print(f"   👀 Review attempts: {feature.review_attempts}")
    
    def get_phase_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for each TDD phase"""
        metrics = {
            "total_features": len(self.features),
            "phase_summary": {
                "RED": {"count": 0, "total_duration": 0.0, "avg_duration": 0.0},
                "YELLOW": {"count": 0, "total_duration": 0.0, "avg_duration": 0.0},
                "GREEN": {"count": 0, "total_duration": 0.0, "avg_duration": 0.0}
            },
            "test_metrics": {
                "total_test_files": 0,
                "total_test_functions": 0,
                "avg_test_execution_time": 0.0,
                "total_fix_iterations": 0,
                "avg_coverage": 0.0
            }
        }
        
        # Collect phase metrics
        for feature in self.features.values():
            # Count current phases
            if feature.tdd_phase:
                metrics["phase_summary"][feature.tdd_phase]["count"] += 1
            
            # Aggregate phase durations
            for phase, duration in feature.phase_durations.items():
                metrics["phase_summary"][phase]["total_duration"] += duration
            
            # Test metrics
            metrics["test_metrics"]["total_test_files"] += feature.test_file_count
            metrics["test_metrics"]["total_test_functions"] += feature.test_function_count
            metrics["test_metrics"]["total_fix_iterations"] += feature.test_fix_iterations
        
        # Calculate averages
        for phase in ["RED", "YELLOW", "GREEN"]:
            total_duration = metrics["phase_summary"][phase]["total_duration"]
            count = len([f for f in self.features.values() if phase in f.phase_durations])
            if count > 0:
                metrics["phase_summary"][phase]["avg_duration"] = total_duration / count
        
        # Average test execution time
        all_exec_times = []
        for feature in self.features.values():
            all_exec_times.extend(feature.test_execution_times)
        if all_exec_times:
            metrics["test_metrics"]["avg_test_execution_time"] = sum(all_exec_times) / len(all_exec_times)
        
        metrics["test_metrics"]["avg_coverage"] = self._calculate_average_coverage() or 0.0
        
        return metrics
    
    def print_test_progression(self):
        """Show how tests evolved from RED to GREEN"""
        if not self.features:
            return
            
        print("\n🧪 TEST PROGRESSION")
        print("="*60)
        
        for feature_id, feature in self.features.items():
            if not feature.tests_written:
                continue
                
            print(f"\n📋 {feature.feature_title}")
            
            # Show test creation
            if feature.test_file_count > 0:
                print(f"   📝 Tests created: {feature.test_file_count} files, {feature.test_function_count} functions")
            
            # Show failure progression
            if feature.test_failure_counts:
                print("   📊 Test failure progression:")
                for attempt, failures in sorted(feature.test_failure_counts.items()):
                    status = "✗" if failures > 0 else "✓"
                    print(f"      Attempt {attempt}: {status} {failures} failures")
            
            # Show final state
            if feature.tests_passing:
                coverage_str = f" (coverage: {feature.code_coverage:.1f}%)" if feature.code_coverage else ""
                print(f"   ✅ All tests passing{coverage_str}")
            else:
                print(f"   ❌ Tests still failing")
    
    def print_phase_progress_bars(self):
        """Print visual progress bars showing time spent in each TDD phase"""
        if not self.features:
            return
            
        print("\n📊 TDD PHASE DISTRIBUTION")
        print("="*60)
        
        # Collect all phase durations
        total_by_phase = {"RED": 0.0, "YELLOW": 0.0, "GREEN": 0.0}
        
        for feature in self.features.values():
            for phase, duration in feature.phase_durations.items():
                total_by_phase[phase] += duration
        
        total_time = sum(total_by_phase.values())
        if total_time == 0:
            print("No phase timing data available yet.")
            return
        
        # Print overall distribution
        print("\nOverall Time Distribution:")
        bar_width = 40
        for phase in ["RED", "YELLOW", "GREEN"]:
            duration = total_by_phase[phase]
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            filled = int(bar_width * percentage / 100)
            
            phase_icons = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}
            bar = "█" * filled + "░" * (bar_width - filled)
            mins = int(duration // 60)
            secs = int(duration % 60)
            
            print(f"{phase_icons[phase]} {phase:6} [{bar}] {percentage:5.1f}% ({mins}m {secs}s)")
        
        # Print per-feature breakdown
        print("\nPer-Feature Breakdown:")
        for feature_id, feature in self.features.items():
            if not feature.phase_durations:
                continue
                
            print(f"\n📋 {feature.feature_title}")
            feature_total = sum(feature.phase_durations.values())
            
            for phase in ["RED", "YELLOW", "GREEN"]:
                if phase not in feature.phase_durations:
                    continue
                    
                duration = feature.phase_durations[phase]
                percentage = (duration / feature_total * 100) if feature_total > 0 else 0
                filled = int(20 * percentage / 100)  # Smaller bars for features
                
                phase_icons = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}
                bar = "█" * filled + "░" * (20 - filled)
                mins = int(duration // 60)
                secs = int(duration % 60)
                
                print(f"   {phase_icons[phase]} [{bar}] {percentage:5.1f}% ({mins}m {secs}s)")