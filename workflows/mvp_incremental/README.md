# 🚀 MVP Incremental Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   MVP INCREMENTAL WORKFLOW                      │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌─────────┐   │
│  │ PLANNER │───▶│DESIGNER │───▶│ INCREMENTAL │───▶│ FINAL   │   │
│  │         │    │         │    │   CODER     │    │ OUTPUT  │   │
│  └────┬────┘    └────┬────┘    └──────┬──────┘    └─────────┘   │
│       │              │                 │                        │
│       ▼              ▼                 ▼                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                    │
│  │REVIEWER │    │REVIEWER │    │VALIDATOR│                    │
│  └─────────┘    └─────────┘    └────┬────┘                    │
│                                     │                          │
│                                     ▼                          │
│                               ┌─────────┐                      │
│                               │REVIEWER │                      │
│                               └─────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## 📖 Table of Contents
- [Quick Start](#quick-start)
- [Overview](#overview)
- [ELI5 - Explain Like I'm Five](#eli5---explain-like-im-five)
- [Features](#features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Phases of Development](#phases-of-development)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Interactive Demo (Recommended)
```bash
# Run the interactive demo
python demos/advanced/mvp_incremental_demo.py
```

### Quick Examples
```bash
# Build a calculator with tests
python demos/advanced/mvp_incremental_demo.py --preset calculator

# Create a TODO API with all phases
python demos/advanced/mvp_incremental_demo.py --preset todo-api --all-phases

# Custom requirements
python demos/advanced/mvp_incremental_demo.py --requirements "Create a web scraper for news articles"
```

### Run Example Scripts
```bash
# See various features in action
python workflows/mvp_incremental/examples/calculator_with_tests.py
python workflows/mvp_incremental/examples/todo_api_with_validation.py
```

## Overview

The MVP Incremental Workflow is an intelligent code generation system that breaks down complex requirements into manageable features and implements them one at a time. It includes validation, error recovery, dependency management, and real-time progress monitoring.

## 🧸 ELI5 - Explain Like I'm Five

Imagine you want to build a big LEGO castle! 🏰

Instead of trying to build the whole castle at once (which would be confusing!), the MVP Incremental Workflow is like having a team of helpers who:

1. **Planner Helper** 📋: Looks at the picture of the castle and makes a list of all the parts (towers, walls, gates)
2. **Designer Helper** 🎨: Draws detailed instructions for each part
3. **Builder Helper** 🔨: Builds one part at a time (first the gate, then a wall, then a tower...)
4. **Checker Helper** ✅: After each part, checks if it's built correctly
5. **Fixer Helper** 🔧: If something's wrong, figures out what went wrong and helps fix it

And while they work, there's a **Progress Board** 📊 that shows:
- Which part they're building now
- How many parts are done
- If any parts needed to be rebuilt

This way, even if one tower falls down, you don't have to rebuild the whole castle - just that one tower!

## Features

### 🎯 Core Features
- **Feature Decomposition**: Automatically breaks down requirements into implementable features
- **Sequential Implementation**: Builds features one at a time for clarity
- **Real-time Validation**: Validates each feature immediately after implementation
- **Smart Retry Logic**: Automatically retries failed features with context
- **Dependency Management**: Orders features based on dependencies
- **Progress Monitoring**: Visual progress tracking with timing metrics

### 🛡️ Advanced Features
- **Error Analysis**: Categorizes errors and provides recovery hints
- **Session Persistence**: Maintains Docker container sessions for validation
- **Incremental Building**: Each feature builds upon previous ones
- **Comprehensive Reporting**: Detailed metrics and summaries
- **Quality Reviews**: Automated code reviews at each phase
- **Review-Guided Retries**: Combines technical and qualitative analysis for retry decisions
- **Review Summary Document**: Auto-generated README with insights and recommendations

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Workflow Components                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │     PLANNING     │  │     DESIGN      │  │  IMPLEMENTATION │   │
│  │                 │  │                 │  │                 │   │
│  │ • Parse reqs    │  │ • Tech design   │  │ • Feature loop  │   │
│  │ • Identify      │  │ • Break into    │  │ • Code each     │   │
│  │   components    │  │   features      │  │ • Validate      │   │
│  │                 │  │ • Define deps   │  │ • Retry if fail │   │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │
│           │                    │                     │             │
│           ▼                    ▼                     ▼             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    PROGRESS MONITOR                          │  │
│  │  [████████████████████░░░░░░░░] 75% | 3/4 features done    │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Planning Phase
```
Input Requirements ──▶ Planner Agent ──▶ High-level Plan
```

### 2. Design Phase
```
Plan ──▶ Designer Agent ──▶ Technical Design with Features
                               │
                               ▼
                        Feature List:
                        1. Feature A
                        2. Feature B (depends on A)
                        3. Feature C
```

### 3. Implementation Phase
```
For each feature:
    ┌─────────────────────────────────────┐
    │  1. Code Feature                    │
    │       ↓                             │
    │  2. Review Implementation           │
    │       ↓                             │
    │  3. Validate in Docker              │
    │       ↓                             │
    │  4. Pass? ─── Yes ──▶ Next Feature │
    │       │                             │
    │       No                            │
    │       ↓                             │
    │  5. Review Validation Result        │
    │       ↓                             │
    │  6. Analyze Error + Review Feedback │
    │       ↓                             │
    │  7. Retry with Fix + Suggestions    │
    └─────────────────────────────────────┘
```

### 4. Final Phase
```
All Features Complete ──▶ Final Review ──▶ Generate Review Summary
                                              │
                                              ▼
                                         README.md with:
                                         • Project Overview
                                         • Quality Assessment
                                         • Recommendations
                                         • Technical Debt
```

## Usage

### Basic Usage

```python
from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow

# Define your requirements
input_data = CodingTeamInput(
    requirements="""
    Create a Calculator class with:
    1. add(a, b) - returns sum
    2. subtract(a, b) - returns difference
    3. multiply(a, b) - returns product
    4. divide(a, b) - returns quotient with error handling
    """,
    workflow_type="mvp_incremental"
)

# Execute the workflow
results, report = await execute_workflow(input_data)
```

### With Custom Configuration

```python
from workflows.mvp_incremental.retry_strategy import RetryConfig

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=3,  # Try up to 3 times per feature
    extract_error_context=True,
    modify_prompt_on_retry=True
)
```

## Configuration

### Retry Configuration
- `max_retries`: Maximum retry attempts per feature (default: 2)
- `extract_error_context`: Extract detailed error information (default: True)
- `modify_prompt_on_retry`: Enhance prompts with error context (default: True)

### Progress Monitor Settings
- Real-time progress bars
- Phase timing tracking
- Feature-level status updates
- Comprehensive workflow summaries

## Testing

### Running Tests

```bash
# Test individual phases
python tests/integration/incremental/test_phase2_summary.py        # Validation integration
python tests/integration/incremental/test_phase3_validation.py     # Dependency ordering
python tests/integration/incremental/test_phase4_validation.py     # Retry logic
python tests/integration/incremental/test_phase5_validation.py     # Error analysis
python tests/integration/incremental/test_phase6_validation.py     # Progress monitoring
python tests/integration/incremental/test_phase7_validation.py     # Feature reviewer
python tests/integration/incremental/test_phase8_validation.py     # Review integration
python tests/integration/incremental/test_phase8_review_integration.py  # Review module

# Run comprehensive workflow test
python tests/test_workflows.py mvp_incremental
```

### Test Structure
```
tests/
├── integration/
│   ├── incremental/
│   │   ├── test_phase2_summary.py
│   │   ├── test_phase3_validation.py
│   │   ├── test_phase4_validation.py
│   │   ├── test_phase4_retry_trigger.py
│   │   ├── test_phase5_validation.py
│   │   ├── test_phase6_validation.py
│   │   ├── test_phase6_progress_simple.py
│   │   ├── test_phase7_validation.py
│   │   ├── test_phase8_validation.py
│   │   └── test_phase8_review_integration.py
│   └── ...
└── test_workflows.py
```

## Phases of Development (All 10 Phases Complete! 🎉)

### Phase 1: Basic Feature Breakdown ✅
- Parse design into individual features
- Implement features sequentially
- Basic code accumulation

### Phase 2: Validation Integration ✅
- Docker-based validation after each feature
- Session management for consistency
- Pass/fail detection

### Phase 3: Dependency Management ✅
- Topological sorting of features
- Smart ordering based on keywords
- Dependency graph visualization

### Phase 4: Retry Logic ✅
- Configurable retry attempts
- Context preservation between retries
- Non-retryable error detection

### Phase 5: Error Analysis ✅
- Error categorization (Syntax, Runtime, Import, etc.)
- Recovery hint generation
- Enhanced retry prompts with error context

### Phase 6: Progress Monitoring ✅
- Real-time progress visualization
- Phase timing breakdown
- Comprehensive metrics export
- Visual progress bars

### Phase 7: Feature Reviewer Agent ✅
- Specialized agent for reviewing individual features
- Context-aware reviews for incremental development
- Actionable feedback generation
- Integration with existing codebase considerations

### Phase 8: Review Integration ✅
- Reviews at all major phases (planning, design, implementation, final)
- Review-guided retry decisions
- Comprehensive review summary document generation
- Review history tracking and approval management

### Phase 9: Test Execution ✅
- Execute generated tests after each feature implementation
- Test failure analysis and fixing
- Test-driven retry loop
- Test coverage tracking
- Verification loop closure

### Phase 10: Integration Verification ✅
- Full application integration testing
- Build verification and smoke tests
- Feature interaction validation
- Comprehensive completion report generation
- Basic documentation auto-generation

**Note**: For complete phase documentation, see [MVP Incremental Phases Documentation](../../docs/mvp_incremental_phases.md)

## Review Summary Document

The workflow automatically generates a comprehensive review summary document (`README.md`) that includes:

### 📋 Sections Included

1. **Project Overview**
   - Summary of what was built
   - Key features implemented
   - Overall architecture

2. **Implementation Status**
   - Feature-by-feature breakdown
   - Success/failure status
   - Retry attempts and outcomes

3. **Code Quality Assessment**
   - Review findings at each phase
   - Code patterns and practices
   - Adherence to requirements

4. **Key Recommendations**
   - High-priority improvements
   - Refactoring suggestions
   - Security considerations

5. **Technical Debt**
   - Known issues to address
   - Future maintenance needs
   - Scalability concerns

6. **Success Metrics**
   - What went well
   - Performance achievements
   - Clean implementations

7. **Lessons Learned**
   - Insights from the development process
   - Common error patterns
   - Effective solutions

## Example Output

```
🚀 Starting MVP Incremental Workflow (Phase 8 - Review Integration)
============================================================
⏰ Started at: 14:23:15
📋 Total features to implement: 4
============================================================

============================================================
📍 PHASE: PLANNING
============================================================
⚙️  Planning: Starting...
   ✅ Completed in 2.3s

============================================================
📍 PHASE: DESIGN
============================================================
⚙️  Design: Starting...
   ✅ Completed in 1.8s

============================================================
📍 PHASE: IMPLEMENTATION
============================================================
⚙️  Feature 1/4: Add method
   Status: Starting implementation...
   ✅ Validation: PASSED
   ✅ Completed in 3.2s

📊 Progress: [██████████░░░░░░░░░░░░░░░░░░░░] 25% | Time: 0:07

⚙️  Feature 2/4: Subtract method
   Status: Starting implementation...
   ❌ Validation: FAILED
   🔄 First retry attempt...
   ✅ Validation: PASSED
   ✅ Completed in 5.1s

📊 Progress: [████████████████████░░░░░░░░░░] 50% | Time: 0:12

[... continues for all features ...]

============================================================
📈 WORKFLOW SUMMARY
============================================================
⏱️  Total Duration: 45.2 seconds
📊 Total Steps: 12

📋 Phase Breakdown:
   - planning: 2.3s
   - design: 1.8s
   - feature: 35.1s
   - validation: 6.0s

🔧 Feature Implementation:
   - Total: 4
   - Successful: 4
   - Failed: 0
   - Required Retry: 1

============================================================
```

## Architecture Details

### Component Interactions

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Planner   │────▶│   Designer   │────▶│ Feature Parser  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │ Dependency      │
                                         │ Analyzer        │
                                         └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              ▼                              │
                    │                    ┌─────────────────┐                      │
                    │                    │ Feature Queue   │                      │
                    │                    └────────┬────────┘                      │
                    │                             │                               │
                    │      ┌──────────────────────┼──────────────────────┐       │
                    │      │                      ▼                      │       │
                    │      │            ┌─────────────────┐              │       │
                    │      │            │ Feature Coder   │              │       │
                    │      │            └────────┬────────┘              │       │
                    │      │                     │                       │       │
                    │      │                     ▼                       │       │
                    │      │            ┌─────────────────┐              │       │
                    │      │            │   Validator     │              │       │
                    │      │            └────────┬────────┘              │       │
                    │      │                     │                       │       │
                    │      │                  Pass/Fail                  │       │
                    │      │                   ┌─┴─┐                     │       │
                    │      │               Fail│   │Pass                 │       │
                    │      │                   ▼   ▼                     │       │
                    │      │         ┌──────────────┐                    │       │
                    │      └─────────│Error Analyzer│                    │       │
                    │                └──────────────┘                    │       │
                    │                        │                           │       │
                    │                    Retry Loop                      │       │
                    └────────────────────────────────────────────────────┘       │
                                                                                 │
                                         Next Feature ◀──────────────────────────┘
```

## 📚 Examples

Explore the `workflows/mvp_incremental/examples/` directory for ready-to-run examples:

### Available Examples
- **calculator_with_tests.py** - Simple calculator with comprehensive tests (Phase 9)
- **todo_api_with_validation.py** - REST API with validation and retries
- **file_processor_retry.py** - CSV processor demonstrating error recovery
- **data_pipeline_dependencies.py** - Complex pipeline with feature dependencies

### Running Examples
```bash
cd workflows/mvp_incremental/examples/
python calculator_with_tests.py
```

## 🛠️ Visual Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MVP INCREMENTAL WORKFLOW (10 PHASES)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Requirements ──► Phase 1-2: Planning & Design                         │
│       │              │                                                  │
│       ▼              ▼                                                  │
│  ┌─────────┐    ┌─────────┐                                           │
│  │ PLANNER │───►│DESIGNER │                                           │
│  └────┬────┘    └────┬────┘                                           │
│       │              │                                                  │
│       ▼              ▼                                                  │
│  ┌─────────────────────────────────────────────────┐                  │
│  │          Phase 3-8: Feature Implementation       │                  │
│  │  ┌───────────────────────────────────────────┐  │                  │
│  │  │  For Each Feature:                        │  │                  │
│  │  │  1. Parse & Order (Phase 3)               │  │                  │
│  │  │  2. Implement Code                        │  │                  │
│  │  │  3. Validate (Phase 2)                    │  │                  │
│  │  │  4. Review (Phase 7-8)                    │  │                  │
│  │  │  5. Retry if Failed (Phase 4-5)           │  │                  │
│  │  │  6. Track Progress (Phase 6)              │  │                  │
│  │  └───────────────────────────────────────────┘  │                  │
│  └─────────────────────────────────────────────────┘                  │
│                           │                                             │
│                           ▼                                             │
│  ┌─────────────────────────────────────────────────┐                  │
│  │        Phase 9-10: Testing & Integration        │                  │
│  │  ┌───────────────┐     ┌────────────────────┐  │                  │
│  │  │ Test Execution│────►│Integration Verify  │  │                  │
│  │  │  (Phase 9)    │     │    (Phase 10)      │  │                  │
│  │  └───────────────┘     └────────────────────┘  │                  │
│  └─────────────────────────────────────────────────┘                  │
│                           │                                             │
│                           ▼                                             │
│                    Final Output + Reports                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Contributing

When adding new features to the MVP Incremental Workflow:

1. Follow the phased approach
2. Add comprehensive tests
3. Update progress monitoring integration
4. Document error categories and recovery strategies
5. Ensure backward compatibility

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **Docker not running**
```bash
# Check Docker status
docker info

# Start Docker daemon (macOS)
open -a Docker

# Start Docker daemon (Linux)
sudo systemctl start docker
```

#### 2. **Import errors during validation**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# For specific packages
pip install fastapi pydantic pytest
```

#### 3. **Validation timeouts**
```python
# Increase timeout in your code
from workflows.mvp_incremental.config_helper import MVPIncrementalConfig

config = MVPIncrementalConfig()
config.test_timeout = 120  # Increase to 2 minutes
```

#### 4. **Session cleanup issues**
```bash
# Manually clean up Docker containers
docker ps -a | grep validator
docker rm -f <container_id>
```

#### 5. **Feature parsing problems**
- Ensure requirements have clear, numbered features
- Use bullet points or numbered lists
- Keep feature descriptions concise

#### 6. **Retry loops getting stuck**
```python
# Limit retries in configuration
config = MVPIncrementalConfig()
config.max_retries = 2  # Reduce from default
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export MVP_DEBUG=1
```

### Getting Help

1. Check the [examples directory](./examples/) for working code
2. Review [test files](../../tests/mvp_incremental/) for usage patterns
3. Enable debug logging to see detailed execution flow
4. Check Docker logs: `docker logs <container_id>`

## Future Enhancements

Beyond the planned Phase 9 and 10:

- **Parallel Processing**: Implement independent features in parallel when no dependencies exist
- **Caching**: Cache successful implementations for faster retries
- **Learning**: Adapt retry strategies based on historical success rates
- **Multi-Language Support**: Extend validation beyond Python
- **Performance Optimization**: Profile and optimize slow features
- **Semantic Versioning**: Track feature versions and compatibility

---

Built with ❤️ by the Ground Up Team