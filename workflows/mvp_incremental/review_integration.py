"""Review integration module for the MVP incremental workflow.

This module coordinates review checkpoints throughout the workflow,
ensuring quality at each phase while managing the retry strategy.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from acp_sdk import Message
from acp_sdk.models import MessagePart


class ReviewPhase(Enum):
    """Phases where review can occur."""
    PLANNING = "planning"
    DESIGN = "design"
    TEST_SPECIFICATION = "test_specification"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    VALIDATION_RESULT = "validation_result"
    FINAL_IMPLEMENTATION = "final_implementation"


@dataclass
class ReviewRequest:
    """Request for review at a specific phase."""
    phase: ReviewPhase
    content: str
    context: Dict[str, any]
    feature_id: Optional[str] = None
    retry_count: int = 0
    previous_feedback: Optional[str] = None


@dataclass
class ReviewResult:
    """Result from a review."""
    approved: bool
    feedback: str
    suggestions: List[str]
    must_fix: List[str]
    phase: ReviewPhase
    feature_id: Optional[str] = None


class ReviewIntegration:
    """Manages review integration within the MVP incremental workflow."""
    
    def __init__(self, feature_reviewer_agent):
        """Initialize with the feature reviewer agent function."""
        self.feature_reviewer_agent = feature_reviewer_agent
        self.review_history: Dict[str, List[ReviewResult]] = {}
        self.approval_cache: Dict[str, bool] = {}
        
    async def request_review(self, request: ReviewRequest) -> ReviewResult:
        """Request a review for a specific phase and content."""
        # Build review context
        review_prompt = self._build_review_prompt(request)
        
        # Call the feature reviewer agent
        messages = [Message(parts=[MessagePart(
            content=review_prompt,
            content_type="text/plain"
        )])]
        
        # Collect response
        response_parts = []
        async for part in self.feature_reviewer_agent(messages):
            response_parts.append(part.content)
        
        response = ''.join(response_parts)
        
        # Parse review result
        result = self._parse_review_response(response, request.phase, request.feature_id)
        
        # Store in history
        key = f"{request.phase.value}_{request.feature_id or 'global'}"
        if key not in self.review_history:
            self.review_history[key] = []
        self.review_history[key].append(result)
        
        # Cache approval status
        self.approval_cache[key] = result.approved
        
        return result
    
    def _build_review_prompt(self, request: ReviewRequest) -> str:
        """Build a review prompt based on the phase and content."""
        prompts = {
            ReviewPhase.PLANNING: self._build_planning_review_prompt,
            ReviewPhase.DESIGN: self._build_design_review_prompt,
            ReviewPhase.TEST_SPECIFICATION: self._build_test_specification_review_prompt,
            ReviewPhase.FEATURE_IMPLEMENTATION: self._build_feature_review_prompt,
            ReviewPhase.VALIDATION_RESULT: self._build_validation_review_prompt,
            ReviewPhase.FINAL_IMPLEMENTATION: self._build_final_review_prompt,
        }
        
        builder = prompts.get(request.phase)
        if not builder:
            raise ValueError(f"Unknown review phase: {request.phase}")
            
        return builder(request)
    
    def _build_planning_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing the planning phase."""
        prompt = f"""Review this incremental development plan:

{request.content}

Context:
- This is an MVP incremental workflow
- Features will be implemented one at a time
- Each feature will be validated independently

Please review for:
1. Are the features properly broken down?
2. Are dependencies clearly identified?
3. Is the implementation order logical?
4. Are there any missing features based on the requirements?

Provide your review in the format:
REVIEW: APPROVED or NEEDS REVISION
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Suggestion 1
- Suggestion 2
MUST FIX:
- Critical issue 1 (if any)
"""
        
        if request.retry_count > 0:
            prompt += f"\n\nThis is retry attempt {request.retry_count}."
            if request.previous_feedback:
                prompt += f"\nPrevious feedback: {request.previous_feedback}"
                
        return prompt
    
    def _build_design_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing the design phase."""
        prompt = f"""Review this incremental design approach:

{request.content}

Context:
- This design will guide feature-by-feature implementation
- Each feature should be independently testable
- The design should support the planned implementation order

Please review for:
1. Does the design support incremental implementation?
2. Are interfaces between features well-defined?
3. Will this design allow for independent feature validation?
4. Are there any architectural concerns?

