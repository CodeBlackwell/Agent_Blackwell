# MVP Incremental Workflow Documentation

The MVP Incremental Workflow is a sophisticated, feature-by-feature development approach that breaks down your requirements and builds applications incrementally with validation at each step.

## 📋 Quick Navigation

### Essential Documentation
- **[User Guide](user-guide.md)** - Comprehensive guide with all details
- **[Quick Reference](quick-reference.md)** - Commands and options at a glance
- **[Phases Documentation](phases.md)** - Detailed explanation of all 10 phases
- **[TDD Enhancement](tdd-enhancement.md)** - Test-driven development integration

### Test Results & Validation
- **[Test Results](test-results.md)** - Validation results and bug fixes
- **[Testing Guide](../../mvp_incremental/TESTING_GUIDE.md)** - Testing strategies
- **[TDD Guide](../../mvp_incremental/TDD_GUIDE.md)** - TDD workflow guide

### Examples & Tutorials
- **[Examples](../../mvp_incremental/examples/README.md)** - Code examples
- **[Tutorial Mode](#tutorial-mode)** - Interactive learning

## 🚀 Quick Start

### Run Your First Example (2 minutes)
```bash
# Start the orchestrator (in a separate terminal)
python orchestrator/orchestrator_agent.py

# Run the calculator example
python demos/advanced/mvp_incremental_demo.py --preset calculator
```

### Interactive Mode (Recommended for Beginners)
```bash
python demos/advanced/mvp_incremental_demo.py
```

### Custom Project
```bash
python demos/advanced/mvp_incremental_demo.py \
  --requirements "Create a REST API for task management" \
  --all-phases
```

## 🎯 What It Does

The MVP Incremental Workflow orchestrates a team of specialized AI agents:

1. **Planner Agent** 📋 - Analyzes requirements and creates development plan
2. **Designer Agent** 🏗️ - Designs architecture and structure
3. **Coder Agent** 💻 - Implements features incrementally
4. **Test Writer Agent** 🧪 - Creates comprehensive tests
5. **Reviewer Agent** 🔍 - Reviews code quality
6. **Executor Agent** ✅ - Validates implementation
7. **Feature Reviewer** 👁️ - Ensures feature completeness

## 📊 Available Presets

| Preset | Difficulty | Time | Description |
|--------|-----------|------|-------------|
| `calculator` | Beginner | 2-3 min | Basic calculator with operations |
| `todo-api` | Intermediate | 5-7 min | RESTful task management API |
| `auth-system` | Advanced | 10-15 min | User authentication system |
| `file-processor` | Intermediate | 5-8 min | File processing utilities |

## 🔧 Key Features

### Progressive Development
- Features implemented one at a time
- Validation after each feature
- Automatic retry on failures
- Progress tracking throughout

### Comprehensive Testing
- Optional test generation (Phase 9)
- Integration testing (Phase 10)
- Test execution and validation
- Coverage reporting

### Smart Error Handling
- Automatic error analysis
- Intelligent retry strategies
- Stagnation detection
- Detailed error reporting

## 💡 When to Use

### Perfect For:
- ✅ Learning the system
- ✅ Building MVPs and prototypes
- ✅ Projects needing iterative development
- ✅ When you want visibility into progress
- ✅ Projects requiring comprehensive testing

### Consider Alternatives For:
- ❌ Single-file scripts (use individual steps)
- ❌ Pure refactoring tasks (use full workflow)
- ❌ When you need maximum speed over quality

## 📁 Output Structure

```
generated/app_generated_[timestamp]/
├── [main_files]           # Core implementation
├── tests/                 # Test files (if Phase 9 enabled)
│   ├── test_*.py         # Individual test files
│   └── integration/      # Integration tests (if Phase 10)
├── requirements.txt       # Dependencies
├── README.md             # Project documentation
└── setup.py              # Package setup (if applicable)
```

## 🔗 Related Documentation

- [Workflow Overview](../README.md) - All workflow types
- [Architecture](../../developer-guide/architecture/README.md) - System design
- [Testing Guide](../../developer-guide/testing-guide.md) - Testing strategies
- [API Reference](../../reference/api-reference.md) - REST API docs

## 🎓 Tutorial Mode

New to the system? Try tutorial mode for guided learning:

```bash
python demos/advanced/mvp_incremental_demo.py --tutorial
```

This provides:
- Step-by-step explanations
- Interactive prompts
- Learning tips
- Best practices

## 🆘 Need Help?

1. Check the [User Guide](user-guide.md) for detailed information
2. See [Quick Reference](quick-reference.md) for command options
3. Review [Troubleshooting](user-guide.md#troubleshooting) section
4. Explore [Examples](../../mvp_incremental/examples/README.md)

[← Back to Workflows](../README.md) | [← Back to Docs](../../README.md)