# MVP Incremental Demo - Quick Reference

## 🚀 Quick Commands

### Interactive Mode (Recommended)
```bash
python demos/advanced/mvp_incremental_demo.py
```

### Common Use Cases

#### Try a Simple Example
```bash
python demos/advanced/mvp_incremental_demo.py --preset calculator
```

#### Build a TODO API with Tests
```bash
python demos/advanced/mvp_incremental_demo.py --preset todo-api --tests
```

#### Custom Project with All Features
```bash
python demos/advanced/mvp_incremental_demo.py --requirements "Your project description" --all-phases
```

#### Preview Without Running
```bash
python demos/advanced/mvp_incremental_demo.py --preset auth-system --dry-run
```

## 📋 Available Presets

| Preset | Difficulty | Time | Command |
|--------|-----------|------|---------|
| calculator | Beginner | 2-3 min | `--preset calculator` |
| todo-api | Intermediate | 5-7 min | `--preset todo-api` |
| auth-system | Advanced | 10-15 min | `--preset auth-system` |
| file-processor | Intermediate | 5-8 min | `--preset file-processor` |

## ⚙️ Phase Options

| Option | Effect | Use When |
|--------|--------|----------|
| `--tests` | Enable Phase 9 | You want unit tests |
| `--integration` | Enable Phase 10 | You need integration tests |
| `--all-phases` | Enable both 9 & 10 | Production-ready code |
| `--no-tests` | Disable Phase 9 | Quick prototypes |
| `--no-integration` | Disable Phase 10 | Simple projects |

## 🛠️ Utility Options

| Option | Purpose |
|--------|---------|
| `--dry-run` | Preview without executing |
| `--verbose` | Show detailed output |
| `--save-output` | Save results to file |
| `--skip-checks` | Skip preflight checks |
| `--list-presets` | Show all presets |
| `--help` | Get detailed help |

## 📁 Output Location

Generated code appears in:
```
generated/app_generated_[timestamp]/
```

## 🔧 Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`uv pip install -r requirements.txt`)
- [ ] Orchestrator running (`python orchestrator/orchestrator_agent.py`)

## 💡 Pro Tips

1. **First time?** Use interactive mode
2. **In a hurry?** Use `--preset calculator`
3. **Need tests?** Add `--tests`
4. **Complex project?** Use `--all-phases`
5. **Debugging?** Add `--verbose`

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Server not running" | Start orchestrator: `python orchestrator/orchestrator_agent.py` |
| "Missing dependencies" | Install: `uv pip install -r requirements.txt` |
| "Not in venv" | Activate: `source .venv/bin/activate` |
| "Execution failed" | Check logs in `logs/` directory |

## 📝 Custom Requirements Template

```
Create a [type of application] that:
1. [Primary feature]
2. [Secondary feature]
3. [Data storage requirement]
4. [API/Interface requirement]
5. [Testing requirement]
6. [Additional features...]
```

## 🎯 Example Commands

```bash
# Beginner: Simple calculator with tests
python demos/advanced/mvp_incremental_demo.py --preset calculator

# Intermediate: API with full testing
python demos/advanced/mvp_incremental_demo.py --preset todo-api --all-phases

# Advanced: Custom project with preview
python demos/advanced/mvp_incremental_demo.py \
  --requirements "Create a blog engine with user auth" \
  --dry-run

# Production: Full workflow with output
python demos/advanced/mvp_incremental_demo.py \
  --preset auth-system \
  --all-phases \
  --save-output \
  --verbose
```

---

*Need more help? Run `python demos/advanced/mvp_incremental_demo.py --help` or check the full guide.*

---

[← Back to MVP Incremental](../mvp-incremental/) | [← Back to Workflows](../) | [← Back to Docs](../../)