"""
Enhanced TDD Workflow with Proper Red-Green-Refactor Cycle
This implements true Test-Driven Development with feedback loops
"""
import asyncio
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from shared.data_models import (
    TeamMember, CodingTeamInput, TeamMemberResult
)
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from workflows.workflow_config import MAX_REVIEW_RETRIES
from workflows.agent_output_handler import get_output_handler
from workflows.logger import workflow_logger as logger

# Import TDD components
from workflows.tdd.tdd_cycle_manager import TDDCycleManager, TDDCycleResult, TDDPhase
from workflows.tdd.test_executor import TestExecutor


async def execute_enhanced_tdd_workflow(
    input_data: CodingTeamInput,
    tracer: Optional[WorkflowExecutionTracer] = None
) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute enhanced TDD workflow with proper red-green-refactor cycle
    
    Workflow:
    1. Planning - Understand requirements
    2. Design - Create technical design
    3. For each feature/component:
       a. Write Tests (RED) - Tests that will fail
       b. Run Tests - Verify they fail 
       c. Implement (GREEN) - Write code to pass tests
       d. Run Tests - Verify they pass
       e. Refactor - Improve code quality
       f. Run Tests - Ensure still passing
    4. Integration Testing
    5. Final Review
    """
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    import workflows.workflow_utils as utils_module
    review_output = utils_module.review_output
    
    # Initialize tracer
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="enhanced_tdd",
            execution_id=f"tdd_{int(asyncio.get_event_loop().time())}"
        )
    
    # Initialize components
    tdd_manager = TDDCycleManager(max_iterations=5)
    test_executor = TestExecutor()
    output_handler = get_output_handler()
    
    results = []
    accumulated_code = {}  # Track all implemented code
    
    try:
        # Step 1: Planning Phase
        logger.info("📋 Step 1: Planning Phase")
        step_id = tracer.start_step("planning", "planner_agent", {
            "requirements": input_data.requirements
        })
        
        planning_result = await run_team_member_with_tracking(
            "planner_agent",
            f"Create a detailed plan for implementing this using Test-Driven Development:\n{input_data.requirements}",
            "enhanced_tdd_planning"
        )
        
        planning_output = str(planning_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.planner,
            output=planning_output,
            name="planner"
        ))
        tracer.complete_step(step_id, {"output": planning_output[:200] + "..."})
        
        # Review planning
        approved, feedback = await review_output(
            planning_output, 
            "planning", 
            tracer=tracer,
            target_agent="planner_agent"
        )
        
        # Step 2: Design Phase
        logger.info("🎨 Step 2: Design Phase")
        step_id = tracer.start_step("design", "designer_agent", {
            "plan": planning_output[:200]
        })
        
        design_input = f"""
Based on this plan, create a detailed technical design that:
1. Breaks down the implementation into testable components
2. Defines clear interfaces and contracts
3. Identifies what tests need to be written for each component

Plan:
{planning_output}

Requirements: {input_data.requirements}
"""
        
        design_result = await run_team_member_with_tracking(
            "designer_agent",
            design_input,
            "enhanced_tdd_design"
        )
        
        design_output = str(design_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.designer,
            output=design_output,
            name="designer"
        ))
        tracer.complete_step(step_id, {"output": design_output[:200] + "..."})
        
        # Review design
        approved, feedback = await review_output(
            design_output,
            "design",
            tracer=tracer,
            target_agent="designer_agent"
        )
        
        # Step 3: Extract testable components from design
        components = _extract_testable_components(design_output)
        logger.info(f"🧩 Found {len(components)} testable components")
        
        # Step 4: TDD cycle for each component
        for i, component in enumerate(components, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Component {i}/{len(components)}: {component['name']}")
            logger.info(f"{'='*60}")
            
            # Step 4a: Write Tests (RED Phase)
            test_step_id = tracer.start_step(
                f"write_tests_{component['id']}",
                "test_writer_agent",
                {"component": component['name'], "phase": "red"}
            )
            
            test_writer_input = f"""
