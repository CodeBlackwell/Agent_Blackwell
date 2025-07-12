# Workflow Visual Guide 🎨

## Workflow Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator System                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     TDD      │  │     Full     │  │ Incremental  │      │
│  │  Workflow    │  │  Workflow    │  │  Workflow    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │     MVP      │  │   MVP TDD    │  │  Individual  │      │
│  │ Incremental  │  │   Workflow   │  │   Workflow   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │                   Agent Pool                        │      │
│  │  Planner • Designer • Coder • Test Writer         │      │
│  │  Executor • Reviewer • Validator                  │      │
│  └────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Flow Patterns

### 🧪 TDD Workflow
```
Requirements
    ↓
[Planning] → [Test Writing] → [Implementation] → [Testing] → [Review]
                    ↑                    ↓
                    └────── Fail ────────┘
```

### 📋 Full Workflow
```
Requirements
    ↓
[Planning] → [Design] → [Implementation] → [Test Writing] → [Testing] → [Review]
```

### 🔄 Incremental Workflow
```
Requirements
    ↓
[Planning] → [Design] → [Feature Orchestrator]
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
              [Feature 1]         [Feature 2] ...
              ↓         ↓         ↓         ↓
         [Implement] [Validate] [Implement] [Validate]
                    ↓                   ↓
                    └─────────┬─────────┘
                              ↓
                          [Review]
```

### 🎯 MVP Incremental Workflow
```
Requirements
    ↓
[Expansion] → [Planning] → [10 Phases]
                               │
    ┌──────────────────────────┴──────────────────────────┐
    │ 1.Foundation  2.Entities  3.Storage  4.Logic  5.API │
    │ 6.Integration 7.Errors    8.Tests    9.Docs  10.Deploy│
    └──────────────────────────┬──────────────────────────┘
                               ↓
                           [Review]
```

### 🧪🎯 MVP TDD Workflow
```
Requirements
    ↓
[Planning] → [Feature Extraction]
                    │
            ┌───────┴────────┐
            ↓                ↓
    [Feature Tests]    [Feature Code]
    (Red Phase)        (Green Phase)
            ↓                ↓
            └───────┬────────┘
                    ↓
              [Refactor]
            (Yellow Phase)
                    ↓
            [Integration]
```

### 👤 Individual Workflow
```
Requirements
    ↓
[Selected Phase Only]
    │
    ├─→ Planning
    ├─→ Design
    ├─→ Implementation
    ├─→ Test Writing
    └─→ Review
```

## Workflow Selection Flowchart

```
                    START
                      │
                      ↓
            ┌─────────────────┐
            │ Need tests first?│
            └────────┬────────┘
                Yes  │  No
        ┌───────────┴────────────┐
        ↓                        ↓
┌───────────────┐        ┌───────────────┐
│Quality Critical?│       │  Need Speed?  │
└───────┬───────┘        └───────┬───────┘
   Yes  │  No                Yes │  No
    ↓   ↓                     ↓  ↓
  TDD  MVP TDD          ┌────────┴───────┐
                        │  Building MVP?  │
                        └────────┬────────┘
                           Yes   │   No
                            ↓    ↓
                    MVP Incremental Individual
                                      │
                                      ↓
                              ┌───────────────┐
                              │Complex Project?│
                              └───────┬───────┘
                                 Yes  │  No
                                  ↓   ↓
                            Incremental Full
```

## Workflow Characteristics Radar Chart

```
TDD Workflow:
Quality     ████████████████████ 100%
Speed       ████░░░░░░░░░░░░░░░░  20%
Flexibility ████████░░░░░░░░░░░░  40%
Testing     ████████████████████ 100%
Complexity  ████████████░░░░░░░░  60%

Full Workflow:
Quality     ████████████████░░░░  80%
Speed       ████████████░░░░░░░░  60%
Flexibility ████████████░░░░░░░░  60%
Testing     ████████████████░░░░  80%
Complexity  ████████░░░░░░░░░░░░  40%

Incremental:
Quality     ████████████████░░░░  80%
Speed       ████████████░░░░░░░░  60%
Flexibility ████████████████░░░░  80%
Testing     ████████████░░░░░░░░  60%
Complexity  ████████████████░░░░  80%

MVP Incremental:
Quality     ████████████░░░░░░░░  60%
Speed       ████████████████████ 100%
Flexibility ████████████░░░░░░░░  60%
Testing     ████████░░░░░░░░░░░░  40%
Complexity  ████████████░░░░░░░░  60%

MVP TDD:
Quality     ████████████████████  90%
Speed       ████████████████░░░░  80%
Flexibility ████████████░░░░░░░░  60%
Testing     ████████████████████  90%
Complexity  ████████████████░░░░  80%

Individual:
Quality     ████████░░░░░░░░░░░░  40%
Speed       ████████████████████ 100%
Flexibility ████████████████████ 100%
Testing     ████░░░░░░░░░░░░░░░░  20%
Complexity  ████░░░░░░░░░░░░░░░░  20%
```

## Workflow Timeline Comparison

```
Time (minutes) →
0    10   20   30   40   50   60   70   80   90   100  110  120

Individual:   ■■■■■
TDD:          ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
Full:         ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
Incremental:  ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MVP Inc:      ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MVP TDD:      ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

■ = Active development time
```

## Agent Utilization by Workflow

```
                Planner Designer Coder TestWriter Executor Reviewer
TDD:              ■■■     ■■      ■■■■■   ■■■■■     ■■■■     ■■
Full:             ■■■     ■■■■    ■■■■■   ■■■       ■■■      ■■
Incremental:      ■■      ■■■     ■■■■■   ■         ■■■■     ■■
MVP Incremental:  ■■      ■■      ■■■■■   ■■        ■■■      ■
MVP TDD:          ■■      ■■      ■■■■    ■■■■■     ■■■■     ■■
Individual:       ■       ■       ■       ■         ■        ■

■ = Relative usage (more blocks = higher usage)
```

## Quick Decision Matrix

| Your Situation | Recommended Workflow |
|----------------|---------------------|
| 🚨 "I need it yesterday!" | Individual |
| 🏃 "I need an MVP ASAP" | MVP Incremental |
| 🎯 "Quality matters but I'm in a hurry" | MVP TDD |
| 🏗️ "This is a big, complex project" | Incremental |
| 🏛️ "This is a standard business app" | Full |
| 🔬 "Bugs would be catastrophic" | TDD |
| 🧪 "I want to learn TDD properly" | Enhanced TDD |
| 🔧 "I just need one thing done" | Individual |

## Workflow Combinations

You can combine workflows for different project phases:

```
Project Lifecycle:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Individual  │ →  │     MVP     │ →  │ Incremental │ →  │     TDD     │
│ (Planning)  │    │(Prototype)  │    │  (Scaling)  │    │(Maintenance)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Performance Tips by Workflow

**TDD**: Enable test caching to speed up red-green cycles
**Full**: Use parallel agent execution for independent phases
**Incremental**: Configure optimal retry strategies
**MVP**: Enable phase parallelization where possible
**Individual**: Chain multiple individual runs for custom flows