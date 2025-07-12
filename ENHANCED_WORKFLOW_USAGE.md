# Enhanced Full Workflow - Quick Usage Guide

The enhanced_full workflow is now integrated into run.py and can be used in multiple ways:

## 1. Interactive Mode
```bash
python run.py
# Select "enhanced_full" from the menu (option 3)
# Enter your requirements
```

## 2. Command Line Mode
```bash
# Basic usage
python run.py workflow enhanced_full --task "Build a Hello World REST API"

# With debug logging
python run.py --debug workflow enhanced_full --task "Create a calculator API"

# Skip orchestrator auto-start (if managing manually)
python run.py --no-orchestrator workflow enhanced_full --task "Build a web scraper"
```

## 3. What Makes It Enhanced?

The enhanced_full workflow includes these advanced features:

- **🔄 Retry Logic**: Automatic retries with exponential backoff
- **💾 Intelligent Caching**: 50-80% faster on repeated runs
- **📊 Performance Monitoring**: Detailed metrics and optimization suggestions
- **↩️ Rollback Capabilities**: Restore from checkpoints on failure
- **🔗 Context Enrichment**: Better agent coordination
- **⚙️ Fully Configurable**: Customize timeouts, retries, and features

## 4. Example Run

```bash
# Start the orchestrator (if not using auto-start)
python orchestrator/orchestrator_agent.py

# In another terminal, run the enhanced workflow
python run.py workflow enhanced_full --task "Create a Python package for data validation with:
- Type checking for common data types
- Custom validation rules
- Error reporting
- Unit tests"
```

## 5. What to Expect

1. **First Run**: Full execution with all phases
   - Planning phase
   - Design phase
   - Implementation phase (using incremental coder)
   - Review phase
   - Performance metrics displayed

2. **Subsequent Runs**: Faster execution due to caching
   - Cached phases show "📦 Using cached result"
   - Only changed phases re-execute
   - Cache hit rate displayed in metrics

## 6. Performance Metrics

After execution, you'll see:
```
📈 Performance Metrics:
  Total duration: 25.43s
  Phase count: 4
  Error count: 0
  Retry count: 1
  Cache hit rate: 75.0%

💡 Optimization Suggestions:
  - Phase 'designer' averages 12.3s - consider optimization
```

## 7. Workflow Reports

Reports are saved in:
- `workflow_reports/workflow_enhanced_full_[timestamp].json`
- `workflow_reports/execution_report.json` (latest)
- `workflow_reports/execution_report.csv` (latest)

## 8. When to Use Enhanced Full

**Use enhanced_full when:**
- Building production applications
- Need reliability with automatic retries
- Want performance optimization
- Require detailed execution metrics
- Working on complex projects

**Use standard full when:**
- Quick prototypes
- Simple projects
- Learning the system
- Minimal overhead needed

## 9. Troubleshooting

If you encounter issues:
1. Ensure orchestrator is running: `python orchestrator/orchestrator_agent.py`
2. Check port 8080 is not blocked
3. Use `--debug` flag for detailed logs
4. Check `workflow_reports/` for execution details

The enhanced workflow provides enterprise-grade reliability while maintaining the simplicity of the standard workflow interface!