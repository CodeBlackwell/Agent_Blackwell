# MVP Incremental Workflow Testing Guide

This comprehensive guide walks you through testing the MVP incremental workflow with all its enhancements, including the interactive demo, presets, examples, and configuration options.

## Prerequisites

### 1. **Start the Orchestrator Server**
```bash
# In terminal 1
cd /Users/lechristopherblackwell/Desktop/Ground_up/rebuild
python orchestrator/orchestrator_agent.py
```
**Expected:** Server starts on port 8080 with message "Server running on port 8080"

### 2. **Ensure Docker is Running**
```bash
# Check Docker status
docker info
```
**Expected:** Docker version info displayed. If not running:
- macOS: `open -a Docker`
- Linux: `sudo systemctl start docker`

## Testing Steps

### 3. **Test the Interactive Demo (Recommended First)**
```bash
# In terminal 2
cd /Users/lechristopherblackwell/Desktop/Ground_up/rebuild
python demo_mvp_incremental.py
```

**Expected Flow:**
- Welcome banner with "🚀 MVP Incremental Workflow Demo"
- Menu with 3 options (use preset, custom, exit)
- Choose option 1
- See list of 4 examples (calculator, todo-api, auth-system, file-processor)
- Select "calculator"
- Option to modify phases (try 'n' first time)
- Confirmation prompt
- Watch real-time progress with feature parsing, validation, retries

**What to Watch For:**
- Progress bars showing completion percentage
- Validation messages (PASS/FAIL)
- Retry attempts if validation fails
- Final success message

### 4. **Test CLI Mode with Presets**
```bash
# Simple calculator
python demo_mvp_incremental.py --preset calculator

# TODO API with all phases enabled
python demo_mvp_incremental.py --preset todo-api --all-phases

# File processor with custom phase config
python demo_mvp_incremental.py --preset file-processor --tests --no-integration
```

**Expected:** Each runs without interaction, shows configuration, executes workflow

### 5. **Test Custom Requirements**
```bash
# Simple custom requirement
python demo_mvp_incremental.py --requirements "Create a function to calculate fibonacci numbers"

# Complex requirement with all phases
python demo_mvp_incremental.py --requirements "Create a REST API for managing books with CRUD operations" --all-phases
```

**Expected:** Workflow processes your custom requirements, breaks them into features

### 6. **Test Example Scripts**

#### 6a. Calculator with Tests
```bash
cd workflows/mvp_incremental/examples
python calculator_with_tests.py
```
**Expected:** 
- Creates calculator with comprehensive tests
- Shows test execution after each feature
- Demonstrates Phase 9 in action

#### 6b. TODO API with Validation
```bash
python todo_api_with_validation.py
```
**Expected:**
- Uses the basic_api preset
- Shows validation and retry mechanisms
- Creates full FastAPI application

#### 6c. File Processor with Error Recovery
```bash
python file_processor_retry.py
```
**Expected:**
- Demonstrates error recovery
- Shows retry attempts with context
- Highlights Phase 4-5 features

#### 6d. Data Pipeline with Dependencies
```bash
python data_pipeline_dependencies.py
```
**Expected:**
- Shows automatic dependency ordering
- Features implemented in correct sequence
- Demonstrates Phase 3 dependency management

### 7. **Test Configuration Helper**
```bash
# Interactive Python session
python
```
```python
from workflows.mvp_incremental.config_helper import ConfigHelper, load_preset

# Load a preset
config = load_preset("basic_api")
print(f"Max retries: {config.max_retries}")
print(f"Test timeout: {config.test_timeout}")

# Create helper and explore
helper = ConfigHelper()
print(helper.available_presets)

# Get recommendations
recs = helper.get_performance_recommendations("complex")
print(recs)

# Exit Python
exit()
```

### 8. **Examine Generated Output**
```bash
# Check generated code
ls -la generated/app_generated_*/

# View a generated file
cat generated/app_generated_*/main.py

# Check completion report (if Phase 10 was enabled)
cat generated/app_generated_*/COMPLETION_REPORT.md
```

### 9. **Test Validation and Retries**
Create a file with intentionally problematic requirements:
```bash
python demo_mvp_incremental.py --requirements "Create a calculator that uses undefined_module and has syntax errors"
```
**Expected:** 
- Validation fails on first attempt
- Error analyzer provides context
- Retry with fixes
- Eventually succeeds or reaches max retries

### 10. **Run Unit Tests**
```bash
# Test new components
pytest tests/mvp_incremental/test_config_helper.py -v
pytest tests/mvp_incremental/test_demo_script.py -v
pytest tests/mvp_incremental/test_presets.py -v

# Run all MVP incremental tests
pytest tests/mvp_incremental/ -v
```

## Variations to Try