Provide your review in the format:
REVIEW: APPROVED or NEEDS REVISION
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Suggestion 1
- Suggestion 2
MUST FIX:
- Critical issue 1 (if any)
"""
        
        if request.retry_count > 0:
            prompt += f"\n\nThis is retry attempt {request.retry_count}."
            if request.previous_feedback:
                prompt += f"\nPrevious feedback: {request.previous_feedback}"
                
        return prompt
    
    def _build_test_specification_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing TDD test specifications."""
        feature = request.context.get('feature', {})
        
        prompt = f"""Review this test specification for Test-Driven Development:

Feature: {feature.get('title', 'Unknown')}
Description: {feature.get('description', 'No description')}

Test Code:
{request.content}

Context:
- These tests are written BEFORE implementation (TDD Red Phase)
- Tests should define the expected behavior clearly
- Tests must fail initially since no implementation exists yet
- {request.context.get('purpose', 'Ensure comprehensive test coverage')}

Please review for:
1. Do the tests clearly define expected behavior?
2. Are both positive and negative test cases included?
3. Are edge cases and error conditions covered?
4. Will these tests effectively guide the implementation?
5. Are the test names descriptive and clear?

Provide your review in the format:
REVIEW: APPROVED or NEEDS REVISION
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Suggestion 1
- Suggestion 2
MUST FIX:
- Critical issue 1 (if any)
"""
        
        if request.retry_count > 0:
            prompt += f"\n\nThis is retry attempt {request.retry_count}."
            if request.previous_feedback:
                prompt += f"\nPrevious feedback: {request.previous_feedback}"
                
        return prompt
    
    def _build_feature_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing a feature implementation."""
        feature_context = request.context.get('feature_info', {})
        existing_code = request.context.get('existing_code', '')
        dependencies = request.context.get('dependencies', [])
        
        prompt = f"""Review this feature implementation:

Feature: {feature_context.get('name', 'Unknown')}
Description: {feature_context.get('description', 'No description')}

Implementation:
{request.content}

Existing Code Context:
{existing_code if existing_code else 'No existing code yet'}

Dependencies: {', '.join(dependencies) if dependencies else 'None'}

Please review for:
1. Does the implementation meet the feature requirements?
2. Does it integrate well with existing code?
3. Are all edge cases handled?
4. Is error handling appropriate?
5. Does it follow the established patterns?

