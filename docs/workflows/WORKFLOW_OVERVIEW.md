# Workflow Overview - Complete Library Guide

This document describes all available workflows in the multi-agent orchestrator system. Each workflow represents a different software development approach with specialized agent coordination patterns.

## Core Workflows

### 1. **TDD Workflow** (`workflows/tdd/tdd_workflow.py`)

**Purpose**: Test-Driven Development approach where tests are written before implementation.

**Flow Pattern**: 
```
Requirements → Planning → Test Writing → Implementation → Testing → Review
```

**Key Features**:
- Tests are written first based on requirements
- Implementation is driven by making tests pass
- Ensures high test coverage from the start
- Best for projects where quality and reliability are critical

**When to Use**:
- Mission-critical applications
- Projects with strict quality requirements
- When refactoring legacy code
- API development with contract-first approach

**Agents Involved**:
- Planner: Creates development strategy
- Test Writer: Writes comprehensive test suite
- Coder: Implements code to pass tests
- Executor: Runs tests and validates
- Reviewer: Reviews implementation quality

---

### 2. **Full Workflow** (`workflows/full/full_workflow.py`)

**Purpose**: Traditional complete development cycle with all phases.

**Flow Pattern**:
```
Requirements → Planning → Design → Implementation → Testing → Review
```

**Key Features**:
- Comprehensive approach with all development phases
- Design phase before implementation
- Tests written after implementation
- Suitable for well-understood projects

**When to Use**:
- New projects with clear requirements
- When you need detailed design documentation
- Projects requiring architectural planning
- Standard web applications or services

**Agents Involved**:
- Planner: Strategic planning
- Designer: Technical design and architecture
- Coder: Full implementation
- Test Writer: Creates test suite
- Reviewer: Final quality check

---

### 3. **Incremental Workflow** (`workflows/incremental/incremental_workflow.py`)

**Purpose**: Feature-by-feature implementation with validation after each feature.

**Flow Pattern**:
```
Requirements → Planning → Design → [Feature Implementation → Validation]* → Review
```

**Key Features**:
- Uses Feature Orchestrator to manage incremental development
- Each feature is implemented and validated before proceeding
- Smart retry strategies for failed features
- Progress tracking and stagnation detection
- Dependencies between features are respected

**When to Use**:
- Large, complex projects
- When you need early feedback on features
- Projects with many interdependent components
- When risk mitigation is important

**Agents Involved**:
- Planner: High-level strategy
- Designer: Creates feature breakdown
- Coder: Implements one feature at a time
- Executor: Validates each feature
- Reviewer: Reviews complete implementation

**Special Components**:
- Feature Orchestrator: Manages feature implementation
- Progress Monitor: Tracks development progress
- Retry Strategies: Handles failures intelligently
- Stagnation Detector: Identifies when stuck

---

### 4. **MVP Incremental Workflow** (`workflows/mvp_incremental/mvp_incremental.py`)

**Purpose**: Rapid MVP development with 10 structured phases.

**Flow Pattern**:
```
Requirements → Expansion → Planning → [10 Implementation Phases] → Review
```

**10 Phases**:
1. **Foundation**: Core structure and setup
2. **Core Entities**: Main data models
3. **Storage Layer**: Database/persistence
4. **Business Logic**: Core functionality
5. **API Layer**: External interfaces
6. **Integration**: Component connections
7. **Error Handling**: Robustness
8. **Testing Suite**: Comprehensive tests
9. **Documentation**: User/API docs
10. **Deployment**: Production readiness

**Key Features**:
- Highly structured phased approach
- Each phase builds on previous ones
- Parallel processing where possible
- Built-in error recovery
- Progress visualization

**When to Use**:
- MVP/prototype development
- Startups needing quick iteration
- Proof of concept projects
- When you need predictable progress

---

### 5. **MVP Incremental TDD** (`workflows/mvp_incremental/mvp_incremental_tdd.py`)

**Purpose**: Combines MVP phased approach with Test-Driven Development.

**Flow Pattern**:
```
Requirements → Planning → [Red → Green → Yellow → Refactor]* → Integration
```

**TDD Phases per Feature**:
- **Red Phase**: Write failing tests
- **Green Phase**: Implement to pass tests
- **Yellow Phase**: Optimize and refactor
- **Integration**: Verify with existing code

**Key Features**:
- TDD cycle for each MVP phase
- Test caching for efficiency
- Parallel test execution
- Coverage validation
- Intelligent error analysis

**When to Use**:
- Quality-critical MVPs
- When you need both speed and reliability
- Projects with compliance requirements
- API-first development

---

### 6. **Individual Workflow** (`workflows/individual/individual_workflow.py`)

**Purpose**: Execute single development phases independently.

**Flow Pattern**:
```
Requirements → [Selected Phase] → Output
```

