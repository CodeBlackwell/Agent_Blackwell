# MVP Incremental Workflow - User Guide

## 🌟 Overview

The MVP Incremental Workflow is a beginner-friendly tool that helps you create production-ready software using AI agents. This sophisticated system breaks down your requirements and builds your application step-by-step, with validation and testing at each phase.

### What Does It Do?

This workflow orchestrates a team of specialized AI agents to:
- 📋 Analyze your requirements and create a development plan
- 🏗️ Design the architecture and structure  
- 💻 Implement features incrementally with validation
- 🧪 Write and run comprehensive tests
- 🔍 Review code for quality and best practices
- ✅ Ensure all components work together seamlessly

## 🚀 Quick Start

### Prerequisites

Before running the workflow, ensure you have:
- Python 3.8 or higher
- UV package manager (`pip install uv`)
- A virtual environment set up
- All dependencies installed (`uv pip install -r requirements.txt`)

### First-Time Setup

1. **Clone the repository** (if not already done)
2. **Set up the environment:**
   ```bash
   # Create virtual environment
   uv venv
   
   # Activate it
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

3. **Start the orchestrator server** (in a separate terminal):
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

4. **Run the demo:**
   ```bash
   python demos/advanced/mvp_incremental_demo.py
   ```

## 🎯 Usage Modes

### 1. Interactive Mode (Recommended for Beginners)

Simply run without arguments:
```bash
python demos/advanced/mvp_incremental_demo.py
```

This mode provides:
- Step-by-step guidance
- Detailed explanations for each option
- Tutorial mode for first-time users
- Pre-flight checks to ensure everything is ready
- Interactive configuration options

### 2. CLI Mode (For Experienced Users)

Use command-line arguments for direct execution:

#### Using Presets
```bash
# Simple calculator example
python demos/advanced/mvp_incremental_demo.py --preset calculator

# TODO API with all phases enabled
python demos/advanced/mvp_incremental_demo.py --preset todo-api --all-phases

# Authentication system with custom configuration
python demos/advanced/mvp_incremental_demo.py --preset auth-system --tests --no-integration
```

#### Custom Requirements
```bash
# Basic custom project
python demos/advanced/mvp_incremental_demo.py --requirements "Create a web scraper for news articles"

# Custom project with testing enabled
python demos/advanced/mvp_incremental_demo.py --requirements "Build a chat application" --tests
```

### 3. Tutorial Mode

Perfect for absolute beginners:
1. Choose option 3 in interactive mode
2. Follow the guided walkthrough
3. Learn about each component as you go

## 📚 Available Presets

### Calculator (Beginner)
- **Time:** 2-3 minutes
- **Description:** Basic Python calculator with mathematical operations
- **Features:** Add, subtract, multiply, divide, square root
- **Includes:** Unit tests, error handling

### TODO API (Intermediate)
- **Time:** 5-7 minutes
- **Description:** RESTful API using FastAPI
- **Features:** CRUD operations, pagination, validation
- **Includes:** API documentation, comprehensive tests

### Authentication System (Advanced)
- **Time:** 10-15 minutes
- **Description:** Complete auth system with JWT tokens
- **Features:** Registration, login, password reset, RBAC
- **Includes:** Security best practices, email verification

### CSV File Processor (Intermediate)
- **Time:** 5-8 minutes
- **Description:** Tool for processing and analyzing CSV files
- **Features:** Validation, filtering, aggregation, streaming
- **Includes:** Error handling, multiple export formats

## ⚙️ Configuration Options

### Phase 9: Test Execution
- **What it does:** Runs unit tests after each feature implementation
- **Benefits:** Catches bugs early, ensures feature correctness
- **Time impact:** Adds ~20% to execution time
- **Recommended for:** Production code, APIs, complex logic

### Phase 10: Integration Verification
- **What it does:** Runs full test suite and integration tests
- **Benefits:** Verifies all components work together
- **Time impact:** Adds ~30% to execution time
- **Recommended for:** Multi-component systems, full applications

## 🛠️ Command-Line Options

### Basic Options
- `--preset <name>`: Use a pre-configured example
- `--requirements <text>`: Specify custom requirements
- `--help`: Show comprehensive help message

### Phase Configuration
- `--all-phases`: Enable both Phase 9 and 10
- `--tests`: Enable Phase 9 (test execution)
- `--no-tests`: Disable Phase 9
- `--integration`: Enable Phase 10 (integration verification)
- `--no-integration`: Disable Phase 10

### Utility Options
- `--dry-run`: Preview what would happen without executing
- `--verbose`: Show detailed output during execution
- `--save-output`: Save results to file
- `--skip-checks`: Skip preflight checks (not recommended)
- `--list-presets`: Display all available presets with details

## 📁 Output Structure

Generated code is saved in the `generated/` directory:

```
generated/
└── 20250107_143022_Calculator-App/
    ├── main.py              # Main application file
    ├── requirements.txt     # Python dependencies
    ├── test_*.py           # Test files
    ├── README.md           # Project documentation
    └── COMPLETION_REPORT.md # Detailed workflow report