### 11. **Different Complexity Levels**
```bash
# Very simple
python demo_mvp_incremental.py --requirements "Create a hello world function"

# Medium complexity
python demo_mvp_incremental.py --requirements "Create a password strength checker with multiple rules"

# High complexity
python demo_mvp_incremental.py --preset auth-system --all-phases
```

### 12. **Phase Combinations**
```bash
# Only Phase 9 (tests)
python demo_mvp_incremental.py --preset calculator --tests --no-integration

# Only Phase 10 (integration)
python demo_mvp_incremental.py --preset calculator --no-tests --integration

# Neither Phase 9 nor 10 (fastest)
python demo_mvp_incremental.py --preset calculator --no-tests --no-integration
```

### 13. **Save and Inspect Output**
```bash
# Run with output saving
python demo_mvp_incremental.py --preset todo-api --all-phases --save-output

# Check saved output
ls -la demo_outputs/
cat demo_outputs/mvp_demo_*_summary.json
```

## What to Look For

### Success Indicators:
- ✅ Features parsed correctly
- ✅ Validation passes (or retries succeed)
- ✅ Progress bars reach 100%
- ✅ Final code is generated
- ✅ Tests pass (if Phase 9 enabled)
- ✅ Integration verification succeeds (if Phase 10 enabled)

### Common Issues:
- ❌ Docker not running (validation fails)
- ❌ Import errors (watch retry fixes)
- ❌ Max retries exceeded (complex requirements)
- ❌ Timeout errors (increase in config)

### Performance Observations:
- Simple projects: 30-60 seconds
- Medium projects: 1-3 minutes
- Complex projects: 3-5 minutes
- With all phases: Add 1-2 minutes

## Advanced Testing

### 14. **Debug Mode**
```bash
# Enable debug logging
export MVP_DEBUG=1
python demo_mvp_incremental.py --preset calculator
```

### 15. **Custom Configuration**
Create a test script `test_custom_config.py`:
```python
from workflows.mvp_incremental.config_helper import MVPIncrementalConfig
from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
import asyncio

async def test_custom():
    # Create custom config
    config = MVPIncrementalConfig(
        max_retries=5,
        test_timeout=120,
        run_tests=True
    )
    
    # Create input
    input_data = CodingTeamInput(
        requirements="Create a simple key-value store",
        run_tests=config.run_tests
    )
    
    # Execute
    result = await execute_workflow("mvp_incremental", input_data)
    print("Custom workflow completed!")

# Run
asyncio.run(test_custom())
```

### 16. **Interactive Configuration Wizard**
```python
from workflows.mvp_incremental.config_helper import ConfigHelper

helper = ConfigHelper()
config = helper.interactive_wizard()
print(f"Created config: {config.name}")
```

## Testing Workflow Phases

### Phase 1-2: Planning and Design
Watch for:
- Clear breakdown of requirements
- Technical design generation

### Phase 3: Feature Dependencies
Look for:
- "Analyzing feature dependencies..." message
- Features reordered based on dependencies

### Phase 4-5: Retry and Error Analysis
Observe:
- Retry messages with attempt counts
- Error categorization (Syntax, Import, Runtime, etc.)
- Context-aware fix suggestions

### Phase 6: Progress Monitoring
Notice:
- Progress bars with percentages
- Time tracking per phase
- Feature completion status

### Phase 7-8: Review Integration
Check for:
- Review status messages (APPROVED/NEEDS REVISION)
- Feedback incorporation
- Review summary document generation

### Phase 9: Test Execution
Verify:
- "Running tests for [feature]..." messages
- Test pass/fail results
- Automatic test fixing attempts

### Phase 10: Integration Verification
Confirm:
- Full test suite execution
- Build verification
- Completion report generation

## Quick Test Checklist

- [ ] Orchestrator running
- [ ] Docker running
- [ ] Interactive demo works
- [ ] CLI mode with preset works
- [ ] Custom requirements work
- [ ] Example scripts run
- [ ] Generated code is valid
- [ ] Tests pass
- [ ] Retries work correctly
- [ ] Progress tracking displays
- [ ] Review messages appear
- [ ] Completion report generated (Phase 10)

## Troubleshooting

### If the demo won't start:
1. Check orchestrator is running
2. Verify Python path is correct
3. Check for missing dependencies: `pip install -r requirements.txt`

### If validation always fails:
1. Ensure Docker is running
2. Check Docker permissions
3. Try simpler requirements first

### If tests fail:
1. Some tests require orchestrator running
2. Check test file paths are correct
3. Run with pytest -v for details

## Next Steps

After testing the basics:
1. Try creating your own presets
2. Modify example scripts
3. Test with real project requirements
4. Explore the generated code quality
5. Benchmark performance with different configurations

---

This testing guide covers all aspects of the MVP incremental workflow. Start with the interactive demo (step 3) for the best introduction!