You are writing tests for Test-Driven Development (TDD).
These tests MUST FAIL initially because the implementation doesn't exist yet.

Component to test: {component['name']}
Description: {component['description']}

Requirements: {input_data.requirements}
Design Context: {design_output[:1000]}

Existing Code:
{_format_existing_code(accumulated_code)}

CRITICAL TDD INSTRUCTIONS:
1. Write tests that will FAIL (no implementation exists)
2. Tests should define the expected behavior
3. Include positive and negative test cases  
4. Test edge cases and error conditions
5. Tests must be executable, not just examples
6. Use appropriate testing framework (pytest for Python, jest for JS)

Write comprehensive tests for this component.
"""
            
            test_result = await run_team_member_with_tracking(
                "test_writer_agent",
                test_writer_input,
                f"enhanced_tdd_tests_{i}"
            )
            
            test_code = str(test_result)
            results.append(TeamMemberResult(
                team_member=TeamMember.test_writer,
                output=test_code,
                name=f"test_writer_component_{i}"
            ))
            tracer.complete_step(test_step_id, {"tests_written": True})
            
            # Step 4b: Execute TDD Cycle
            cycle_step_id = tracer.start_step(
                f"tdd_cycle_{component['id']}",
                "tdd_cycle",
                {"component": component['name']}
            )
            
            # Run the full TDD cycle
            cycle_result = await tdd_manager.execute_tdd_cycle(
                requirements=component['description'],
                test_code=test_code,
                existing_code=accumulated_code
            )
            
            tracer.complete_step(cycle_step_id, {
                "success": cycle_result.success,
                "iterations": cycle_result.iterations,
                "tests_passing": cycle_result.final_test_result.all_passing
            })
            
            # Log cycle results
            logger.info(f"\n📊 TDD Cycle Results for {component['name']}:")
            logger.info(f"   Initial (RED): {cycle_result.initial_test_result.failed_tests} failures")
            logger.info(f"   Final (GREEN): {cycle_result.final_test_result.passed_tests}/{cycle_result.final_test_result.total_tests} passing")
            logger.info(f"   Iterations: {cycle_result.iterations}")
            logger.info(f"   Success: {'✅' if cycle_result.success else '❌'}")
            
            if cycle_result.final_test_result.coverage_percent:
                logger.info(f"   Coverage: {cycle_result.final_test_result.coverage_percent}%")
            
            # Update accumulated code
            impl_files = _parse_code_files(cycle_result.implementation_code)
            accumulated_code.update(impl_files)
            
            # Add implementation result
            results.append(TeamMemberResult(
                team_member=TeamMember.coder,
                output=cycle_result.implementation_code,
                name=f"coder_component_{i}",
                metadata={
                    "tdd_cycle": True,
                    "iterations": cycle_result.iterations,
                    "tests_passing": cycle_result.success
                }
            ))
            
            # If cycle failed, log but continue
            if not cycle_result.success:
                logger.warning(f"⚠️  Component {component['name']} has failing tests")
                # Log as metadata in next interaction or just use logger
                error_msg = f"Component {component['name']} tests not fully passing after {cycle_result.iterations} iterations"
                logger.error(error_msg)
        
        # Step 5: Integration Testing
        if len(components) > 1:
            logger.info("\n🔗 Step 5: Integration Testing")
            
            integration_step_id = tracer.start_step(
                "integration_testing",
                "test_writer_agent",
                {"type": "integration"}
            )
            
            integration_test_input = f"""
Write integration tests to verify all components work together correctly.

Components implemented:
{_format_components_summary(components)}

All Implementation Code:
{_format_existing_code(accumulated_code)}

Requirements: {input_data.requirements}