```

## 🔍 Pre-flight Checks

The tool automatically verifies:

1. **Python Version**: Ensures Python 3.8+ is installed
2. **Virtual Environment**: Checks if running in a virtual environment
3. **Dependencies**: Validates all required packages are installed
4. **Orchestrator Server**: Confirms the server is running on port 8080

If any check fails, you'll see:
- ❌ Clear indication of what failed
- 📌 Specific instructions to fix the issue
- 💡 Tips for troubleshooting

## 🎓 Tips for Success

### For Beginners
1. Start with Tutorial Mode to understand the system
2. Use the "calculator" preset for your first run
3. Enable Phase 9 to see automatic test generation
4. Read the generated COMPLETION_REPORT.md for insights

### For Custom Requirements
1. Be specific and detailed in your requirements
2. List features as numbered items
3. Mention specific technologies or frameworks
4. Include any constraints or preferences

### Example of Good Requirements
```
Create a task management API that:
1. Uses FastAPI framework
2. Stores tasks in SQLite database
3. Supports task categories and priorities
4. Includes due date tracking
5. Provides filtering and sorting options
6. Returns paginated results
7. Includes input validation
8. Has comprehensive error handling
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### "Orchestrator server not running"
**Solution:**
1. Open a new terminal
2. Run: `python orchestrator/orchestrator_agent.py`
3. Keep it running while using the demo

#### "Missing dependencies"
**Solution:**
1. Ensure virtual environment is activated
2. Run: `uv pip install -r requirements.txt`

#### "Workflow execution failed"
**Solutions:**
1. Check if orchestrator server is still running
2. Try a simpler example first
3. Review logs in the `logs/` directory
4. Use `--verbose` flag for more details

### Getting Help
- Use `--help` for command-line assistance
- Check generated `COMPLETION_REPORT.md` for workflow details
- Review logs in `logs/` directory for debugging
- Report issues at: https://github.com/anthropics/claude-code/issues

## 📊 Understanding the Workflow

### The 10 Phases Explained

1. **Planning**: Analyzes requirements and creates project structure
2. **Design**: Develops architecture and database schemas
3. **Feature Parsing**: Breaks design into implementable features
4. **Implementation**: Builds features incrementally
5. **Validation**: Tests each feature as it's built
6. **Error Analysis**: Identifies and fixes issues
7. **Progress Tracking**: Monitors development progress
8. **Review**: Ensures code quality and best practices
9. **Test Execution** (Optional): Runs comprehensive tests
10. **Integration Verification** (Optional): Validates full system

### Time Estimates

Base execution times (without optional phases):
- Simple projects: 2-3 minutes
- Medium complexity: 5-7 minutes
- Complex systems: 10-15 minutes

Add approximately:
- +20% for Phase 9 (Test Execution)
- +30% for Phase 10 (Integration Verification)

## 🎯 Best Practices

### 1. Start Simple
Begin with the calculator preset to understand the workflow before attempting complex projects.

### 2. Use Appropriate Phases
- Enable Phase 9 for production code
- Enable Phase 10 for multi-component systems
- Skip both for quick prototypes

### 3. Review Generated Code
Always review the generated code to:
- Understand the implementation
- Learn from AI-generated patterns
- Customize for your specific needs

### 4. Iterate and Improve
Use the generated code as a starting point and enhance it with your domain knowledge.

## 📋 Example Workflows

### Quick Prototype
```bash
python demos/advanced/mvp_incremental_demo.py --preset calculator --no-tests --no-integration
```

### Production API
```bash
python demos/advanced/mvp_incremental_demo.py --preset todo-api --all-phases --save-output
```

### Custom Project with Preview
```bash
# First, preview what will happen
python demos/advanced/mvp_incremental_demo.py --requirements "Create a blog engine" --dry-run

# Then execute if satisfied
python demos/advanced/mvp_incremental_demo.py --requirements "Create a blog engine" --tests
```

## 🚀 Advanced Usage

### Batch Processing
Create a script to run multiple projects:
```bash
#!/bin/bash
for preset in calculator todo-api file-processor; do
    python demos/advanced/mvp_incremental_demo.py --preset $preset --save-output
done
```

### Integration with CI/CD
The tool can be integrated into automated pipelines:
```bash
# In your CI script
python demos/advanced/mvp_incremental_demo.py \
    --requirements "$PROJECT_REQUIREMENTS" \
    --all-phases \
    --save-output \
    --skip-checks
```

## 📝 Next Steps After Generation

1. **Navigate to Generated Code**
   ```bash
   cd generated/[timestamp]_[App-Name]
   ```

2. **Review the Structure**
   ```bash
   ls -la
   cat README.md
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Tests** (if generated)
   ```bash
   pytest
   ```

5. **Start the Application**
   ```bash
   python main.py
   # or for APIs: uvicorn main:app --reload
   ```

## 📍 Output Locations

### Generated Code
```
generated/[timestamp]_[App-Name]/
├── [your_module].py      # Main application files
├── test_*.py            # Test files (if Phase 9 enabled)
├── requirements.txt     # Python dependencies
├── README.md           # Generated documentation with review summary
├── session_metadata.json # Workflow execution metadata
└── COMPLETION_REPORT.md # Detailed report (if Phase 10 enabled)
```

### Session Logs
```
logs/demo_[session_id]_[timestamp]/
├── workflow.log        # Main workflow execution log
├── agents.log         # Agent interactions log
├── validation.log     # Code validation log
└── workflow_trace.json # Complete execution trace
```

### Demo Results
```
demo_outputs/
└── mvp_demo_[timestamp]_summary.json  # Summary of the demo run
```

## 🎉 Conclusion

The MVP Incremental Workflow makes it easy to generate high-quality, production-ready code using AI agents. Whether you're a beginner exploring AI-assisted development or an experienced developer looking to accelerate your workflow, this tool provides the flexibility and guidance you need.

Remember: The generated code is a starting point. Feel free to modify, extend, and improve it to meet your specific requirements!

---

[← Back to MVP Incremental](README.md) | [← Back to Workflows](../README.md) | [← Back to Docs](../../README.md)