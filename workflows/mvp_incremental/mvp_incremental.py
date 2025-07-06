"""
MVP Incremental Workflow - Phase 6
Basic feature breakdown and sequential implementation with validation, retry logic, error analysis, and progress monitoring
"""
import re
from typing import List, Dict, Optional
from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus




def parse_simple_features(design_output: str) -> List[Dict[str, str]]:
    """
    Simple feature parsing - just extract numbered items or bullet points.
    Returns list of feature dictionaries with title and description.
    """
    features = []
    
    # Look for numbered features (1. 2. etc) or bullet points
    # Updated pattern to be more flexible
    pattern = r'(?:^|\n)\s*(?:\d+\.|-|\*|•)\s+([^\n]+(?:\n(?!\s*(?:\d+\.|-|\*|•))[^\n]+)*)'
    matches = re.findall(pattern, design_output, re.MULTILINE)
    
    if not matches:
        # Fallback: look for features in sections
        if "features" in design_output.lower() or "requirements" in design_output.lower():
            # Try to find feature-like content
            lines = design_output.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and len(line) < 200:
                    # Basic heuristic: non-empty lines of reasonable length
                    if any(keyword in line.lower() for keyword in ['add', 'create', 'implement', 'support', 'handle', 'method', 'function', 'class']):
                        features.append({
                            "id": f"feature_{len(features) + 1}",
                            "title": line[:100],
                            "description": line
                        })
        
        # If still no features, create one big feature
        if not features:
            features.append({
                "id": "feature_1",
                "title": "Complete Implementation",
                "description": design_output[:500] + "..."
            })
    else:
        for i, match in enumerate(matches, 1):
            # Clean up the match
            title = match.strip().split('\n')[0][:100]  # First line, max 100 chars
            features.append({
                "id": f"feature_{i}",
                "title": title,
                "description": match.strip()
            })
    
    return features


