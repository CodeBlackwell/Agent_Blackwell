# 🚀 MVP Incremental Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   MVP INCREMENTAL WORKFLOW                      │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌─────────┐   │
│  │ PLANNER │───▶│DESIGNER │───▶│ INCREMENTAL │───▶│ FINAL   │   │
│  │         │    │         │    │   CODER     │    │ OUTPUT  │   │
│  └─────────┘    └─────────┘    └──────┬──────┘    └─────────┘   │
│                                       │                         │
│                                  ┌────▼────┐                    │
│                                  │VALIDATOR│                    │
│                                  └─────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## 📖 Table of Contents
- [Overview](#overview)
- [ELI5 - Explain Like I'm Five](#eli5---explain-like-im-five)
- [Features](#features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Phases of Development](#phases-of-development)

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
    │  2. Validate in Docker              │
    │       ↓                             │
    │  3. Pass? ─── Yes ──▶ Next Feature │
    │       │                             │
    │       No                            │
    │       ↓                             │
    │  4. Analyze Error                   │
    │       ↓                             │
    │  5. Retry with Fix                  │
    └─────────────────────────────────────┘
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
python test_phase1_validation.py  # Basic feature breakdown
python test_phase2_validation.py  # Validation integration
python test_phase3_validation.py  # Dependency ordering
python test_phase4_validation.py  # Retry logic
python test_phase5_validation.py  # Error analysis
python test_phase6_validation.py  # Progress monitoring

# Run comprehensive tests
python tests/test_mvp_incremental_phase6.py
```

### Test Structure
```
tests/
├── test_mvp_incremental_phase1.py
├── test_mvp_incremental_phase2.py
├── test_mvp_incremental_phase3.py
├── test_mvp_incremental_phase4.py
├── test_mvp_incremental_phase5.py
└── test_mvp_incremental_phase6.py
```

## Phases of Development

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

### Phase 7: Advanced Features 🚧
- Stagnation detection
- Parallel feature implementation
- Advanced error recovery strategies

## Example Output

```
🚀 Starting MVP Incremental Workflow (Phase 6 - Progress Monitoring)
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

## Contributing

When adding new features to the MVP Incremental Workflow:

1. Follow the phased approach
2. Add comprehensive tests
3. Update progress monitoring integration
4. Document error categories and recovery strategies
5. Ensure backward compatibility

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker daemon is running for validation
2. **Import errors**: Check that all dependencies are installed
3. **Validation timeouts**: Increase timeout in validator configuration
4. **Session cleanup**: Validator sessions are automatically cleaned up

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Phase 7**: Stagnation detection and advanced recovery
- **Parallel Processing**: Implement independent features in parallel
- **Caching**: Cache successful implementations for faster retries
- **Learning**: Adapt retry strategies based on historical success rates

---

Built with ❤️ by the Ground Up Team