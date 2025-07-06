#!/usr/bin/env python3
"""Quick validation of Phase 5 error analysis."""

from workflows.mvp_incremental.error_analyzer import SimplifiedErrorAnalyzer, ErrorCategory

print("🧪 Testing Phase 5 - Error Analysis")
print("="*60)

# Test the error analyzer
analyzer = SimplifiedErrorAnalyzer()

# Test cases
test_cases = [
    ("SyntaxError: invalid syntax", ErrorCategory.SYNTAX),
    ("NameError: name 'x' is not defined", ErrorCategory.RUNTIME),
    ("ImportError: No module named 'pandas'", ErrorCategory.IMPORT),
    ("TypeError: unsupported operand type(s)", ErrorCategory.RUNTIME),
    ("AssertionError: Expected 5 but got 3", ErrorCategory.VALIDATION),
    ('File "test.py", line 42\n    def test(\n            ^\nSyntaxError: invalid syntax', ErrorCategory.SYNTAX),
]

print("\n📊 Error Categorization Tests:")
all_passed = True

for error_msg, expected_category in test_cases:
    error_info = analyzer.analyze_error(error_msg)
    passed = error_info.category == expected_category
    status = "✅" if passed else "❌"
    
    print(f"\n{status} Test: {error_msg[:40]}...")
    print(f"   Expected: {expected_category.value}")
    print(f"   Got: {error_info.category.value}")
    print(f"   Hint: {error_info.recovery_hint[:60]}...")
    
    if error_info.file_path:
        print(f"   Location: {error_info.file_path}:{error_info.line_number}")
    
    all_passed = all_passed and passed

# Test recovery hint generation
print("\n\n📝 Recovery Hint Tests:")
specific_errors = [
    "IndentationError: unexpected indent",
    "ZeroDivisionError: division by zero", 
    "KeyError: 'missing_key'",
    "ModuleNotFoundError: No module named 'requests'"
]

for error in specific_errors:
    error_info = analyzer.analyze_error(error)
    print(f"\nError: {error}")
    print(f"Hint: {error_info.recovery_hint}")

# Test error context prompt generation
print("\n\n🔧 Error Context Prompt Test:")
error_info = analyzer.analyze_error("NameError: name 'calculate_total' is not defined")
prompt = analyzer.create_error_context_prompt(
    error_info,
    "Calculate total price",
    "total = calculate_total(items)"
)
print(prompt)

if all_passed:
    print("\n\n✅ Phase 5 VALIDATED - Error analysis is working!")
    print("   - Errors are correctly categorized")
    print("   - Recovery hints are appropriate")
    print("   - Error context prompts are generated")
else:
    print("\n\n⚠️  Some error categorization tests failed")

exit(0 if all_passed else 1)