Provide your review in the format:
REVIEW: FEATURE APPROVED or NEEDS REVISION
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Suggestion 1
- Suggestion 2
MUST FIX:
- Critical issue 1 (if any)
"""
        
        if request.retry_count > 0:
            prompt += f"\n\nThis is retry attempt {request.retry_count}."
            if request.previous_feedback:
                prompt += f"\nPrevious feedback: {request.previous_feedback}"
                
        return prompt
    
    def _build_validation_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing validation results."""
        validation_result = request.context.get('validation_result', {})
        error_info = request.context.get('error_info', '')
        
        prompt = f"""Review this validation result and determine if retry is warranted:

Feature: {request.feature_id}
Validation Status: {'PASSED' if validation_result.get('success') else 'FAILED'}

{request.content}

{f'Error Details: {error_info}' if error_info else ''}

Context:
- Retry count: {request.retry_count}
- Maximum retries: {request.context.get('max_retries', 3)}

Please review and determine:
1. If validation failed, is the error retryable?
2. What specific changes would fix the issue?
3. Should we retry or accept the current state?

Provide your review in the format:
REVIEW: RETRY RECOMMENDED or ACCEPT CURRENT STATE
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Specific fix 1
- Specific fix 2
MUST FIX:
- Critical issue that prevents retry (if any)
"""
        
        return prompt
    
    def _build_final_review_prompt(self, request: ReviewRequest) -> str:
        """Build prompt for reviewing the final implementation."""
        feature_summary = request.context.get('feature_summary', {})
        
        prompt = f"""Review this final implementation:

{request.content}

Implementation Summary:
- Total features: {feature_summary.get('total', 0)}
- Successful features: {feature_summary.get('successful', 0)}
- Features with retries: {feature_summary.get('retried', 0)}
- Failed features: {feature_summary.get('failed', 0)}

Please provide a final review:
1. Does the implementation meet all requirements?
2. Is the code production-ready?
3. Are there any remaining issues?
4. Overall quality assessment

Provide your review in the format:
REVIEW: APPROVED or NEEDS REVISION
FEEDBACK: Your detailed feedback
SUGGESTIONS: 
- Future improvement 1
- Future improvement 2
MUST FIX:
- Critical issue 1 (if any)
"""
        
        return prompt
    
    def _parse_review_response(self, response: str, phase: ReviewPhase, feature_id: Optional[str]) -> ReviewResult:
        """Parse the review response into a structured result."""
        # Default values
        approved = False
        feedback = ""
        suggestions = []
        must_fix = []
        
        # Parse approval status
        response_upper = response.upper()
        if "APPROVED" in response_upper or "FEATURE APPROVED" in response_upper:
            approved = True
        elif "RETRY RECOMMENDED" in response_upper:
            approved = False  # For validation reviews, retry means not approved yet
        
        # Extract sections
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if line.startswith("FEEDBACK:"):
                current_section = "feedback"
                feedback = line[9:].strip()
            elif line.startswith("SUGGESTIONS:"):
                current_section = "suggestions"
            elif line.startswith("MUST FIX:"):
                current_section = "must_fix"
            elif current_section == "feedback" and not line.startswith('-'):
                feedback += " " + line
            elif current_section == "suggestions" and line.startswith('-'):
                suggestions.append(line[1:].strip())
            elif current_section == "must_fix" and line.startswith('-'):
                must_fix.append(line[1:].strip())
        
        return ReviewResult(
            approved=approved,
            feedback=feedback.strip(),
            suggestions=suggestions,
            must_fix=must_fix,
            phase=phase,
            feature_id=feature_id
        )
    
    def should_retry_feature(self, feature_id: str, validation_result: Dict) -> Tuple[bool, Optional[str]]:
        """Determine if a feature should be retried based on validation and review."""
        # Quick check if validation passed
        if validation_result.get('success', False):
            return False, None
            
        # Get review history for this validation
        key = f"{ReviewPhase.VALIDATION_RESULT.value}_{feature_id}"
        reviews = self.review_history.get(key, [])
        
        if not reviews:
            # No review yet, default to retry if under limit
            return True, "Validation failed, retrying with error context"
            
        latest_review = reviews[-1]
        if latest_review.approved:
            # Review says don't retry
            return False, latest_review.feedback
        else:
            # Review recommends retry
            return True, latest_review.feedback
    
    def get_feature_feedback(self, feature_id: str) -> Optional[str]:
        """Get the latest feedback for a feature."""
        # Check multiple phases for feedback
        for phase in [ReviewPhase.FEATURE_IMPLEMENTATION, ReviewPhase.VALIDATION_RESULT]:
            key = f"{phase.value}_{feature_id}"
            reviews = self.review_history.get(key, [])
            if reviews:
                return reviews[-1].feedback
        return None
    
    def get_retry_suggestions(self, feature_id: str) -> List[str]:
        """Get specific suggestions for retrying a feature."""
        suggestions = []
        
        # Collect suggestions from all reviews for this feature
        for phase in ReviewPhase:
            key = f"{phase.value}_{feature_id}"
            reviews = self.review_history.get(key, [])
            for review in reviews:
                suggestions.extend(review.suggestions)
                
        return list(set(suggestions))  # Remove duplicates
    
    def get_must_fix_items(self, phase: Optional[ReviewPhase] = None) -> List[str]:
        """Get all must-fix items, optionally filtered by phase."""
        must_fix_items = []
        
        for key, reviews in self.review_history.items():
            if phase and not key.startswith(phase.value):
                continue
                
            for review in reviews:
                must_fix_items.extend(review.must_fix)
                
        return list(set(must_fix_items))  # Remove duplicates
    
    def get_approval_summary(self) -> Dict[str, Dict]:
        """Get a summary of all approvals."""
        summary = {}
        
        for key, approved in self.approval_cache.items():
            phase, feature_id = key.split('_', 1)
            if phase not in summary:
                summary[phase] = {'approved': 0, 'rejected': 0, 'features': {}}
                
            if approved:
                summary[phase]['approved'] += 1
            else:
                summary[phase]['rejected'] += 1
                
            if feature_id != 'global':
                summary[phase]['features'][feature_id] = approved
                
        return summary