**Available Phases**:
- `planning`: Just create a plan
- `design`: Only technical design
- `implementation`: Code writing only
- `test_writing`: Just write tests
- `review`: Review existing code

**Key Features**:
- Flexible single-phase execution
- Quick iterations on specific tasks
- Useful for debugging workflow issues
- Can be chained manually

**When to Use**:
- Quick prototypes
- Fixing specific issues
- When you only need one phase
- Testing individual agents

---

## Workflow Selection Guide

### Decision Matrix

| Workflow | Speed | Quality | Complexity | Best For |
|----------|-------|---------|------------|----------|
| TDD | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Quality-critical projects |
| Full | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | Standard applications |
| Incremental | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Large, complex projects |
| MVP Incremental | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Rapid prototyping |
| MVP TDD | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Quality MVPs |
| Individual | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | Quick tasks |

### Quick Selection Guide

**Choose TDD Workflow when**:
- Testing is paramount
- Working on financial/healthcare/security software
- Refactoring existing code
- Building APIs with strict contracts

**Choose Full Workflow when**:
- Building standard web applications
- Requirements are well understood
- Need comprehensive documentation
- Team prefers traditional approach

**Choose Incremental Workflow when**:
- Project has many features
- Features have complex dependencies
- Need to show progress incrementally
- Risk mitigation is important

**Choose MVP Incremental when**:
- Building a startup MVP
- Need rapid time-to-market
- Working on proof of concept
- Iterating based on feedback

**Choose MVP TDD when**:
- MVP needs high reliability
- Building API-first product
- Have compliance requirements
- Need both speed and quality

**Choose Individual when**:
- Just need a quick plan
- Reviewing existing code
- Writing tests for legacy code
- Debugging specific issues

---

### 7. **Enhanced TDD Workflow** (`workflows/tdd/enhanced_tdd_workflow.py`)

**Purpose**: Advanced TDD implementation with proper Red-Green-Refactor cycles.

**Flow Pattern**:
```
Requirements → Planning → Design → [Write Tests (Red) → Run Tests → Implement (Green) → Run Tests → Refactor → Run Tests]* → Integration → Review
```

**Key Features**:
- True TDD cycle with explicit phases
- Tests are run after each phase to verify state
- Refactoring phase for code quality
- Feature-by-feature TDD implementation
- Integration testing after all features

**Enhanced Over Standard TDD**:
- Explicit Red-Green-Refactor phases
- Test execution verification at each step
- Better feedback loops
- Component-wise TDD cycles

**When to Use**:
- When you need strict TDD discipline
- Teaching/demonstrating TDD principles
- Complex refactoring projects
- When code quality is paramount

**Note**: This workflow is experimental and may not be registered in the main workflow manager yet.

## Usage Examples

### Basic Usage
```python
from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow

# Choose your workflow
input_data = CodingTeamInput(
    requirements="Create a task management API",
    workflow_type="incremental",  # or "tdd", "full", "mvp_incremental", etc.
)

# Execute
results, report = await execute_workflow(input_data)
```

### Command Line Usage
```bash
# Start orchestrator
python orchestrator/orchestrator_agent.py

# Run workflow
python run.py workflow incremental --task "Build a blog platform"
```

## Workflow Components

### Shared Components
- **WorkflowExecutionTracer**: Monitors execution
- **WorkflowConfig**: Configuration management
- **WorkflowVisualizer**: Progress visualization
- **ErrorAnalyzer**: Intelligent error analysis
- **RetryStrategies**: Failure recovery

### Workflow-Specific Components
- **Feature Orchestrator** (Incremental): Manages features
- **Phase Managers** (MVP): Handles 10 phases
- **TDD Tracker** (TDD workflows): Tracks test cycles
- **Progress Monitor**: Real-time progress tracking

## Performance Characteristics

### Execution Times (Approximate)
- **Individual**: 1-5 minutes per phase
- **TDD**: 15-30 minutes for small projects
- **Full**: 20-40 minutes typically
- **Incremental**: 30-60 minutes (depends on features)
- **MVP Incremental**: 45-90 minutes for full MVP
- **MVP TDD**: 60-120 minutes with full testing

### Resource Usage
- All workflows support parallel agent execution
- Memory usage scales with project size
- Network calls are batched where possible
- Docker containers are reused efficiently

## Advanced Features

### Workflow Customization
- Modify retry strategies
- Adjust validation criteria
- Configure parallel execution
- Custom progress reporting

### Integration Options
- GitHub Actions support
- CI/CD pipeline integration
- Custom agent endpoints
- Monitoring webhooks

## Troubleshooting

### Common Issues
1. **Workflow Selection**: Use the decision matrix
2. **Performance**: Enable parallel execution
3. **Failures**: Check retry strategies
4. **Quality**: Use TDD variants for critical code

### Getting Help
- Run workflow demos in `examples/`
- Check workflow-specific READMEs
- Review test files for usage patterns
- Enable debug logging for details