async def execute_mvp_incremental_workflow(
    input_data: CodingTeamInput,
    tracer: WorkflowExecutionTracer = None
) -> List[TeamMemberResult]:
    """
    Execute MVP incremental workflow.
    Planning → Design → Sequential Feature Implementation with Validation
    """
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    
    if not tracer:
        tracer = WorkflowExecutionTracer("mvp_incremental")
    
    # Phase 6: Initialize progress monitor
    progress_monitor = ProgressMonitor()
    
    results = []
    validator_session_id = None  # Track validator session
    
    # Step 1: Planning
    progress_monitor.start_phase("Planning")
    progress_monitor.start_step("planning", "planning")
    
    planning_step_id = tracer.start_step("planning", "planner_agent", {
        "requirements": input_data.requirements
    })
    
    planning_result = await run_team_member_with_tracking(
        "planner_agent",
        input_data.requirements,
        "mvp_incremental_planning"
    )
    
    # Extract content from response
    if isinstance(planning_result, list) and len(planning_result) > 0:
        planning_output = planning_result[0].parts[0].content
    else:
        planning_output = str(planning_result)
    
    planner_result = TeamMemberResult(
        team_member=TeamMember.planner,
        output=planning_output,
        name="planner"
    )
    results.append(planner_result)
    
    tracer.complete_step(planning_step_id, {
        "output_length": len(planner_result.output),
        "status": "completed"
    })
    
    progress_monitor.complete_step("planning", success=True)
    
    # Step 2: Design
    progress_monitor.start_phase("Design")
    progress_monitor.start_step("design", "design")
    
    design_step_id = tracer.start_step("design", "designer_agent", {
        "plan": planner_result.output
    })
    
    design_result = await run_team_member_with_tracking(
        "designer_agent",
        f"Based on this plan, create a detailed technical design with clear features:\n\n{planner_result.output}",
        "mvp_incremental_design"
    )
    
    # Extract content from response
    if isinstance(design_result, list) and len(design_result) > 0:
        design_output = design_result[0].parts[0].content
    else:
        design_output = str(design_result)
    
    designer_result = TeamMemberResult(
        team_member=TeamMember.designer,
        output=design_output,
        name="designer"
    )
    results.append(designer_result)
    
    tracer.complete_step(design_step_id, {
        "output_length": len(designer_result.output),
        "status": "completed"
    })
    
    progress_monitor.complete_step("design", success=True)
    
    # Step 3: Parse features from design
    print("\n🔍 Parsing features from design...")
    features = parse_simple_features(design_output)
    print(f"Found {len(features)} features to implement")
    
    # Phase 3: Order features by dependencies
    print("\n🔗 Analyzing feature dependencies...")
    from workflows.mvp_incremental.feature_dependency_parser import FeatureDependencyParser
    features = FeatureDependencyParser.order_features_smart(features, design_output)
    print("📊 Features ordered by dependencies")
    
    # Start the workflow with total feature count
    progress_monitor.start_workflow(total_features=len(features))
    
    # Step 4: Implement features sequentially
    progress_monitor.start_phase("Implementation")
    accumulated_code = {}  # Track all code files created
    retry_config = RetryConfig()  # Phase 4: Initialize retry configuration
    retry_strategy = RetryStrategy()  # Phase 5: Initialize retry strategy with error analyzer
    
    for i, feature in enumerate(features):
        # Phase 6: Start tracking feature progress
        progress_monitor.start_feature(feature['id'], feature['title'], i+1)
        
        # Phase 4: Retry loop for feature implementation
        retry_count = 0
        feature_implemented = False
        feature_validation_passed = False
        last_validation_error = None
        
        while not feature_implemented and retry_count <= retry_config.max_retries:
            feature_step_id = tracer.start_step(
                f"feature_{feature['id']}_attempt_{retry_count}",
                "coder_agent",
                {"feature": feature['title'], "retry_count": retry_count}
            )
        
            # Prepare context for coder
            if retry_count > 0 and last_validation_error:
                # We're retrying - use special retry prompt
                error_context = retry_strategy.extract_error_context(last_validation_error)
                coder_context = retry_strategy.create_retry_prompt(
                    "",  # original context not needed
                    feature,
                    last_validation_error,
                    error_context,
                    retry_count,
                    accumulated_code
                )
                print(f"   {RetryStrategy.get_backoff_message(retry_count, retry_config.max_retries)}")
                progress_monitor.update_step(f"feature_{feature['id']}", StepStatus.RETRYING)
            elif accumulated_code:
                # We have existing code - tell coder to modify/extend it
                coder_context = f"""
You are implementing a specific feature as part of an EXISTING project. DO NOT create a new project.

ORIGINAL REQUIREMENTS:
{input_data.requirements}

FEATURE TO IMPLEMENT: {feature['title']}
Description: {feature['description']}

EXISTING CODE THAT YOU MUST BUILD UPON:
{_format_existing_code(accumulated_code)}

CRITICAL INSTRUCTIONS:
1. DO NOT create a new project or use "PROJECT CREATED" format
2. MODIFY or EXTEND the existing files shown above
3. Only show the files you're changing or adding
4. Implement ONLY the specific feature requested
5. Preserve all existing functionality
6. Use the same code style and structure as the existing code

OUTPUT FORMAT:
For each file you modify or create, use this format:

```python
# filename: path/to/file.py
<file contents>
```
"""
            else:
                # First feature - create initial structure
                coder_context = f"""
You are implementing the FIRST feature of a new project.

ORIGINAL REQUIREMENTS:
{input_data.requirements}

FEATURE TO IMPLEMENT: {feature['title']}
Description: {feature['description']}

INSTRUCTIONS:
1. Create the initial project structure
2. Implement ONLY this specific feature
3. Create complete, runnable code
4. Include all necessary imports

OUTPUT FORMAT:
For each file you create, use this format:

```python
# filename: path/to/file.py
<file contents>
```
"""
        
            # Run feature coder agent (not regular coder)
            coder_result = await run_team_member_with_tracking(
                "feature_coder_agent",
                coder_context,
                f"mvp_incremental_feature_{i+1}_attempt_{retry_count}"
            )
        
            # Extract content from response
            if isinstance(coder_result, list) and len(coder_result) > 0:
                code_output = coder_result[0].parts[0].content
            else:
                code_output = str(coder_result)
            
            # Parse files from code output
            new_files = _parse_code_files(code_output)
            # For retries, we need to update the accumulated code, not just add
            if retry_count > 0:
                # On retry, replace the code completely with the new version
                accumulated_code.clear()
                accumulated_code.update(new_files)
            else:
                accumulated_code.update(new_files)
            
            # PHASE 2: Validate the feature implementation
            validation_passed = True
            validation_error = None
        
            if accumulated_code:  # Only validate if we have code
                validation_step_id = tracer.start_step(
                    f"validate_feature_{feature['id']}",
                    "validator_agent",
                    {"feature": feature['title']}
                )
                
                try:
                    # Prepare validation input with session ID if available
                    validation_input = f"""
{f'SESSION_ID: {validator_session_id}' if validator_session_id else ''}

Please validate this code implementation for feature: {feature['title']}

{_format_code_for_validator(accumulated_code)}
"""
                    
                    # Run validator agent
                    validation_result = await run_team_member_with_tracking(
                        "validator_agent",
                        validation_input,
                        f"mvp_incremental_validate_{i+1}"
                    )
                    
                    # Extract validation output
                    if isinstance(validation_result, list) and len(validation_result) > 0:
                        validation_output = validation_result[0].parts[0].content
                    else:
                        validation_output = str(validation_result)
                    
                    # Extract session ID if this is the first validation
                    if not validator_session_id and "SESSION_ID:" in validation_output:
                        session_line = [line for line in validation_output.split('\n') if 'SESSION_ID:' in line][0]
                        validator_session_id = session_line.split('SESSION_ID:')[1].strip()
                        print(f"   🔑 Validator session created: {validator_session_id}")
                    
                    # Check validation result
                    if "VALIDATION_RESULT: PASS" in validation_output:
                        validation_passed = True
                        progress_monitor.update_feature_validation(feature['id'], True)
                    elif "VALIDATION_RESULT: FAIL" in validation_output:
                        validation_passed = False
                        # Extract error details
                        if "DETAILS:" in validation_output:
                            validation_error = validation_output.split("DETAILS:")[1].strip()
                        progress_monitor.update_feature_validation(feature['id'], False, validation_error)
                    
                    tracer.complete_step(validation_step_id, {
                        "validation_passed": validation_passed,
                        "session_id": validator_session_id,
                        "status": "completed"
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Validation error: {str(e)}")
                    validation_passed = False  # Mark as failed so we can retry
                    validation_error = str(e)
                    tracer.complete_step(validation_step_id, {
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Phase 4: Check if we should retry
            if not validation_passed:
                last_validation_error = validation_output if 'validation_output' in locals() else str(validation_error)
                feature_validation_passed = False
                
                if retry_strategy.should_retry(validation_error, retry_count, retry_config):
                    retry_count += 1
                    tracer.complete_step(feature_step_id, {
                        "files_created": list(new_files.keys()),
                        "validation_passed": False,
                        "will_retry": True,
                        "retry_count": retry_count,
                        "status": "retry"
                    })
                    continue  # Retry the feature
                else:
                    # Max retries reached or non-retryable error
                    print(f"   ⚠️  Feature {i+1} failed validation - max retries reached or non-retryable error")
                    if validation_error:
                        print(f"      Final error: {validation_error}")
                    feature_implemented = True  # Move on to next feature
                    progress_monitor.update_step(f"feature_{feature['id']}", StepStatus.FAILED, validation_error)
            else:
                # Validation passed
                feature_validation_passed = True
                feature_implemented = True
                progress_monitor.update_step(f"feature_{feature['id']}", StepStatus.COMPLETED)
            
            # Record feature result with validation status
            feature_result = TeamMemberResult(
                team_member=TeamMember.coder,
                output=code_output,
                name=f"coder_feature_{i+1}",
                metadata={
                    "validation_passed": validation_passed,
                    "validation_error": validation_error,
                    "retry_count": retry_count,
                    "final_success": feature_validation_passed
                }
            )
            results.append(feature_result)
            
            tracer.complete_step(feature_step_id, {
                "files_created": list(new_files.keys()),
                "validation_passed": validation_passed,
                "retry_count": retry_count,
                "status": "completed"
            })
        
        # Complete feature tracking
        progress_monitor.complete_feature(feature['id'], feature_validation_passed)
        
        # Show progress bar periodically
        if (i + 1) % 2 == 0 or i == len(features) - 1:  # Every 2 features or at the end
            progress_monitor.print_progress_bar()
    
    # Create final consolidated result
    print("\n📦 Consolidating final implementation...")
    final_code = _consolidate_code(accumulated_code)
    
    # Count validation results - Phase 4: Include retry information
    validation_results = [r for r in results if hasattr(r, 'metadata') and r.metadata and 'validation_passed' in r.metadata]
    passed_validations = sum(1 for r in validation_results if r.metadata.get('final_success', r.metadata.get('validation_passed', False)))
    failed_validations = len(validation_results) - passed_validations
    retried_features = sum(1 for r in validation_results if r.metadata.get('retry_count', 0) > 0)
    
    final_result = TeamMemberResult(
        team_member=TeamMember.coder,
        output=final_code,
        name="final_implementation"
    )
    results.append(final_result)
    
    # Phase 6: End workflow and show summary
    progress_monitor.end_workflow()
    
    # Export metrics for potential further analysis
    metrics = progress_monitor.export_metrics()
    
    # Add metrics to the final result
    final_result.metadata = metrics
    
    # Cleanup validator container
    if validator_session_id:
        print(f"\n🧹 Cleaning up validator session: {validator_session_id}")
        try:
            from agents.validator.container_manager import get_container_manager
            container_manager = get_container_manager()
            container_manager.cleanup_container(validator_session_id)
        except Exception as e:
            print(f"   ⚠️  Cleanup error: {e}")
    
    print("=" * 60)
    
    return results


def _format_code_for_validator(code_dict: Dict[str, str]) -> str:
    """Format code for validator agent with proper file markers."""
    if not code_dict:
        return "No code to validate yet."
    
    formatted_parts = []
    for filename, content in code_dict.items():
        formatted_parts.append(f"""```python
# filename: {filename}
{content}
```""")
    
    return "\n\n".join(formatted_parts)


def _format_existing_code(code_dict: Dict[str, str]) -> str:
    """Format existing code for context."""
    if not code_dict:
        return "No existing code yet. This is the first feature."
    
    formatted = "The following files have been created so far:\n"
    for filename in sorted(code_dict.keys()):
        formatted += f"\n--- {filename} ---\n"
        # Show first 20 lines or 500 chars, whichever is shorter
        content = code_dict[filename]
        lines = content.split('\n')[:20]
        preview = '\n'.join(lines)
        if len(preview) > 500:
            preview = preview[:500] + "\n... (truncated)"
        formatted += preview + "\n"
    
    return formatted


def _parse_code_files(code_output: str) -> Dict[str, str]:
    """Extract files from coder output."""
    files = {}
    
    # First, check if this is the coder agent's structured output format
    if "--- IMPLEMENTATION DETAILS ---" in code_output:
        # Parse the structured format
        # Look for FILENAME: followed by code blocks
        file_pattern = r'FILENAME:\s*(\S+)\s*\n```(?:\w+)?\n(.*?)```'
        matches = re.findall(file_pattern, code_output, re.DOTALL)
        
        if matches:
            for filename, content in matches:
                files[filename] = content.strip()
            return files
    
    # Check for our new format: ```python\n# filename: path/to/file.py
    file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
    matches = re.findall(file_pattern, code_output, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            files[filename] = content.strip()
        return files
    
    # Fallback to original parsing for other formats
    # Look for file markers like ```python filename.py or just ```python
    file_pattern = r'```(?:python|py|javascript|js)\s*(?:# )?(\S+\.(?:py|js))?\n(.*?)```'
    matches = re.findall(file_pattern, code_output, re.DOTALL)
    
    if matches:
        for i, (filename, content) in enumerate(matches):
            if not filename:
                # Default filename if not specified
                filename = f"main.py" if i == 0 else f"module_{i}.py"
            files[filename] = content.strip()
    else:
        # Last fallback: treat entire output as main.py
        # But skip if it contains obvious non-code content
        if not any(marker in code_output for marker in ["✅ PROJECT CREATED", "📁 Location", "📄 Files created"]):
            files["main.py"] = code_output.strip()
    
    return files


def _consolidate_code(code_dict: Dict[str, str]) -> str:
    """Consolidate all code files into final output."""
    if not code_dict:
        return "# No code generated"
    
    output_parts = ["# Final Implementation\n"]
    
    for filename in sorted(code_dict.keys()):
        output_parts.append(f"\n## File: {filename}")
        output_parts.append("```python")
        output_parts.append(code_dict[filename])
        output_parts.append("```")
    
    return "\n".join(output_parts)


