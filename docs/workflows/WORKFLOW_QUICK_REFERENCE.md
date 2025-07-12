# Workflow Quick Reference Card

## 🚀 Available Workflows

### 1. **TDD** - Test-Driven Development
```bash
python run.py workflow tdd --task "Your task"
```
- ✅ Tests written first
- ✅ High quality code
- ✅ Great test coverage
- ⏱️ Slower development
- 🎯 Use for: Critical systems, APIs, financial software

### 2. **Full** - Traditional Development
```bash
python run.py workflow full --task "Your task"
```
- ✅ Complete development cycle
- ✅ Detailed design phase
- ✅ Comprehensive approach
- ⏱️ Moderate speed
- 🎯 Use for: Standard web apps, well-defined projects

### 3. **Incremental** - Feature-by-Feature
```bash
python run.py workflow incremental --task "Your task"
```
- ✅ Builds features one at a time
- ✅ Validates each feature
- ✅ Handles dependencies
- ⏱️ Good for large projects
- 🎯 Use for: Complex systems, large teams

### 4. **MVP Incremental** - Rapid MVP Development
```bash
python run.py workflow mvp_incremental --task "Your task"
```
- ✅ 10 structured phases
- ✅ Fast time-to-market
- ✅ Progressive enhancement
- ⏱️ Optimized for speed
- 🎯 Use for: Startups, prototypes, POCs

### 5. **MVP TDD** - Quality MVP Development
```bash
python run.py workflow mvp_tdd --task "Your task"
```
- ✅ Combines MVP + TDD
- ✅ Fast but reliable
- ✅ Test coverage included
- ⏱️ Balanced approach
- 🎯 Use for: Quality-critical MVPs, API products

### 6. **Individual** - Single Phase Execution
```bash
# Just planning
python run.py workflow planning --task "Your task"

# Just design
python run.py workflow design --task "Your task"

# Just implementation
python run.py workflow implementation --task "Your task"

# Just test writing
python run.py workflow test_writing --task "Your task"

# Just review
python run.py workflow review --task "Your task"
```
- ✅ Execute one phase only
- ✅ Maximum flexibility
- ✅ Quick iterations
- ⏱️ Fastest option
- 🎯 Use for: Quick tasks, debugging, specific needs

## 🎯 Decision Tree

```
Need tests first? 
├─ Yes → Quality critical?
│        ├─ Yes → TDD Workflow
│        └─ No → MVP TDD Workflow
└─ No → Need speed?
         ├─ Yes → Building MVP?
         │        ├─ Yes → MVP Incremental
         │        └─ No → Individual Workflow
         └─ No → Complex project?
                  ├─ Yes → Incremental Workflow
                  └─ No → Full Workflow
```

## 📊 Comparison Table

| Workflow | Development Time | Code Quality | Test Coverage | Best For |
|----------|-----------------|--------------|---------------|----------|
| TDD | 🕐🕐🕐🕐 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Critical systems |
| Full | 🕐🕐🕐 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Standard projects |
| Incremental | 🕐🕐🕐 | ⭐⭐⭐⭐ | ⭐⭐⭐ | Large projects |
| MVP Incremental | 🕐🕐 | ⭐⭐⭐ | ⭐⭐ | Quick MVPs |
| MVP TDD | 🕐🕐🕐 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Quality MVPs |
| Individual | 🕐 | ⭐⭐ | ⭐ | Specific tasks |

## 💡 Pro Tips

1. **Start with Individual** workflow to test your requirements
2. **Use Incremental** for projects with 5+ features
3. **Choose TDD** when bugs are expensive
4. **Pick MVP** workflows for rapid iteration
5. **Combine workflows** - use Individual for planning, then Full for implementation

## 🔧 Advanced Usage

### With specific team members:
```python
input_data = CodingTeamInput(
    requirements="Your requirements",
    workflow_type="incremental",
    team_members=[
        TeamMember.planner,
        TeamMember.designer,
        TeamMember.coder,
        TeamMember.reviewer
    ]
)
```

### With custom configuration:
```python
# For incremental workflow
max_retries = 5
stagnation_threshold = 0.8

# For MVP workflow
parallel_phases = True
phase_timeout = 3600
```

## 📚 Detailed Guides

- Full overview: `WORKFLOW_OVERVIEW.md`
- Incremental guide: `INCREMENTAL_WORKFLOW_GUIDE.md`
- MVP guide: `docs/workflows/mvp-incremental/`
- Examples: `examples/` directory

## 🚦 Quick Start

1. **Simple task?** → Individual workflow
2. **Building API?** → TDD workflow
3. **Complex system?** → Incremental workflow
4. **Need MVP?** → MVP Incremental workflow
5. **Quality MVP?** → MVP TDD workflow
6. **Standard app?** → Full workflow