# Operation Red Yellow Reference

## Document Location
`/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/memory/operation_red_yellow.md`

## Purpose
Operation Red Yellow is the comprehensive plan to completely transform the MVP Incremental Workflow into a pure Test-Driven Development (TDD) system. This is not an optional feature or mode - it's a full evolution of how the workflow operates.

## Key Points to Remember

### What It Does
- Implements mandatory RED-YELLOW-GREEN phases for every feature
- RED: Tests written first and must fail (no implementation exists)
- YELLOW: Tests pass but code awaits review
- GREEN: Tests pass AND code is reviewed/approved

### Implementation Structure
- 11 phases total, each with implementation (a) and testing (b) sub-phases
- Logical dependency ordering ensures each component builds on previous ones
- Estimated 11 days for complete implementation

### Critical Changes
1. Test Writer Agent becomes mandatory after design phase
2. Code cannot be written until tests fail (RED phase enforcement)
3. No configuration options - TDD is the only way the workflow operates
4. Existing non-TDD code paths will be completely removed
5. Test execution happens multiple times per feature (not just at end)

### Why This Matters
This represents a fundamental shift in how the MVP incremental workflow operates. After Operation Red Yellow is implemented, every feature developed through this workflow will follow strict TDD principles, ensuring higher quality code and better test coverage from the start.

## Related Files
- Current workflow: `workflows/mvp_incremental/mvp_incremental.py`
- Test execution: `workflows/mvp_incremental/test_execution.py`
- Future TDD components will be in: `workflows/mvp_incremental/tdd_*.py`

Last updated: 2025-07-08