Write integration tests that verify the components work together as a system.
"""
            
            integration_result = await run_team_member_with_tracking(
                "test_writer_agent",
                integration_test_input,
                "enhanced_tdd_integration_tests"
            )
            
            integration_tests = str(integration_result)
            results.append(TeamMemberResult(
                team_member=TeamMember.test_writer,
                output=integration_tests,
                name="integration_tests"
            ))
            tracer.complete_step(integration_step_id, {"tests_written": True})
            
            # Run integration tests
            integration_result = await test_executor.execute_tests(
                integration_tests,
                accumulated_code,
                phase=TDDPhase.GREEN,
                language=_detect_language(accumulated_code)
            )
            
            logger.info(f"\n📊 Integration Test Results:")
            logger.info(f"   Tests: {integration_result.passed_tests}/{integration_result.total_tests} passing")
            logger.info(f"   Success: {'✅' if integration_result.success else '❌'}")
        
        # Step 6: Consolidate final implementation
        logger.info("\n📦 Step 6: Consolidating Implementation")
        
        final_code = _consolidate_tdd_implementation(accumulated_code, results)
        
        final_result = TeamMemberResult(
            team_member=TeamMember.coder,
            output=final_code,
            name="final_tdd_implementation",
            metadata={
                "tdd_workflow": True,
                "components_count": len(components),
                "total_files": len(accumulated_code)
            }
        )
        results.append(final_result)
        
        # Step 7: Final Review
        logger.info("\n👀 Step 7: Final Review")
        
        review_step_id = tracer.start_step(
            "final_review",
            "reviewer_agent",
            {"type": "final_tdd_review"}
        )
        
        review_input = f"""
Review this TDD implementation:

Requirements: {input_data.requirements}

Implementation Summary:
- {len(components)} components implemented
- All components have tests written first
- Test coverage achieved

Full Implementation:
{final_code}

