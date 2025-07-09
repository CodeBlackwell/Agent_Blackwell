"""
Parallel Feature Processor for MVP Incremental Workflow

Enables concurrent processing of independent features to improve performance,
while respecting dependencies and maintaining correct execution order.
"""

import asyncio
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging
from datetime import datetime

from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, TDDFeatureResult
from workflows.logger import workflow_logger as logger


@dataclass
class FeatureDependency:
    """Represents dependencies between features."""
    feature_id: str
    depends_on: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    @property
    def is_independent(self) -> bool:
        """Check if feature has no dependencies."""
        return len(self.depends_on) == 0


@dataclass
class ProcessingMetrics:
    """Metrics for parallel processing performance."""
    total_features: int = 0
    parallel_batches: int = 0
    max_concurrency: int = 0
    total_duration_seconds: float = 0.0
    average_feature_time: float = 0.0
    speedup_factor: float = 1.0  # Compared to sequential processing
    
    def calculate_speedup(self, sequential_time: float):
        """Calculate speedup compared to sequential processing."""
        if sequential_time > 0:
            self.speedup_factor = sequential_time / self.total_duration_seconds


class ParallelFeatureProcessor:
    """
    Processes features in parallel while respecting dependencies.
    """
    
    def __init__(self,
                 max_workers: int = 3,
                 batch_timeout: int = 300):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum concurrent feature implementations
            batch_timeout: Timeout for each batch of features (seconds)
        """
        self.max_workers = max_workers
        self.batch_timeout = batch_timeout
        self.semaphore = asyncio.Semaphore(max_workers)
        self.completed_features: Set[str] = set()
        self.failed_features: Set[str] = set()
        self.feature_results: Dict[str, TDDFeatureResult] = {}
        self.metrics = ProcessingMetrics()
        
    def analyze_dependencies(self, features: List[Dict[str, Any]]) -> Dict[str, FeatureDependency]:
        """
        Analyze feature dependencies to determine processing order.
        
        Args:
            features: List of feature dictionaries
            
        Returns:
            Dictionary mapping feature_id to dependency information
        """
        dependencies = {}
        
        for feature in features:
            feature_id = feature['id']
            deps = FeatureDependency(feature_id)
            
            # Extract dependencies from feature metadata
            if 'depends_on' in feature:
                deps.depends_on = set(feature['depends_on'])
            elif 'dependencies' in feature:
                deps.depends_on = set(feature['dependencies'])
            
            # Check for implicit dependencies in description
            description = feature.get('description', '')
            for other_feature in features:
                if other_feature['id'] != feature_id:
                    # Check if this feature references another
                    if other_feature['id'] in description or other_feature['title'] in description:
                        deps.depends_on.add(other_feature['id'])
            
            dependencies[feature_id] = deps
        
        # Build reverse dependencies (dependents)
        for feature_id, deps in dependencies.items():
            for dep_id in deps.depends_on:
                if dep_id in dependencies:
                    dependencies[dep_id].dependents.add(feature_id)
        
        return dependencies
    
    def get_processable_features(self,
                               features: List[Dict[str, Any]],
                               dependencies: Dict[str, FeatureDependency]) -> List[Dict[str, Any]]:
        """
        Get features that can be processed in the current batch.
        
        Args:
            features: All features
            dependencies: Dependency information
            
        Returns:
            List of features ready to process
        """
        processable = []
        
        for feature in features:
            feature_id = feature['id']
            
            # Skip if already processed or failed
            if feature_id in self.completed_features or feature_id in self.failed_features:
                continue
            
            # Check if all dependencies are satisfied
            deps = dependencies.get(feature_id)
            if deps and all(dep_id in self.completed_features for dep_id in deps.depends_on):
                processable.append(feature)
            elif deps and deps.is_independent:
                processable.append(feature)
        
        return processable
    
    async def process_feature_with_semaphore(self,
                                           feature: Dict[str, Any],
                                           feature_index: int,
                                           implementer: TDDFeatureImplementer,
                                           existing_code: Dict[str, str],
                                           requirements: str,
                                           design_output: str) -> Tuple[str, TDDFeatureResult]:
        """
        Process a single feature with semaphore control.
        
        Returns:
            Tuple of (feature_id, result)
        """
        async with self.semaphore:
            feature_id = feature['id']
            logger.info(f"🚀 Starting parallel processing of {feature['title']}")
            
            try:
                # Get accumulated code from completed features
                accumulated_code = existing_code.copy()
                for completed_id in self.completed_features:
                    if completed_id in self.feature_results:
                        result = self.feature_results[completed_id]
                        # Parse and add implementation code
                        code_files = implementer._parse_code_files(result.implementation_code)
                        accumulated_code.update(code_files)
                
                # Process the feature
                result = await implementer.implement_feature_tdd(
                    feature=feature,
                    existing_code=accumulated_code,
                    requirements=requirements,
                    design_output=design_output,
                    feature_index=feature_index
                )
                
                if result.success:
                    logger.info(f"✅ Completed parallel processing of {feature['title']}")
                else:
                    logger.warning(f"⚠️ Failed parallel processing of {feature['title']}")
                
                return feature_id, result
                
            except Exception as e:
                logger.error(f"Error processing feature {feature_id}: {e}")
                # Create a failed result
                result = TDDFeatureResult(
                    feature_id=feature_id,
                    feature_title=feature['title'],
                    test_code="",
                    implementation_code="",
                    initial_test_result=None,
                    final_test_result=None,
                    success=False
                )
                return feature_id, result
    
    async def process_features_parallel(self,
                                      features: List[Dict[str, Any]],
                                      implementer: TDDFeatureImplementer,
                                      existing_code: Dict[str, str],
                                      requirements: str,
                                      design_output: str) -> List[TDDFeatureResult]:
        """
        Process features in parallel batches respecting dependencies.
        
        Args:
            features: List of features to implement
            implementer: TDD feature implementer instance
            existing_code: Base code to build upon
            requirements: Project requirements
            design_output: Design phase output
            
        Returns:
            List of feature results in original order
        """
        start_time = datetime.now()
        self.metrics.total_features = len(features)
        
        # Analyze dependencies
        dependencies = self.analyze_dependencies(features)
        
        # Create feature index mapping
        feature_index_map = {f['id']: i for i, f in enumerate(features)}
        
        results = []
        batch_num = 0
        
        while len(self.completed_features) + len(self.failed_features) < len(features):
            batch_num += 1
            
            # Get features ready for processing
            processable = self.get_processable_features(features, dependencies)
            
            if not processable:
                # Check for circular dependencies
                remaining = set(f['id'] for f in features) - self.completed_features - self.failed_features
                logger.error(f"No processable features found. Remaining: {remaining}")
                break
            
            logger.info(f"📦 Processing batch {batch_num} with {len(processable)} features")
            self.metrics.parallel_batches = batch_num
            self.metrics.max_concurrency = max(self.metrics.max_concurrency, len(processable))
            
            # Process batch in parallel
            tasks = []
            for feature in processable:
                feature_index = feature_index_map[feature['id']]
                task = self.process_feature_with_semaphore(
                    feature=feature,
                    feature_index=feature_index,
                    implementer=implementer,
                    existing_code=existing_code,
                    requirements=requirements,
                    design_output=design_output
                )
                tasks.append(task)
            
            # Wait for batch completion with timeout
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=self.batch_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Batch {batch_num} timed out after {self.batch_timeout}s")
                # Mark timed out features as failed
                for feature in processable:
                    if feature['id'] not in self.completed_features:
                        self.failed_features.add(feature['id'])
                continue
            
            # Process results
            for feature_id, result in batch_results:
                self.feature_results[feature_id] = result
                if result.success:
                    self.completed_features.add(feature_id)
                else:
                    self.failed_features.add(feature_id)
                results.append(result)
        
        # Calculate metrics
        end_time = datetime.now()
        self.metrics.total_duration_seconds = (end_time - start_time).total_seconds()
        if self.metrics.total_features > 0:
            self.metrics.average_feature_time = self.metrics.total_duration_seconds / self.metrics.total_features
        
        # Sort results by original feature order
        sorted_results = []
        for feature in features:
            if feature['id'] in self.feature_results:
                sorted_results.append(self.feature_results[feature['id']])
        
        logger.info(f"🏁 Parallel processing complete: {len(self.completed_features)} succeeded, {len(self.failed_features)} failed")
        logger.info(f"   Total time: {self.metrics.total_duration_seconds:.1f}s")
        logger.info(f"   Batches: {self.metrics.parallel_batches}")
        logger.info(f"   Max concurrency: {self.metrics.max_concurrency}")
        
        return sorted_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        return {
            "total_features": self.metrics.total_features,
            "completed_features": len(self.completed_features),
            "failed_features": len(self.failed_features),
            "parallel_batches": self.metrics.parallel_batches,
            "max_concurrency": self.metrics.max_concurrency,
            "total_duration_seconds": self.metrics.total_duration_seconds,
            "average_feature_time": self.metrics.average_feature_time,
            "speedup_factor": self.metrics.speedup_factor
        }


def should_use_parallel_processing(features: List[Dict[str, Any]], 
                                 min_features: int = 3,
                                 max_dependencies_ratio: float = 0.3) -> bool:
    """
    Determine if parallel processing would be beneficial.
    
    Args:
        features: List of features
        min_features: Minimum features needed for parallel processing
        max_dependencies_ratio: Maximum ratio of dependencies to features
        
    Returns:
        True if parallel processing is recommended
    """
    if len(features) < min_features:
        return False
    
    # Count total dependencies
    total_deps = 0
    for feature in features:
        deps = feature.get('depends_on', []) or feature.get('dependencies', [])
        total_deps += len(deps)
    
    # Check dependency ratio
    dep_ratio = total_deps / len(features) if features else 0
    
    return dep_ratio <= max_dependencies_ratio