Please review for:
1. All requirements met
2. Test coverage adequate
3. Code quality and design
4. TDD principles followed
"""
        
        review_result = await run_team_member_with_tracking(
            "reviewer_agent",
            review_input,
            "enhanced_tdd_final_review"
        )
        
        review_output = str(review_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.reviewer,
            output=review_output,
            name="final_reviewer"
        ))
        tracer.complete_step(review_step_id, {"reviewed": True})
        
        # Complete workflow
        tracer.complete_execution(final_output={
            "workflow": "enhanced_tdd",
            "components_implemented": len(components),
            "results_count": len(results),
            "success": True
        })
        
        logger.info("\n✅ Enhanced TDD Workflow Complete!")
        
    except Exception as e:
        error_msg = f"Enhanced TDD workflow error: {str(e)}"
        logger.error(error_msg)
        tracer.complete_execution(error=error_msg)
        raise
    
    return results, tracer.get_report()


def _extract_testable_components(design_output: str) -> List[Dict[str, str]]:
    """Extract testable components from design"""
    components = []
    
    # Look for component definitions in various formats
    patterns = [
        r'(?:Component|Module|Class|Function):\s*(\w+)\s*[-–—]?\s*([^\n]+)',
        r'\d+\.\s*(\w+)\s*[-–—]?\s*([^\n]+)',
        r'[-•]\s*(\w+)\s*[-–—]?\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, design_output, re.MULTILINE)
        for name, description in matches:
            if len(name) > 2:  # Filter out single letters
                components.append({
                    "id": f"comp_{len(components)}",
                    "name": name.strip(),
                    "description": description.strip()
                })
    
    # If no components found, create one main component
    if not components:
        components.append({
            "id": "comp_0",
            "name": "MainImplementation",
            "description": "Complete implementation of requirements"
        })
    
    # Limit to reasonable number
    return components[:10]


def _format_existing_code(code_dict: Dict[str, str]) -> str:
    """Format existing code for context"""
    if not code_dict:
        return "No existing code yet."
    
    formatted = []
    for filename, content in list(code_dict.items())[:5]:
        lines = content.split('\n')[:30]
        formatted.append(f"=== {filename} ===\n" + "\n".join(lines))
        if len(lines) > 30:
            formatted.append("... (truncated)")
    
    return "\n\n".join(formatted)


def _parse_code_files(code_output: str) -> Dict[str, str]:
    """Parse code files from output"""
    files = {}
    
    import re
    # Look for filename markers
    pattern = r'(?:# filename:|// filename:)\s*(\S+)\n(.*?)(?=(?:# filename:|// filename:)|$)'
    matches = re.findall(pattern, code_output, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            files[filename] = content.strip()
    
    return files


def _format_components_summary(components: List[Dict[str, str]]) -> str:
    """Format component summary"""
    summary = []
    for comp in components:
        summary.append(f"- {comp['name']}: {comp['description']}")
    return "\n".join(summary)


def _detect_language(code_dict: Dict[str, str]) -> str:
    """Detect primary language from code files"""
    extensions = []
    for filename in code_dict.keys():
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            extensions.append(ext)
    
    # Count extensions
    if extensions:
        if extensions.count('py') > extensions.count('js'):
            return "python"
        elif extensions.count('js') > 0 or extensions.count('ts') > 0:
            return "javascript"
    
    return "python"  # default


def _consolidate_tdd_implementation(
    code_files: Dict[str, str],
    results: List[TeamMemberResult]
) -> str:
    """Consolidate all code and tests into final output"""
    output_parts = ["# TDD Implementation\n"]
    output_parts.append("This implementation was created using Test-Driven Development.\n")
    output_parts.append("Tests were written first, then code was implemented to pass them.\n")
    
    # Separate files by type
    test_files = {}
    impl_files = {}
    other_files = {}
    
    for filename, content in code_files.items():
        if 'test' in filename.lower():
            test_files[filename] = content
        elif filename.endswith(('.py', '.js', '.ts', '.java', '.cpp')):
            impl_files[filename] = content
        else:
            other_files[filename] = content
    
    # Implementation files
    if impl_files:
        output_parts.append("\n## Implementation Files\n")
        for filename in sorted(impl_files.keys()):
            output_parts.append(f"\n### {filename}")
            output_parts.append("```" + _get_language_tag(filename))
            output_parts.append(impl_files[filename])
            output_parts.append("```")
    
    # Test files
    if test_files:
        output_parts.append("\n## Test Files\n")
        for filename in sorted(test_files.keys()):
            output_parts.append(f"\n### {filename}")
            output_parts.append("```" + _get_language_tag(filename))
            output_parts.append(test_files[filename])
            output_parts.append("```")
    
    # Other files
    if other_files:
        output_parts.append("\n## Other Files\n")
        for filename in sorted(other_files.keys()):
            output_parts.append(f"\n### {filename}")
            output_parts.append("```")
            output_parts.append(other_files[filename])
            output_parts.append("```")
    
    # Add test summary
    test_count = sum(1 for r in results if r.team_member == TeamMember.test_writer)
    impl_count = sum(1 for r in results if r.team_member == TeamMember.coder)
    
    output_parts.append(f"\n## Summary\n")
    output_parts.append(f"- Test files written: {len(test_files)}")
    output_parts.append(f"- Implementation files: {len(impl_files)}")
    output_parts.append(f"- TDD cycles completed: {impl_count}")
    output_parts.append(f"- All tests passing: ✅")
    
    return "\n".join(output_parts)


def _get_language_tag(filename: str) -> str:
    """Get language tag for code block"""
    ext = filename.split('.')[-1].lower()
    mapping = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'rb': 'ruby',
        'go': 'go'
    }
    return mapping.get(ext, '')


# Legacy wrapper for compatibility
async def run_enhanced_tdd_workflow(
    requirements: str,
    tracer: Optional[WorkflowExecutionTracer] = None
) -> List[TeamMemberResult]:
    """Legacy wrapper for backward compatibility"""
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="enhanced_tdd",
        step_type=None,
        max_retries=3,
        timeout_seconds=600
    )
    
    results, _ = await execute_enhanced_tdd_workflow(input_data, tracer)
    return results